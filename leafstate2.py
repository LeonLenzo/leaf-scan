import os
import numpy as np
import cv2
from PIL import Image
from skimage import morphology, measure
import pandas as pd
import logging
from datetime import datetime

# Configuration
DIRECTORY_PATH = "./intergrain"
OUTPUT_DIRECTORY = os.path.join(DIRECTORY_PATH, "output")
NECROSIS_HUE = 21  # 30 * 255/360 ≈ 21 in OpenCV scale
CHLOROSIS_HUE = 31  # 43 * 255/360 ≈ 31 in OpenCV scale
HEALTHY_HUE = 95  # Upper bound for green/healthy tissue
MIN_LEAF_SIZE = 500
MIN_NECROSIS_SIZE = 10
MIN_LEAF_WIDTH = 50
MIN_LEAF_HEIGHT = 100

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_leaf_mask(hsv_image):
    """Create comprehensive leaf mask including all tissue types"""
    # Green, yellow/chlorotic, and brown/necrotic tissue
    green_mask = cv2.inRange(hsv_image, np.array([25, 20, 20]), np.array([HEALTHY_HUE, 255, 255]))
    
    yellow_mask = cv2.inRange(hsv_image, np.array([NECROSIS_HUE, 30, 30]), np.array([CHLOROSIS_HUE, 255, 255]))
    
    brown_mask = cv2.inRange(hsv_image, np.array([0, 30, 30]), np.array([NECROSIS_HUE + 10, 255, 200]))
    
    # Background subtraction (blue background)
    blue_bg = cv2.inRange(hsv_image, np.array([100, 50, 50]), np.array([130, 255, 255]))
    
    # Combine all leaf tissue + non-background areas
    leaf_mask = green_mask | yellow_mask | brown_mask | cv2.bitwise_not(blue_bg)
    
    # Clean up mask
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    leaf_mask = cv2.morphologyEx(leaf_mask, cv2.MORPH_CLOSE, kernel)
    leaf_mask = cv2.morphologyEx(leaf_mask, cv2.MORPH_OPEN, kernel)
    leaf_mask = morphology.remove_small_objects(leaf_mask.astype(bool), MIN_LEAF_SIZE)
    leaf_mask = morphology.remove_small_holes(leaf_mask, MIN_LEAF_SIZE)
    
    return leaf_mask

def separate_leaves(image_np, leaf_mask):
    """Extract individual leaves using connected components"""
    labeled_mask = measure.label(leaf_mask, connectivity=2)
    regions = measure.regionprops(labeled_mask)
    
    leaves = []
    for region in regions:
        if region.area < MIN_LEAF_SIZE:
            continue
            
        min_row, min_col, max_row, max_col = region.bbox
        if (max_col - min_col) < MIN_LEAF_WIDTH or (max_row - min_row) < MIN_LEAF_HEIGHT:
            continue
        
        leaf_mask_crop = (labeled_mask == region.label)[min_row:max_row, min_col:max_col]
        leaves.append({
            'image': image_np[min_row:max_row, min_col:max_col],
            'mask': leaf_mask_crop,
            'bbox': region.bbox
        })
    
    return leaves

def analyze_leaf(leaf_image, leaf_mask, hsv_full=None, bbox=None):
    """Analyze single leaf for necrosis and chlorosis"""
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
    
    # Create tissue masks
    necrosis_mask = cv2.inRange(masked_hsv, np.array([0, 0, 0]), np.array([NECROSIS_HUE, 255, 255]))
    necrosis_mask = necrosis_mask & (leaf_mask.astype(np.uint8) * 255)
    necrosis_mask = morphology.remove_small_objects(necrosis_mask.astype(bool), MIN_NECROSIS_SIZE)
    
    chlorosis_mask = cv2.inRange(masked_hsv, np.array([NECROSIS_HUE, 0, 0]), np.array([CHLOROSIS_HUE, 255, 255]))
    chlorosis_mask = chlorosis_mask & (leaf_mask.astype(np.uint8) * 255)
    chlorosis_mask = morphology.remove_small_objects(chlorosis_mask.astype(bool), MIN_NECROSIS_SIZE)
    
    # Calculate areas and percentages
    leaf_area = np.sum(leaf_mask)
    necrosis_area = np.sum(necrosis_mask)
    chlorosis_area = np.sum(chlorosis_mask)
    healthy_area = leaf_area - necrosis_area - chlorosis_area
    
    # Create visualization
    output = cv2.cvtColor(leaf_image, cv2.COLOR_RGB2RGBA)
    output[~leaf_mask] = [0, 0, 0, 0]
    output[necrosis_mask] = [166, 56, 22, 200]  # Brown for necrosis
    output[chlorosis_mask] = [255, 222, 83, 200]  # Yellow for chlorosis
    
    return {
        'leaf_area_px': int(leaf_area),
        'healthy_area_px': int(healthy_area),
        'necrosis_area_px': int(necrosis_area),
        'chlorosis_area_px': int(chlorosis_area),
        'percent_healthy': round((healthy_area / leaf_area * 100) if leaf_area > 0 else 0, 2),
        'percent_necrosis': round((necrosis_area / leaf_area * 100) if leaf_area > 0 else 0, 2),
        'percent_chlorosis': round((chlorosis_area / leaf_area * 100) if leaf_area > 0 else 0, 2)
    }, output

