"""
Leaf Health Analysis Tool

Analyzes plant leaf images to detect and quantify:
- Healthy tissue (green)
- Chlorosis (yellowing/stress)
- Necrosis (brown/dead tissue)

Author: Leon Lenzo
Usage: python leafstate2.py [input_directory] [output_directory]
"""

import os
import sys
import argparse
import numpy as np
import cv2
from PIL import Image
from skimage import morphology, measure
import pandas as pd
import logging
from datetime import datetime
from pathlib import Path

class LeafAnalysisConfig:
    """Configuration parameters for leaf analysis"""
    # HSV thresholds (OpenCV scale 0-179 for hue)
    NECROSIS_HUE = 21       # Brown/dead tissue threshold
    CHLOROSIS_HUE = 31      # Yellow/stressed tissue threshold
    HEALTHY_HUE = 95        # Upper bound for green/healthy tissue

    # Size filters
    MIN_LEAF_SIZE = 500     # Minimum pixels for valid leaf
    MIN_NECROSIS_SIZE = 10  # Minimum pixels for necrosis detection
    MIN_LEAF_WIDTH = 50     # Minimum leaf width in pixels
    MIN_LEAF_HEIGHT = 80    # Minimum leaf height in pixels

    # Supported image formats
    SUPPORTED_FORMATS = ('.tif', '.tiff', '.png', '.jpg', '.jpeg')

