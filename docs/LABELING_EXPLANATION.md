# How Frame Labeling Works

## Current Approach: Folder-Based Labeling

The current `prepare_training_from_videos.py` script uses **folder-based labeling**:

1. **Videos are organized by species folder:**
   ```
   training_videos/
   ├── Bald_Eagle/
   │   └── video1.mp4
   ├── Red_Tailed_Hawk/
   │   └── video1.mp4
   ```

2. **Frames inherit the label from the folder:**
   - All frames extracted from `Bald_Eagle/video1.mp4` are labeled as `Bald_Eagle`
   - The folder name becomes the class label in the training dataset

3. **Output structure:**
   ```
   data/bird_species/
   ├── train/
   │   ├── Bald_Eagle/
   │   │   └── video1_frame_000001.jpg  ← Labeled as "Bald_Eagle"
   │   └── Red_Tailed_Hawk/
   │       └── video1_frame_000001.jpg  ← Labeled as "Red_Tailed_Hawk"
   ```

## Limitations

This approach has several limitations:

1. **No verification**: Frames are labeled based on folder name, not actual content
2. **Empty frames**: May extract frames without birds
3. **Multiple species**: If a video contains multiple species, all frames get the same label
4. **Mislabeled videos**: If a video is in the wrong folder, all frames are mislabeled

## Better Approach: Detection-Based Extraction

For better quality training data, you should:

### Option 1: Use Detection System to Extract Only Bird Frames

Use the existing `test_videos_folder.py` script to extract only frames with detected birds:

```bash
# Extract crops of detected birds (these are already labeled by detection)
python scripts/test_videos_folder.py \
    --input-dir training_videos/Bald_Eagle \
    --output-dir training_output \
    --save-crops \
    --save-json
```

This will:
- Only extract frames where birds are detected
- Save cropped bird images (not full frames)
- Include detection confidence scores
- You can then manually verify and organize by species

### Option 2: Manual Curation

After extracting frames:

1. **Review extracted frames** to ensure they contain the correct species
2. **Remove empty frames** (frames without birds)
3. **Reorganize frames** if videos contain multiple species
4. **Verify labels** match the actual content

### Option 3: Use Species Classification for Labeling

If you have a pre-trained species classifier:

1. Extract all frames from videos
2. Run species classification on each frame
3. Use the predicted species as the label (if confidence is high enough)
4. Manually review low-confidence predictions

## Recommended Workflow

### Step 1: Organize Videos by Known Species

```
training_videos/
├── Bald_Eagle/
│   └── videos...
├── Red_Tailed_Hawk/
│   └── videos...
```

### Step 2: Extract Frames with Detection

Use the detection system to extract only frames with birds:

```bash
# For each species folder
python scripts/test_videos_folder.py \
    --input-dir training_videos/Bald_Eagle \
    --output-dir training_output/Bald_Eagle \
    --save-crops \
    --save-json
```

This extracts cropped bird images (not full frames), which are better for training.

### Step 3: Review and Organize

1. Review the extracted crops in `training_output/Bald_Eagle/crops/`
2. Remove any crops that don't contain the expected species
3. Organize into train/val structure:

```bash
data/bird_species/
├── train/
│   ├── Bald_Eagle/
│   │   └── (reviewed crops)
│   └── Red_Tailed_Hawk/
│       └── (reviewed crops)
└── val/
    ├── Bald_Eagle/
    └── Red_Tailed_Hawk/
```

### Step 4: Train Model

```bash
python scripts/train_bird_species_classifier.py \
    --data-dir data/bird_species
```

## Best Practices

1. **Use cropped bird images** (from detection) rather than full frames
2. **Manually review** extracted images to ensure correct labeling
3. **Remove empty frames** and frames without clear bird visibility
4. **Balance your dataset** - try to have similar numbers of images per species
5. **Use high-confidence detections** - only use crops with high bird detection confidence

## Future Improvements

A better script would:
1. Use the detection system to find frames with birds
2. Extract cropped bird images (not full frames)
3. Optionally use species classification to verify labels
4. Allow manual review/curation
5. Automatically organize into train/val splits

This would ensure:
- Only frames with birds are included
- Labels match actual content
- Higher quality training data


