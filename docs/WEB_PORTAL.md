# SkyGuard Web Portal

![SkyGuard Logo](../skyGuardShield.png)

A comprehensive web-based interface for managing and monitoring your SkyGuard raptor detection system.

## 🌐 **Features**

### **Dashboard**
- **Real-time System Status**: Monitor system, camera, AI model, and alert status
- **Detection Statistics**: View total detections, daily/weekly/monthly counts
- **Recent Detections**: Browse latest detections with images and details
- **System Information**: Uptime, last detection, camera specs, AI confidence
- **Quick Actions**: Test camera, AI model, and alert systems

### **Detection Management**
- **Detection History**: Browse all detections with search and filtering
- **Detection Images**: View captured images from detections
- **Detection Details**: Confidence scores, timestamps, bounding boxes
- **Export Functionality**: Download detection data and images

### **Configuration Management**
- **System Settings**: Detection interval, history limits, debug mode
- **Camera Configuration**: Resolution, FPS, rotation, flip settings
- **AI Model Settings**: Confidence thresholds, NMS settings, model selection
- **Notification Settings**: Audio, SMS, email, Discord webhook alert configuration
- **Real-time Updates**: Changes take effect immediately

### **System Monitoring**
- **Camera Management**: Test camera connection, capture test images
- **AI Model Management**: Test model loading, performance monitoring
- **Alert System**: Test notification systems, configure alert settings
- **System Logs**: View real-time logs with filtering and search
- **Statistics**: CPU, memory, disk usage, detection rates

## 🚀 **Quick Start**

### **Installation**

```bash
# Install web portal dependencies
pip install -r requirements-web.txt
```

### **Set a login password (required)**

The portal requires authentication. Create a `.env` file from the template and
set a strong password **before** the first start:

```bash
cp .env.example .env
chmod 600 .env
# then edit .env and set SKYGUARD_WEB_PASSWORD=<a strong passphrase>
```

`.env` is loaded automatically at startup and is gitignored, so your password
is never committed. If you skip this step, the portal still refuses anonymous
access — it generates a **random one-time password** and prints it to the
console (and `logs/web.log`) on every startup, which you must copy to log in.

```bash
# Start the web portal (loads .env automatically)
python scripts/start_web_portal.py
```

### **Access the Portal**

Open your web browser and navigate to:
```
http://localhost:8080
```

You will be redirected to a **login page**. Sign in with the username
(default `admin`) and the password you configured. Use the **Log out** link in
the sidebar to end your session.

### **Default Configuration**

- **Host**: `127.0.0.1` (loopback only — not reachable from the network unless
  you explicitly pass `--host 0.0.0.0`)
- **Port**: `8080`
- **Authentication**: Required (session login; see above)
- **Debug Mode**: Disabled by default, and **refused** on any non-loopback host

> **Note:** The bundled `scripts/start_skyguard.sh` intentionally launches the
> portal with `--host 0.0.0.0` so you can reach it from a phone or laptop on
> your LAN. Because that exposes it to the network, a strong
> `SKYGUARD_WEB_PASSWORD` in `.env` is mandatory in that mode.

## ⚙️ **Configuration**

### **Command Line Options**

```bash
python scripts/start_web_portal.py [OPTIONS]

Options:
  --host HOST          Host to bind to (default: 127.0.0.1; use 0.0.0.0 to
                       expose on the local network)
  --port PORT          Port to bind to (default: 8080)
  --debug              Enable debug mode (ignored unless --host is loopback)
  --config CONFIG      Configuration file path
```

### **Environment Variables**

All security settings are supplied via environment variables (typically through
the gitignored `.env` file). Every value overrides the matching field in
`config/skyguard.yaml`.

| Variable | Purpose |
|----------|---------|
| `SKYGUARD_WEB_USERNAME` | Portal login username (default `admin`) |
| `SKYGUARD_WEB_PASSWORD` | Portal login password (hashed at startup) |
| `SKYGUARD_WEB_PASSWORD_HASH` | Pre-computed werkzeug hash (overrides the plaintext password) |
| `SKYGUARD_SECRET_KEY` | Flask session signing key (optional; a persistent key is generated at `data/.flask_secret` if unset) |
| `SKYGUARD_EMAIL_PASSWORD` | SMTP password for email alerts |
| `SKYGUARD_SMS_ACCOUNT_SID` / `SKYGUARD_SMS_AUTH_TOKEN` | Twilio SMS credentials |
| `SKYGUARD_PUSH_API_KEY` | Pushbullet API key |
| `SKYGUARD_DISCORD_WEBHOOK` | Discord webhook URL |

```bash
# Example .env contents
SKYGUARD_WEB_USERNAME=admin
SKYGUARD_WEB_PASSWORD=a-long-random-passphrase
SKYGUARD_EMAIL_PASSWORD=your-smtp-app-password
```

To generate a password hash instead of storing the plaintext:

