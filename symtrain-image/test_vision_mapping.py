#!/usr/bin/env python3
"""
Quick test script to debug vision mapping issues
Scans ALL JSON files in /data folder (all companies)
"""

import json
from pathlib import Path
from vision_mapper import VisionMapper

def load_all_visual_items(data_directory="./data"):
    """Load visual items from ALL JSON files in data directory."""
    data_path = Path(data_directory)
    
    if not data_path.exists():
        print(f"❌ Directory not found: {data_directory}")
        return [], {}
    
    # Find all JSON files recursively
    json_files = list(data_path.rglob("*.json"))
    
    print(f"\n📂 Scanning: {data_directory}")
    print(f"✅ Found {len(json_files)} JSON file(s)")
    
    all_visual_items = []
    visual_items_by_file = {}  # Track which file each visual item came from
    
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            visual_items = data.get('visualContentItems', [])
            
            if visual_items:
                print(f"\n   📄 {json_file.relative_to(data_path)}")
                print(f"      └─ {len(visual_items)} visual items")
                
                # Count hotspots
                hotspot_count = sum(len(item.get('hotspots', [])) for item in visual_items)
                non_audio = sum(
                    1 for item in visual_items 
                    for hotspot in item.get('hotspots', [])
                    if hotspot.get('type', '').upper() != 'AUDIO'
                )
                print(f"      └─ {hotspot_count} total hotspots ({non_audio} non-audio)")
                
                # Track source file for each visual item
                for item in visual_items:
                    item_copy = item.copy()
                    item_copy['_source_file'] = str(json_file)
                    all_visual_items.append(item_copy)
                    visual_items_by_file[item.get('fileId')] = str(json_file.parent)
        
        except Exception as e:
            print(f"   ⚠️  Error loading {json_file.name}: {e}")
    
    return all_visual_items, visual_items_by_file

def test_vision_mapping():
    """Test vision mapping with ALL your data."""
    
    print("\n" + "="*80)
    print("VISION MAPPING DEBUG TEST - ALL DATA SOURCES")
    print("="*80)
    
    # Load ALL visual items from all JSON files
    all_visual_items, visual_items_by_file = load_all_visual_items("./data")
    
    if not all_visual_items:
        print("\n❌ No visual content items found in any JSON files!")
        print("\nTried scanning: ./data")
        print("\nMake sure your JSON files have 'visualContentItems' field.")
        return
    
    print(f"\n{'='*80}")
    print(f"TOTAL VISUAL CONTENT LOADED:")
    print(f"{'='*80}")
    print(f"   Total visual items: {len(all_visual_items)}")
    print(f"   From {len(set(item.get('_source_file') for item in all_visual_items))} different JSON file(s)")
    
    # Count total hotspots
    total_hotspots = sum(len(item.get('hotspots', [])) for item in all_visual_items)
    non_audio_hotspots = sum(
        1 for item in all_visual_items
        for hotspot in item.get('hotspots', [])
        if hotspot.get('type', '').upper() != 'AUDIO'
    )
    print(f"   Total hotspots: {total_hotspots}")
    print(f"   Non-audio hotspots: {non_audio_hotspots}")
    
    # Show sample hotspots from first few images
    print(f"\n📋 Sample hotspots from first 3 images:")
    for i, item in enumerate(all_visual_items[:3], 1):
        file_id = item.get('fileId', 'N/A')
        source = Path(item.get('_source_file', 'unknown')).name
        print(f"\n   Image {i}: {file_id[:40]}...")
        print(f"   Source: {source}")
        hotspots = item.get('hotspots', [])[:3]
        for j, hotspot in enumerate(hotspots, 1):
            name = hotspot.get('name', 'N/A')
            h_type = hotspot.get('type', 'N/A')
            print(f"      {j}. {name:30s} | Type: {h_type}")
        if len(item.get('hotspots', [])) > 3:
            print(f"      ... and {len(item.get('hotspots', [])) - 3} more hotspots")
    
    # Test with sample steps
    print(f"\n{'='*80}")
    print("🧪 TESTING WITH SAMPLE STEPS:")
    print(f"{'='*80}")
    
    test_steps = [
        "Click on Account Settings in the top right corner",
        "Navigate to Payment Methods from the menu",
        "Enter your credit card number in the card number field",
        "Click the Submit button to save changes"
    ]
    
    print("\nTest steps:")
    for i, step in enumerate(test_steps, 1):
        print(f"   {i}. {step}")
    
    # Create mapper
    mapper = VisionMapper()
    
    # Test mapping with DEBUG enabled
    print(f"\n{'='*80}")
    print("MAPPING TEST (with debug output):")
    print(f"{'='*80}")
    
    mappings = mapper.map_steps_to_images(
        test_steps,
        all_visual_items,
        threshold=0.2,
        debug=True  # Enable debug output
    )
    
    # Summary
    print(f"\n{'='*80}")
    print("RESULTS:")
    print(f"{'='*80}")
    
    mapped_count = sum(1 for m in mappings if m['file_id'])
    print(f"\n✅ Mapped: {mapped_count}/{len(test_steps)} steps")
    print(f"   Mapping rate: {mapped_count/len(test_steps)*100:.1f}%")
    
    if mapped_count == 0:
        print("\n❌ NO MATCHES FOUND!")
        print("\n🔍 Possible issues:")
        print("  1. Threshold too high (currently 0.2)")
        print("  2. Hotspot names don't match test steps")
        print("  3. All hotspots are AUDIO type")
        print("  4. Penalty for generic names too harsh")
        print("\nCheck the debug output above to see scoring details.")
        
        # Show what hotspot names actually exist
        print("\n📋 Actual hotspot names in your data (first 20):")
        all_hotspot_names = set()
        for item in all_visual_items:
            for hotspot in item.get('hotspots', []):
                if hotspot.get('type', '').upper() != 'AUDIO':
                    all_hotspot_names.add(hotspot.get('name', 'N/A'))
        
        for name in sorted(all_hotspot_names)[:20]:
            print(f"      • {name}")
        if len(all_hotspot_names) > 20:
            print(f"      ... and {len(all_hotspot_names) - 20} more")
        
    else:
        print("\n✅ Vision mapping is working!")
        print("\nMatched images:")
        unique_images = set()
        for m in mappings:
            if m['file_id']:
                file_id = m['file_id']
                source_dir = visual_items_by_file.get(file_id, 'unknown')
                print(f"  • {file_id[:40]}...")
                print(f"    └─ From: {source_dir}")
                print(f"    └─ Hotspot: {m['hotspot'].get('text', 'N/A')}")
                print(f"    └─ Score: {m['relevance_score']:.2f}")
                unique_images.add(file_id)
        
        print(f"\n📊 Statistics:")
        print(f"   Unique images used: {len(unique_images)}")
        print(f"   Average score: {sum(m['relevance_score'] for m in mappings if m['file_id']) / mapped_count:.2f}")
    
    print()
    
    # Additional recommendations
    if mapped_count < len(test_steps):
        print("💡 To improve mapping rate:")
        print("   1. Lower threshold to 0.1 or 0.15")
        print("   2. Check if hotspot names match your steps")
        print("   3. Adjust scoring weights in vision_mapper.py")
        print()

if __name__ == "__main__":
    import sys
    
    # Allow custom data directory
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "./data"
    
    if not Path(data_dir).exists():
        print(f"❌ Directory not found: {data_dir}")
        print(f"\nUsage: python test_vision_mapping.py [data_directory]")
        print(f"Example: python test_vision_mapping.py ./data/company/images")
    else:
        test_vision_mapping()

