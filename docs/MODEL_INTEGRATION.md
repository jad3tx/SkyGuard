# SkyGuard Model Integration Guide

![SkyGuard Logo](../skyGuardShield.png)

This guide explains how to download, integrate, and use AI models with SkyGuard for raptor detection.

## 🎯 **Model Options**

### **Option 1: Pre-trained YOLO Model (Recommended for Testing)**

The easiest way to get started is with a pre-trained YOLO model that can detect birds (class 14 in COCO dataset).

#### **Quick Setup:**
```bash
# Download YOLO11 segmentation model (recommended)
python -c "from ultralytics import YOLO; YOLO('yolo11n-seg.pt')"

# The model will be downloaded to the current directory
# Move it to the models directory
mv yolo11n-seg.pt models/yolo11n-seg.pt
```

The default configuration already uses `models/yolo11n-seg.pt`, so no config changes are needed.

#### **Manual Setup:**
```bash
# Download YOLO11 segmentation model
python -c "from ultralytics import YOLO; YOLO('yolo11n-seg.pt')"

# Move to models directory
mv yolo11n-seg.pt models/yolo11n-seg.pt

# Verify configuration
# Check that config/skyguard.yaml has:
# ai:
#   model_path: models/yolo11n-seg.pt
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
  model_path: "models/yolo11n-seg.pt"  # YOLO11 segmentation model
  model_type: "yolo"  # "yolo" or "tensorflow"
  confidence_threshold: 0.6
  nms_threshold: 0.5
  input_size: 1080
  classes:
    - "bird"
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
python -c "from ultralytics import YOLO; YOLO('yolo11n-seg.pt')"

# Replace old model
mv yolo11n-seg.pt models/yolo11n-seg.pt

# Test new model
python -c "from ultralytics import YOLO; model = YOLO('models/yolo11n-seg.pt'); print('Model loaded successfully')"
```

### **Switch Between Models:**
```bash
# Backup current model
cp models/yolo11n-seg.pt models/yolo11n-seg_backup.pt

# Download and switch to different model
python -c "from ultralytics import YOLO; YOLO('yolo11s-seg.pt')"
mv yolo11s-seg.pt models/yolo11s-seg.pt

# Update config/skyguard.yaml to use new model
# ai:
#   model_path: models/yolo11s-seg.pt
```

## 🐛 **Troubleshooting**

### **Common Issues:**

#### **Model Not Found:**
```
Error: Model file not found: models/yolo11n-seg.pt
```
**Solution:** Download the model:
```bash
python -c "from ultralytics import YOLO; YOLO('yolo11n-seg.pt')"
mv yolo11n-seg.pt models/yolo11n-seg.pt
```

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