```bash
python -c "from werkzeug.security import generate_password_hash as g; print(g('yourpassword'))"
```

## 📱 **Web Interface Guide**

### **Dashboard**

The main dashboard provides an overview of your SkyGuard system:

1. **Status Indicators**: 
   - 🟢 **System**: Running/Stopped
   - 🟢 **Camera**: Connected/Disconnected
   - 🟢 **AI Model**: Loaded/Not Loaded
   - 🟢 **Alerts**: Enabled/Disabled

2. **Statistics Cards**:
   - Total detections
   - Today's detections
   - This week's detections
   - This month's detections

3. **Recent Detections**:
   - Latest 5 detections with images
   - Detection details and timestamps
   - Confidence scores

4. **Quick Actions**:
   - Test camera connection
   - Test AI model
   - Test alert system
   - Configure system

### **Detection Management**

Browse and manage all detections:

1. **Search and Filter**:
   - Search by detection ID or class
   - Filter by date range (today, week, month)
   - Sort by timestamp or confidence

2. **Detection Cards**:
   - Detection image thumbnails
   - Class and confidence information
   - Timestamp and bounding box details
   - Click to view full details

3. **Export Options**:
   - Download detection images
   - Export detection data (CSV, JSON)
   - Generate detection reports

### **Configuration Management**

Configure all aspects of your SkyGuard system:

1. **System Settings**:
   - Detection interval (0.1-10 seconds)
   - Maximum detection history (100-10000)
   - Debug mode toggle

2. **Camera Settings**:
   - Resolution (320x240 to 1920x1080)
   - FPS (1-60)
   - Rotation and flip settings

3. **AI Model Settings**:
   - Confidence threshold (0.0-1.0)
   - NMS threshold (0.0-1.0)
   - Model selection

4. **Notification Settings**:
   - Audio alerts (enabled/disabled, volume control)
   - SMS alerts (enabled/disabled, requires Twilio account)
   - Email alerts (enabled/disabled, requires SMTP server)
   - Discord webhook alerts (enabled/disabled, free webhook setup)
   
   **Discord Webhook Setup:**
   1. Open your Discord server
   2. Go to **Server Settings** → **Integrations** → **Webhooks**
   3. Click **New Webhook** or **Create Webhook**
   4. Choose a channel for alerts
   5. Name the webhook (e.g., "SkyGuard Alerts")
   6. Click **Copy Webhook URL**
   7. Paste the URL into the Discord Webhook URL field in the web portal
   8. Optionally set a custom bot username
   9. Enable Discord alerts and save

### **System Monitoring**

Monitor and test system components:

1. **Camera Management**:
   - Test camera connection
   - Capture test images
   - View camera specifications
   - Monitor camera performance

2. **AI Model Management**:
   - Test model loading
   - Monitor model performance
   - View model information
   - Test detection accuracy

3. **Alert System**:
   - Test notification systems
   - Configure alert settings
   - Monitor alert delivery
   - View alert history

4. **System Logs**:
   - Real-time log viewing
   - Log filtering and search
   - Log level filtering
   - Log export

5. **Statistics**:
   - System resource usage
   - Detection statistics
   - Performance metrics
   - Historical data

## 🔧 **Advanced Features**

### **Real-time Updates**

The web portal automatically refreshes every 5 seconds to show:
- Latest system status
- New detections
- Updated statistics
- Current configuration

### **Responsive Design**

The interface is optimized for:
- **Desktop**: Full-featured interface
- **Tablet**: Touch-friendly navigation
- **Mobile**: Compact view with essential features

### **Security Features**

- **Authentication**: Every route requires a logged-in session. Unauthenticated
  API calls return `401`; browser requests are redirected to the login page.
- **Loopback by default**: Binds to `127.0.0.1` unless you explicitly expose it
  with `--host 0.0.0.0`.
- **Hashed credentials**: The password is stored only as a werkzeug hash; the
  plaintext lives solely in your gitignored `.env`.
- **CSRF protection**: All state-changing requests (config updates, restart)
  require a per-session CSRF token, sent automatically by the UI.
- **Same-origin only**: Cross-origin (CORS) access is disabled.
- **Config safety**: Model paths supplied through the config API are validated
  (no absolute, UNC, `..`, or non-`models/` paths) to prevent loading arbitrary
  files. Credential fields are redacted in API responses.
- **Debug lockout**: The Werkzeug debugger cannot be enabled on a non-loopback
  bind address.
- **HTTPS**: Terminate TLS at a reverse proxy (see Deployment) for encrypted
  access beyond localhost.

### **API Endpoints**

All routes below require an authenticated session. Endpoints that change state
(`POST`) additionally require the `X-CSRF-Token` header; the web UI adds this
automatically, and scripted clients must first obtain the token from the
`<meta name="csrf-token">` tag on any page.

