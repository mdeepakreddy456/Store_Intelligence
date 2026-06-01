from ultralytics import YOLO
import cv2
from pathlib import Path

from tracker import VisitorTracker
from emit import (
    build_event,
    emit_event,
    clear_events_file,
)

# =====================================
# CONFIG
# =====================================

VIDEO_FOLDER = "data/videos"

STORE_ID = "STORE_BLR_002"

CAMERA_MAPPING = {
    "CAM 1.mp4": "CAM_MAIN_01",
    "CAM 2.mp4": "CAM_MAIN_02",
    "CAM 3.mp4": "CAM_ENTRY_01",
    "CAM 4.mp4": "CAM_STAFF_01",
    "CAM 5.mp4": "CAM_BILLING_01",
}

ENTRY_LINE_Y = 350

# zones for CAM1/CAM2
# x1, y1, x2, y2
ZONES = {
    "SKINCARE": (200, 100, 800, 500),
    "MAKEUP": (800, 100, 1500, 700),
}

# billing region CAM5
BILLING_ZONE = (100, 100, 1200, 800)

# =====================================
# INIT
# =====================================

model = YOLO("yolov8n.pt")

tracker = VisitorTracker()

clear_events_file()


# =====================================
# HELPERS
# =====================================

def inside_zone(x, y, zone):
    x1, y1, x2, y2 = zone
    return x1 <= x <= x2 and y1 <= y <= y2


def create_and_emit(
    camera_id,
    visitor_id,
    event_type,
    confidence,
    zone_id=None,
    dwell_ms=0,
    queue_depth=None,
):

    event = build_event(
        store_id=STORE_ID,
        camera_id=camera_id,
        visitor_id=visitor_id,
        event_type=event_type,
        confidence=confidence,
        zone_id=zone_id,
        dwell_ms=dwell_ms,
        is_staff=False,
        queue_depth=queue_depth,
        session_seq=tracker.get_session_seq(visitor_id),
    )

    emit_event(event)


# =====================================
# PROCESS VIDEO
# =====================================

def process_video(video_path):

    video_name = Path(video_path).name
    camera_id = CAMERA_MAPPING.get(video_name)

    print(f"\nProcessing {video_name}")

    cap = cv2.VideoCapture(video_path)

    while cap.isOpened():

        success, frame = cap.read()

        if not success:
            break

        results = model.track(
            frame,
            persist=True,
            tracker="bytetrack.yaml",
            classes=[0],
            verbose=False,
        )

        if len(results) == 0:
            continue

        boxes = results[0].boxes

        if boxes.id is None:
            continue

        ids = boxes.id.cpu().numpy()
        confs = boxes.conf.cpu().numpy()
        xyxy = boxes.xyxy.cpu().numpy()

        queue_depth = len(ids)

        for track_id, conf, box in zip(
            ids,
            confs,
            xyxy
        ):

            track_id = int(track_id)

            visitor_id = (
                tracker.get_visitor_id(track_id)
            )

            x1, y1, x2, y2 = box

            center_x = int((x1 + x2) / 2)
            center_y = int((y1 + y2) / 2)

            # =================================
            # ENTRY / EXIT CAMERA (CAM3)
            # =================================

            if camera_id == "CAM_ENTRY_01":

                previous_y = (
                    tracker.update_position(
                        track_id,
                        center_y
                    )
                )

                event_type = (
                    tracker.detect_entry_exit(
                        track_id,
                        previous_y,
                        center_y,
                        ENTRY_LINE_Y,
                    )
                )

                if event_type:

                    create_and_emit(
                        camera_id,
                        visitor_id,
                        event_type,
                        conf,
                    )

                cv2.line(
                    frame,
                    (0, ENTRY_LINE_Y),
                    (frame.shape[1],
                     ENTRY_LINE_Y),
                    (0, 0, 255),
                    3,
                )

            # =================================
            # MAIN FLOOR (CAM1/CAM2)
            # =================================

            elif camera_id in [
                "CAM_MAIN_01",
                "CAM_MAIN_02",
            ]:

                current_zone = None

                for zone_name, coords in (
                    ZONES.items()
                ):

                    if inside_zone(
                        center_x,
                        center_y,
                        coords,
                    ):
                        current_zone = zone_name
                        break

                if current_zone:

                    entered = (
                        tracker.enter_zone(
                            visitor_id,
                            current_zone,
                        )
                    )

                    if entered:

                        create_and_emit(
                            camera_id,
                            visitor_id,
                            "ZONE_ENTER",
                            conf,
                            zone_id=current_zone,
                        )

                    if tracker.should_emit_dwell(
                        visitor_id
                    ):

                        create_and_emit(
                            camera_id,
                            visitor_id,
                            "ZONE_DWELL",
                            conf,
                            zone_id=current_zone,
                            dwell_ms=30000,
                        )

            # =================================
            # BILLING CAMERA (CAM5)
            # =================================

            elif (
                camera_id
                == "CAM_BILLING_01"
            ):

                if inside_zone(
                    center_x,
                    center_y,
                    BILLING_ZONE,
                ):

                    create_and_emit(
                        camera_id,
                        visitor_id,
                        "BILLING_QUEUE_JOIN",
                        conf,
                        queue_depth=queue_depth,
                    )

            # =================================
            # DRAW
            # =================================

            cv2.rectangle(
                frame,
                (int(x1), int(y1)),
                (int(x2), int(y2)),
                (0, 255, 0),
                2,
            )

            cv2.putText(
                frame,
                visitor_id,
                (
                    int(x1),
                    int(y1) - 10,
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2,
            )

        cv2.imshow(
            camera_id,
            frame,
        )

        if (
            cv2.waitKey(1)
            & 0xFF
            == ord("q")
        ):
            break

    cap.release()


# =====================================
# MAIN
# =====================================

def main():

    video_files = (
        Path(VIDEO_FOLDER)
        .glob("*.mp4")
    )

    for video in video_files:
        process_video(str(video))

    cv2.destroyAllWindows()

    print("\nFinished!")
    print(
        "Events saved to "
        "pipeline/output/events.jsonl"
    )


if __name__ == "__main__":
    main()