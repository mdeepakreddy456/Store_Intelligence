from collections import defaultdict
import time
from typing import Dict, List, Tuple


class VisitorTracker:
    """
    Handles:
    - entry / exit detection
    - re-entry tracking and detection
    - dwell time tracking in zones
    - session counting
    - cross-camera Re-ID
    - billing queue abandonment
    """

    def __init__(self):

        # track previous y positions
        self.track_positions = {}

        # last seen time
        self.last_seen = {}

        # re-entry memory
        self.exited_visitors = {}

        # zone tracking
        self.current_zone = {}

        # dwell tracking
        self.zone_entry_time = {}

        # session sequence
        self.session_seq = defaultdict(int)
        
        # Cross-camera Re-ID: visitor ID to feature vector
        self.visitor_features: Dict[str, Dict] = {}
        
        # Billing queue tracking
        self.billing_queue_join_time: Dict[str, float] = {}
        self.billing_queue_abandoned: set = set()
        
        # Re-ID confidence threshold
        self.reid_confidence_threshold = 0.6
        
        # Queue abandonment threshold (seconds)
        self.queue_abandon_threshold = 120  # 2 minutes

    def get_visitor_id(self, track_id):
        return f"VIS_{track_id}"

    def update_position(self, track_id, center_y):
        """
        Save current position for entry/exit detection
        """
        previous = self.track_positions.get(track_id)

        self.track_positions[track_id] = center_y
        self.last_seen[track_id] = time.time()

        return previous

    def detect_entry_exit(
        self,
        track_id,
        previous_y,
        current_y,
        line_y,
    ):
        """
        Detect entry, exit, and re-entry events
        """

        if previous_y is None:
            return None

        visitor_id = self.get_visitor_id(track_id)

        # ENTRY
        if previous_y < line_y and current_y >= line_y:

            # re-entry check
            if visitor_id in self.exited_visitors:

                last_exit = self.exited_visitors[visitor_id]

                if time.time() - last_exit < 600:  # 10 minute window
                    return "REENTRY"

            return "ENTRY"

        # EXIT
        elif previous_y > line_y and current_y <= line_y:

            self.exited_visitors[visitor_id] = time.time()

            return "EXIT"

        return None

    def enter_zone(self, visitor_id, zone_name):
        """
        Track zone entry and update session sequence
        """

        current_zone = self.current_zone.get(visitor_id)

        if current_zone != zone_name:

            self.current_zone[visitor_id] = zone_name
            self.zone_entry_time[visitor_id] = time.time()

            self.session_seq[visitor_id] += 1

            return True

        return False

    def exit_zone(self, visitor_id):

        if visitor_id in self.current_zone:

            zone = self.current_zone.pop(visitor_id)

            start_time = self.zone_entry_time.pop(visitor_id)

            dwell_ms = int(
                (time.time() - start_time) * 1000
            )

            return zone, dwell_ms

        return None, 0

    def should_emit_dwell(
        self,
        visitor_id,
        seconds=30,
    ):
        """
        Emit dwell every 30s
        """

        if visitor_id not in self.zone_entry_time:
            return False

        elapsed = (
            time.time()
            - self.zone_entry_time[visitor_id]
        )

        return elapsed >= seconds

    def get_session_seq(self, visitor_id):
        return self.session_seq[visitor_id]

    # ============================================
    # Cross-Camera Re-ID Methods
    # ============================================

    def extract_features(
        self,
        visitor_id: str,
        bbox: Tuple[float, float, float, float],
        confidence: float,
        camera_id: str
    ):
        """
        Extract and store feature vector for cross-camera Re-ID.
        Uses bounding box dimensions and camera context as features.
        """
        x1, y1, x2, y2 = bbox
        bbox_height = y2 - y1
        bbox_width = x2 - x1

        feature = {
            "camera_id": camera_id,
            "bbox_height": bbox_height,
            "bbox_width": bbox_width,
            "confidence": confidence,
            "timestamp": time.time(),
            "aspect_ratio": bbox_width / (bbox_height + 1e-6)
        }

        self.visitor_features[visitor_id] = feature

    def match_across_cameras(
        self,
        bbox: Tuple[float, float, float, float],
        confidence: float,
        camera_id: str,
        time_window: float = 30.0
    ) -> Tuple[str, float]:
        """
        Attempt to match person across cameras using feature similarity.
        
        Returns:
            (matched_visitor_id, match_confidence)
        """
        x1, y1, x2, y2 = bbox
        bbox_height = y2 - y1
        bbox_width = x2 - x1
        current_aspect_ratio = bbox_width / (bbox_height + 1e-6)

        best_match = None
        best_score = 0

        current_time = time.time()

        for visitor_id, feature in self.visitor_features.items():
            # Time-based filtering
            if current_time - feature["timestamp"] > time_window:
                continue

            # Same camera - skip
            if feature["camera_id"] == camera_id:
                continue

            # Calculate feature similarity
            aspect_ratio_diff = abs(
                current_aspect_ratio - feature["aspect_ratio"]
            )

            height_sim = 1.0 - min(
                abs(bbox_height - feature["bbox_height"]) /
                (feature["bbox_height"] + 1e-6),
                1.0
            )

            conf_sim = min(confidence, feature["confidence"])

            # Combined score
            match_score = (height_sim + conf_sim) / 2.0

            if match_score > best_score:
                best_score = match_score
                best_match = visitor_id

        if best_score > self.reid_confidence_threshold:
            return best_match, best_score
        else:
            return None, 0.0

    # ============================================
    # Billing Queue Abandonment Methods
    # ============================================

    def track_billing_queue_join(
        self,
        visitor_id: str
    ):
        """
        Record when visitor joins billing queue
        """
        if visitor_id not in self.billing_queue_join_time:
            self.billing_queue_join_time[visitor_id] = time.time()

    def check_queue_abandonment(
        self,
        visitor_id: str
    ) -> bool:
        """
        Check if visitor abandoned queue (joined but exited without conversion).
        
        Returns:
            True if visitor abandoned queue
        """
        if visitor_id not in self.billing_queue_join_time:
            return False

        if visitor_id in self.billing_queue_abandoned:
            return False

        join_time = self.billing_queue_join_time[visitor_id]
        time_in_queue = time.time() - join_time

        # Mark as abandoned if in queue > threshold without exiting properly
        if time_in_queue > self.queue_abandon_threshold:
            self.billing_queue_abandoned.add(visitor_id)
            return True

        return False

    def clear_billing_queue_join(
        self,
        visitor_id: str
    ):
        """
        Clear billing queue join time (visitor proceeded or exited)
        """
        if visitor_id in self.billing_queue_join_time:
            del self.billing_queue_join_time[visitor_id]