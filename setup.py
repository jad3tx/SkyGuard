#!/usr/bin/env python3
"""
SkyGuard - Open-Source Raptor Alert System
Setup script for installation and configuration
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements-minimal.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="skyguard",
    version="0.1.0",
    author="John Daughtridge",
    author_email="johnd@tamu.edu",
    description="Open-source AI-powered raptor alert system for small poultry farms",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/jad3tx/SkyGuard",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Home Automation",
        "Topic :: Multimedia :: Video :: Capture",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ],
        "ai": [
            "torch>=2.0.0",
            "torchvision>=0.15.0",
            "ultralytics>=8.0.0",
        ],
        "raspberry-pi": [
            "RPi.GPIO>=0.7.1",
            "picamera2>=0.3.0",
            "adafruit-circuitpython-neopixel>=6.3.0",
        ],
        "jetson": [
            # Note: PyTorch and torchvision should be installed from NVIDIA's repository
            # See requirements-jetson.txt for details
            "ultralytics>=8.0.0",
            "opencv-python>=4.8.0",
            "numpy>=1.24.0",
        ],
        "notifications": [
            "twilio>=8.5.0",
            "pushbullet.py>=0.11.0",
        ],
        "all": [
            "torch>=2.0.0",
            "torchvision>=0.15.0",
            "ultralytics>=8.0.0",
            "twilio>=8.5.0",
            "pushbullet.py>=0.11.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "skyguard=skyguard.main:main",
            "skyguard-train=skyguard.training.train_model:main",
            "skyguard-setup=skyguard.setup.configure:main",
        ],
    },
    include_package_data=True,
    package_data={
        "skyguard": [
            "config/*.yaml",
            "models/*.h5",
            "models/*.pt",
            "data/sample/*.jpg",
            "docs/*.md",
        ],
    },
)
