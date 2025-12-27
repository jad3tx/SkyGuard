# Screenshot Guidelines for README

This directory contains screenshots used in the main README.md to showcase SkyGuard's features.

## Recommended Screenshots

### 1. **Web Portal Dashboard** (`web_portal_dashboard.png`)
**What to capture:**
- Full dashboard view showing:
  - System status indicators (all green/healthy)
  - Detection statistics (total detections, recent activity)
  - Recent detections list with thumbnails
  - System information panel
- **Best if:** Dashboard shows some recent detections (not empty)
- **Size:** 1920x1080 or similar (will be resized in README)
- **Format:** PNG (for transparency) or JPG

### 2. **Live Detection** (`live_detection.png`)
**What to capture:**
- Camera feed with active detection:
  - Bird/raptor visible in frame
  - Bounding box drawn around detection
  - Confidence score displayed
  - Species label (if species classification is enabled)
- **Best if:** Clear, well-lit image with a visible bird
- **Tip:** Use a detection from your actual system, not a test image

### 3. **Detection History** (`detection_history.png`)
**What to capture:**
- Detection history page showing:
  - List of detections with thumbnails
  - Timestamps visible
  - Confidence scores
  - Species names (if available)
  - Filter/search functionality visible
- **Best if:** Shows multiple detections (3-5+) to demonstrate it's working

### 4. **System Configuration** (`system_config.png`)
**What to capture:**
- Configuration page showing:
  - Camera settings section
  - AI model settings
  - Notification settings
  - Clean, organized layout
- **Best if:** Shows the interface is user-friendly and comprehensive

## Optional Additional Screenshots

### 5. **Hardware Setup** (`hardware_setup.png`)
- Physical setup showing:
  - Raspberry Pi with camera
  - Mounting position
  - Clean installation
- **Best if:** Professional-looking, well-lit photo

### 6. **Alert Notification** (`alert_notification.png`)
- Screenshot of:
  - SMS alert on phone
  - Push notification
  - Email alert
- **Best if:** Shows actual alert from the system

### 7. **Detection Detail View** (`detection_detail.png`)
- Single detection detail page showing:
  - Full-size detection image
  - All metadata (timestamp, confidence, species, etc.)
  - Bounding box coordinates
  - Polygon segmentation (if available)

## Screenshot Best Practices

1. **Resolution:** 
   - Minimum: 1920x1080
   - Recommended: 2560x1440 or higher
   - Will be displayed at ~800-1000px wide in README

2. **Format:**
   - PNG for screenshots with text (better quality)
   - JPG for photos (smaller file size)
   - Keep file sizes reasonable (< 500KB if possible)

3. **Content:**
   - Remove any sensitive information (IP addresses, personal data)
   - Use real data when possible (not dummy/test data)
   - Show the system working, not error states

4. **Styling:**
   - Use browser zoom to make text readable
   - Hide browser UI if possible (F11 for fullscreen)
   - Use a clean, modern browser theme

5. **Naming:**
   - Use descriptive, lowercase names with underscores
   - Match the names used in README.md exactly

## Current Screenshot Placeholders

The README currently references these screenshots:
- `docs/screenshots/web_portal_dashboard.png`
- `docs/screenshots/live_detection.png`
- `docs/screenshots/detection_history.png`
- `docs/screenshots/system_config.png`

Replace these placeholder paths with your actual screenshots when ready.

