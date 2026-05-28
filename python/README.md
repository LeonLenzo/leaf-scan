# 🍃 Leaf Health Analysis Tool

A comprehensive Python toolkit for analyzing plant leaf health from images. Detects and quantifies healthy tissue, chlorosis (yellowing), and necrosis (browning) in plant leaves with both command-line and GUI interfaces.

## ✨ Key Features

- **🔍 Multi-leaf Detection**: Automatically separates and analyzes individual leaves in each image
- **📊 Health Quantification**: Measures percentages of healthy, chlorotic, and necrotic tissue
- **🎨 Visual Output**: Generates color-coded visualizations of detected areas
- **⚡ Batch Processing**: Processes entire directories of images efficiently
- **🖥️ Dual Interface**: Both command-line tool and user-friendly GUI
- **⚙️ Flexible Configuration**: Adjustable parameters for different leaf sizes and analysis needs
- **📈 Detailed Reports**: CSV output with comprehensive statistics

## 🚀 Quick Start

### 🖱️ GUI Version (Recommended - just double-click!)
```bash
python leafstate.GUI.py
```
**Or simply double-click the `leafstate.GUI.py` file!**

### 💻 Command Line Version
```bash
# Analyze current directory
python leafstate.CLI.py

# Analyze specific directory
python leafstate.CLI.py --input ./my_leaf_images

# See all options
python leafstate.CLI.py --help
```

## 📦 Installation

### 1. Clone from GitHub
```bash
git clone [repository-url]
cd leaf-state
```

### 2. Install Requirements
```bash
# Option 1: Use requirements file (recommended)
pip install -r requirements.txt

# Option 2: Install manually
pip install opencv-python pillow scikit-image pandas numpy
```

### 3. Launch!
- **GUI**: Double-click `leafstate.GUI.py` or run `python leafstate.GUI.py`
- **CLI**: Run `python leafstate.CLI.py --help` for options

> **Note**: If emojis display as boxes or question marks, this is normal and doesn't affect functionality.

### Requirements
- Python 3.7+
- tkinter (usually included with Python)

## 🖼️ Supported Image Formats

- TIFF (.tif, .tiff)
- PNG (.png)
- JPEG (.jpg, .jpeg)

## 📁 Output

The tool generates:

1. **Individual leaf images** with color-coded health analysis
2. **Combined visualizations** showing all leaves in each input image
3. **CSV results file** with detailed quantitative data

### CSV Output Columns
- `filename`: Source image name
- `leaf_index`: Leaf number within the image
- `leaf_area_px`: Total leaf area in pixels
- `healthy_area_px`: Healthy tissue area
- `necrosis_area_px`: Necrotic (brown/dead) tissue area
- `chlorosis_area_px`: Chlorotic (yellow/stressed) tissue area
- `percent_healthy`: Percentage of healthy tissue
- `percent_necrosis`: Percentage of necrotic tissue
- `percent_chlorosis`: Percentage of chlorotic tissue

## ⚙️ Configuration Options

### Command Line
- `--input` / `-i`: Input directory (default: current directory)
- `--output` / `-o`: Output directory (default: auto-generated)
- `--verbose` / `-v`: Enable detailed logging
- `--min-leaf-size`: Minimum leaf size in pixels (default: 500)
- `--min-height`: Minimum leaf height in pixels (default: 80)

### GUI Settings
- **Size Filters**:
  - Minimum Leaf Size: Filters out small objects (pixels)
  - Minimum Leaf Height: Filters out very short objects (pixels)
- **Color Detection** (with live color previews):
  - Necrosis Hue: Brown/dead tissue detection threshold (0-30)
  - Chlorosis Hue: Yellow/stressed tissue detection threshold (20-50)
  - Healthy Hue: Green tissue upper limit (60-120)
  - Real-time color swatches show exactly what each setting detects
- **Options**:
  - Verbose Logging: Shows detailed processing information

## 🎨 New Features

### Interactive Color Controls
The GUI now includes **live color previews** for all HSV hue settings:
- Adjust sliders and see the exact colors being detected
- Fine-tune detection for your specific leaf types
- Perfect for different lighting conditions or plant varieties

### User-Friendly File Names
- `leafstate.GUI.py` - Double-click to launch
- `leafstate.CLI.py` - Command-line version
- Clear, simple naming for easy GitHub distribution

### Enhanced Interface
- Larger dialog window (650x750) for better visibility
- Organized settings sections for clarity
- Improved button layout and text
- Better cross-platform emoji compatibility


## 💡 Image Preparation Tips

For best results:
- Use images with good contrast between leaves and background
- Ensure leaves are well-lit and in focus
- Blue backgrounds work particularly well for leaf segmentation
- Remove or minimize shadows when possible

## 🧠 Algorithm Overview

1. **Color Space Conversion**: Converts images to HSV for better color analysis
2. **Leaf Segmentation**: Creates masks to identify leaf tissue vs background
3. **Individual Leaf Separation**: Uses connected components to separate touching leaves
4. **Tissue Classification**: Analyzes HSV values to classify tissue health:
   - Green hues → Healthy tissue
   - Yellow hues → Chlorotic tissue
   - Brown hues → Necrotic tissue
5. **Quantification**: Calculates areas and percentages for each tissue type

## 🛠️ Troubleshooting

### No leaves detected
- Check if images contain recognizable leaf shapes
- Adjust `--min-leaf-size` and `--min-height` parameters
- Ensure good contrast between leaves and background

### Wrong tissue classification
- The tool is calibrated for typical leaf colors
- Very dark or unusual colored leaves may not classify correctly
- Consider adjusting the HSV thresholds in the code if needed

### Performance issues
- Large images or many files will take longer to process
- Consider resizing very large images before analysis
- Use `--verbose` mode to monitor progress

## 📋 Example Output Structure

```
output/
└── 20241201_143022/
    ├── plot10_leaf_01_masked.png      # Individual leaf analysis
    ├── plot10_leaf_02_masked.png
    ├── ...
    ├── plot10_all_leaves_masked.png   # Combined visualization
    └── leaf_analysis_results_20241201_143024.csv
```

## 🆕 Recent Updates

### Version 2.0 Features
- **Fixed 7-leaf detection limit**: Now correctly detects all leaves in images
- **Interactive color controls**: Live HSV hue previews with color swatches
- **Improved GUI layout**: Larger window, better organization, cleaner buttons
- **User-friendly file names**: Simple `leafstate.GUI.py` and `leafstate.CLI.py`
- **Enhanced error handling**: Better dependency checking and user guidance
- **Cross-platform compatibility**: Improved emoji handling for different systems

## 🔧 Legacy Tools

This repository also includes legacy tools for specialized workflows:

### Image Temperature Adjustment (`thermostat.py`)
Adjusts color temperature for consistent lighting conditions

### Original Leaf Analysis (`leafState.py`)
Earlier version of the analysis tool

## 🔬 Research Applications

This tool has been designed for:
- Plant pathology research
- Agricultural monitoring
- Disease progression studies
- Stress response analysis
- High-throughput phenotyping


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
