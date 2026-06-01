from collections import defaultdict
import time


class VisitorTracker:
    """
    Handles:
    - entry / exit
    - re-entry
    - dwell tracking
    - session counting
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

    def get_visitor_id(self, track_id):
        return f"VIS_{track_id}"

    def update_position(self, track_id, center_y):
        """
        Save current position
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
        Detect entry / exit
        """

        if previous_y is None:
            return None

        visitor_id = self.get_visitor_id(track_id)

        # ENTRY
        if previous_y < line_y and current_y >= line_y:

            # re-entry check
            if visitor_id in self.exited_visitors:

                last_exit = self.exited_visitors[visitor_id]

                if time.time() - last_exit < 600:
                    return "REENTRY"

            return "ENTRY"

        # EXIT
        elif previous_y > line_y and current_y <= line_y:

            self.exited_visitors[visitor_id] = time.time()

            return "EXIT"

        return None

    def enter_zone(self, visitor_id, zone_name):

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