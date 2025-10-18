# Camera Snapshot Troubleshooting Guide

This guide helps resolve issues with the camera not showing in the "Recent Captures" area of the SkyGuard web portal.

## 🔍 **Quick Diagnosis**

Run the diagnostic script to identify the issue:

```bash
python scripts/diagnose_camera_snapshots.py
```

## 🛠️ **Common Issues & Solutions**

### **Issue 1: Camera Snapshot File Missing**

**Symptoms:**
- Web portal shows "No camera snapshot available"
- Recent captures area is blank
- Camera feed shows test image

**Solution:**
```bash
# Create test snapshot
python scripts/diagnose_camera_snapshots.py --create-test

# Or run the fix script
python scripts/fix_camera_snapshots.py
```

### **Issue 2: Main Process Not Running**

**Symptoms:**
- No camera snapshots being created
- Web portal shows test image
- Logs show "Main process not running"

**Solution:**
```bash
# Start the main system
./scripts/start_skyguard.sh

# Or using systemd
sudo systemctl start skyguard.service
```

### **Issue 3: Web Portal Not Running**

**Symptoms:**
- Can't access web portal
- API endpoints not responding
- Browser shows connection error

**Solution:**
```bash
# Start web portal
./scripts/start_skyguard.sh --web-only

# Or using systemd
sudo systemctl start skyguard-web.service
```

### **Issue 4: Camera Not Accessible**

**Symptoms:**
- Camera test fails
- "Camera not available" message
- Permission denied errors

**Solution:**
```bash
# Test camera manually
python -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'Failed')"

# Check camera permissions
ls -la /dev/video*

# Add user to video group (if needed)
sudo usermod -a -G video pi
```

### **Issue 5: Snapshot File Permissions**

**Symptoms:**
- Snapshot file exists but web portal can't read it
- Permission denied errors in logs

**Solution:**
```bash
# Fix file permissions
chmod 644 data/camera_snapshot.jpg
chmod 755 data/

# Or run the fix script
python scripts/fix_camera_snapshots.py
```

## 🔧 **Step-by-Step Fix Process**

### **Step 1: Check System Status**
```bash
# Check if services are running
sudo systemctl status skyguard.service skyguard-web.service

# Check if snapshot file exists
ls -la data/camera_snapshot.jpg

# Check file age
stat data/camera_snapshot.jpg
```

### **Step 2: Restart Services**
```bash
# Stop all services
./scripts/stop_skyguard.sh

# Wait a moment
sleep 3

# Start services
./scripts/start_skyguard.sh
```

### **Step 3: Create Test Snapshot**
```bash
# Create a test snapshot
python scripts/diagnose_camera_snapshots.py --create-test

# Verify it was created
ls -la data/camera_snapshot.jpg
```

### **Step 4: Test Web Portal**
```bash
# Test camera status API
curl http://localhost:8080/api/camera/status

# Test camera feed API
curl -I http://localhost:8080/api/camera/feed
```

### **Step 5: Check Logs**
```bash
# Check main system logs
tail -f logs/skyguard.log

# Check web portal logs
tail -f logs/web.log

# Check systemd logs
sudo journalctl -u skyguard.service -f
sudo journalctl -u skyguard-web.service -f
```

## 🐛 **Advanced Troubleshooting**

### **Check Camera Hardware**
```bash
# List video devices
ls -la /dev/video*

# Test camera with v4l2
v4l2-ctl --list-devices

# Test camera with OpenCV
python -c "
import cv2
cap = cv2.VideoCapture(0)
if cap.isOpened():
    ret, frame = cap.read()
    if ret:
        print('Camera working - frame shape:', frame.shape)
    else:
        print('Camera opened but no frame')
    cap.release()
else:
    print('Camera not accessible')
"
```

### **Check Network Connectivity**
```bash
# Test web portal locally
curl http://localhost:8080/api/camera/status

# Test from another machine
curl http://<PI_IP>:8080/api/camera/status
```

### **Check File System**
```bash
# Check disk space
df -h

# Check data directory permissions
ls -la data/

# Check if directory is writable
touch data/test_file && rm data/test_file
```

## 🔄 **Automatic Fix Scripts**

### **Quick Fix**
```bash
# Run the automatic fix script
python scripts/fix_camera_snapshots.py
```

### **Full Diagnostic**
```bash
# Run comprehensive diagnostic
python scripts/diagnose_camera_snapshots.py
```

### **Restart Everything**
```bash
# Stop everything
./scripts/stop_skyguard.sh
sudo systemctl stop skyguard.service skyguard-web.service

# Start everything
./scripts/start_skyguard.sh
```

## 📋 **Verification Steps**

After applying fixes, verify everything is working:

1. **Check snapshot file exists and is recent:**
   ```bash
   ls -la data/camera_snapshot.jpg
   ```

2. **Test web portal:**
   - Open http://<PI_IP>:8080
   - Navigate to "Recent Captures" section
   - Verify image is displayed

3. **Test API endpoints:**
   ```bash
   curl http://localhost:8080/api/camera/status
   curl -I http://localhost:8080/api/camera/feed
   ```

4. **Check logs for errors:**
   ```bash
   tail -f logs/skyguard.log
   ```

## 🆘 **Still Not Working?**

If the issue persists:

1. **Check hardware:**
   - Ensure camera is properly connected
   - Try a different USB port
   - Test with a different camera

2. **Check software:**
   - Update system: `sudo apt update && sudo apt upgrade`
   - Reinstall OpenCV: `pip install --upgrade opencv-python`
   - Check Python version: `python3 --version`

3. **Check configuration:**
   - Verify camera settings in `config/skyguard.yaml`
   - Check camera source (usually 0 for first camera)

4. **Get help:**
   - Run diagnostic: `python scripts/diagnose_camera_snapshots.py`
   - Check logs: `tail -f logs/skyguard.log`
   - Contact support with diagnostic output

## 📊 **Expected Behavior**

When working correctly:

- ✅ Snapshot file exists at `data/camera_snapshot.jpg`
- ✅ File is updated every 3 seconds
- ✅ Web portal shows live camera feed
- ✅ Recent captures section displays current image
- ✅ API endpoints return valid responses

## 🔧 **Prevention**

To prevent future issues:

1. **Regular maintenance:**
   ```bash
   # Check system health
   ./deployment/scripts/health_check.sh
   ```

2. **Monitor logs:**
   ```bash
   # Set up log monitoring
   tail -f logs/skyguard.log | grep -i error
   ```

3. **Keep system updated:**
   ```bash
   # Update system regularly
   sudo apt update && sudo apt upgrade
   ```

4. **Backup configuration:**
   ```bash
   # Backup config files
   cp config/skyguard.yaml config/skyguard.yaml.backup
   ```
