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
import numpy as np
import logging
from pathlib import Path
from typing import List, Dict, Any

# Ensure project root on sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from skyguard.core.config_manager import ConfigManager  # noqa: E402
from skyguard.core.detector import RaptorDetector  # noqa: E402
from skyguard.utils.logger import setup_logging  # noqa: E402


SUPPORTED_EXTS = {".mp4", ".avi", ".mov", ".mkv"}


def find_videos(input_dir: Path) -> List[Path]:
    return sorted([
        p for p in input_dir.iterdir()
        if p.suffix.lower() in SUPPORTED_EXTS
    ])


def annotate_frame(frame, detections):
    """Minimal annotation: draw boxes and labels if present."""
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


def draw_segmented_frame(frame: np.ndarray, detections: List[Dict[str, Any]]) -> np.ndarray:
    """Draw segmentation masks, bounding boxes, and labels on frame.
    
    Args:
        frame: Input frame as numpy array
        detections: List of detection dictionaries
        
    Returns:
        Annotated frame with segmentation masks and labels
    """
    annotated_frame = frame.copy()
    
    for detection in detections or []:
        bbox = detection.get("bbox")
        confidence = float(detection.get("confidence", 0.0))
        class_name = detection.get("class_name", "bird")
        polygon = detection.get("polygon")
        species = detection.get("species")
        species_confidence = detection.get("species_confidence")
        
        # Draw segmentation mask if available
        if polygon is not None and len(polygon) > 0:
            overlay = annotated_frame.copy()
            pts = np.array(polygon, dtype=np.int32)
            # Use green color for segmentation mask
            cv2.fillPoly(overlay, [pts], color=(0, 255, 0))
            # Alpha blend mask for transparency
            alpha = 0.3
            annotated_frame = cv2.addWeighted(
                overlay,
                alpha,
                annotated_frame,
                1 - alpha,
                0,
            )
        
        # Draw bounding box
        if bbox and len(bbox) == 4:
            x1, y1, x2, y2 = map(int, bbox)
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Build label text
            if species and species_confidence is not None:
                label = f"{class_name}: {confidence:.2f} | {species}: {species_confidence:.2f}"
            else:
                label = f"{class_name}: {confidence:.2f}"
            
            # Calculate label size for background
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            thickness = 2
            (label_width, label_height), baseline = cv2.getTextSize(
                label, font, font_scale, thickness
            )
            
            # Draw label background
            label_y = max(label_height + 5, y1)
            cv2.rectangle(
                annotated_frame,
                (x1, label_y - label_height - 5),
                (x1 + label_width, label_y + baseline),
                (0, 255, 0),
                -1,
            )
            
            # Draw label text
            cv2.putText(
                annotated_frame,
                label,
                (x1, label_y),
                font,
                font_scale,
                (0, 0, 0),
                thickness,
                cv2.LINE_AA,
            )
    
    return annotated_frame


