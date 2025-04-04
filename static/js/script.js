document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const analyzeText = document.getElementById('analyzeText');
    const analyzeSpinner = document.getElementById('analyzeSpinner');
    const resultsCard = document.getElementById('resultsCard');
    const resultsTable = document.getElementById('resultsTable');
    const originalPreview = document.getElementById('originalPreview');
    const segmentedPreview = document.getElementById('segmentedPreview');
    const coloredPreview = document.getElementById('coloredPreview');
    const plotsCard = document.getElementById('plotsCard');
    const downloadBtn = document.getElementById('downloadBtn');
    const errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
    
    let currentResults = null;
    
function displayResults(data) {
    // Show the results card and plots card
    resultsCard.classList.remove('d-none');
    plotsCard.classList.remove('d-none');
    
    // Display global statistics
    const stats = data.global_stats;
    resultsTable.innerHTML = `
        <!-- Keep the same table content -->
    `;
    
    // Display processed images (remove check for original image)
    if (data.segmented_image) {
        segmentedPreview.classList.remove('d-none');
        document.getElementById('segmentedImg').src = `data:image/jpeg;base64,${data.segmented_image}`;
    }
    
    if (data.colored_image) {
        coloredPreview.classList.remove('d-none');
        document.getElementById('coloredImg').src = `data:image/jpeg;base64,${data.colored_image}`;
    }
    
    // Display distribution plot
    if (data.distribution_plot) {
        document.getElementById('distributionPlot').src = `data:image/png;base64,${data.distribution_plot}`;
    }
}
    
    // Handle form submission
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(uploadForm);
        const fileInput = document.getElementById('imageFile');
        
        if (fileInput.files.length === 0) {
            showError('Please select an image file');
            return;
        }
        
        // Show loading state
        analyzeText.textContent = 'Analyzing...';
        analyzeSpinner.classList.remove('d-none');
        analyzeBtn.disabled = true;
        
        fetch('/', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw err; });
            }
            return response.json();
        })
        .then(data => {
            currentResults = data;
            displayResults(data);
        })
        .catch(error => {
            showError(error.error || 'An error occurred during analysis');
        })
        .finally(() => {
            // Reset button state
            analyzeText.textContent = 'Analyze Image';
            analyzeSpinner.classList.add('d-none');
            analyzeBtn.disabled = false;
        });
    });
    
    // Handle CSV download
    downloadBtn.addEventListener('click', function() {
        if (!currentResults) return;
        
        fetch('/download_csv', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(currentResults)
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw err; });
            }
            return response.blob();
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${currentResults.image_name}_measurements.csv`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        })
        .catch(error => {
            showError(error.error || 'Failed to download CSV');
        });
    });
    
    function displayResults(data) {
        // Show the results card and plots card
        resultsCard.classList.remove('d-none');
        plotsCard.classList.remove('d-none');
        
        // Display global statistics
        const stats = data.global_stats;
        resultsTable.innerHTML = `
            <tr>
                <th>Total number of particles</th>
                <td>${stats.total_particles}</td>
            </tr>
            <tr>
                <th>Surface Coverage (%)</th>
                <td>${stats.surface_coverage}</td>
            </tr>
            <tr>
                <th>Total grain area (µm²)</th>
                <td>${stats.total_grain_area}</td>
            </tr>
            <tr>
                <th>Mean grain area (µm²)</th>
                <td>${stats.mean_grain_area}</td>
            </tr>
            <tr>
                <th>Particle density (particles/µm²)</th>
                <td>${stats.particle_density}</td>
            </tr>
            <tr>
                <th>Mean area (µm²)</th>
                <td>${stats.mean_area}</td>
            </tr>
            <tr>
                <th>Median area (µm²)</th>
                <td>${stats.median_area}</td>
            </tr>
            <tr>
                <th>Standard deviation of area (µm²)</th>
                <td>${stats.std_area}</td>
            </tr>
            <tr>
                <th>Mean perimeter (µm)</th>
                <td>${stats.mean_perimeter}</td>
            </tr>
            <tr>
                <th>Median perimeter (µm)</th>
                <td>${stats.median_perimeter}</td>
            </tr>
            <tr>
                <th>Standard deviation of perimeter (µm)</th>
                <td>${stats.std_perimeter}</td>
            </tr>
        `;
        
        // Display processed images
        if (data.segmented_image) {
            segmentedPreview.classList.remove('d-none');
            document.getElementById('segmentedImg').src = `data:image/jpeg;base64,${data.segmented_image}`;
        }
        
        if (data.colored_image) {
            coloredPreview.classList.remove('d-none');
            document.getElementById('coloredImg').src = `data:image/jpeg;base64,${data.colored_image}`;
        }
        
        // Display distribution plot
        if (data.distribution_plot) {
            document.getElementById('distributionPlot').src = `data:image/png;base64,${data.distribution_plot}`;
        }
    }
    
    function showError(message) {
        document.getElementById('errorMessage').textContent = message;
        errorModal.show();
    }
});