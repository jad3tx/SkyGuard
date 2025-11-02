# SkyGuard Model Integration Guide

![SkyGuard Logo](../skyGuardShield.png)

This guide explains how to download, integrate, and use AI models with SkyGuard for raptor detection.

## 🎯 **Model Options**

### **Option 1: Pre-trained YOLO Model (Recommended for Testing)**

The easiest way to get started is with a pre-trained YOLO model that can detect birds (class 14 in COCO dataset).

#### **Quick Setup:**
```bash
python scripts/setup_model.py
```

This will:
- Download YOLOv8n (nano) model
- Copy it to `models/raptor_detector.pt`
- Update SkyGuard configuration
- Test the integration

#### **Manual Setup:**
```bash
# Download model
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

# Copy to SkyGuard location
cp yolov8n.pt models/raptor_detector.pt

# Update config
python -c "
import yaml
with open('config/skyguard.yaml', 'r') as f: config = yaml.safe_load(f)
config['ai']['model_path'] = 'models/raptor_detector.pt'
config['ai']['model_type'] = 'yolo'
with open('config/skyguard.yaml', 'w') as f: yaml.dump(config, f)
"
```

### **Option 2: Custom Dataset Training**

If you have your own raptor images, you can train a custom model.

#### **Prepare Your Dataset:**
1. **Organize images** in YOLO format:
   ```
   data/custom/
   ├── images/
   │   ├── train/
   │   └── val/
   └── labels/
       ├── train/
       └── val/
   ```

2. **Create dataset.yaml:**
   ```yaml
   path: data/custom
   train: images/train
   val: images/val
   nc: 1
   names: ['raptor']
   ```

3. **Train model:**
   ```bash
   python -m skyguard.training.train_model --data-path data/custom/dataset.yaml
   ```

## 🔧 **Model Configuration**

### **Configuration File: `config/skyguard.yaml`**

```yaml
ai:
  model_path: "models/raptor_detector.pt"
  model_type: "yolo"  # "yolo" or "tensorflow"
  confidence_threshold: 0.5
  nms_threshold: 0.4
  input_size: [640, 640]
  classes:
    - "bird"
    # OR for COCO dataset:
    # - "person", "bicycle", "car", ..., "bird", ...
```

### **Model Performance Tuning:**

#### **Confidence Threshold:**
- **0.3-0.4**: More detections, higher false positives
- **0.5-0.6**: Balanced (recommended)
- **0.7-0.8**: Fewer detections, higher precision

#### **Input Size:**
- **416x416**: Faster, less accurate
- **640x640**: Balanced (recommended)
- **832x832**: Slower, more accurate

#### **Model Size:**
- **YOLOv8n**: Fastest, least accurate
- **YOLOv8s**: Good balance
- **YOLOv8m**: Better accuracy, slower
- **YOLOv8l**: High accuracy, slow
- **YOLOv8x**: Best accuracy, slowest

## 🚀 **Testing Your Model**

### **Test Model Loading:**
```bash
python -c "
from skyguard.core.detector import RaptorDetector
from skyguard.core.config_manager import ConfigManager
config = ConfigManager('config/skyguard.yaml').get_config()
detector = RaptorDetector(config['ai'])
print('Model loaded:', detector.load_model())
"
```

### **Test with Camera:**
```bash
python -m skyguard.main --verbose
```

### **Test Detection:**
```bash
python -c "
import cv2
from skyguard.core.detector import RaptorDetector
from skyguard.core.config_manager import ConfigManager

config = ConfigManager('config/skyguard.yaml').get_config()
detector = RaptorDetector(config['ai'])
detector.load_model()

# Test with webcam
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
if ret:
    detections = detector.detect(frame)
    print(f'Detections: {len(detections)}')
    for det in detections:
        print(f'  {det[\"class_name\"]}: {det[\"confidence\"]:.2f}')
cap.release()
"
```

## 📊 **Model Performance**

### **Expected Performance:**

| Model | Size | Speed (ms) | mAP@0.5 | Use Case |
|-------|------|------------|---------|----------|
| YOLOv8n | 6MB | ~15 | 0.37 | Testing, Raspberry Pi |
| YOLOv8s | 22MB | ~25 | 0.44 | Production, Desktop |
| YOLOv8m | 50MB | ~40 | 0.50 | High accuracy |
| Custom | 50MB | ~40 | 0.60+ | Raptor-specific |

### **Optimization Tips:**

#### **For Raspberry Pi:**
```yaml
ai:
  input_size: [416, 416]  # Smaller input
  confidence_threshold: 0.6  # Higher threshold
```

#### **For Desktop:**
```yaml
ai:
  input_size: [640, 640]  # Standard input
  confidence_threshold: 0.5  # Balanced threshold
```

## 🔄 **Model Updates**

### **Update Existing Model:**
```bash
# Download new model
python -c "from ultralytics import YOLO; YOLO('yolov8s.pt')"

# Replace old model
cp yolov8s.pt models/raptor_detector.pt

# Test new model
python scripts/setup_model.py
```

### **Switch Between Models:**
```bash
# Backup current model
cp models/raptor_detector.pt models/raptor_detector_backup.pt

# Switch to different model
cp models/yolov8s.pt models/raptor_detector.pt

# Update config if needed
python scripts/setup_model.py
```

## 🐛 **Troubleshooting**

### **Common Issues:**

#### **Model Not Found:**
```
Error: Model file not found: models/raptor_detector.pt
```
**Solution:** Run `python scripts/setup_model.py`

#### **Model Loading Error:**
```
Error: Failed to load model
```
**Solution:** Check model file integrity, re-download if needed

#### **Low Detection Accuracy:**
- Lower confidence threshold
- Use larger model (YOLOv8s instead of YOLOv8n)
- Train custom model on raptor data

#### **Slow Performance:**
- Use smaller model (YOLOv8n)
- Reduce input size to 416x416
- Increase confidence threshold

### **Performance Monitoring:**
```bash
# Monitor detection performance
python -c "
from skyguard.storage.event_logger import EventLogger
logger = EventLogger({'database_path': 'data/skyguard.db'})
logger.initialize()
stats = logger.get_detection_stats(days=7)
print(f'Detections last week: {stats[\"total_detections\"]}')
"
```

## 📚 **Additional Resources**

### **Datasets:**
- [COCO Dataset](https://cocodataset.org/) - General object detection
- [Open Images](https://storage.googleapis.com/openimages/web/index.html) - Large-scale dataset

### **Model Sources:**
- [Ultralytics YOLO](https://github.com/ultralytics/ultralytics) - YOLOv8 models
- [Hugging Face Models](https://huggingface.co/models) - Pre-trained models
- [Roboflow Universe](https://universe.roboflow.com/) - Custom datasets

### **Training Resources:**
- [YOLO Documentation](https://docs.ultralytics.com/)
- [Computer Vision Tutorials](https://pytorch.org/tutorials/beginner/transfer_learning_tutorial.html)
- [Data Augmentation](https://albumentations.ai/)

## 🎯 **Next Steps**

1. **Start with pre-trained model** for testing
2. **Collect your own raptor images** for better accuracy
3. **Train custom model** on your specific data
4. **Optimize for your hardware** (Raspberry Pi vs Desktop)
5. **Monitor performance** and adjust thresholds

Your SkyGuard system is now ready with AI-powered raptor detection! 🦅
