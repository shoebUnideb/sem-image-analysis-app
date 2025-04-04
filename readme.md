# SEM Image Analysis Tool

## Overview
A web-based application for analyzing Scanning Electron Microscope (SEM) images to extract grain statistics. This tool uses computer vision and image processing techniques to segment, analyze, and visualize grain properties in SEM images.
This project integrates multiple advanced image processing libraries (OpenCV, scikit-image) with web technologies to create an accessible tool for materials scientists.

## Features
- Automated grain segmentation using watershed algorithm
- Grain property measurements (area, perimeter, orientation, etc.)
- Statistical analysis of grain distributions
- Interactive visualization of segmented grains
- Downloadable CSV reports of analysis results

## Requirements
- Python 3.6+
- Flask
- OpenCV
- NumPy
- SciPy
- scikit-image
- Matplotlib

## Installation
```bash
git clone https://github.com/yourusername/sem-image-analysis.git
cd sem-image-analysis
pip install -r requirements.txt
```

## Usage
1. Run the application:
   ```bash
   python app.py
   ```
2. Open your browser and navigate to `http://localhost:5000`
3. Upload an SEM image
4. Set the pixel-to-micron conversion factor
5. Click "Analyze Image" and view results

## Why It's Complex
This project integrates advanced image processing algorithms (watershed segmentation, distance transforms, morphological operations) with web technologies to create an accessible tool for materials scientists. It handles memory management for large images and generates statistical visualizations in real-time.

## Use Cases
- Materials science research
- Quality control in manufacturing
- Educational tool for microscopy analysis
- Metallurgical studies