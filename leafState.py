import os
from PIL import Image
import numpy as np
import cv2
from skimage import morphology
import pandas as pd
import time
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("leaf_analysis.log"),
        logging.StreamHandler()
    ]
)

# HARD-CODED CONFIGURATION
DIRECTORY_PATH = "."  # Replace with your actual path
OUTPUT_DIRECTORY = os.path.join(DIRECTORY_PATH, "output")
DISEASE_HUE = 30  # Adjusted hue value for disease
CHLOROSIS_HUE_RANGE = (30, 43)  # Hue range for chlorosis (yellowing)
MIN_LEAF_SIZE = 500  # Minimum size of leaf area in pixels
MIN_DISEASE_SIZE = 300  # Minimum size of disease area in pixels
def normalize_hue(h):
    """Normalize hue from [0, 360] to [0, 255]"""
    return int(h * 255 / 360)

def process_image(image_path, output_directory):
    """Process a single image to detect leaf disease and chlorosis"""
    try:
        image = Image.open(image_path)
        image_np = np.array(image)
        hsv_image = cv2.cvtColor(image_np, cv2.COLOR_RGB2HSV)

        disease_hue = normalize_hue(DISEASE_HUE)
        chlorosis_hue_min, chlorosis_hue_max = map(normalize_hue, CHLOROSIS_HUE_RANGE)

        # Create binary masks
        leaf_mask = cv2.inRange(hsv_image, np.array([0, 0, 0], dtype=np.uint8), np.array([90, 255, 255], dtype=np.uint8))
        leaf_mask = morphology.remove_small_objects(leaf_mask.astype(bool), MIN_LEAF_SIZE)
        leaf_mask = morphology.remove_small_holes(leaf_mask, MIN_LEAF_SIZE)

        disease_mask = cv2.inRange(hsv_image, np.array([0, 0, 0], dtype=np.uint8), np.array([disease_hue, 255, 255], dtype=np.uint8))
        disease_mask = morphology.remove_small_objects(disease_mask.astype(bool), MIN_DISEASE_SIZE)
        disease_mask = morphology.remove_small_holes(disease_mask, MIN_DISEASE_SIZE)

        # Chlorosis mask
        chlorosis_mask = cv2.inRange(hsv_image, np.array([chlorosis_hue_min, 0, 0], dtype=np.uint8), np.array([chlorosis_hue_max, 255, 255], dtype=np.uint8))
        chlorosis_mask = morphology.remove_small_objects(chlorosis_mask.astype(bool), MIN_DISEASE_SIZE)
        chlorosis_mask = morphology.remove_small_holes(chlorosis_mask, MIN_DISEASE_SIZE)

        # Calculate areas
        leaf_area = np.sum(leaf_mask)
        disease_area = np.sum(disease_mask)
        chlorosis_area = np.sum(chlorosis_mask)
        healthy_area = leaf_area - disease_area - chlorosis_area
        
        # Calculate percentages
        percent_healthy = (healthy_area / leaf_area * 100) if leaf_area > 0 else 0
        percent_disease = (disease_area / leaf_area * 100) if leaf_area > 0 else 0
        percent_chlorosis = (chlorosis_area / leaf_area * 100) if leaf_area > 0 else 0
        
        # Create output
        output = cv2.cvtColor(image_np, cv2.COLOR_RGB2RGBA)
        output[leaf_mask == 0] = [0, 0, 0, 0]  # Background transparency
        output[disease_mask != 0] = [166, 56, 22, 200]  # Disease Color - brownish red
        output[chlorosis_mask != 0] = [255, 222, 83, 200]  # Chlorosis Color - yellow

        # Save the images
        base_filename = os.path.splitext(os.path.basename(image_path))[0]
        output_path = os.path.join(output_directory, f"{base_filename}_masked.png")
        Image.fromarray(output).save(output_path)

        return {
            "filename": base_filename,
            "leaf_area_px": int(leaf_area),
            "healthy_area_px": int(healthy_area),
            "disease_area_px": int(disease_area),
            "chlorosis_area_px": int(chlorosis_area),
            "percent_healthy": round(percent_healthy, 2),
            "percent_disease": round(percent_disease, 2),
            "percent_chlorosis": round(percent_chlorosis, 2),
        }
    except Exception as e:
        logging.error(f"Error processing {image_path}: {str(e)}")
        return None

def process_directory():
    """Process all images in the directory"""
    start_time = time.time()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create output directory with timestamp
    timestamped_output_dir = os.path.join(OUTPUT_DIRECTORY, timestamp)
    if not os.path.exists(timestamped_output_dir):
        os.makedirs(timestamped_output_dir)

    logging.info(f"Starting processing of directory: {DIRECTORY_PATH}")
    logging.info(f"Output will be saved to: {timestamped_output_dir}")
    
    results = []
    valid_extensions = (".tif", ".tiff", ".png", ".jpg", ".jpeg")
    total_files = len([f for f in os.listdir(DIRECTORY_PATH) if f.lower().endswith(valid_extensions)])
    processed_files = 0
    
    for filename in os.listdir(DIRECTORY_PATH):
        if filename.lower().endswith(valid_extensions):
            image_path = os.path.join(DIRECTORY_PATH, filename)
            logging.info(f"Processing image {processed_files+1}/{total_files}: {filename}")
            
            result = process_image(image_path, timestamped_output_dir)
            if result:
                results.append(result)
                processed_files += 1
    
    # Convert results to a DataFrame and save to CSV
    if results:
        df = pd.DataFrame(results)
        output_csv_path = os.path.join(timestamped_output_dir, "summary_results.csv")
        df.to_csv(output_csv_path, index=False)
        
        # Also save a summary file
        summary_file = os.path.join(timestamped_output_dir, "analysis_summary.txt")
        with open(summary_file, 'w') as f:
            f.write(f"Leaf Disease Analysis Summary - {timestamp}\n")
            f.write(f"----------------------------------------\n")
            f.write(f"Total images processed: {len(results)}\n")
            f.write(f"Average healthy area: {df['percent_healthy'].mean():.2f}%\n")
            f.write(f"Average disease area: {df['percent_disease'].mean():.2f}%\n")
            f.write(f"Average chlorosis area: {df['percent_chlorosis'].mean():.2f}%\n")
            f.write(f"----------------------------------------\n")
            f.write(f"Disease hue value: {DISEASE_HUE}\n")
            f.write(f"Chlorosis hue range: {CHLOROSIS_HUE_RANGE}\n")
        
        logging.info(f"Results saved to {output_csv_path}")
        logging.info(f"Summary saved to {summary_file}")
    else:
        logging.warning("No valid results were produced.")
    
    elapsed_time = time.time() - start_time
    logging.info(f"Processing complete. Time elapsed: {elapsed_time:.2f} seconds")
    
    return results

if __name__ == "__main__":
    # Create output directory if it doesn't exist
    if not os.path.exists(OUTPUT_DIRECTORY):
        os.makedirs(OUTPUT_DIRECTORY)
        
    # Process all images in the directory
    results = process_directory()
    
    # Print summary of results
    if results:
        df = pd.DataFrame(results)
        print("\nSummary of Results:")
        print(f"Total images processed: {len(results)}")
        print(f"Average healthy area: {df['percent_healthy'].mean():.2f}%")
        print(f"Average disease area: {df['percent_disease'].mean():.2f}%")
        print(f"Average chlorosis area: {df['percent_chlorosis'].mean():.2f}%")