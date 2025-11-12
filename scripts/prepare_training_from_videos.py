#!/usr/bin/env python3
"""
Extract frames from videos organized by bird species for training.

This script reads videos organized by species and extracts frames,
organizing them into train/val splits for YOLO classification training.
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional
import shutil
import random
import argparse

# Add the project root to the Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    import cv2
except ImportError:
    print("❌ OpenCV not found. Install it with: pip install opencv-python")
    sys.exit(1)

try:
    import yaml
except ImportError:
    print("❌ PyYAML not found. Install it with: pip install pyyaml")
    sys.exit(1)


SUPPORTED_VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv"}
SUPPORTED_IMAGE_EXTS = {".jpg", ".jpeg", ".png"}


def find_videos(species_dir: Path) -> List[Path]:
    """Find all videos in a species directory.
    
    Args:
        species_dir: Directory containing videos for a species
        
    Returns:
        List of video file paths
    """
    videos = []
    for ext in SUPPORTED_VIDEO_EXTS:
        videos.extend(species_dir.glob(f"*{ext}"))
        videos.extend(species_dir.glob(f"*{ext.upper()}"))
    return sorted(videos)


def extract_frames(
    video_path: Path,
    output_dir: Path,
    frames_per_video: int,
    frame_interval: Optional[int] = None,
) -> List[Path]:
    """Extract frames from a video.
    
    Args:
        video_path: Path to video file
        output_dir: Directory to save extracted frames
        frames_per_video: Number of frames to extract
        frame_interval: Extract every Nth frame (None = auto-calculate)
        
    Returns:
        List of extracted frame file paths
    """
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"   [WARNING] Failed to open video: {video_path}")
        return []
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    
    if total_frames == 0:
        print(f"   [WARNING] Video has no frames: {video_path}")
        cap.release()
        return []
    
    # Calculate frame interval if not provided
    if frame_interval is None:
        if total_frames <= frames_per_video:
            frame_interval = 1
        else:
            frame_interval = max(1, total_frames // frames_per_video)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    extracted_frames = []
    frame_count = 0
    saved_count = 0
    
    while saved_count < frames_per_video:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Extract frame if it matches the interval
        if frame_count % frame_interval == 0:
            frame_filename = f"{video_path.stem}_frame_{frame_count:06d}.jpg"
            frame_path = output_dir / frame_filename
            
            if cv2.imwrite(str(frame_path), frame):
                extracted_frames.append(frame_path)
                saved_count += 1
            else:
                print(f"   [WARNING] Failed to save frame: {frame_path}")
        
        frame_count += 1
    
    cap.release()
    return extracted_frames


def prepare_training_from_videos(
    input_dir: Path,
    output_dir: Path,
    frames_per_video: int = 50,
    val_split_ratio: float = 0.2,
    frame_interval: Optional[int] = None,
    min_frames_per_class: int = 10,
    seed: int = 42,
) -> bool:
    """Prepare training dataset from videos organized by species.
    
    Args:
        input_dir: Directory containing species folders with videos
        output_dir: Output directory for extracted frames
        frames_per_video: Number of frames to extract per video
        val_split_ratio: Ratio of data to use for validation (0.0-1.0)
        frame_interval: Extract every Nth frame (None = auto-calculate)
        min_frames_per_class: Minimum frames required per class
        seed: Random seed for reproducibility
        
    Returns:
        True if successful, False otherwise
    """
    if not input_dir.exists():
        print(f"❌ Input directory not found: {input_dir}")
        return False
    
    # Set random seed for reproducibility
    random.seed(seed)
    
    # Find species directories
    species_dirs = [d for d in input_dir.iterdir() if d.is_dir()]
    
    if not species_dirs:
        print(f"❌ No species directories found in {input_dir}")
        print("   Expected structure: input_dir/Species_Name/video1.mp4, ...")
        return False
    
    print(f"✅ Found {len(species_dirs)} species directories")
    
    # Create output directories
    train_dir = output_dir / "train"
    val_dir = output_dir / "val"
    
    train_dir.mkdir(parents=True, exist_ok=True)
    val_dir.mkdir(parents=True, exist_ok=True)
    
    # Track statistics
    stats = {
        'species': {},
        'total_videos': 0,
        'total_frames': 0,
        'train_frames': 0,
        'val_frames': 0,
    }
    
    # Process each species
    print("\n[INFO] Extracting frames from videos...")
    
    for species_dir in sorted(species_dirs):
        species_name = species_dir.name
        print(f"\n   Processing: {species_name}")
        
        # Find videos for this species
        videos = find_videos(species_dir)
        
        if not videos:
            print(f"   [WARNING] No videos found in {species_dir}")
            continue
        
        print(f"   Found {len(videos)} videos")
        
        # Extract frames from all videos
        all_frames = []
        for video in videos:
            video_frames = extract_frames(
                video,
                output_dir / "temp" / species_name,
                frames_per_video,
                frame_interval,
            )
            all_frames.extend(video_frames)
            stats['total_videos'] += 1
        
        if len(all_frames) < min_frames_per_class:
            print(f"   [WARNING] Only {len(all_frames)} frames extracted (minimum: {min_frames_per_class})")
            print(f"   Consider adding more videos or increasing --frames-per-video")
            # Continue anyway, but warn user
        
        # Split frames into train/val
        random.shuffle(all_frames)
        split_idx = int(len(all_frames) * (1 - val_split_ratio))
        train_frames = all_frames[:split_idx]
        val_frames = all_frames[split_idx:]
        
        # Create species directories
        train_species_dir = train_dir / species_name
        val_species_dir = val_dir / species_name
        
        train_species_dir.mkdir(parents=True, exist_ok=True)
        val_species_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy frames to train/val directories
        for frame_path in train_frames:
            dest_path = train_species_dir / frame_path.name
            shutil.copy2(frame_path, dest_path)
        
        for frame_path in val_frames:
            dest_path = val_species_dir / frame_path.name
            shutil.copy2(frame_path, dest_path)
        
        # Clean up temp directory
        temp_dir = output_dir / "temp" / species_name
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        
        # Update statistics
        stats['species'][species_name] = {
            'videos': len(videos),
            'total_frames': len(all_frames),
            'train_frames': len(train_frames),
            'val_frames': len(val_frames),
        }
        stats['total_frames'] += len(all_frames)
        stats['train_frames'] += len(train_frames)
        stats['val_frames'] += len(val_frames)
        
        print(f"   ✅ Extracted {len(all_frames)} frames ({len(train_frames)} train, {len(val_frames)} val)")
    
    # Clean up temp directory if empty
    temp_root = output_dir / "temp"
    if temp_root.exists():
        try:
            temp_root.rmdir()
        except OSError:
            pass
    
    # Create dataset info
    create_dataset_info(output_dir, stats)
    
    # Print summary
    print("\n" + "=" * 60)
    print("✅ Dataset preparation completed!")
    print("=" * 60)
    print(f"Output directory: {output_dir}")
    print(f"Species: {len(stats['species'])}")
    print(f"Total videos: {stats['total_videos']}")
    print(f"Total frames: {stats['total_frames']}")
    print(f"Train frames: {stats['train_frames']}")
    print(f"Val frames: {stats['val_frames']}")
    print("\nSpecies breakdown:")
    for species_name, species_stats in sorted(stats['species'].items()):
        print(f"  {species_name}: {species_stats['total_frames']} frames "
              f"({species_stats['train_frames']} train, {species_stats['val_frames']} val)")
    
    return True


def create_dataset_info(
    output_dir: Path,
    stats: Dict,
) -> None:
    """Create dataset info YAML file.
    
    Args:
        output_dir: Dataset directory
        stats: Statistics dictionary
    """
    class_names = sorted(stats['species'].keys())
    
    info = {
        'dataset_name': 'Custom Bird Species Dataset (from videos)',
        'source': 'User-provided videos',
        'format': 'YOLO Classification',
        'num_classes': len(class_names),
        'total_samples': stats['total_frames'],
        'train_samples': stats['train_frames'],
        'val_samples': stats['val_frames'],
        'classes': class_names,
        'path': str(output_dir.resolve()),
        'species_stats': stats['species'],
    }
    
    # Save YAML
    info_path = output_dir / "dataset_info.yaml"
    with open(info_path, 'w', encoding='utf-8') as f:
        yaml.dump(info, f, default_flow_style=False, indent=2, allow_unicode=True)
    
    print(f"\n[INFO] Dataset info saved to: {info_path}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Extract frames from videos organized by species for training",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script extracts frames from videos organized by bird species and prepares
them for YOLO classification training.

Expected input structure:
  input_dir/
    ├── Bald_Eagle/
    │   ├── video1.mp4
    │   └── video2.mp4
    ├── Red_Tailed_Hawk/
    │   └── video1.mp4
    └── ...

Example usage:
  python scripts/prepare_training_from_videos.py \\
      --input-dir training_videos \\
      --output-dir data/bird_species \\
      --frames-per-video 100 \\
      --val-split 0.2
        """
    )
    parser.add_argument(
        "--input-dir",
        required=True,
        help="Directory containing species folders with videos",
    )
    parser.add_argument(
        "--output-dir",
        default=str(PROJECT_ROOT / "data" / "bird_species"),
        help="Output directory for extracted frames (default: data/bird_species)",
    )
    parser.add_argument(
        "--frames-per-video",
        type=int,
        default=50,
        help="Number of frames to extract per video (default: 50)",
    )
    parser.add_argument(
        "--val-split",
        type=float,
        default=0.2,
        help="Ratio of data to use for validation (0.0-1.0, default: 0.2)",
    )
    parser.add_argument(
        "--frame-interval",
        type=int,
        default=None,
        help="Extract every Nth frame (default: auto-calculated)",
    )
    parser.add_argument(
        "--min-frames-per-class",
        type=int,
        default=10,
        help="Minimum frames required per class (default: 10)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Run non-interactively",
    )
    
    args = parser.parse_args()
    
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    
    print("=" * 60)
    print("Video Frame Extraction for Training")
    print("=" * 60)
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    print(f"Frames per video: {args.frames_per_video}")
    print(f"Validation split: {args.val_split * 100:.1f}%")
    print(f"Min frames per class: {args.min_frames_per_class}")
    print()
    
    if not args.yes:
        try:
            response = input("Do you want to proceed? (y/N): ").strip().lower()
        except EOFError:
            response = "n"
        if response not in ["y", "yes"]:
            print("Cancelled.")
            return 0
    
    # Prepare dataset
    success = prepare_training_from_videos(
        input_dir=input_dir,
        output_dir=output_dir,
        frames_per_video=args.frames_per_video,
        val_split_ratio=args.val_split,
        frame_interval=args.frame_interval,
        min_frames_per_class=args.min_frames_per_class,
        seed=args.seed,
    )
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 Frame extraction completed!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Train the species classification model:")
        print(f"   python scripts/train_bird_species_classifier.py --data-dir {output_dir}")
        print("\n2. Or train manually:")
        print("   from ultralytics import YOLO")
        print("   model = YOLO('yolo11n-cls.pt')")
        print(f"   model.train(data='{output_dir}', epochs=100, imgsz=224)")
        print("\n3. Update config/skyguard.yaml with the trained model path")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())


