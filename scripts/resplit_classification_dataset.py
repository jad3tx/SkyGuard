#!/usr/bin/env python3
"""
Rebuild train/val splits for YOLO classification from a mismatched dataset.

Pools images from data_dir/train/<class> and data_dir/val/<class>, then writes a
fresh split so every class exists in BOTH train and val (when enough images exist).

Use when train/val folder names differ, some classes are missing from val, or
you merged data by hand and labels no longer line up.
"""

from __future__ import annotations

import argparse
import random
import shutil
import sys
from pathlib import Path
from typing import List, Set

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG")


def list_images(class_dir: Path) -> List[Path]:
    out: List[Path] = []
    for ext in IMAGE_EXTS:
        out.extend(class_dir.glob(f"*{ext}"))
    return sorted(out)


def class_names(split_dir: Path) -> Set[str]:
    if not split_dir.exists():
        return set()
    return {d.name for d in split_dir.iterdir() if d.is_dir()}


def collect_union_classes(train_dir: Path, val_dir: Path) -> List[str]:
    names = class_names(train_dir) | class_names(val_dir)
    return sorted(names)


def resplit(
    data_dir: Path,
    output_dir: Path,
    val_ratio: float,
    seed: int,
) -> bool:
    train_in = data_dir / "train"
    val_in = data_dir / "val"

    if not train_in.exists():
        print(f"[ERROR] Missing {train_in}")
        return False

    classes = collect_union_classes(train_in, val_in)
    if not classes:
        print(f"[ERROR] No class folders under {train_in} or {val_in}")
        return False

    random.seed(seed)
    train_out = output_dir / "train"
    val_out = output_dir / "val"
    if output_dir.resolve() == data_dir.resolve():
        print("[ERROR] Output must differ from input (avoid wiping data). Use a new folder, then swap.")
        return False

    train_out.mkdir(parents=True, exist_ok=True)
    val_out.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Classes (union of train/val names): {len(classes)}")
    only_train = class_names(train_in) - class_names(val_in)
    only_val = class_names(val_in) - class_names(train_in)
    if only_train:
        print(f"[WARN] Only in train (no val folder): {sorted(only_train)}")
    if only_val:
        print(f"[WARN] Only in val (no train folder): {sorted(only_val)}")

    for c in classes:
        pool: List[Path] = []
        for src_root in (train_in, val_in):
            d = src_root / c
            if d.is_dir():
                pool.extend(list_images(d))
        # de-dupe by resolved path
        seen = set()
        unique: List[Path] = []
        for p in pool:
            r = str(p.resolve())
            if r not in seen:
                seen.add(r)
                unique.append(p)
        pool = unique

        if not pool:
            print(f"[WARN] No images for class {c!r}; skipping")
            continue

        random.shuffle(pool)
        n = len(pool)
        if n < 2:
            n_val = 0
        else:
            n_val = max(1, int(round(n * val_ratio)))
            n_val = min(n_val, n - 1)

        val_files = pool[:n_val]
        train_files = pool[n_val:]

        if not train_files:
            print(f"[WARN] Class {c!r} has no train split; skipping")
            continue

        t_dir = train_out / c
        t_dir.mkdir(parents=True, exist_ok=True)

        def copy_unique(files: List[Path], dest_dir: Path) -> None:
            for i, src in enumerate(files):
                dest = dest_dir / src.name
                if dest.exists():
                    dest = dest_dir / f"{src.stem}_{i}{src.suffix}"
                shutil.copy2(src, dest)

        copy_unique(train_files, t_dir)
        if val_files:
            v_dir = val_out / c
            v_dir.mkdir(parents=True, exist_ok=True)
            copy_unique(val_files, v_dir)
        print(f"   {c}: {len(train_files)} train, {len(val_files)} val (pooled {n})")

    print(f"\n[OK] Wrote aligned dataset to {output_dir}")
    print("   Train with: python scripts/train_bird_species_classifier.py --data-dir <path> ...")
    return True


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--data-dir",
        type=Path,
        default=PROJECT_ROOT / "data" / "bird_species",
        help="Existing dataset root (contains train/ and val/)",
    )
    p.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="New dataset root (must not be the same as data-dir)",
    )
    p.add_argument(
        "--val-split",
        type=float,
        default=0.2,
        help="Fraction of images per class for validation (default: 0.2)",
    )
    p.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for shuffling",
    )
    args = p.parse_args()

    data_dir = args.data_dir
    if not data_dir.is_absolute():
        data_dir = PROJECT_ROOT / data_dir
    output_dir = args.output_dir
    if not output_dir.is_absolute():
        output_dir = PROJECT_ROOT / output_dir

    if args.val_split <= 0 or args.val_split >= 1:
        print("[ERROR] --val-split must be between 0 and 1 (exclusive)")
        return 1

    ok = resplit(data_dir, output_dir, args.val_split, args.seed)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
