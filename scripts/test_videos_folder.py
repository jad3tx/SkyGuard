#!/usr/bin/env python3
"""
Batch video tester for SkyGuard.

- Scans an input directory for videos (mp4/avi/mov/mkv)
- Runs the SkyGuard detector on frames
- Prints detection stats and optionally writes annotated output videos
"""

import sys
import cv2
import time
import json
import argparse
from pathlib import Path
from typing import List

# Ensure project root on sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from skyguard.core.config_manager import ConfigManager  # noqa: E402
from skyguard.core.detector import RaptorDetector  # noqa: E402


SUPPORTED_EXTS = {".mp4", ".avi", ".mov", ".mkv"}


def find_videos(input_dir: Path) -> List[Path]:
    return sorted([
        p for p in input_dir.iterdir()
        if p.suffix.lower() in SUPPORTED_EXTS
    ])


def annotate_frame(frame, detections):
    # Minimal annotation: draw boxes and labels if present
    for det in detections or []:
        conf = float(det.get("confidence", 0.0))
        if conf < 0.80:
            continue
        bbox = det.get("bbox")
        if bbox and len(bbox) == 4:
            x1, y1, x2, y2 = map(int, bbox)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        label = (
            f"{det.get('class_name', 'obj')} "
            f"{conf:.2f}"
        )
        if bbox:
            cv2.putText(
                frame,
                label,
                (int(bbox[0]), max(0, int(bbox[1]) - 6)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                1,
                cv2.LINE_AA,
            )
    return frame


def process_video(
    detector: RaptorDetector,
    video_path: Path,
    output_dir: Path,
    save_annotated: bool,
) -> dict:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return {"video": str(video_path), "error": "failed_to_open"}

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 640)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 480)

    writer = None
    if save_annotated:
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / f"{video_path.stem}_annotated.mp4"
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(out_path), fourcc, fps, (width, height))

    stats = {
        "video": str(video_path),
        "frames": 0,
        "detections": 0,
        "max_confidence": 0.0,
        "duration_s": 0.0,
    }

    start = time.time()
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            stats["frames"] += 1

            dets = detector.detect(frame)
            high_conf_dets = [
                d for d in (dets or [])
                if float(d.get("confidence", 0.0)) >= 0.80
            ]
            if high_conf_dets:
                stats["detections"] += 1
                stats["max_confidence"] = max(
                    stats["max_confidence"],
                    max(float(d.get("confidence", 0.0)) for d in high_conf_dets),
                )

            if writer is not None:
                annotated = annotate_frame(frame.copy(), dets)
                writer.write(annotated)
    finally:
        stats["duration_s"] = round(time.time() - start, 3)
        cap.release()
        if writer is not None:
            writer.release()

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Run SkyGuard detector on all videos in a folder"
    )
    parser.add_argument(
        "--input-dir",
        default=str(PROJECT_ROOT / "videos_in"),
        help="Folder with input videos",
    )
    parser.add_argument(
        "--output-dir",
        default=str(PROJECT_ROOT / "videos_out"),
        help="Folder for outputs (annotations, summary)",
    )
    parser.add_argument(
        "--config",
        default=str(PROJECT_ROOT / "config" / "skyguard.yaml"),
        help="Path to config file",
    )
    parser.add_argument(
        "--save-annotated",
        action="store_true",
        help="Write annotated output videos",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    summary_path = output_dir / "summary.json"

    if not input_dir.exists():
        print(f"❌ Input directory not found: {input_dir}")
        return 1

    # Load config and detector
    cfg = ConfigManager(args.config).get_config()
    detector = RaptorDetector(cfg.get("ai", {}))
    if not detector.load_model():
        print("⚠️ Model loading failed; continuing (dummy mode may be used)")

    videos = find_videos(input_dir)
    if not videos:
        print(
            f"⚠️ No videos found in {input_dir} "
            f"({', '.join(sorted(SUPPORTED_EXTS))})"
        )
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)
    all_stats = []
    print(f"🎬 Found {len(videos)} videos. Processing...")
    for idx, v in enumerate(videos, 1):
        print(f"[{idx}/{len(videos)}] {v.name}")
        stats = process_video(detector, v, output_dir, args.save_annotated)
        all_stats.append(stats)
        print(
            "   - frames={frames} detections={dets} max_conf={maxc:.3f} "
            "time={dur}s".format(
                frames=stats["frames"],
                dets=stats["detections"],
                maxc=stats["max_confidence"],
                dur=stats["duration_s"],
            )
        )

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(all_stats, f, indent=2)
    print(f"\n✅ Done. Summary written to {summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
