# Training a Bird Species Classifier from Videos

This guide explains how to prepare videos with known bird types for training a new species classification model.

## Overview

The training system expects images organized by bird species in a specific directory structure. You'll need to:

1. Organize your videos by bird species
2. Extract frames from videos
3. Organize frames into train/val splits
4. Train the model

## Step 1: Organize Your Videos

Create a directory structure with your videos organized by bird species:

```
training_videos/
├── Bald_Eagle/
│   ├── video1.mp4
│   ├── video2.mp4
│   └── ...
├── Red_Tailed_Hawk/
│   ├── video1.mp4
│   └── ...
├── Brewer's_Blackbird/
│   └── ...
└── ...
```

**Important Notes:**
- Use filesystem-safe names (replace spaces with underscores, avoid special characters)
- Supported video formats: `.mp4`, `.avi`, `.mov`, `.mkv`
- Each folder name will become a class name in the model

## Step 2: Extract Frames from Videos

Use the provided script to extract frames from your videos:

```bash
python scripts/prepare_training_from_videos.py \
    --input-dir training_videos \
    --output-dir data/bird_species \
    --frames-per-video 50 \
    --val-split 0.2
```

**Script Options:**
- `--input-dir`: Directory containing species folders with videos
- `--output-dir`: Output directory for extracted frames (default: `data/bird_species`)
- `--frames-per-video`: Number of frames to extract per video (default: 50)
- `--val-split`: Ratio of data to use for validation (default: 0.2 = 20%)
- `--frame-interval`: Extract every Nth frame (default: auto-calculated)
- `--min-frames-per-class`: Minimum frames required per class (default: 10)

## Step 3: Verify Dataset Structure

After extraction, you should have:

```
data/bird_species/
├── train/
│   ├── Bald_Eagle/
│   │   ├── frame_000001.jpg
│   │   ├── frame_000002.jpg
│   │   └── ...
│   ├── Red_Tailed_Hawk/
│   │   └── ...
│   └── ...
├── val/
│   ├── Bald_Eagle/
│   │   └── ...
│   └── ...
└── dataset_info.yaml
```

## Step 4: Train the Model

Once your dataset is prepared, train the model:

```bash
python scripts/train_bird_species_classifier.py \
    --data-dir data/bird_species \
    --epochs 100 \
    --batch-size 16 \
    --model-size n
```

**Training Options:**
- `--data-dir`: Path to your prepared dataset
- `--epochs`: Number of training epochs (default: 100)
- `--batch-size`: Batch size (default: 16, adjust based on GPU memory)
- `--model-size`: Model size - `n` (nano), `s` (small), `m` (medium), `l` (large), `x` (xlarge)
- `--imgsz`: Image size (default: 224 for classification)
- `--device`: Device to use (`auto`, `cpu`, `cuda`)

## Best Practices

### Video Quality
- Use videos with clear, well-lit bird images
- Avoid videos with heavy motion blur
- Ensure birds are clearly visible (not too far away)

### Frame Selection
- Extract frames where birds are clearly visible
- Consider extracting frames at different time intervals to get variety
- Aim for at least 50-100 frames per species for good results

### Dataset Balance
- Try to have similar numbers of frames per species
- Minimum recommended: 10-20 frames per species
- More data generally leads to better results

### Validation Split
- Use 20% of data for validation (default)
- This helps monitor training progress and prevent overfitting

## Example Workflow

```bash
# 1. Organize your videos
mkdir -p training_videos/Bald_Eagle
cp my_eagle_videos/*.mp4 training_videos/Bald_Eagle/

# 2. Extract frames
python scripts/prepare_training_from_videos.py \
    --input-dir training_videos \
    --output-dir data/bird_species \
    --frames-per-video 100

# 3. Check the dataset
ls data/bird_species/train/
cat data/bird_species/dataset_info.yaml

# 4. Train the model
python scripts/train_bird_species_classifier.py \
    --data-dir data/bird_species \
    --epochs 100 \
    --batch-size 16 \
    --model-size n \
    --yes
```

## Troubleshooting

### "No classes found in train directory"
- Make sure your videos are organized in species folders
- Check that the extraction script completed successfully
- Verify the output directory structure

### "Not enough training samples"
- Increase `--frames-per-video` to extract more frames
- Add more videos for species with low frame counts
- Lower `--min-frames-per-class` if you have limited data

### Training is slow
- Reduce `--batch-size` if running out of memory
- Use a smaller model size (`n` instead of `s` or `m`)
- Consider using GPU (`--device cuda`)

## Next Steps

After training:
1. The model will be saved to `models/bird_species_classifier.pt`
2. The config will be automatically updated
3. SkyGuard will use the new model for species classification

You can test the model using:
```bash
python scripts/test_videos_folder.py --save-segmented-images
```


