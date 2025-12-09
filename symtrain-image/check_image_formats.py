#!/usr/bin/env python3
"""
Quick diagnostic script to check image formats in your data directory
Recursively scans all subfolders
"""

import os
from pathlib import Path
from collections import Counter, defaultdict

def check_image_formats_recursive(root_directory):
    """Check what image formats exist in a directory and all subdirectories."""
    root_path = Path(root_directory)
    
    if not root_path.exists():
        print(f"❌ Directory not found: {root_directory}")
        return
    
    print(f"\n{'='*80}")
    print(f"📂 Scanning: {root_directory}")
    print(f"{'='*80}\n")
    
    # Find all image files recursively
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.JPG', '.JPEG', '.PNG', '.GIF', '.BMP'}
    
    # Group images by subdirectory
    images_by_folder = defaultdict(list)
    all_images = []
    
    for item in root_path.rglob('*'):
        if item.is_file() and item.suffix in image_extensions:
            # Get relative folder path
            relative_folder = item.parent.relative_to(root_path)
            images_by_folder[str(relative_folder)].append(item)
            all_images.append(item)
    
    if not all_images:
        print("❌ No image files found in any subfolder!")
        return
    
    # Overall statistics
    print(f"✅ Found {len(all_images)} total images across {len(images_by_folder)} folder(s)\n")
    
    # Overall extension breakdown
    overall_extension_counts = Counter(img.suffix for img in all_images)
    print("📊 Overall Format Distribution:")
    print("-" * 80)
    for ext, count in sorted(overall_extension_counts.items()):
        percentage = (count / len(all_images)) * 100
        print(f"  {ext:8s} : {count:4d} files ({percentage:5.1f}%)")
    print()
    
    # Check for mixed case issues
    extensions_set = set(overall_extension_counts.keys())
    warnings = []
    
    if '.jpg' in extensions_set and '.JPG' in extensions_set:
        warnings.append("Mixed case: .jpg and .JPG")
    if '.jpeg' in extensions_set and '.JPEG' in extensions_set:
        warnings.append("Mixed case: .jpeg and .JPEG")
    if '.png' in extensions_set and '.PNG' in extensions_set:
        warnings.append("Mixed case: .png and .PNG")
    if '.gif' in extensions_set and '.GIF' in extensions_set:
        warnings.append("Mixed case: .gif and .GIF")
    
    if warnings:
        print("⚠️  Format Warnings:")
        print("-" * 80)
        for warning in warnings:
            print(f"  • {warning}")
        print("  → The vision_mapper code handles this automatically! ✅")
        print()
    
    # Per-folder breakdown
    print("📁 Breakdown by Folder:")
    print("=" * 80)
    
    for folder_path in sorted(images_by_folder.keys()):
        images = images_by_folder[folder_path]
        extension_counts = Counter(img.suffix for img in images)
        
        # Display folder name
        display_folder = folder_path if folder_path != '.' else '(root)'
        print(f"\n📂 {display_folder}")
        print(f"   {len(images)} images")
        
        # Show format breakdown
        for ext, count in sorted(extension_counts.items()):
            print(f"      {ext:8s} : {count:3d} files")
        
        # Show sample files (first 3)
        if len(images) <= 5:
            print(f"   Files:")
            for img in sorted(images):
                print(f"      • {img.name}")
        else:
            print(f"   Sample files (showing 3 of {len(images)}):")
            for img in sorted(images)[:3]:
                print(f"      • {img.name}")
            print(f"      ... and {len(images) - 3} more")
    
    print("\n" + "=" * 80)
    print("\n✅ Scan complete!\n")
    
    # Summary
    print("💡 Summary:")
    print(f"   • Total images: {len(all_images)}")
    print(f"   • Folders with images: {len(images_by_folder)}")
    print(f"   • Unique formats: {len(overall_extension_counts)}")
    if warnings:
        print(f"   • Mixed case detected: Yes (handled automatically)")
    else:
        print(f"   • Mixed case detected: No")
    print()

def check_single_folder(directory):
    """Check a single directory (non-recursive) for comparison."""
    path = Path(directory)
    
    if not path.exists():
        print(f"❌ Directory not found: {directory}")
        return
    
    print(f"\n📂 Single Folder Check: {directory}")
    print("=" * 80)
    
    # Find all image files in this folder only
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.JPG', '.JPEG', '.PNG', '.GIF', '.BMP'}
    images = [f for f in path.iterdir() if f.is_file() and f.suffix in image_extensions]
    
    if not images:
        print("❌ No image files found in this folder!")
        return
    
    # Count by extension
    extension_counts = Counter(img.suffix for img in images)
    
    print(f"\n✅ Found {len(images)} images:")
    for ext, count in sorted(extension_counts.items()):
        print(f"  {ext:8s} : {count:3d} files")
    
    print("\n📋 Files:")
    for img in sorted(images)[:10]:
        print(f"  • {img.name}")
    if len(images) > 10:
        print(f"  ... and {len(images) - 10} more")
    print()

if __name__ == "__main__":
    import sys
    
    # Default to checking the data directory recursively
    default_directory = "./data"
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        target_directory = sys.argv[1]
    else:
        target_directory = default_directory
    
    # Check if path exists
    if not Path(target_directory).exists():
        print(f"\n❌ Directory not found: {target_directory}")
        print("\nUsage:")
        print(f"  python check_image_formats.py [directory]")
        print(f"\nExamples:")
        print(f"  python check_image_formats.py ./data                    # Check all subfolders")
        print(f"  python check_image_formats.py ./data/SymTrain-Overview  # Check specific folder")
        exit(1)
    
    # Run the recursive check
    check_image_formats_recursive(target_directory)
    
    print("💾 Want to check a specific folder only? Run:")
    print(f"   python check_image_formats.py <specific-folder-path>")
    print()
