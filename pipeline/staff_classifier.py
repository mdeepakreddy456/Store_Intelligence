"""
Staff vs Customer classification logic.

Implements heuristics and models to differentiate staff from customers.
Uses zone behavior, movement patterns, and camera context.
"""

from typing import List, Tuple


class StaffClassifier:
    """Classifies persons as staff or customers based on contextual signals."""

    def __init__(self):
        # Staff cameras have higher baseline staff probability
        self.staff_camera_multiplier = {
            "CAM_STAFF_01": 0.95,      # Staff area camera
            "CAM_ENTRY_01": 0.05,      # Entry camera (mostly customers)
            "CAM_MAIN_01": 0.15,       # Main floor (mostly customers)
            "CAM_MAIN_02": 0.15,
            "CAM_BILLING_01": 0.20,    # Billing area (some staff)
        }

    def classify_person(
        self,
        camera_id: str,
        bbox: Tuple[float, float, float, float],
        confidence: float,
        event_type: str = None,
        zone_id: str = None,
        previous_events: List[str] = None
    ) -> bool:
        """
        Classify a person as staff (True) or customer (False).

        Args:
            camera_id: Camera where person detected
            bbox: Bounding box coordinates (x1, y1, x2, y2)
            confidence: Detection confidence
            event_type: Current event type (ENTRY, EXIT, etc.)
            zone_id: Zone where person detected
            previous_events: Historical events for this visitor

        Returns:
            True if staff, False if customer
        """

        # Rule 1: Camera context
        staff_prob = self.staff_camera_multiplier.get(camera_id, 0.1)

        # Rule 2: Billing area - lower staff probability (mostly customers)
        if zone_id == "BILLING_QUEUE":
            staff_prob *= 0.3

        # Rule 3: Entry/Exit events - mostly customers
        if event_type in ["ENTRY", "EXIT", "REENTRY"]:
            staff_prob *= 0.2

        # Rule 4: Staff camera - high probability
        if camera_id == "CAM_STAFF_01":
            staff_prob = 0.95

        # Rule 5: Recurring presence in main floor zones
        # (staff tend to move through zones more frequently)
        if previous_events and len(previous_events) > 10:
            if event_type in ["ZONE_ENTER", "ZONE_EXIT"]:
                staff_prob += 0.15

        # Threshold decision
        return staff_prob > 0.5

    def detect_group_entry(
        self,
        detected_ids: List[int],
        frame_width: int,
        frame_height: int,
        entry_line_y: int,
        proximity_threshold: int = 100,
        time_window_frames: int = 5
    ) -> List[Tuple[List[int], str]]:
        """
        Detect group entries (multiple people entering together).

        Args:
            detected_ids: List of track IDs in current frame
            frame_width: Frame width
            frame_height: Frame height
            entry_line_y: Y-coordinate of entry line
            proximity_threshold: Distance threshold for grouping (pixels)
            time_window_frames: Frames to consider as "together"

        Returns:
            List of (group_ids, group_type) tuples
        """
        groups = []

        if len(detected_ids) < 2:
            return groups

        # Detect if multiple people close together
        if len(detected_ids) >= 3:
            groups.append((detected_ids, "LARGE_GROUP"))
        elif len(detected_ids) == 2:
            groups.append((detected_ids, "PAIR"))

        return groups


class EdgeCaseHandler:
    """Handles edge cases in detection."""

    @staticmethod
    def handle_empty_store(
        frame_count: int,
        detection_count: int,
        empty_threshold: int = 10
    ) -> bool:
        """Check if store is empty (no detections)."""
        return detection_count == 0

    @staticmethod
    def handle_crowded_billing(
        queue_depth: int,
        crowding_threshold: int = 5
    ) -> bool:
        """Detect crowded billing area."""
        return queue_depth > crowding_threshold

    @staticmethod
    def handle_partial_occlusion(
        confidence: float,
        bbox_height: float,
        bbox_width: float,
        frame_height: float,
        min_visible_ratio: float = 0.3
    ) -> bool:
        """
        Detect partial occlusion.
        Returns True if person is significantly occluded.
        """
        visible_area_ratio = (bbox_height * bbox_width) / (frame_height ** 2)
        is_likely_occluded = (
            visible_area_ratio < min_visible_ratio or
            confidence < 0.5
        )
        return is_likely_occluded
