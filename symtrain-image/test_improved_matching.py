#!/usr/bin/env python3
"""
Test script to validate improved vision mapping with enhanced matching algorithms
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

    json_files = list(data_path.rglob("*.json"))
    print(f"\n📂 Scanning: {data_directory}")
    print(f"✅ Found {len(json_files)} JSON file(s)")

    all_visual_items = []
    image_dirs = {}

    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)

            visual_items = data.get('visualContentItems', [])

            if visual_items:
                sim_dir = str(json_file.parent)

                for item in visual_items:
                    file_id = item.get('fileId')
                    if file_id:
                        image_dirs[file_id] = sim_dir

                all_visual_items.extend(visual_items)

        except Exception as e:
            continue

    return all_visual_items, image_dirs

def test_enhanced_matching():
    """Test enhanced matching algorithms with various test cases."""

    print("\n" + "="*80)
    print("ENHANCED VISION MAPPING TEST")
    print("="*80)

    # Load ALL visual items
    all_visual_items, image_dirs = load_all_visual_items("./data")

    if not all_visual_items:
        print("\n❌ No visual content items found!")
        return

    total_hotspots = sum(len(item.get('hotspots', [])) for item in all_visual_items)
    non_audio = sum(
        1 for item in all_visual_items
        for hotspot in item.get('hotspots', [])
        if hotspot.get('type', '').upper() != 'AUDIO'
    )

    print(f"\n📊 Loaded Data:")
    print(f"   Visual items: {len(all_visual_items)}")
    print(f"   Total hotspots: {total_hotspots}")
    print(f"   Non-audio hotspots: {non_audio}")

    # Test cases with various scenarios
    test_cases = [
        {
            "name": "Payment Update Request",
            "request": "I need to update my payment method for my recent order",
            "steps": [
                "Navigate to Account Settings",
                "Click on Payment Methods",
                "Select Edit for your current payment method",
                "Enter your new credit card number",
                "Click Save to update"
            ]
        },
        {
            "name": "Insurance Claim Filing",
            "request": "I need to file an insurance claim for my car accident",
            "steps": [
                "Navigate to Claims section",
                "Click File New Claim button",
                "Enter policy number",
                "Provide accident details",
                "Submit the claim form"
            ]
        },
        {
            "name": "Order Status Check",
            "request": "I want to check the status of my order",
            "steps": [
                "Go to Orders page",
                "Find your recent order",
                "Click View Details",
                "Check tracking information"
            ]
        },
        {
            "name": "Generic UI Navigation",
            "request": "I need help navigating the website",
            "steps": [
                "Click the menu button",
                "Select your desired option",
                "Fill in required fields",
                "Submit the form"
            ]
        }
    ]

    # Create mapper
    mapper = VisionMapper()

    # Test each case
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"TEST CASE {i}: {test_case['name']}")
        print(f"{'='*80}")
        print(f"\n📝 Request: {test_case['request']}")
        print(f"\n📋 Steps ({len(test_case['steps'])}):")
        for j, step in enumerate(test_case['steps'], 1):
            print(f"   {j}. {step}")

        # Test with different thresholds
        thresholds = [0.15, 0.25, 0.35]

        print(f"\n🧪 Testing with multiple thresholds:")

        best_threshold = None
        best_rate = 0

        for threshold in thresholds:
            mappings = mapper.map_steps_to_images(
                test_case['steps'],
                all_visual_items,
                threshold=threshold,
                request_context=test_case['request'],
                debug=False
            )

            mapped_count = sum(1 for m in mappings if m['file_id'])
            mapping_rate = (mapped_count / len(test_case['steps']) * 100) if test_case['steps'] else 0

            print(f"   Threshold {threshold:.2f}: {mapped_count}/{len(test_case['steps'])} steps ({mapping_rate:.1f}%)")

            if mapping_rate > best_rate:
                best_rate = mapping_rate
                best_threshold = threshold

        print(f"\n✅ Best threshold: {best_threshold:.2f} with {best_rate:.1f}% mapping rate")

        # Show detailed results for best threshold
        print(f"\n📊 Detailed Results (threshold={best_threshold}):")

        mappings = mapper.map_steps_to_images(
            test_case['steps'],
            all_visual_items,
            threshold=best_threshold,
            request_context=test_case['request'],
            debug=False
        )

        for mapping in mappings:
            step_num = mapping['step_index'] + 1
            if mapping['file_id']:
                print(f"\n   Step {step_num}: ✅ MATCHED")
                print(f"      Hotspot: {mapping['hotspot'].get('text', 'N/A')}")
                print(f"      Type: {mapping['hotspot'].get('type', 'N/A')}")
                print(f"      Score: {mapping['relevance_score']:.2f}")
            else:
                print(f"\n   Step {step_num}: ❌ NO MATCH")

    # Overall summary
    print(f"\n{'='*80}")
    print("SUMMARY OF IMPROVEMENTS")
    print(f"{'='*80}")
    print("\n✨ Enhanced Features:")
    print("   • Fuzzy string matching for partial word matches")
    print("   • Expanded keyword synonyms (payment→billing, order→booking, etc.)")
    print("   • Context-aware semantic matching")
    print("   • Improved scoring algorithm with higher max score (2.0)")
    print("   • Configurable thresholds and diversity penalties")
    print("   • Better cross-word similarity detection")

    print("\n💡 Recommendations:")
    print("   • Use threshold 0.15-0.25 for balanced results")
    print("   • Enable request_context for better semantic matching")
    print("   • Adjust diversity_penalty (default 0.15) to control image reuse")
    print("   • Set max_image_reuse (default 3) to ensure variety")

    print()

if __name__ == "__main__":
    import sys

    # Allow custom data directory
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
        if not Path(data_dir).exists():
            print(f"❌ Directory not found: {data_dir}")
            sys.exit(1)

    test_enhanced_matching()
