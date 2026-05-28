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
DIRECTORY_PATH = "./coinday10/thermo"  # Replace with your actual path
OUTPUT_DIRECTORY = os.path.join(DIRECTORY_PATH, "output")
MIN_LEAF_SIZE = 500  # Minimum size of leaf area in pixels

def process_image(image_path, output_directory):
    """Process a single image to remove background only"""
    try:
        image = Image.open(image_path)
        image_np = np.array(image)
        hsv_image = cv2.cvtColor(image_np, cv2.COLOR_RGB2HSV)

        # Create leaf mask to identify non-background areas
        leaf_mask = cv2.inRange(hsv_image, np.array([0, 0, 0], dtype=np.uint8), np.array([90, 255, 255], dtype=np.uint8))
        leaf_mask = morphology.remove_small_objects(leaf_mask.astype(bool), MIN_LEAF_SIZE)
        leaf_mask = morphology.remove_small_holes(leaf_mask, MIN_LEAF_SIZE)

        # Calculate leaf area
        leaf_area = np.sum(leaf_mask)
        
        # Create output with background removed
        output = cv2.cvtColor(image_np, cv2.COLOR_RGB2RGBA)
        output[leaf_mask == 0] = [0, 0, 0, 0]  # Background transparency

        # Save the image with background removed
        base_filename = os.path.splitext(os.path.basename(image_path))[0]
        output_path = os.path.join(output_directory, f"{base_filename}_background_removed.png")
        Image.fromarray(output).save(output_path)

        return {
            "filename": base_filename,
            "leaf_area_px": int(leaf_area),
            "output_path": output_path
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
        output_csv_path = os.path.join(timestamped_output_dir, "background_removal_results.csv")
        df.to_csv(output_csv_path, index=False)
        
        # Also save a summary file
        summary_file = os.path.join(timestamped_output_dir, "processing_summary.txt")
        with open(summary_file, 'w') as f:
            f.write(f"Background Removal Summary - {timestamp}\n")
            f.write(f"----------------------------------------\n")
            f.write(f"Total images processed: {len(results)}\n")
            f.write(f"Average leaf area: {df['leaf_area_px'].mean():.2f} pixels\n")
            f.write(f"Output directory: {timestamped_output_dir}\n")
        
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
        print(f"Average leaf area: {df['leaf_area_px'].mean():.2f} pixels")