def setup_logging(verbose=False):
    """Configure logging output"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('leaf_analysis.log')
        ]
    )

def create_leaf_mask(hsv_image, config=LeafAnalysisConfig()):
    """
    Create comprehensive leaf mask including all tissue types

    Args:
        hsv_image: HSV color space image
        config: Configuration object with analysis parameters

    Returns:
        Binary mask identifying leaf pixels
    """
    # Define tissue color ranges in HSV
    green_mask = cv2.inRange(
        hsv_image,
        np.array([25, 20, 20]),
        np.array([config.HEALTHY_HUE, 255, 255])
    )

    yellow_mask = cv2.inRange(
        hsv_image,
        np.array([config.NECROSIS_HUE, 30, 30]),
        np.array([config.CHLOROSIS_HUE, 255, 255])
    )

    brown_mask = cv2.inRange(
        hsv_image,
        np.array([0, 30, 30]),
        np.array([config.NECROSIS_HUE + 10, 255, 200])
    )

    # Background subtraction (blue background)
    blue_bg = cv2.inRange(
        hsv_image,
        np.array([100, 50, 50]),
        np.array([130, 255, 255])
    )

    # Combine all leaf tissue + non-background areas
    leaf_mask = green_mask | yellow_mask | brown_mask | cv2.bitwise_not(blue_bg)

    # Clean up mask with morphological operations
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    leaf_mask = cv2.morphologyEx(leaf_mask, cv2.MORPH_CLOSE, kernel)
    leaf_mask = cv2.morphologyEx(leaf_mask, cv2.MORPH_OPEN, kernel)

    # Remove small objects and holes
    leaf_mask = morphology.remove_small_objects(
        leaf_mask.astype(bool), config.MIN_LEAF_SIZE
    )
    leaf_mask = morphology.remove_small_holes(leaf_mask, config.MIN_LEAF_SIZE)

    return leaf_mask

def separate_leaves(image_np, leaf_mask, config=LeafAnalysisConfig()):
    """
    Extract individual leaves using connected components

    Args:
        image_np: Original image as numpy array
        leaf_mask: Binary mask of leaf pixels
        config: Configuration object with size thresholds

    Returns:
        List of dictionaries containing leaf data
    """
    labeled_mask = measure.label(leaf_mask, connectivity=2)
    regions = measure.regionprops(labeled_mask)

    leaves = []
    for region in regions:
        # Filter by area
        if region.area < config.MIN_LEAF_SIZE:
            continue

        # Filter by dimensions
        min_row, min_col, max_row, max_col = region.bbox
        width = max_col - min_col
        height = max_row - min_row

        if width < config.MIN_LEAF_WIDTH or height < config.MIN_LEAF_HEIGHT:
            continue

        # Extract leaf data
        leaf_mask_crop = (labeled_mask == region.label)[min_row:max_row, min_col:max_col]
        leaves.append({
            'image': image_np[min_row:max_row, min_col:max_col],
            'mask': leaf_mask_crop,
            'bbox': region.bbox,
            'area': region.area
        })

    return leaves

def analyze_leaf(leaf_image, leaf_mask, config=LeafAnalysisConfig(), hsv_full=None, bbox=None):
    """
    Analyze single leaf for necrosis and chlorosis

    Args:
        leaf_image: RGB image of the leaf
        leaf_mask: Binary mask of leaf pixels
        config: Configuration object with analysis parameters
        hsv_full: Full HSV image (optional, for efficiency)
        bbox: Bounding box coordinates (optional)

    Returns:
        Tuple of (analysis_results_dict, visualization_image)
    """
    # Get HSV representation
    if hsv_full is not None and bbox is not None:
        min_row, min_col, max_row, max_col = bbox
        hsv_image = hsv_full[min_row:max_row, min_col:max_col]
        if hsv_image.shape[:2] != leaf_image.shape[:2]:
            hsv_image = cv2.resize(hsv_image, (leaf_image.shape[1], leaf_image.shape[0]))
    else:
        hsv_image = cv2.cvtColor(leaf_image, cv2.COLOR_RGB2HSV)

    # Mask HSV to leaf area only
    masked_hsv = hsv_image.copy()
    masked_hsv[~leaf_mask] = [0, 0, 0]

    # Create tissue-specific masks
    necrosis_mask = cv2.inRange(
        masked_hsv,
        np.array([0, 0, 0]),
        np.array([config.NECROSIS_HUE, 255, 255])
    )
    necrosis_mask = necrosis_mask & (leaf_mask.astype(np.uint8) * 255)
    necrosis_mask = morphology.remove_small_objects(
        necrosis_mask.astype(bool), config.MIN_NECROSIS_SIZE
    )

    chlorosis_mask = cv2.inRange(
        masked_hsv,
        np.array([config.NECROSIS_HUE, 0, 0]),
        np.array([config.CHLOROSIS_HUE, 255, 255])
    )
    chlorosis_mask = chlorosis_mask & (leaf_mask.astype(np.uint8) * 255)
    chlorosis_mask = morphology.remove_small_objects(
        chlorosis_mask.astype(bool), config.MIN_NECROSIS_SIZE
    )

    # Calculate areas and percentages
    leaf_area = np.sum(leaf_mask)
    necrosis_area = np.sum(necrosis_mask)
    chlorosis_area = np.sum(chlorosis_mask)
    healthy_area = leaf_area - necrosis_area - chlorosis_area

    # Create visualization overlay
    output = cv2.cvtColor(leaf_image, cv2.COLOR_RGB2RGBA)
    output[~leaf_mask] = [0, 0, 0, 0]  # Transparent background
    output[necrosis_mask] = [166, 56, 22, 200]  # Brown for necrosis
    output[chlorosis_mask] = [255, 222, 83, 200]  # Yellow for chlorosis

    # Compile results
    results = {
        'leaf_area_px': int(leaf_area),
        'healthy_area_px': int(healthy_area),
        'necrosis_area_px': int(necrosis_area),
        'chlorosis_area_px': int(chlorosis_area),
        'percent_healthy': round((healthy_area / leaf_area * 100) if leaf_area > 0 else 0, 2),
        'percent_necrosis': round((necrosis_area / leaf_area * 100) if leaf_area > 0 else 0, 2),
        'percent_chlorosis': round((chlorosis_area / leaf_area * 100) if leaf_area > 0 else 0, 2)
    }

    return results, output

def process_image(image_path, output_dir, config=LeafAnalysisConfig()):
    """
    Process single image with multiple leaves

    Args:
        image_path: Path to input image
        output_dir: Directory for output files
        config: Configuration object

    Returns:
        List of analysis results for each leaf
    """
    try:
        logging.info(f"Processing: {os.path.basename(image_path)}")

        # Load and convert image
        image = Image.open(image_path)
        image_np = np.array(image)
        hsv_image = cv2.cvtColor(image_np, cv2.COLOR_RGB2HSV)

        # Create leaf mask and separate leaves
        leaf_mask = create_leaf_mask(hsv_image, config)
        individual_leaves = separate_leaves(image_np, leaf_mask, config)

        if not individual_leaves:
            logging.warning(f"No leaves detected in {image_path}")
            return []

        logging.info(f"Found {len(individual_leaves)} leaves")

        # Analyze each leaf
        base_filename = Path(image_path).stem
        results = []

        for i, leaf_data in enumerate(individual_leaves):
            analysis, visualization = analyze_leaf(
                leaf_data['image'],
                leaf_data['mask'],
                config,
                hsv_image,
                leaf_data['bbox']
            )

            # Add metadata
            analysis.update({
                'filename': base_filename,
                'leaf_index': i + 1,
                'total_leaves_in_image': len(individual_leaves)
            })
            results.append(analysis)

            # Save individual leaf visualization
            leaf_path = output_dir / f"{base_filename}_leaf_{i+1:02d}_masked.png"
            Image.fromarray(visualization).save(leaf_path)

        # Save combined visualization
        combined_output = cv2.cvtColor(image_np, cv2.COLOR_RGB2RGBA)
        combined_output[:, :, 3] = 0  # Start with transparent background

        for leaf_data in individual_leaves:
            _, leaf_vis = analyze_leaf(
                leaf_data['image'],
                leaf_data['mask'],
                config,
                hsv_image,
                leaf_data['bbox']
            )
            min_row, min_col, max_row, max_col = leaf_data['bbox']

            # Only blend where there is leaf content (non-transparent pixels)
            leaf_alpha = leaf_vis[:, :, 3] > 0
            combined_output[min_row:max_row, min_col:max_col][leaf_alpha] = leaf_vis[leaf_alpha]

        combined_path = output_dir / f"{base_filename}_all_leaves_masked.png"
        Image.fromarray(combined_output).save(combined_path)

        return results

    except Exception as e:
        logging.error(f"Error processing {image_path}: {str(e)}")
        return []

def analyze_directory(input_dir, output_dir=None, config=LeafAnalysisConfig(), verbose=False):
    """
    Analyze all leaf images in a directory

    Args:
        input_dir: Directory containing images to process
        output_dir: Output directory (auto-generated if None)
        config: Configuration object
        verbose: Enable verbose logging

    Returns:
        Path to results CSV file
    """
    setup_logging(verbose)

    input_path = Path(input_dir)
    if not input_path.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    # Create output directory
    if output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = input_path / "output" / timestamp
    else:
        output_path = Path(output_dir)

    output_path.mkdir(parents=True, exist_ok=True)

    logging.info(f"Processing directory: {input_path}")
    logging.info(f"Output directory: {output_path}")

    # Find all image files
    image_files = []
    for ext in config.SUPPORTED_FORMATS:
        image_files.extend(input_path.glob(f"*{ext}"))
        image_files.extend(input_path.glob(f"*{ext.upper()}"))

    if not image_files:
        logging.warning(f"No supported image files found in {input_path}")
        return None

    logging.info(f"Found {len(image_files)} image files")

    # Process all images
    all_results = []
    for image_path in image_files:
        results = process_image(image_path, output_path, config)
        all_results.extend(results)

    # Save results
    if all_results:
        df = pd.DataFrame(all_results)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = output_path / f"leaf_analysis_results_{timestamp}.csv"
        df.to_csv(csv_path, index=False)
        logging.info(f"Results saved to {csv_path}")

        # Print summary
        print(f"\n🍃 Leaf Analysis Complete:")
        print(f"📊 Total leaves analyzed: {len(all_results)}")
        print(f"💚 Average healthy tissue: {df['percent_healthy'].mean():.1f}%")
        print(f"🟤 Average necrosis: {df['percent_necrosis'].mean():.1f}%")
        print(f"🟡 Average chlorosis: {df['percent_chlorosis'].mean():.1f}%")

        print(f"\n📁 Per-image breakdown:")
        for filename in df['filename'].unique():
            file_data = df[df['filename'] == filename]
            print(f"  {filename}: {len(file_data)} leaves")

        return csv_path
    else:
        logging.warning("No results generated")
        return None


def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(
        description="Analyze plant leaf health from images",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python leafstate2.py                    # Process current directory
  python leafstate2.py --input ./images  # Process specific directory
  python leafstate2.py --verbose         # Enable detailed logging
        """
    )

    parser.add_argument(
        '--input', '-i',
        type=str,
        default='.',
        help='Input directory containing images (default: current directory)'
    )

    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output directory (default: auto-generated in input/output/)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    parser.add_argument(
        '--min-leaf-size',
        type=int,
        default=LeafAnalysisConfig.MIN_LEAF_SIZE,
        help=f'Minimum leaf size in pixels (default: {LeafAnalysisConfig.MIN_LEAF_SIZE})'
    )

    parser.add_argument(
        '--min-height',
        type=int,
        default=LeafAnalysisConfig.MIN_LEAF_HEIGHT,
        help=f'Minimum leaf height in pixels (default: {LeafAnalysisConfig.MIN_LEAF_HEIGHT})'
    )

    args = parser.parse_args()

    # Create custom config if needed
    config = LeafAnalysisConfig()
    if args.min_leaf_size != LeafAnalysisConfig.MIN_LEAF_SIZE:
        config.MIN_LEAF_SIZE = args.min_leaf_size
    if args.min_height != LeafAnalysisConfig.MIN_LEAF_HEIGHT:
        config.MIN_LEAF_HEIGHT = args.min_height

    try:
        result_path = analyze_directory(
            args.input,
            args.output,
            config,
            args.verbose
        )

        if result_path:
            print(f"\n✅ Analysis complete! Results saved to: {result_path}")
        else:
            print("\n❌ No images were processed")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()