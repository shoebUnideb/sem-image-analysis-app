import os
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename
import cv2
import numpy as np
from pathlib import Path
import matplotlib
matplotlib.use('Agg')  # Set the backend to non-interactive Agg
from matplotlib import pyplot as plt
from scipy import ndimage
from skimage import measure, color, io
from skimage.segmentation import clear_border
import tempfile
import shutil
import base64
import io as pyio

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def create_size_distribution_plots(areas, perimeters, image_name):
    """Create histograms and return as base64 encoded images"""
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
    
    # Plot area distribution
    ax1.hist(areas, bins='auto', color='blue', alpha=0.7)
    ax1.set_title(f'Grain Area Distribution - {image_name}')
    ax1.set_xlabel('Area (µm²)')
    ax1.set_ylabel('Frequency')
    ax1.grid(True, alpha=0.3)
    
    # Plot perimeter distribution
    ax2.hist(perimeters, bins='auto', color='green', alpha=0.7)
    ax2.set_title(f'Grain Perimeter Distribution - {image_name}')
    ax2.set_xlabel('Perimeter (µm)')
    ax2.set_ylabel('Frequency')
    ax2.grid(True, alpha=0.3)
    
    # Save plot to a bytes buffer
    buf = pyio.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
    plt.close(fig)  # THIS IS THE CRUCIAL ADDITION
    buf.seek(0)
    
    # Encode as base64
    plot_data = base64.b64encode(buf.read()).decode('ascii')
    return plot_data

def preprocess_image(image):
    """Preprocess the input image for grain analysis."""
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply Otsu's thresholding
    ret, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return gray, thresh

def perform_watershed_segmentation(image, thresh):
    """Perform watershed segmentation on the image."""
    # Define kernel for morphological operations
    kernel = np.ones((3,3), np.uint8)
    
    # Perform morphological operations
    opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)
    opening = clear_border(opening)  # Remove edge touching grains
    
    # Sure background area
    sure_bg = cv2.dilate(opening, kernel, iterations=2)
    
    # Finding sure foreground area
    dist_transform = cv2.distanceTransform(opening, cv2.DIST_L2, 3)
    ret, sure_fg = cv2.threshold(dist_transform, 0.2 * dist_transform.max(), 255, 0)
    
    # Finding unknown region
    sure_fg = np.uint8(sure_fg)
    unknown = cv2.subtract(sure_bg, sure_fg)
    
    # Marker labelling
    ret, markers = cv2.connectedComponents(sure_fg)
    markers = markers + 10
    markers[unknown == 255] = 0
    
    # Apply watershed
    markers = cv2.watershed(image, markers)
    
    # Mark boundaries in yellow
    image_copy = image.copy()
    image_copy[markers == -1] = [0, 255, 255]
    
    return markers, image_copy

def calculate_grain_properties(markers, intensity_image, image_name, pixels_to_um=0.5):
    """Calculate grain properties and return results as dictionary."""
    # Properties to measure
    prop_list = [
        'Area',
        'equivalent_diameter',
        'orientation',
        'MajorAxisLength',
        'MinorAxisLength',
        'Perimeter'
    ]
    
    # Get region properties
    regions = measure.regionprops(markers, intensity_image=intensity_image)
    
    # Sort regions by area to identify the background (typically largest)
    sorted_regions = sorted(regions, key=lambda x: x.area, reverse=True)
    
    # Remove the background (largest) region
    grain_regions = sorted_regions[1:]
    
    # Collect areas and perimeters for plotting
    areas = [region.area * (pixels_to_um ** 2) for region in grain_regions]
    perimeters = [region.perimeter * pixels_to_um for region in grain_regions]
    
    # Create distribution plots
    plot_data = create_size_distribution_plots(areas, perimeters, image_name)
    
    # Calculate basic statistics
    total_particles = len(grain_regions)
    total_image_area_pixels = intensity_image.shape[0] * intensity_image.shape[1]
    total_image_area_um2 = total_image_area_pixels * (pixels_to_um ** 2)
    
    # Calculate total grain area in µm²
    total_grain_area_pixels = sum(region.area for region in grain_regions)
    total_grain_area_um2 = total_grain_area_pixels * (pixels_to_um ** 2)
    
    # Calculate mean grain area in µm²
    mean_grain_area_um2 = total_grain_area_um2 / total_particles if total_particles > 0 else 0
    
    # Calculate surface coverage percentage
    surface_coverage = (total_grain_area_pixels / total_image_area_pixels) * 100
    
    # Calculate particle density (particles per µm²)
    particle_density = total_particles / total_image_area_um2 if total_image_area_um2 > 0 else 0
    
    # Prepare individual grain measurements
    grain_measurements = []
    for idx, region_props in enumerate(grain_regions, 1):
        measurement = {'grain_number': idx}
        
        for prop in prop_list:
            value = region_props[prop]
            
            # Convert measurements based on property type
            if prop == 'Area':
                value = value * (pixels_to_um ** 2)
            elif prop == 'orientation':
                value = value * 57.2958  # Convert radians to degrees
            elif prop == 'Perimeter':
                value = value * pixels_to_um
            
            # Round to 2 decimal places
            measurement[prop.lower()] = round(value, 2)
        
        grain_measurements.append(measurement)
    
    # Prepare results dictionary
    results = {
        'global_stats': {
            'total_particles': total_particles,
            'surface_coverage': round(surface_coverage, 2),
            'total_grain_area': round(total_grain_area_um2, 2),
            'mean_grain_area': round(mean_grain_area_um2, 2),
            'particle_density': round(particle_density, 6),
            'mean_area': round(np.mean(areas), 2) if areas else 0,
            'median_area': round(np.median(areas), 2) if areas else 0,
            'std_area': round(np.std(areas), 2) if areas else 0,
            'mean_perimeter': round(np.mean(perimeters), 2) if perimeters else 0,
            'median_perimeter': round(np.median(perimeters), 2) if perimeters else 0,
            'std_perimeter': round(np.std(perimeters), 2) if perimeters else 0,
        },
        'distribution_plot': plot_data,
        'individual_measurements': grain_measurements,
        'image_name': image_name
    }
    
    return results