def process_video(
    detector: RaptorDetector,
    video_path: Path,
    output_dir: Path,
    save_annotated: bool,
    save_json: bool = False,
    save_crops: bool = False,
    save_segmented_images: bool = False,
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

    # Detection outputs
    det_root = output_dir / "detections" / video_path.stem
    crops_root = output_dir / "crops" / video_path.stem
    segmented_root = output_dir / "segmented_images" / video_path.stem
    detections_log = []
    if save_json:
        det_root.mkdir(parents=True, exist_ok=True)
    if save_crops:
        crops_root.mkdir(parents=True, exist_ok=True)
    if save_segmented_images:
        segmented_root.mkdir(parents=True, exist_ok=True)

    stats = {
        "video": str(video_path),
        "frames": 0,
        "detections": 0,
        "max_confidence": 0.0,
        "duration_s": 0.0,
    }

    start = time.time()
    try:
        frame_idx = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            stats["frames"] += 1
            frame_idx += 1

            dets = detector.detect(frame)
            
            # Filter to only high-confidence detections (>= 0.20) for species classification
            # Only these will be sent to species classification
            high_conf_dets_for_species = [
                d for d in (dets or [])
                if float(d.get("confidence", 0.0)) >= 0.20
            ]
            
            # Filter to only detections with species confidence >= 0.10
            # Only save segmented images if species is identified with >= 0.10 confidence
            dets_with_species = [
                d for d in high_conf_dets_for_species
                if d.get("species") is not None 
                and d.get("species_confidence") is not None
                and float(d.get("species_confidence", 0.0)) >= 0.10
            ]
            
            # Track all detections for stats (using 0.80 threshold for stats)
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

            # Save detailed detection records and optional crops
            if (save_json or save_crops) and dets:
                for i, d in enumerate(dets):
                    rec = {
                        "frame": frame_idx,
                        "bbox": d.get("bbox"),
                        "confidence": float(d.get("confidence", 0.0)),
                        "class_name": d.get("class_name"),
                        "class_id": d.get("class_id"),
                        "species": d.get("species"),
                        "species_confidence": d.get("species_confidence"),
                        "polygon": d.get("polygon"),
                    }
                    if save_json:
                        detections_log.append(rec)
                    if save_crops and rec["bbox"] and len(rec["bbox"]) == 4:
                        x1, y1, x2, y2 = map(int, rec["bbox"])
                        x1 = max(0, x1); y1 = max(0, y1)
                        x2 = min(width - 1, x2); y2 = min(height - 1, y2)
                        if x2 > x1 and y2 > y1:
                            crop = frame[y1:y2, x1:x2]
                            crop_name = f"{frame_idx:06d}_{i}_{rec['class_name'] or 'bird'}_{rec['confidence']:.2f}.jpg"
                            cv2.imwrite(str(crops_root / crop_name), crop)
            
            # Save segmented images ONLY for detections with:
            # - Bird confidence >= 0.20 (already filtered above)
            # - Species confidence >= 0.10
            # - Species name present
            if save_segmented_images and dets_with_species:
                segmented_frame = draw_segmented_frame(frame.copy(), dets_with_species)
                
                # Build filename with species name
                # If multiple detections, use the first one's species
                if len(dets_with_species) == 1:
                    det = dets_with_species[0]
                    species = det.get("species")
                    species_conf = float(det.get("species_confidence", 0.0))
                    # Sanitize species name for filename (replace spaces/special chars)
                    species_safe = species.replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "").replace(",", "")
                    segmented_name = f"{frame_idx:06d}_{species_safe}_{species_conf:.2f}_segmented.jpg"
                else:
                    # Multiple detections - use first species
                    det = dets_with_species[0]
                    species = det.get("species")
                    species_conf = float(det.get("species_confidence", 0.0))
                    species_safe = species.replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "").replace(",", "")
                    segmented_name = f"{frame_idx:06d}_{species_safe}_{species_conf:.2f}_multi_segmented.jpg"
                
                cv2.imwrite(str(segmented_root / segmented_name), segmented_frame)

            if writer is not None:
                annotated = annotate_frame(frame.copy(), dets)
                writer.write(annotated)
    finally:
        stats["duration_s"] = round(time.time() - start, 3)
        cap.release()
        if writer is not None:
            writer.release()

    # Write detections.json per video
    if save_json and detections_log:
        out_json = det_root / "detections.json"
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump({
                "video": str(video_path),
                "width": width,
                "height": height,
                "fps": fps,
                "detections": detections_log,
            }, f, indent=2)

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
    parser.add_argument(
        "--save-json",
        action="store_true",
        help="Save per-video detections JSON to output/detections/",
    )
    parser.add_argument(
        "--save-crops",
        action="store_true",
        help="Save cropped bird images to output/crops/",
    )
    parser.add_argument(
        "--save-segmented-images",
        action="store_true",
        help="Save labeled segmented images for frames with detections to output/segmented_images/",
    )
    # Optional species classification backend options
    parser.add_argument(
        "--species-backend",
        choices=["ultralytics", "external"],
        help="Species classifier backend",
    )
    parser.add_argument(
        "--species-model-path",
        help="Path to Ultralytics classification model (*.pt)",
    )
    parser.add_argument(
        "--species-repo-path",
        help="Path to external species repo (for external backend)",
    )
    parser.add_argument(
        "--species-module",
        help="Module in external repo that contains prediction function",
    )
    parser.add_argument(
        "--species-function",
        help="Function in module that returns (label, confidence)",
    )
    parser.add_argument(
        "--species-input-size",
        type=str,
        help="Classifier input size as WxH (e.g., 224x224)",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    summary_path = output_dir / "summary.json"

    if not input_dir.exists():
        print(f"❌ Input directory not found: {input_dir}")
        return 1

    # Setup logging based on config
    cfg = ConfigManager(args.config).get_config()
    log_config = cfg.get("logging", {})
    # Ensure console output is enabled for inference details
    log_config["console_output"] = True
    setup_logging(log_config)
    
    # Load config and detector
    ai_cfg = dict(cfg.get("ai", {}))
    # Force an explicit model path relative to project root
    ai_cfg["model_path"] = str(PROJECT_ROOT / "models" / "yolo11n-seg.pt")
    # Apply species options if provided
    if args.species_backend:
        ai_cfg["species_backend"] = args.species_backend
    if args.species_model_path:
        ai_cfg["species_model_path"] = args.species_model_path
    if args.species_repo_path:
        ai_cfg["species_repo_path"] = args.species_repo_path
    if args.species_module:
        ai_cfg["species_module"] = args.species_module
    if args.species_function:
        ai_cfg["species_function"] = args.species_function
    if args.species_input_size:
        try:
            w, h = map(int, args.species_input_size.lower().split("x"))
            ai_cfg["species_input_size"] = [w, h]
        except Exception:
            print("⚠️ Invalid --species-input-size, expected WxH (e.g., 224x224)")
    detector = RaptorDetector(ai_cfg)
    if not detector.load_model():
        print("❌ Model loading failed. Checked:")
        print(f"   - {ai_cfg['model_path']}")
        return 1

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
        stats = process_video(
            detector,
            v,
            output_dir,
            args.save_annotated,
            save_json=args.save_json,
            save_crops=args.save_crops,
            save_segmented_images=args.save_segmented_images,
        )
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
