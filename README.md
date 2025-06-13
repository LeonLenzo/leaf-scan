# Leaf Disease Analysis

An automated image analysis tool for detecting and quantifying leaf diseases and chlorosis in plant images using computer vision techniques.

## Overview

This Python application processes plant leaf images to identify and measure:
- **Disease areas** (brownish/necrotic regions)
- **Chlorosis** (yellowing regions indicating nutrient deficiency)
- **Healthy leaf tissue**

The tool generates masked visualization images and comprehensive analysis reports with percentage breakdowns of each condition.

## Features

- **Batch Processing**: Analyzes entire directories of images automatically
- **Multiple Formats**: Supports TIFF, PNG, JPG, and JPEG image formats
- **Visual Output**: Creates color-coded mask overlays showing disease and chlorosis areas
- **Detailed Reports**: Generates CSV summaries and text reports with statistics
- **Timestamped Results**: Organizes outputs by processing date/time
- **Robust Logging**: Comprehensive logging for debugging and monitoring

## Requirements

### Dependencies

```bash
pip install pillow numpy opencv-python scikit-image pandas
```

### Required Libraries
- `PIL (Pillow)` - Image processing
- `numpy` - Numerical operations
- `opencv-python` - Computer vision operations
- `scikit-image` - Advanced image processing (morphological operations)
- `pandas` - Data analysis and CSV export

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd leaf-disease-analysis
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a directory structure:
```
your-project/
├── touched/          # Input images directory
├── leaf_analysis.py  # Main analysis script
└── output/          # Generated automatically
```

## Usage

### Basic Usage

1. Place your leaf images in the `touched` directory
2. Run the analysis script:
```bash
python leaf_analysis.py
```

### Configuration

Edit the configuration variables at the top of `leaf_analysis.py`:

```python
DIRECTORY_PATH = "touched"              # Input directory
DISEASE_HUE = 30                        # Hue value for disease detection (0-360)
CHLOROSIS_HUE_RANGE = (30, 43)         # Hue range for chlorosis detection
MIN_LEAF_SIZE = 500                     # Minimum leaf area in pixels
MIN_DISEASE_SIZE = 300                  # Minimum disease area in pixels
```

### Output Structure

The tool creates timestamped output directories:

```
output/
└── YYYYMMDD_HHMMSS/
    ├── image1_masked.png           # Visualized results
    ├── image2_masked.png
    ├── summary_results.csv         # Detailed measurements
    └── analysis_summary.txt        # Statistical summary
```

## Output Files

### Masked Images
- **Background**: Transparent (removed)
- **Disease areas**: Brownish-red overlay (RGB: 166, 56, 22)
- **Chlorosis areas**: Yellow overlay (RGB: 255, 222, 83)
- **Healthy areas**: Original leaf color

### CSV Report (`summary_results.csv`)
Contains per-image measurements:
- `filename`: Image filename
- `leaf_area_px`: Total leaf area in pixels
- `healthy_area_px`: Healthy tissue area
- `disease_area_px`: Disease area
- `chlorosis_area_px`: Chlorosis area
- `percent_healthy`: Percentage of healthy tissue
- `percent_disease`: Percentage of diseased tissue
- `percent_chlorosis`: Percentage of chlorotic tissue

### Summary Report (`analysis_summary.txt`)
Contains:
- Processing timestamp
- Total images processed
- Average percentages across all images
- Configuration parameters used

## Algorithm Details

### Image Processing Pipeline

1. **Color Space Conversion**: RGB → HSV for better color segmentation
2. **Hue Normalization**: Converts 360° hue values to 0-255 range
3. **Mask Generation**: Creates binary masks for leaf, disease, and chlorosis areas
4. **Morphological Operations**: 
   - Removes small objects (noise reduction)
   - Fills small holes in detected regions
5. **Area Calculation**: Computes pixel counts and percentages
6. **Visualization**: Creates color-coded overlay images

### Color Detection

- **Leaf Detection**: HSV range [0-90, 0-255, 0-255] (excludes background)
- **Disease Detection**: Hue values up to configured threshold (default: 30°)
- **Chlorosis Detection**: Hue range 30-43° (yellow spectrum)

## Customization

### Adjusting Detection Parameters

**For different plant species or imaging conditions:**

- **DISEASE_HUE**: Increase for more brown/red disease detection
- **CHLOROSIS_HUE_RANGE**: Adjust for different yellowing patterns
- **MIN_LEAF_SIZE**: Change based on image resolution and leaf size
- **MIN_DISEASE_SIZE**: Adjust sensitivity to small disease spots

### Adding New Analysis Types

The modular design allows easy extension for additional conditions:

1. Define new color ranges
2. Create mask generation functions
3. Add area calculations
4. Update visualization colors

## Troubleshooting

### Common Issues

**No results generated:**
- Check image file formats (must be .tif, .tiff, .png, .jpg, .jpeg)
- Verify images are in the correct input directory
- Check log files for error messages

**Poor detection accuracy:**
- Adjust hue thresholds for your specific plant species
- Modify minimum size parameters
- Ensure consistent lighting in images

**Memory issues with large images:**
- Process images in smaller batches
- Resize images before processing if necessary

### Logging

Check `leaf_analysis.log` for detailed processing information and error messages.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request


---

**Note**: This tool is designed for research purposes. Results should be validated against manual assessments for critical applications.