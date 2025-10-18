# SkyGuard AI Models

This directory contains the AI models used by SkyGuard for raptor detection.

## Model Files

### Current Models

- **raptor_detector.pt** - Main YOLO model for raptor detection (not included in repository due to size)
- **raptor_detector.onnx** - ONNX format model for cross-platform compatibility (optional)

### Model Specifications

- **Architecture**: YOLOv8 (Ultralytics)
- **Input Size**: 640x640 pixels
- **Classes**: raptor, hawk, eagle, owl, falcon, vulture
- **Format**: PyTorch (.pt) and ONNX (.onnx)
- **Size**: ~50MB (PyTorch), ~25MB (ONNX)

## Getting Models

### Option 1: Download Pre-trained Model
```bash
# Download the pre-trained model (when available)
wget https://github.com/jad3tx/SkyGuard/releases/download/v0.1.0/raptor_detector.pt -O models/raptor_detector.pt
```

### Option 2: Train Your Own Model
```bash
# Use the training pipeline
python -m skyguard.training.train_model --data-path data/training --epochs 100
```

### Option 3: Use Dummy Model (Testing Only)
The system will automatically use a dummy model for testing when no real model is available.

## Model Performance

### Accuracy Metrics
- **mAP@0.5**: 0.85+ (on validation set)
- **Precision**: 0.90+ (raptor class)
- **Recall**: 0.80+ (raptor class)
- **F1-Score**: 0.85+ (raptor class)

### Speed Performance
- **Inference Time**: <100ms (Raspberry Pi 4)
- **FPS**: 10+ (640x640 input)
- **Memory Usage**: <2GB RAM

## Model Training

### Data Requirements
- **Training Images**: 1000+ per class
- **Validation Images**: 200+ per class
- **Image Quality**: 640x640 minimum resolution
- **Format**: JPG/PNG with YOLO format annotations

### Training Process
1. **Data Collection**: Gather images of raptors and other birds
2. **Annotation**: Label images with bounding boxes
3. **Data Augmentation**: Apply rotations, brightness, contrast changes
4. **Training**: Train YOLO model with validation
5. **Evaluation**: Test on held-out test set
6. **Deployment**: Convert to production format

### Training Commands
```bash
# Basic training
python -m skyguard.training.train_model --data-path data/training

# Advanced training with custom parameters
python -m skyguard.training.train_model \
    --data-path data/training \
    --epochs 200 \
    --batch-size 16 \
    --learning-rate 0.001 \
    --img-size 640
```

## Model Updates

### Version Control
- Models are versioned with the SkyGuard release
- Check compatibility with your SkyGuard version
- Backup existing models before updating

### Update Process
1. Download new model file
2. Test with `skyguard --test-model`
3. Replace old model if performance is better
4. Update configuration if needed

## Troubleshooting

### Common Issues

**Model not found:**
```
Error: Model file not found: models/raptor_detector.pt
```
Solution: Download the model or use dummy mode for testing

**Model loading error:**
```
Error: Failed to load model: models/raptor_detector.pt
```
Solution: Check file integrity, re-download if corrupted

**Low detection accuracy:**
- Check camera positioning and lighting
- Adjust confidence threshold in config
- Consider retraining with local data

**Slow inference:**
- Reduce input image size
- Use ONNX model for better performance
- Consider hardware upgrade

### Performance Optimization

**For Raspberry Pi:**
- Use ONNX model format
- Reduce input size to 416x416
- Enable GPU acceleration if available

**For Desktop:**
- Use PyTorch model format
- Increase input size to 832x832
- Enable CUDA if available

## Future Models

### Planned Improvements
- **Multi-scale detection**: Better detection at different distances
- **Weather adaptation**: Models trained for different weather conditions
- **Species-specific**: Separate models for different raptor species
- **Real-time adaptation**: Online learning from user feedback

### Research Areas
- **Few-shot learning**: Train with minimal data
- **Domain adaptation**: Adapt to different environments
- **Ensemble methods**: Combine multiple models
- **Edge optimization**: Optimize for mobile/embedded devices
