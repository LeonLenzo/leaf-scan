# Foliar Utility and Classification Kit - High-throughput Exploratory Analysis of Disease

Python tools for plant image processing, including automated leaf disease detection and image temperature adjustment for optimal analysis conditions.

## Overview

This repository contains two main tools:

1. **leafState** - Automated detection and quantification of leaf diseases and chlorosis
2. **thermostat** - Color temperature correction for consistent image analysis

## Tools

### 1. Leaf Disease Analysis (`leaf_analysis.py`)

Processes plant leaf images to identify and measure:
- **Disease areas** (brownish/necrotic regions)
- **Chlorosis** (yellowing regions indicating nutrient deficiency) 
- **Healthy leaf tissue**

Generates masked visualization images and comprehensive analysis reports with percentage breakdowns.

### 2. Image Temperature Adjustment (`temperature_tool.py`)

Adjusts the color temperature of images to:
- **Warm images** (increase red, decrease blue)
- **Cool images** (decrease red, increase blue)
- **Standardize lighting conditions** for consistent analysis

## Features

### Leaf Disease Analysis
- **Batch Processing**: Analyzes entire directories automatically
- **Multiple Formats**: Supports TIFF, PNG, JPG, and JPEG
- **Visual Output**: Color-coded mask overlays
- **Detailed Reports**: CSV summaries and statistical reports
- **Timestamped Results**: Organized output by processing date/time
- **Robust Logging**: Comprehensive logging for monitoring

### Temperature Adjustment
- **Batch Processing**: Processes entire directories
- **Precise Control**: Adjustable temperature factors
- **Format Preservation**: Maintains original image quality
- **Non-destructive**: Creates new files, preserves originals


### Required Libraries
- `PIL (Pillow)` - Image processing
- `numpy` - Numerical operations
- `opencv-python` - Computer vision (disease analysis)
- `scikit-image` - Morphological operations (disease analysis)
- `pandas` - Data analysis and reporting (disease analysis)

```bash
pip install pillow numpy opencv-python scikit-image pandas
```

## Usage

### Leaf Disease Analysis

1. Run the analysis:
```bash
python leafState.py
```

**Configuration options:**
```python
DIRECTORY_PATH = "path/to/your/image_directory"              # Input directory
DISEASE_HUE = 30                        # Disease detection threshold
CHLOROSIS_HUE_RANGE = (30, 43)         # Chlorosis detection range
MIN_LEAF_SIZE = 500                     # Minimum leaf area (pixels)
MIN_DISEASE_SIZE = 300                  # Minimum disease area (pixels)
```

### Image Temperature Adjustment

1. Place images in the input directory
2. Modify the script parameters:
```python
input_directory = '2025_Individuals'        # Input folder
output_directory = '2025_Individuals/thermo' # Output folder
temperature_factor = 0.9                     # <1 cooler, >1 warmer
```

3. Run the temperature adjustment:
```bash
python thermostat.py
```

**Temperature Factor Guide:**
- `0.7` - Significantly cooler (more blue)
- `0.9` - Slightly cooler 
- `1.0` - No change
- `1.1` - Slightly warmer
- `1.3` - Significantly warmer (more red)

## Workflow Recommendations

### For Disease Analysis Projects

1. **Preprocessing** (Optional):
   ```bash
   # Adjust temperature for consistent lighting
   python temperature_tool.py
   ```

2. **Disease Analysis**:
   ```bash
   # Analyze preprocessed or original images
   python leaf_analysis.py
   ```

### For Optimal Results

1. Use temperature adjustment to standardize lighting conditions across image batches
2. Process temperature-adjusted images through disease analysis
3. Compare results with and without temperature adjustment to validate improvements

## Output Files

### Disease Analysis Output

**Directory Structure:**
```
output/
└── YYYYMMDD_HHMMSS/
    ├── image1_masked.png           # Visualized results
    ├── summary_results.csv         # Detailed measurements
    └── analysis_summary.txt        # Statistical summary
```

**Masked Images:**
- **Disease areas**: Brownish-red overlay (RGB: 166, 56, 22)
- **Chlorosis areas**: Yellow overlay (RGB: 255, 222, 83)
- **Healthy areas**: Original leaf color
- **Background**: Transparent

**CSV Report Fields:**
- `filename`, `leaf_area_px`, `healthy_area_px`
- `disease_area_px`, `chlorosis_area_px`
- `percent_healthy`, `percent_disease`, `percent_chlorosis`

### Temperature Adjustment Output

Temperature-adjusted images are saved to the specified output directory with:
- Same filename as original
- Preserved image quality and format
- Modified color temperature based on adjustment factor


## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

[MIT License]

## Citation

If you use these tools in your research, please cite:

```
Coming soon
```

## Contact

leon.lenzo@curtin.edu.au

---

**Note**: These tools are designed for research purposes. Results should be validated against manual assessments for critical applications.
