# Training Videos Directory

This directory contains videos organized by bird species for training the species classification model.

## Structure

Place your videos in the appropriate species folder:

```
training_videos/
├── Bald_Eagle/
│   ├── video1.mp4
│   ├── video2.mp4
│   └── ...
├── Red_Tailed_Hawk/
│   └── ...
├── Brewers_Blackbird/
│   └── ...
└── ...
```

## Supported Video Formats

- `.mp4`
- `.avi`
- `.mov`
- `.mkv`

## Adding New Species

To add a new species folder:

1. Create a new folder with the species name (use underscores instead of spaces)
2. Place your videos in that folder
3. Example: `training_videos/Cooper_Hawk/video1.mp4`

## Naming Guidelines

- Use filesystem-safe names (replace spaces with underscores)
- Avoid special characters: `/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|`
- Examples:
  - ✅ `Bald_Eagle`
  - ✅ `Red_Tailed_Hawk`
  - ✅ `Brewers_Blackbird`
  - ❌ `Bald Eagle` (has space)
  - ❌ `Red-Tailed Hawk` (has hyphen)

## Next Steps

After organizing your videos:

1. **Extract frames from videos:**
   ```bash
   python scripts/prepare_training_from_videos.py \
       --input-dir training_videos \
       --output-dir data/bird_species \
       --frames-per-video 50
   ```

2. **Or extract bird crops using detection (recommended):**
   ```bash
   # For each species folder
   python scripts/test_videos_folder.py \
       --input-dir training_videos/Bald_Eagle \
       --output-dir training_output/Bald_Eagle \
       --save-crops \
       --save-json
   ```

3. **Train the model:**
   ```bash
   python scripts/train_bird_species_classifier.py \
       --data-dir data/bird_species \
       --epochs 100 \
       --batch-size 16 \
       --model-size n
   ```

## Current Species Folders

The following species folders have been created:

- `Bald_Eagle/`
- `Red_Tailed_Hawk/`
- `Brewers_Blackbird/`
- `Golden_Eagle/`
- `Red_Shouldered_Hawk/`
- `Cooper_Hawk/`
- `American_Kestrel/`
- `Peregrine_Falcon/`
- `Great_Horned_Owl/`
- `Barn_Owl/`

You can add more species folders as needed, or remove folders for species you don't have videos for.