def process_image_file(file_path, pixels_to_um):
    """Process an image file and return results."""
    try:
        # Read image
        image = cv2.imread(file_path)
        if image is None:
            raise ValueError("Could not read the image file")
        
        height, _, _ = image.shape
        cropped_img = image[:height - 80, :, :] if height > 80 else image
        
        # Process image
        gray, thresh = preprocess_image(cropped_img)
        markers, segmented_image = perform_watershed_segmentation(cropped_img, thresh)
        
        # Calculate grain properties
        image_name = os.path.basename(file_path)
        results = calculate_grain_properties(markers, gray, image_name, pixels_to_um)
        
        # Convert segmented image to base64 for display
        _, buffer = cv2.imencode('.jpg', segmented_image)
        segmented_img_str = base64.b64encode(buffer).decode('utf-8')
        results['segmented_image'] = segmented_img_str
        
        # Convert colored grains image to base64
        colored_grains = color.label2rgb(markers, bg_label=0)
        colored_grains = (colored_grains * 255).astype(np.uint8)
        _, buffer = cv2.imencode('.jpg', cv2.cvtColor(colored_grains, cv2.COLOR_RGB2BGR))
        colored_img_str = base64.b64encode(buffer).decode('utf-8')
        results['colored_image'] = colored_img_str
        
        return results
    
    except Exception as e:
        raise RuntimeError(f"Error processing image: {str(e)}")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if file:
            try:
                # Get pixel to micron conversion factor from form
                pixels_to_um = float(request.form.get('pixels_to_um', 0.5))
                
                # Save uploaded file temporarily
                filename = secure_filename(file.filename)
                temp_dir = tempfile.mkdtemp()
                file_path = os.path.join(temp_dir, filename)
                file.save(file_path)
                
                # Process the image
                results = process_image_file(file_path, pixels_to_um)
                
                # Clean up temporary files
                shutil.rmtree(temp_dir)
                
                return jsonify(results)
            
            except Exception as e:
                return jsonify({'error': str(e)}), 500
    
    return render_template('index.html')

@app.route('/download_csv', methods=['POST'])
def download_csv():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Create a temporary CSV file
        temp_dir = tempfile.mkdtemp()
        csv_path = os.path.join(temp_dir, f"{data['image_name']}_measurements.csv")
        
        with open(csv_path, 'w') as f:
            # Write global statistics
            f.write("Global Statistics\n")
            f.write(f"Total number of particles:,{data['global_stats']['total_particles']}\n")
            f.write(f"Surface Coverage (%):,{data['global_stats']['surface_coverage']}\n")
            f.write(f"Total grain area (µm²):,{data['global_stats']['total_grain_area']}\n")
            f.write(f"Mean grain area (µm²):,{data['global_stats']['mean_grain_area']}\n")
            f.write(f"Particle density (particles/µm²):,{data['global_stats']['particle_density']}\n")
            
            # Write distribution statistics
            f.write("\nSize Distribution Statistics\n")
            f.write(f"Mean area (µm²):,{data['global_stats']['mean_area']}\n")
            f.write(f"Median area (µm²):,{data['global_stats']['median_area']}\n")
            f.write(f"Standard deviation of area (µm²):,{data['global_stats']['std_area']}\n")
            f.write(f"Mean perimeter (µm):,{data['global_stats']['mean_perimeter']}\n")
            f.write(f"Median perimeter (µm):,{data['global_stats']['median_perimeter']}\n")
            f.write(f"Standard deviation of perimeter (µm):,{data['global_stats']['std_perimeter']}\n")
            
            # Write individual measurements
            f.write("\nIndividual Grain Measurements\n")
            f.write("Grain #,Area (µm²),Equivalent Diameter,Orientation (degrees),Major Axis Length,Minor Axis Length,Perimeter (µm)\n")
            
            for measurement in data['individual_measurements']:
                f.write(f"{measurement['grain_number']},{measurement['area']},{measurement['equivalent_diameter']},")
                f.write(f"{measurement['orientation']},{measurement['majoraxislength']},")
                f.write(f"{measurement['minoraxislength']},{measurement['perimeter']}\n")
        
        # Send the file for download
        response = send_file(
            csv_path,
            as_attachment=True,
            download_name=f"{data['image_name']}_measurements.csv",
            mimetype='text/csv'
        )
        
        # Clean up after sending the file
        @response.call_on_close
        def cleanup():
            shutil.rmtree(temp_dir)
        
        return response
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.teardown_request
def shutdown_session(exception=None):
    plt.close('all')  # Close all matplotlib figures
    # If you're using any other resources that need cleanup, add here

if __name__ == '__main__':
    app.run(debug=True, threaded=False)  # Add threaded=False