def process_image(image_path, output_dir):
    """Process single image with multiple leaves"""
    try:
        image = Image.open(image_path)
        image_np = np.array(image)
        hsv_image = cv2.cvtColor(image_np, cv2.COLOR_RGB2HSV)
        
        # Create leaf mask and separate leaves
        leaf_mask = create_leaf_mask(hsv_image)
        individual_leaves = separate_leaves(image_np, leaf_mask)
        
        if not individual_leaves:
            logging.warning(f"No leaves detected in {image_path}")
            return []
        
        logging.info(f"Found {len(individual_leaves)} leaves")
        
        # Analyze each leaf
        base_filename = os.path.splitext(os.path.basename(image_path))[0]
        results = []
        
        for i, leaf_data in enumerate(individual_leaves):
            analysis, visualization = analyze_leaf(
                leaf_data['image'], leaf_data['mask'], hsv_image, leaf_data['bbox']
            )
            
            # Add metadata
            analysis.update({
                'filename': base_filename,
                'leaf_index': i + 1,
                'total_leaves_in_image': len(individual_leaves)
            })
            results.append(analysis)
            
            # Save individual leaf visualization
            leaf_path = os.path.join(output_dir, f"{base_filename}_leaf_{i+1:02d}_masked.png")
            Image.fromarray(visualization).save(leaf_path)
        
        # Save combined visualization
        combined_output = cv2.cvtColor(image_np, cv2.COLOR_RGB2RGBA)
        combined_output[:, :, 3] = 0  # Start with transparent background
        
        for leaf_data in individual_leaves:
            _, leaf_vis = analyze_leaf(leaf_data['image'], leaf_data['mask'], hsv_image, leaf_data['bbox'])
            min_row, min_col, max_row, max_col = leaf_data['bbox']
            
            # Only blend where there is leaf content (non-transparent pixels)
            leaf_alpha = leaf_vis[:, :, 3] > 0
            combined_output[min_row:max_row, min_col:max_col][leaf_alpha] = leaf_vis[leaf_alpha]
        
        combined_path = os.path.join(output_dir, f"{base_filename}_all_leaves_masked.png")
        Image.fromarray(combined_output).save(combined_path)
        
        return results
        
    except Exception as e:
        logging.error(f"Error processing {image_path}: {str(e)}")
        return []

def main():
    """Main processing function"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(OUTPUT_DIRECTORY, f"{timestamp}")
    os.makedirs(output_dir, exist_ok=True)
    
    logging.info(f"Processing directory: {DIRECTORY_PATH}")
    logging.info(f"Output directory: {output_dir}")
    
    # Process all images
    all_results = []
    extensions = (".tif", ".tiff", ".png", ".jpg", ".jpeg")
    
    for filename in os.listdir(DIRECTORY_PATH):
        if filename.lower().endswith(extensions):
            image_path = os.path.join(DIRECTORY_PATH, filename)
            logging.info(f"Processing: {filename}")
            results = process_image(image_path, output_dir)
            all_results.extend(results)
    
    # Save results
    if all_results:
        df = pd.DataFrame(all_results)
        csv_path = os.path.join(output_dir, f"multi_leaf_results_{timestamp}.csv")
        df.to_csv(csv_path, index=False)
        logging.info(f"Results saved to {csv_path}")
        
        # Print summary
        print(f"\nAnalysis Complete:")
        print(f"Total leaves: {len(all_results)}")
        print(f"Average healthy: {df['percent_healthy'].mean():.2f}%")
        print(f"Average necrosis: {df['percent_necrosis'].mean():.2f}%")
        print(f"Average chlorosis: {df['percent_chlorosis'].mean():.2f}%")
        
        for filename in df['filename'].unique():
            file_data = df[df['filename'] == filename]
            print(f"{filename}: {len(file_data)} leaves")
    else:
        logging.warning("No results generated")

if __name__ == "__main__":
    os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
    main()