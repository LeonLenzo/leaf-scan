import os
import numpy as np
from PIL import Image

def adjust_temperature(image, temperature_factor):
    """
    Adjust the temperature of an image.

    :param image: The input image.
    :param temperature_factor: The temperature adjustment factor.
                              >1 for warmer, <1 for cooler.
    :return: The temperature-adjusted image.
    """
    # Convert the image to RGB mode if it's not
    image = image.convert('RGB')

    # Convert image to numpy array
    np_image = np.array(image, dtype=np.float32)

    # Apply temperature adjustment
    if temperature_factor > 1:
        # Warming the image
        np_image[..., 0] = np.clip(np_image[..., 0] * temperature_factor, 0, 255)  # Red channel
        np_image[..., 2] = np.clip(np_image[..., 2] / temperature_factor, 0, 255)  # Blue channel
    else:
        # Cooling the image
        np_image[..., 0] = np.clip(np_image[..., 0] * temperature_factor, 0, 255)  # Red channel
        np_image[..., 2] = np.clip(np_image[..., 2] / temperature_factor, 0, 255)  # Blue channel

    # Convert back to Image
    result_image = Image.fromarray(np_image.astype('uint8'), 'RGB')
    
    return result_image

def process_images(input_dir, output_dir, temperature_factor):
    """
    Process all images in the input directory and save the temperature-adjusted images to the output directory.

    :param input_dir: Directory containing the input images.
    :param output_dir: Directory to save the adjusted images.
    :param temperature_factor: The temperature adjustment factor.
                              >1 for warmer, <1 for cooler.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Processing images from {input_dir} to {output_dir} with temperature factor {temperature_factor}")
    
    # List the contents of the input directory
    input_files = os.listdir(input_dir)
    print(f"Found {len(input_files)} files in the input directory.")

    for filename in input_files:
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tif')):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename)

            try:
                # Open the image
                with Image.open(input_path) as img:
                    # Adjust the temperature
                    adjusted_img = adjust_temperature(img, temperature_factor)
                    # Save the adjusted image
                    adjusted_img.save(output_path)
            except Exception as e:
                print(f"Failed to process {filename}: {e}")

if __name__ == '__main__':
    input_directory = 'intergrain'
    output_directory = 'intergrain/thermo'
    temperature_factor = 0.9  # >1 for warmer, <1 for cooler

    if not os.path.exists(input_directory):
        print(f"Input directory does not exist: {input_directory}")
    else:
        process_images(input_directory, output_directory, temperature_factor)
