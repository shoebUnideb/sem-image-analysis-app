# SEM Image Analysis Tool

## Overview
A web-based application for analyzing Scanning Electron Microscope (SEM) images to extract grain statistics. This tool uses computer vision and image processing techniques to segment, analyze, and visualize grain properties in SEM images. <br>
This project integrates advanced image processing algorithms (watershed segmentation, distance transforms, morphological operations) with web technologies to create an accessible tool for materials scientists. It handles memory management for large images and generates statistical visualizations in real-time.

## Features
- Automated Image Processing: Performs watershed segmentation to identify individual grains
- Comprehensive Analysis: Measures grain area, perimeter, orientation, and shape characteristics
- Interactive Visualization: Displays segmented images and colored grain representations
- Statistical Outputs: Provides summary statistics and distributional analysis
- Data Export: Generates downloadable CSV reports with all measurements

## Requirements
- Flask (Backend)
- Bootstrap 5 (Frontend)
- OpenCV & scikit-image (Image Processing)
- Matplotlib (Visualization)
- NumPy & SciPy (Numerical Processing)

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


## Use Cases
To help in statistical analysis of the SEM images
- Materials science research
- Quality control in manufacturing
- Educational tool for microscopy analysis
- Metallurgical studies