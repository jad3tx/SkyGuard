# AirBirds Dataset Download System

This directory contains the new unified AirBirds dataset download system that replaces the old fragmented scripts.

## 🚀 **New Scripts (Use These)**

### **Primary Scripts**
- **`download_airbirds_universal.py`** - Universal download script with multiple fallback methods
- **`download_airbirds_alternative.py`** - Alternative method that doesn't require datasets library
- **`install_datasets_and_download.py`** - Installs datasets library and downloads dataset

### **Diagnostic Scripts**
- **`diagnose_pi5_datasets.py`** - Diagnoses datasets library issues on Pi 5

## 📋 **Usage**

### **Recommended Method (Universal)**
```bash
# Try multiple methods automatically
python scripts/download_airbirds_universal.py
```

### **Alternative Method (No datasets library required)**
```bash
# Works without datasets library
python scripts/download_airbirds_alternative.py
```

### **Install datasets library first**
```bash
# Install datasets library and download
python scripts/install_datasets_and_download.py
```

### **Diagnose Pi 5 issues**
```bash
# Diagnose why datasets library isn't working
python scripts/diagnose_pi5_datasets.py
```

## 🔧 **Features**

### **Universal Download Script**
- ✅ **Multiple fallback methods** - tries different approaches automatically
- ✅ **Automatic datasets library installation** - installs if missing
- ✅ **Comprehensive error handling** - provides helpful error messages
- ✅ **Pi 5 compatibility** - works on Raspberry Pi 5

### **Alternative Download Script**
- ✅ **No external dependencies** - works without datasets library
- ✅ **Sample dataset creation** - creates test dataset when full download fails
- ✅ **YOLO format conversion** - automatically converts to YOLO format
- ✅ **Cross-platform compatibility** - works on Windows, Linux, Pi

### **Diagnostic Script**
- ✅ **System information** - shows platform and Python details
- ✅ **Dependency checking** - identifies missing packages
- ✅ **Alternative installation methods** - tries different pip options
- ✅ **Solution suggestions** - provides specific fixes

## 📁 **Dataset Structure**

After successful download, the dataset will be organized as:

```
data/airbirds/
├── images/
│   ├── train/          # Training images
│   └── val/            # Validation images
├── labels/
│   ├── train/          # Training labels (YOLO format)
│   └── val/            # Validation labels (YOLO format)
├── dataset.yaml        # YOLO dataset configuration
└── dataset_info.yaml   # Dataset metadata
```

## 🛠️ **Troubleshooting**

### **Pi 5 Issues**
If you're having trouble on Pi 5:

1. **Run diagnostic script:**
   ```bash
   python scripts/diagnose_pi5_datasets.py
   ```

2. **Try alternative method:**
   ```bash
   python scripts/download_airbirds_alternative.py
   ```

3. **Install system dependencies:**
   ```bash
   sudo apt update
   sudo apt install -y python3-dev python3-pip build-essential
   sudo apt install -y libffi-dev libssl-dev
   ```

### **Memory Issues**
If you get out-of-memory errors:

1. **Use alternative method** (creates smaller sample dataset)
2. **Close other applications** to free up RAM
3. **Use swap space** if available

### **Network Issues**
If download fails:

1. **Check internet connection**
2. **Try alternative method** (creates sample dataset)
3. **Use mobile hotspot** if WiFi is unstable

## 🗑️ **Removed Scripts**

The following old scripts have been removed and replaced:

- ❌ `download_airbirds.py` → ✅ `download_airbirds_universal.py`
- ❌ `download_airbirds_fixed.py` → ✅ `download_airbirds_alternative.py`
- ❌ `download_airbirds_hf.py` → ✅ `install_datasets_and_download.py`
- ❌ `setup_airbirds_fixed.py` → ✅ `download_airbirds_universal.py`
- ❌ `setup_airbirds_simple.py` → ✅ `download_airbirds_alternative.py`
- ❌ `inspect_airbirds.py` → ✅ `diagnose_pi5_datasets.py`

## 📊 **What's New**

### **Improvements**
- ✅ **Unified interface** - single script handles all scenarios
- ✅ **Better error handling** - clear error messages and solutions
- ✅ **Pi 5 compatibility** - works on latest Raspberry Pi hardware
- ✅ **Fallback options** - multiple methods if one fails
- ✅ **Sample dataset** - creates test data when full download fails

### **Compatibility**
- ✅ **Windows** - works on development machines
- ✅ **Linux** - works on servers and workstations  
- ✅ **Raspberry Pi** - optimized for Pi 4 and Pi 5
- ✅ **No datasets library** - alternative method works without it

## 🎯 **Quick Start**

For most users, simply run:

```bash
python scripts/download_airbirds_universal.py
```

This will automatically:
1. Check if datasets library is available
2. Install it if needed
3. Download the full AirBirds dataset
4. Convert to YOLO format
5. Create configuration files

If that fails, try:

```bash
python scripts/download_airbirds_alternative.py
```

This creates a sample dataset for testing and development.
