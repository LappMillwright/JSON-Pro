#!/usr/bin/env python3
"""
Create JSON Pro app icon from json.png
Generates all required sizes for macOS .icns file
"""

from PIL import Image
import os

def create_icon_sizes(source_image_path, output_dir):
    """Create all required icon sizes for macOS"""

    # Load the source image
    img = Image.open(source_image_path)

    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Define all required icon sizes for macOS
    # Format: (size, filename)
    sizes = [
        (16, "icon_16x16.png"),
        (32, "icon_16x16@2x.png"),  # 2x retina for 16x16
        (32, "icon_32x32.png"),
        (64, "icon_32x32@2x.png"),  # 2x retina for 32x32
        (128, "icon_128x128.png"),
        (256, "icon_128x128@2x.png"),  # 2x retina for 128x128
        (256, "icon_256x256.png"),
        (512, "icon_256x256@2x.png"),  # 2x retina for 256x256
        (512, "icon_512x512.png"),
        (1024, "icon_512x512@2x.png"),  # 2x retina for 512x512
    ]

    # Generate each size
    for size, filename in sizes:
        # Resize image with high-quality resampling
        resized = img.resize((size, size), Image.Resampling.LANCZOS)

        # Save to iconset directory
        output_path = os.path.join(output_dir, filename)
        resized.save(output_path, "PNG")
        print(f"Created: {filename} ({size}x{size})")

    print(f"\nAll icon sizes created in {output_dir}")
    print("\nNext step: Run this command to create .icns file:")
    print(f"iconutil -c icns {output_dir} -o JSONPro.icns")

def main():
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Source image and output directory
    source_image = os.path.join(script_dir, "json.png")
    iconset_dir = os.path.join(script_dir, "JSONPro.iconset")

    # Check if source image exists
    if not os.path.exists(source_image):
        print(f"Error: Source image not found: {source_image}")
        return

    print(f"Source image: {source_image}")
    print(f"Output directory: {iconset_dir}")
    print()

    # Create all icon sizes
    create_icon_sizes(source_image, iconset_dir)

if __name__ == "__main__":
    main()