```
GET  /login                   # Login page
POST /login                   # Authenticate (username, password)
GET  /logout                  # End session

GET  /api/status              # System status
GET  /api/detections          # Recent detections
GET  /api/detections/{id}     # Specific detection
GET  /api/detections/{id}/image # Detection image
GET  /api/config              # Current configuration (secrets redacted)
POST /api/config              # Update configuration (CSRF required)
GET  /api/camera/test         # Test camera
GET  /api/ai/test             # Test AI model
GET  /api/alerts/test         # Test alerts
POST /api/system/restart      # Restart system (CSRF required; POST only)
GET  /api/logs                # System logs
GET  /api/stats               # System statistics
```

> The previous unauthenticated `GET /api/system/restart` route has been removed;
> restart is now `POST` only and CSRF-protected.

## 🚀 **Deployment**

### **Local Development**

```bash
# Debug mode only works on loopback (it is ignored on 0.0.0.0)
python scripts/start_web_portal.py --debug

# Expose on the LAN (requires SKYGUARD_WEB_PASSWORD to be set in .env)
python scripts/start_web_portal.py --host 0.0.0.0 --port 8080
```

### **Production Deployment**

Set your secrets in `.env` first (see Environment Variables), then:

```bash
# Start as background service (loads .env automatically)
nohup python scripts/start_web_portal.py --host 0.0.0.0 > logs/web.log 2>&1 &

# Or use systemd — reference the env file so secrets are available to the unit:
#   [Service]
#   EnvironmentFile=/opt/SkyGuard/.env
#   ExecStart=/opt/SkyGuard/venv/bin/python scripts/start_web_portal.py --host 0.0.0.0
sudo systemctl start skyguard-web
sudo systemctl enable skyguard-web
```

For anything beyond your trusted LAN, run behind a TLS-terminating reverse
proxy (below) and keep the app bound to `127.0.0.1`.

### **Docker Deployment**

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . .

RUN pip install -r requirements-web.txt

EXPOSE 8080

# Provide SKYGUARD_WEB_PASSWORD (and any notification secrets) at runtime, e.g.
#   docker run -e SKYGUARD_WEB_PASSWORD=... -p 8080:8080 skyguard-web
CMD ["python", "scripts/start_web_portal.py", "--host", "0.0.0.0"]
```

### **Nginx Reverse Proxy**

```nginx
server {
    listen 80;
    server_name skyguard.local;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🔧 **Troubleshooting**

### **Common Issues**

**Web portal won't start:**
```bash
# Check if dependencies are installed
pip install -r requirements-web.txt

# Check if port is available
netstat -tulpn | grep :8080

# Check configuration file
python -c "import yaml; yaml.safe_load(open('config/skyguard.yaml'))"
```

**Can't access from other devices:**
```bash
# The portal binds to 127.0.0.1 by default. To reach it from another device,
# start it on the LAN interface AND make sure a password is set in .env:
python scripts/start_web_portal.py --host 0.0.0.0

# Open the firewall for the port
sudo ufw allow 8080
```

**Forgot the password / locked out:**
```bash
# Set (or reset) it in .env, then restart the portal:
echo 'SKYGUARD_WEB_PASSWORD=a-new-strong-passphrase' >> .env

# If no password was ever set, a temporary one is printed at startup:
grep -i "temporary login" logs/web.log
```

**Getting 401/redirected to /login on API calls:**
```bash
# API clients must authenticate (POST /login) and send the session cookie plus
# the X-CSRF-Token header (from the page's <meta name="csrf-token">) on POSTs.
```

**Configuration not saving:**
```bash
# Check file permissions
ls -la config/skyguard.yaml

# Check if SkyGuard is running
ps aux | grep skyguard
```

**Images not loading:**
```bash
# Check if detection images exist
ls -la data/detections/

# Check file permissions
chmod 755 data/detections/
```

### **Performance Optimization**

**For Raspberry Pi:**
```bash
# Reduce image quality
# Edit config/skyguard.yaml
camera:
  width: 640
  height: 480
  fps: 15

# Reduce detection history
system:
  max_detection_history: 500
```

**For High-Performance Systems:**
```bash
# Increase image quality
camera:
  width: 1280
  height: 720
  fps: 30

# Increase detection history
system:
  max_detection_history: 5000
```

## 📞 **Support**

- **Documentation**: Check `docs/` directory
- **Issues**: GitHub Issues
- **Logs**: Check `web_portal.log`
- **API**: Use browser developer tools to inspect API calls

## 🎯 **Next Steps**

1. **Set a password**: `cp .env.example .env` and set `SKYGUARD_WEB_PASSWORD`
2. **Start the web portal**: `python scripts/start_web_portal.py`
3. **Log in**: Open `http://localhost:8080` and sign in as `admin`
4. **Configure your system**: Use the configuration section
4. **Test all components**: Use the quick actions
5. **Monitor detections**: Check the detection history
6. **Optimize settings**: Adjust based on your needs

---

**Congratulations!** Your SkyGuard system now has a powerful web interface for easy management and monitoring! 🦅
