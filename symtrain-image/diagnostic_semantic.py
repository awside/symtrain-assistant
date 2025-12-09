#!/usr/bin/env python3
"""
Quick diagnostic: Check if your training data has domain-specific content
"""

import json
from pathlib import Path
from collections import Counter

def analyze_hotspots_for_request(data_dir="./data", test_request="I want to update my cruise booking reservation"):
    """Check if training data hotspots match the request domain."""
    
    print("\n" + "="*80)
    print("SEMANTIC MATCHING DIAGNOSTIC")
    print("="*80)
    
    print(f"\n📝 Test Request: {test_request}")
    
    # Extract domain keywords
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 
                  'for', 'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were',
                  'my', 'your', 'can', 'you', 'help', 'me', 'that', 'this', 'want'}
    
    keywords = [word.lower() for word in test_request.split() if len(word) > 4 and word.lower() not in stop_words]
    
    print(f"🎯 Domain Keywords: {', '.join(keywords)}")
    print()
    
    # Load all JSON files
    data_path = Path(data_dir)
    if not data_path.exists():
        print(f"❌ Directory not found: {data_dir}")
        return
    
    json_files = list(data_path.rglob("*.json"))
    print(f"📂 Found {len(json_files)} JSON file(s)")
    
    # Collect all hotspot names
    all_hotspot_names = []
    generic_count = 0
    specific_count = 0
    
    generic_terms = {'click', 'button', 'text', 'field', 'input', 'next', 'back',
                     'submit', 'ok', 'yes', 'no', 'continue', 'cancel', 'close', 'audio'}
    
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            visual_items = data.get('visualContentItems', [])
            for item in visual_items:
                for hotspot in item.get('hotspots', []):
                    name = hotspot.get('name', '').strip()
                    if name:
                        all_hotspot_names.append(name)
                        if name.lower() in generic_terms:
                            generic_count += 1
                        else:
                            specific_count += 1
        except Exception as e:
            continue
    
    print(f"\n📊 Hotspot Analysis:")
    print(f"   Total hotspots: {len(all_hotspot_names)}")
    print(f"   Generic (Click, Button, etc.): {generic_count} ({generic_count/len(all_hotspot_names)*100:.1f}%)")
    print(f"   Specific/descriptive: {specific_count} ({specific_count/len(all_hotspot_names)*100:.1f}%)")
    
    # Show most common hotspot names
    name_counts = Counter(all_hotspot_names)
    print(f"\n📋 Top 20 Most Common Hotspot Names:")
    for name, count in name_counts.most_common(20):
        print(f"   {count:4d}x  {name}")
    
    # Check for domain matches
    print(f"\n🔍 Checking for Domain Keyword Matches:")
    matches_found = {}
    
    for keyword in keywords:
        matches = []
        for name in set(all_hotspot_names):
            if keyword in name.lower():
                matches.append(name)
        
        if matches:
            matches_found[keyword] = matches
            print(f"\n   ✅ '{keyword}' found in {len(matches)} hotspot(s):")
            for match in matches[:5]:  # Show first 5
                print(f"      • {match}")
            if len(matches) > 5:
                print(f"      ... and {len(matches)-5} more")
        else:
            print(f"\n   ❌ '{keyword}' - NOT FOUND in any hotspots")
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY:")
    print(f"{'='*80}")
    
    if matches_found:
        print(f"\n✅ Semantic matching WILL help!")
        print(f"   Found domain keywords in hotspots: {len(matches_found)}/{len(keywords)}")
        print(f"   These hotspots will score higher for your request.")
    else:
        print(f"\n❌ Semantic matching CANNOT help!")
        print(f"   NO domain keywords found in any hotspots ({0}/{len(keywords)} matches)")
        print(f"\n   Your training data contains:")
        if generic_count > specific_count:
            print(f"   • Mostly generic hotspots (Click, Button, Text)")
            print(f"   • No domain-specific content related to: {', '.join(keywords)}")
        else:
            print(f"   • Specific hotspots, but NOT related to your request domain")
        
        print(f"\n   For request '{test_request}':")
        print(f"   → Vision mapping will show GENERIC matches only")
        print(f"   → Images may not be contextually relevant")
        print(f"\n   To improve:")
        print(f"   1. Add training data with {', '.join(keywords)}-related content")
        print(f"   2. Or accept that generic matches are the best available")
        print(f"   3. Or skip vision mapping for unrelated requests")
    
    print()

if __name__ == "__main__":
    import sys
    
    # Default test request
    test_request = "I want to update my cruise booking reservation"
    
    # Allow custom request
    if len(sys.argv) > 1:
        test_request = " ".join(sys.argv[1:])
    
    analyze_hotspots_for_request(test_request=test_request)
    
    print("💡 Try different requests:")
    print("   python diagnostic_semantic.py I need to file an insurance claim")
    print("   python diagnostic_semantic.py Update my shipping address")
    print("   python diagnostic_semantic.py Change payment method")
    print()
