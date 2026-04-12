"""
Reusable Camera Feed Component — Renders live video with optional YOLOv8 inference.
Drop this into any dashboard page:

    from dashboard.components.camera_feed import render_camera_feed
    render_camera_feed(source=0, camera_id="CAM_01", run_detection=True)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import cv2
import numpy as np
import time
from datetime import datetime


def render_camera_feed(
    source=0,
    camera_id: str = "CAM_01",
    run_detection: bool = False,
    max_frames: int = 1,
    confidence: float = 0.35,
):
    """
    Render a camera feed panel in the dashboard.

    Args:
        source: Video source — int (webcam device), str (path to .mp4 / RTSP URL)
        camera_id: Display name for the camera
        run_detection: If True, runs YOLOv8 inference on each frame
        max_frames: Number of frames to capture per refresh cycle
        confidence: Detection confidence threshold
    """

    # --- Source selector ---
    source_options = ["📷 Webcam (Device 0)", "🎥 Video File (.mp4)"]
    feed_key = f"feed_source_{camera_id}"

    if feed_key not in st.session_state:
        st.session_state[feed_key] = source_options[0]

    selected_source = st.radio(
        "Video Source",
        source_options,
        key=feed_key,
        horizontal=True,
        label_visibility="collapsed",
    )

    actual_source = 0  # default webcam
    if "Video File" in selected_source:
        uploaded_video = st.file_uploader(
            "Upload surveillance video (.mp4)",
            type=["mp4", "avi", "mov", "mkv"],
            key=f"video_upload_{camera_id}",
        )
        if uploaded_video is not None:
            # Save to temp location
            video_path = Path(__file__).resolve().parent.parent.parent / "data" / f"feed_{camera_id}.mp4"
            video_path.parent.mkdir(exist_ok=True)
            with open(video_path, "wb") as f:
                f.write(uploaded_video.read())
            actual_source = str(video_path)
        else:
            st.markdown("""
            <div style="height:200px;background:linear-gradient(135deg,#141b2c,#0b1323);
                border-radius:8px;border:1px dashed rgba(110,230,238,0.2);
                display:flex;align-items:center;justify-content:center;color:#69758a;font-size:0.85rem;">
                📁 Upload a surveillance video file to begin
            </div>
            """, unsafe_allow_html=True)
            return
    else:
        actual_source = 0

    # --- Capture frame ---
    frame, fps, capture_ok = _capture_frame(actual_source)

    if not capture_ok or frame is None:
        st.markdown(f"""
        <div style="height:200px;background:linear-gradient(135deg,#141b2c,#0b1323);
            border-radius:8px;border:1px dashed rgba(110,230,238,0.2);
            display:flex;align-items:center;justify-content:center;flex-direction:column;gap:8px;">
            <span style="font-size:2rem;">📹</span>
            <div style="color:#ffb4ab;font-size:0.85rem;font-weight:600;">
                Camera {camera_id} — Unable to connect
            </div>
            <div style="color:#69758a;font-size:0.72rem;">
                Check that device is connected or video file is valid
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # --- Run detection if enabled ---
    num_detections = 0
    avg_confidence = 0.0
    processing_ms = 0

    if run_detection:
        frame, num_detections, avg_confidence, processing_ms = _run_detection_on_frame(frame, confidence)

    # --- Display ---
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Header overlay info
    now = datetime.now().strftime("%H:%M:%S")
    h, w = frame.shape[:2]

    st.markdown(f"""
    <div class="panel" style="padding:0;overflow:hidden;">
        <div style="display:flex;justify-content:space-between;align-items:center;padding:10px 16px;
            border-bottom:1px solid rgba(61,73,74,0.1);">
            <div style="display:flex;align-items:center;gap:10px;">
                <span style="width:8px;height:8px;border-radius:50%;background:#6ee6ee;
                    box-shadow:0 0 6px rgba(110,230,238,0.5);"></span>
                <span style="color:#6ee6ee;font-size:0.75rem;font-weight:600;">LIVE: {camera_id}</span>
                <span style="color:#69758a;font-size:0.65rem;">{w}×{h}</span>
            </div>
            <div style="display:flex;gap:12px;font-size:0.65rem;">
                <span style="color:#bcc9ca;">⏱ {now}</span>
                {"<span style='color:#6ee6ee;font-weight:600;'>🔍 " + str(num_detections) + " detections</span>" if run_detection else ""}
                {"<span style='color:#bcc9ca;'>⚡ " + f"{processing_ms:.0f}ms" + "</span>" if run_detection else ""}
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.image(frame_rgb, use_container_width=True)

    # Detection stats bar
    if run_detection and num_detections > 0:
        st.markdown(f"""
        <div style="display:flex;gap:20px;padding:8px 16px;border-top:1px solid rgba(61,73,74,0.1);
            font-size:0.72rem;">
            <span style="color:#6ee6ee;">Products: <b>{num_detections}</b></span>
            <span style="color:#bcc9ca;">Avg Confidence: <b>{avg_confidence:.1%}</b></span>
            <span style="color:#bcc9ca;">Inference: <b>{processing_ms:.0f}ms</b></span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def _capture_frame(source):
    """Capture a single frame from the video source."""
    try:
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            return None, 0, False

        fps = cap.get(cv2.CAP_PROP_FPS) or 30

        # For video files, pick a random frame to keep it interesting
        if isinstance(source, str):
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames > 10:
                import random
                target = random.randint(0, total_frames - 1)
                cap.set(cv2.CAP_PROP_POS_FRAMES, target)

        ret, frame = cap.read()
        cap.release()

        if not ret or frame is None:
            return None, fps, False

        return frame, fps, True
    except Exception:
        return None, 0, False


def _run_detection_on_frame(frame, confidence=0.35):
    """Run YOLOv8 inference on a single frame and draw boxes."""
    try:
        from models.shelf_detector import ShelfDetector

        detector = _get_cached_detector()

        start = time.time()

        # Run YOLO directly on frame
        if detector.model is not None:
            from config.settings import IMAGE_SIZE, DETECTION_IOU_THRESHOLD
            results = detector.model(frame, conf=confidence, iou=DETECTION_IOU_THRESHOLD, imgsz=IMAGE_SIZE, verbose=False)
            elapsed_ms = (time.time() - start) * 1000

            num_detections = 0
            total_conf = 0

            colors = [
                (110, 230, 238), (206, 203, 91), (255, 180, 171), (219, 226, 249),
                (0, 255, 0), (255, 128, 0), (128, 255, 0), (255, 0, 255),
            ]

            for r in results:
                for box in r.boxes:
                    x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].cpu().numpy()]
                    conf = float(box.conf[0])
                    cls_id = int(box.cls[0])
                    cls_name = detector.model.names.get(cls_id, f"class_{cls_id}")

                    color = colors[cls_id % len(colors)]
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

                    label = f"{cls_name} {conf:.0%}"
                    (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
                    cv2.rectangle(frame, (x1, y1 - lh - 6), (x1 + lw, y1), color, -1)
                    cv2.putText(frame, label, (x1, y1 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)

                    num_detections += 1
                    total_conf += conf

            avg_conf = total_conf / max(num_detections, 1)
            return frame, num_detections, avg_conf, elapsed_ms

    except Exception as e:
        print(f"  ⚠ Detection error: {e}")

    return frame, 0, 0.0, 0.0


@st.cache_resource
def _get_cached_detector():
    """Cache the detector so it's not reloaded on every frame."""
    from models.shelf_detector import ShelfDetector
    return ShelfDetector()
