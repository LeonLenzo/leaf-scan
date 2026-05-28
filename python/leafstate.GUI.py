"""
leafstate - Leaf Health Analysis GUI

🍃 Simple graphical interface for analyzing plant leaf health

Double-click this file to launch the GUI interface.
Analyzes leaf images to detect healthy, chlorotic, and necrotic tissue.

Author: Leon Lenzo
Requirements:
- Python 3.7+
- pip install opencv-python pillow scikit-image pandas numpy
- tkinter (usually included with Python)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import shutil
import sys
import os
from pathlib import Path
import colorsys

# Check for required packages
missing_packages = []
try:
    import cv2
except ImportError:
    missing_packages.append("opencv-python")

try:
    from PIL import Image
except ImportError:
    missing_packages.append("pillow")

try:
    import numpy as np
except ImportError:
    missing_packages.append("numpy")

try:
    import pandas as pd
except ImportError:
    missing_packages.append("pandas")

try:
    from skimage import morphology, measure
except ImportError:
    missing_packages.append("scikit-image")

# Import our analysis module
try:
    from leafstate2 import analyze_directory, LeafAnalysisConfig
except ImportError:
    missing_packages.append("leafstate2.py (make sure it's in the same directory)")

if missing_packages:
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    root.withdraw()  # Hide main window

    error_msg = "Missing required packages:\n\n"
    for pkg in missing_packages:
        error_msg += f"• {pkg}\n"

    if "leafstate2.py" not in str(missing_packages):
        error_msg += "\nTo install packages, run:\n"
        error_msg += "pip install opencv-python pillow numpy pandas scikit-image"

    messagebox.showerror("leafstate - Missing Dependencies", error_msg)
    sys.exit(1)


class LeafAnalysisGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("leafstate")
        self.root.geometry("650x750")
        self.root.resizable(True, True)

        # Configure style
        style = ttk.Style()
        style.theme_use('clam')

        self.config = LeafAnalysisConfig()
        self.current_analysis = None
        self.color_previews = {}  # Store color preview widgets
        self.setup_ui()

    def hsv_to_rgb_hex(self, hue_opencv):
        """Convert OpenCV HSV hue value (0-179) to RGB hex color"""
        # Convert OpenCV hue (0-179) to standard hue (0-1)
        hue_norm = hue_opencv / 179.0
        # Use high saturation and value for vivid colors
        r, g, b = colorsys.hsv_to_rgb(hue_norm, 0.8, 0.9)
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

    def update_color_preview(self, preview_widget, hue_var):
        """Update color preview widget when hue value changes"""
        try:
            hue_value = hue_var.get()
            color = self.hsv_to_rgb_hex(hue_value)
            preview_widget.configure(bg=color)
        except:
            pass  # Handle invalid values gracefully

    def create_hue_control(self, parent, label_text, hue_var, min_val, max_val, row):
        """Create a hue control with color preview"""
        # Label
        ttk.Label(parent, text=label_text).grid(row=row, column=0, sticky=tk.W, pady=5)

        # Spinbox
        spinbox = ttk.Spinbox(
            parent,
            from_=min_val,
            to=max_val,
            textvariable=hue_var,
            width=8,
            command=lambda: self.update_color_preview(self.color_previews[label_text], hue_var)
        )
        spinbox.grid(row=row, column=1, sticky=tk.W, padx=(10, 5), pady=5)

        # Color preview
        preview_frame = tk.Frame(parent, width=30, height=20, relief='sunken', bd=1)
        preview_frame.grid(row=row, column=2, padx=(5, 10), pady=5)
        preview_frame.grid_propagate(False)

        # Store preview widget for updates
        self.color_previews[label_text] = preview_frame

        # Bind events to update color preview
        hue_var.trace('w', lambda *args: self.update_color_preview(preview_frame, hue_var))

        # Initial color update
        self.update_color_preview(preview_frame, hue_var)

    def setup_ui(self):
        """Create the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="Leaf Health Analysis - leafstate",
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # Input directory selection
        ttk.Label(main_frame, text="Input Directory:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.input_var = tk.StringVar(value=str(Path.cwd()))
        input_entry = ttk.Entry(main_frame, textvariable=self.input_var, width=50)
        input_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        ttk.Button(
            main_frame,
            text="Browse...",
            command=self.browse_input
        ).grid(row=1, column=2, padx=(5, 0), pady=5)

        # Output directory selection
        ttk.Label(main_frame, text="Output Directory:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.output_var = tk.StringVar(value="Auto-generate")
        output_entry = ttk.Entry(main_frame, textvariable=self.output_var, width=50)
        output_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        ttk.Button(
            main_frame,
            text="Browse...",
            command=self.browse_output
        ).grid(row=2, column=2, padx=(5, 0), pady=5)

        # Preprocessing frame
        preprocess_frame = ttk.LabelFrame(main_frame, text="Preprocessing", padding="10")
        preprocess_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        preprocess_frame.columnconfigure(2, weight=1)

        self.temp_correct_var = tk.BooleanVar()
        ttk.Checkbutton(
            preprocess_frame,
            text="Apply Temperature Correction",
            variable=self.temp_correct_var,
            command=self.toggle_temp_factor
        ).grid(row=0, column=0, columnspan=3, sticky=tk.W)

        ttk.Label(preprocess_frame, text="Temperature Factor:").grid(row=1, column=0, sticky=tk.W, pady=(8, 0))
        self.temp_factor_var = tk.DoubleVar(value=1.0)
        self.temp_factor_spinbox = ttk.Spinbox(
            preprocess_frame,
            from_=0.5,
            to=2.0,
            increment=0.05,
            textvariable=self.temp_factor_var,
            width=8,
            format="%.2f",
            state='disabled'
        )
        self.temp_factor_spinbox.grid(row=1, column=1, sticky=tk.W, padx=(10, 5), pady=(8, 0))
        ttk.Label(preprocess_frame, text=">1.0 = warmer,  <1.0 = cooler").grid(
            row=1, column=2, sticky=tk.W, padx=(5, 0), pady=(8, 0)
        )

        # Settings frame
        settings_frame = ttk.LabelFrame(main_frame, text="Analysis Settings", padding="10")
        settings_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=20)
        settings_frame.columnconfigure(1, weight=1)

        # Size settings
        size_frame = ttk.LabelFrame(settings_frame, text="Size Filters", padding="5")
        size_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        # Min leaf size
        ttk.Label(size_frame, text="Minimum Leaf Size (pixels):").grid(row=0, column=0, sticky=tk.W)
        self.min_size_var = tk.IntVar(value=self.config.MIN_LEAF_SIZE)
        ttk.Spinbox(
            size_frame,
            from_=100,
            to=2000,
            textvariable=self.min_size_var,
            width=10
        ).grid(row=0, column=1, sticky=tk.W, padx=(10, 0))

        # Min leaf height
        ttk.Label(size_frame, text="Minimum Leaf Height (pixels):").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        self.min_height_var = tk.IntVar(value=self.config.MIN_LEAF_HEIGHT)
        ttk.Spinbox(
            size_frame,
            from_=20,
            to=200,
            textvariable=self.min_height_var,
            width=10
        ).grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=(10, 0))

        # Color/Hue settings
        color_frame = ttk.LabelFrame(settings_frame, text="Color Detection (HSV Hue Values)", padding="5")
        color_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        color_frame.columnconfigure(2, weight=1)

        # Hue variables
        self.necrosis_hue_var = tk.IntVar(value=self.config.NECROSIS_HUE)
        self.chlorosis_hue_var = tk.IntVar(value=self.config.CHLOROSIS_HUE)
        self.healthy_hue_var = tk.IntVar(value=self.config.HEALTHY_HUE)

        # Create hue controls with color previews
        self.create_hue_control(color_frame, "Necrosis (Brown/Dead):", self.necrosis_hue_var, 0, 30, 0)
        self.create_hue_control(color_frame, "Chlorosis (Yellow/Stress):", self.chlorosis_hue_var, 20, 50, 1)
        self.create_hue_control(color_frame, "Healthy (Green) Upper Limit:", self.healthy_hue_var, 60, 120, 2)

        # Options
        options_frame = ttk.LabelFrame(settings_frame, text="Options", padding="5")
        options_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E))

        # Verbose logging
        self.verbose_var = tk.BooleanVar()
        ttk.Checkbutton(
            options_frame,
            text="Verbose logging (detailed output)",
            variable=self.verbose_var
        ).grid(row=0, column=0, sticky=tk.W)

        # Progress frame
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=20)
        progress_frame.columnconfigure(0, weight=1)

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            mode='indeterminate'
        )
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)

        # Status label
        self.status_var = tk.StringVar(value="Ready to analyze images")
        self.status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        self.status_label.grid(row=1, column=0, pady=5)

        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=6, column=0, columnspan=3, pady=20)

        # Start analysis button
        self.start_button = ttk.Button(
            buttons_frame,
            text="Start Analysis",
            command=self.start_analysis
        )
        self.start_button.grid(row=0, column=0, padx=(0, 10))

        # Open results button
        self.results_button = ttk.Button(
            buttons_frame,
            text="Open Results",
            command=self.open_results,
            state='disabled'
        )
        self.results_button.grid(row=0, column=1, padx=10)

        # Help button
        ttk.Button(
            buttons_frame,
            text="Help",
            command=self.show_help
        ).grid(row=0, column=2, padx=(10, 0))

    def toggle_temp_factor(self):
        """Enable or disable the temperature factor spinbox based on checkbox state"""
        state = 'normal' if self.temp_correct_var.get() else 'disabled'
        self.temp_factor_spinbox.config(state=state)

    def apply_temperature_correction(self, input_dir, temp_dir):
        """Copy images to temp_dir with temperature adjustment applied"""
        from thermostat import adjust_temperature

        os.makedirs(temp_dir, exist_ok=True)
        factor = self.temp_factor_var.get()
        valid_extensions = ('.tif', '.tiff', '.png', '.jpg', '.jpeg')

        for filename in os.listdir(input_dir):
            if filename.lower().endswith(valid_extensions):
                src = os.path.join(input_dir, filename)
                dst = os.path.join(temp_dir, filename)
                with Image.open(src) as img:
                    adjust_temperature(img, factor).save(dst)

    def browse_input(self):
        """Browse for input directory"""
        directory = filedialog.askdirectory(
            title="Select Input Directory",
            initialdir=self.input_var.get()
        )
        if directory:
            self.input_var.set(directory)

    def browse_output(self):
        """Browse for output directory"""
        directory = filedialog.askdirectory(
            title="Select Output Directory",
            initialdir=self.output_var.get() if self.output_var.get() != "Auto-generate" else self.input_var.get()
        )
        if directory:
            self.output_var.set(directory)

    def update_config(self):
        """Update configuration from GUI values"""
        self.config.MIN_LEAF_SIZE = self.min_size_var.get()
        self.config.MIN_LEAF_HEIGHT = self.min_height_var.get()
        self.config.NECROSIS_HUE = self.necrosis_hue_var.get()
        self.config.CHLOROSIS_HUE = self.chlorosis_hue_var.get()
        self.config.HEALTHY_HUE = self.healthy_hue_var.get()

    def start_analysis(self):
        """Start the analysis in a separate thread"""
        input_dir = self.input_var.get()
        if not input_dir or not Path(input_dir).exists():
            messagebox.showerror("Error", "Please select a valid input directory")
            return

        # Check if directory contains images
        input_path = Path(input_dir)
        image_files = []
        for ext in self.config.SUPPORTED_FORMATS:
            image_files.extend(input_path.glob(f"*{ext}"))
            image_files.extend(input_path.glob(f"*{ext.upper()}"))

        if not image_files:
            messagebox.showwarning(
                "No Images Found",
                f"No supported image files found in {input_dir}\n\n"
                f"Supported formats: {', '.join(self.config.SUPPORTED_FORMATS)}"
            )
            return

        # Update configuration
        self.update_config()

        # Disable start button and enable progress
        self.start_button.config(state='disabled')
        self.results_button.config(state='disabled')
        self.progress_bar.start()
        self.status_var.set(f"Analyzing {len(image_files)} images...")

        # Start analysis in separate thread
        output_dir = None if self.output_var.get() == "Auto-generate" else self.output_var.get()

        analysis_thread = threading.Thread(
            target=self.run_analysis,
            args=(input_dir, output_dir),
            daemon=True
        )
        analysis_thread.start()

    def run_analysis(self, input_dir, output_dir):
        """Run analysis in background thread"""
        temp_dir = None
        try:
            analysis_input = input_dir

            if self.temp_correct_var.get():
                temp_dir = os.path.join(input_dir, "_temp_corrected")
                self.root.after(0, lambda: self.status_var.set("Applying temperature correction..."))
                self.apply_temperature_correction(input_dir, temp_dir)
                analysis_input = temp_dir

            result_path = analyze_directory(
                analysis_input,
                output_dir,
                self.config,
                self.verbose_var.get()
            )

            self.root.after(0, self.analysis_complete, result_path)

        except Exception as e:
            self.root.after(0, self.analysis_error, str(e))

        finally:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def analysis_complete(self, result_path):
        """Handle successful analysis completion"""
        self.progress_bar.stop()
        self.start_button.config(state='normal')

        if result_path:
            self.current_analysis = result_path
            self.results_button.config(state='normal')
            self.status_var.set(f"Analysis complete! Results saved to: {result_path.parent}")

            messagebox.showinfo(
                "Analysis Complete",
                f"Leaf analysis completed successfully!\n\n"
                f"Results saved to:\n{result_path}\n\n"
                f"Click 'Open Results' to view the output directory."
            )
        else:
            self.status_var.set("Analysis completed but no results generated")
            messagebox.showwarning("No Results", "Analysis completed but no leaves were detected.")

    def analysis_error(self, error_message):
        """Handle analysis error"""
        self.progress_bar.stop()
        self.start_button.config(state='normal')
        self.status_var.set(f"Error: {error_message}")

        messagebox.showerror("Analysis Error", f"An error occurred during analysis:\n\n{error_message}")

    def open_results(self):
        """Open the results directory"""
        if self.current_analysis:
            result_dir = self.current_analysis.parent
            try:
                # Try to open in file manager
                if sys.platform == "win32":
                    os.startfile(result_dir)
                elif sys.platform == "darwin":
                    os.system(f"open '{result_dir}'")
                else:
                    os.system(f"xdg-open '{result_dir}'")
            except Exception as e:
                messagebox.showerror("Error", f"Could not open results directory: {e}")

    def show_help(self):
        """Show help information"""
        help_text = """
Leaf Health Analysis Tool

This tool analyzes plant leaf images to detect and quantify:
- Healthy tissue (green areas)
- Chlorosis (yellowing/stress indicators)
- Necrosis (brown/dead tissue)

How to use:
1. Select an input directory containing your leaf images
2. Optionally choose an output directory (or use auto-generate)
3. Adjust analysis settings if needed
4. Click 'Start Analysis'

Supported image formats:
.tif, .tiff, .png, .jpg, .jpeg

The tool will:
- Detect individual leaves in each image
- Analyze tissue health for each leaf
- Generate visualizations showing detected areas
- Save results to a CSV file with detailed statistics

Settings:
- Size Filters: Minimum leaf size and height thresholds
- Color Detection: HSV hue values with live color previews
- Options: Verbose logging for detailed output

Output:
- Individual leaf images with color-coded health analysis
- Combined visualization for each input image
- CSV file with quantitative results for all leaves
        """

        help_window = tk.Toplevel(self.root)
        help_window.title("Help - Leaf Analysis Tool")
        help_window.geometry("600x500")

        text_widget = tk.Text(help_window, wrap=tk.WORD, padx=20, pady=20)
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert(tk.END, help_text)
        text_widget.config(state=tk.DISABLED)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(help_window, command=text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.config(yscrollcommand=scrollbar.set)


def main():
    """Run the GUI application"""
    root = tk.Tk()
    app = LeafAnalysisGUI(root)

    # Set window icon if available
    try:
        root.iconphoto(True, tk.PhotoImage(data=""))  # You can add an icon here
    except:
        pass

    root.mainloop()


if __name__ == "__main__":
    main()