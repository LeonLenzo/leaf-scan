#!/usr/bin/env python3
"""
Leaf Analysis Launcher

Simple launcher script that lets users choose between GUI and command-line interfaces.
"""

import sys
import os
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'cv2', 'PIL', 'numpy', 'pandas', 'skimage'
    ]

    missing = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)

    if missing:
        print("❌ Missing required packages:")
        for pkg in missing:
            print(f"   - {pkg}")
        print("\nInstall with:")
        print("pip install opencv-python pillow numpy pandas scikit-image")
        return False
    return True

def main():
    print("🍃 Leaf Health Analysis Tool")
    print("=" * 40)

    if not check_dependencies():
        sys.exit(1)

    print("\nChoose interface:")
    print("1. 🖥️  GUI (Graphical User Interface)")
    print("2. 💻 Command Line Interface")
    print("3. ❓ Help")
    print("4. 🚪 Exit")

    while True:
        choice = input("\nEnter your choice (1-4): ").strip()

        if choice == '1':
            print("\n🚀 Launching GUI...")
            try:
                subprocess.run([sys.executable, 'leaf_gui.py'])
            except FileNotFoundError:
                print("❌ Error: leaf_gui.py not found in current directory")
            except KeyboardInterrupt:
                print("\n👋 GUI closed")
            break

        elif choice == '2':
            print("\n💻 Command Line Interface")
            print("Examples:")
            print("  python leafstate2.py                    # Analyze current directory")
            print("  python leafstate2.py --input ./images  # Analyze specific folder")
            print("  python leafstate2.py --help            # Show all options")

            cmd = input("\nEnter command (or press Enter for basic analysis): ").strip()
            if not cmd:
                cmd = "python leafstate2.py"

            try:
                subprocess.run(cmd, shell=True)
            except KeyboardInterrupt:
                print("\n⏹️ Analysis interrupted")
            break

        elif choice == '3':
            print("\n❓ Help")
            print("""
🍃 Leaf Health Analysis Tool

This tool analyzes plant leaf images to detect and quantify:
• Healthy tissue (green areas)
• Chlorosis (yellowing/stress indicators)
• Necrosis (brown/dead tissue)

GUI Mode:
- Easy drag-and-drop interface
- Visual progress feedback
- Built-in help and configuration

Command Line Mode:
- Batch processing capabilities
- Scriptable for automation
- Advanced configuration options

For detailed documentation, see README.md
            """)
            input("\nPress Enter to continue...")

        elif choice == '4':
            print("\n👋 Goodbye!")
            break

        else:
            print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")

if __name__ == "__main__":
    main()