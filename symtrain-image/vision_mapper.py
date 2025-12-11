"""
Bonus Task: Vision-based Step-to-Image Mapping
Updated to support SymTrain JSON format with enhanced matching algorithms
"""

import json
import re
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from difflib import SequenceMatcher

class VisionMapper:
    """
    Maps generated steps to relevant UI images and highlights hotspots.
    Supports both standard format and SymTrain format.
    """
    
    def __init__(self):
        # Common UI action keywords with expanded synonyms
        self.action_keywords = {
            'click': ['click', 'press', 'tap', 'select', 'choose', 'hit', 'push'],
            'enter': ['enter', 'type', 'input', 'fill', 'write', 'provide', 'insert', 'add'],
            'navigate': ['navigate', 'go to', 'open', 'access', 'visit', 'move to', 'switch to'],
            'update': ['update', 'change', 'modify', 'edit', 'alter', 'revise', 'adjust'],
            'view': ['view', 'see', 'check', 'look at', 'review', 'examine', 'inspect'],
            'submit': ['submit', 'save', 'confirm', 'apply', 'complete', 'finish'],
            'search': ['search', 'find', 'lookup', 'locate', 'seek']
        }

        # Common UI element types
        self.element_types = [
            'button', 'link', 'menu', 'dropdown', 'field', 'input',
            'checkbox', 'radio', 'tab', 'icon', 'text', 'form', 'box'
        ]

        # Common action-element synonyms
        self.element_synonyms = {
            'payment': ['payment', 'pay', 'billing', 'card', 'credit', 'transaction'],
            'order': ['order', 'purchase', 'transaction', 'booking', 'reservation'],
            'account': ['account', 'profile', 'settings', 'preferences'],
            'address': ['address', 'location', 'shipping', 'delivery'],
            'insurance': ['insurance', 'policy', 'claim', 'coverage'],
            'contact': ['contact', 'phone', 'email', 'call', 'reach']
        }
    
    def normalize_hotspot(self, hotspot: Dict[str, Any], image_size: Tuple[int, int] = (1200, 800)) -> Dict[str, Any]:
        """
        Normalize SymTrain hotspot format to standard format.
        
        Args:
            hotspot: Hotspot data (SymTrain or standard format)
            image_size: Image dimensions for denormalizing coordinates
            
        Returns:
            Normalized hotspot dict
        """
        # If already in standard format, return as-is
        if 'text' in hotspot and 'coordinates' in hotspot:
            return hotspot
        
        # Convert SymTrain format
        normalized = {}
        
        # Get text from 'name' field
        normalized['text'] = hotspot.get('name', '')
        
        # Get type (convert to lowercase)
        hotspot_type = hotspot.get('type', '').lower()
        # Map SymTrain types to standard
        type_mapping = {
            'button': 'button',
            'text_field': 'input_field',
            'audio': 'audio',
            'highlight': 'highlight'
        }
        normalized['type'] = type_mapping.get(hotspot_type, hotspot_type)
        
        # Get coordinates from settings
        settings = hotspot.get('settings', {})
        if isinstance(settings, dict):
            # Denormalize coordinates (SymTrain uses 0-1 range)
            pos_x = settings.get('positionX', 0)
            pos_y = settings.get('positionY', 0)
            width = settings.get('width', 0.1)
            height = settings.get('height', 0.05)
            
            # Convert to pixels
            img_width, img_height = image_size
            normalized['coordinates'] = {
                'x': int(pos_x * img_width),
                'y': int(pos_y * img_height),
                'width': int(width * img_width),
                'height': int(height * img_height)
            }
        else:
            # Default coordinates if settings is not a dict
            normalized['coordinates'] = {
                'x': 0,
                'y': 0,
                'width': 100,
                'height': 40
            }
        
        return normalized

    def fuzzy_match_score(self, str1: str, str2: str) -> float:
        """Calculate fuzzy string similarity using SequenceMatcher.

        Args:
            str1: First string
            str2: Second string

        Returns:
            Similarity score between 0 and 1
        """
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

    def expand_keywords_with_synonyms(self, keywords: List[str]) -> List[str]:
        """Expand keywords with known synonyms.

        Args:
            keywords: Original keywords

        Returns:
            Expanded list including synonyms
        """
        expanded = set(keywords)

        for keyword in keywords:
            keyword_lower = keyword.lower()
            # Check if keyword matches any synonym category
            for category, synonyms in self.element_synonyms.items():
                if keyword_lower in synonyms:
                    expanded.update(synonyms)
                    break

        return list(expanded)

    def extract_keywords_from_step(self, step: str) -> Dict[str, List[str]]:
        """Extract relevant keywords from a step description."""
        step_lower = step.lower()
        
        keywords = {
            'actions': [],
            'elements': [],
            'targets': []
        }
        
        # Extract actions
        for action_type, variations in self.action_keywords.items():
            for variation in variations:
                if variation in step_lower:
                    keywords['actions'].append(action_type)
                    break
        
        # Extract element types
        for element in self.element_types:
            if element in step_lower:
                keywords['elements'].append(element)
        
        # Extract quoted text or capitalized terms
        quoted = re.findall(r'["\']([^"\']+)["\']', step)
        keywords['targets'].extend(quoted)
        
        # Look for capitalized words
        words = step.split()
        for i, word in enumerate(words):
            if i > 0 and len(word) > 3 and word[0].isupper():
                clean_word = re.sub(r'[^\w\s]', '', word)
                if clean_word and clean_word not in ['Click', 'Select', 'Enter', 'Navigate', 'Open']:
                    keywords['targets'].append(clean_word)
        
        return keywords
    
    def calculate_relevance_score(self, step: str, hotspot: Dict[str, Any], request_context: str = "") -> float:
        """Calculate how relevant a hotspot is to a step with enhanced matching.

        Args:
            step: The instruction step
            hotspot: The UI hotspot
            request_context: The original user request for domain matching
        """
        # Normalize hotspot first
        norm_hotspot = self.normalize_hotspot(hotspot)

        step_keywords = self.extract_keywords_from_step(step)
        hotspot_text = norm_hotspot.get('text', '').lower()
        hotspot_type = norm_hotspot.get('type', '').lower()

        # Generic terms that shouldn't score high
        generic_terms = {'click', 'button', 'text', 'field', 'input', 'next', 'back',
                        'submit', 'ok', 'yes', 'no', 'continue', 'cancel', 'close',
                        'audio', 'for', 'the'}

        # Stop words to ignore in matching
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
                     'for', 'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were',
                     'my', 'your', 'can', 'you', 'help', 'me', 'that', 'this'}

        score = 0.0

        # PENALTY: Penalize generic hotspot names (but not too harshly)
        if hotspot_text.strip() in generic_terms:
            score -= 0.15  # Reduced penalty from 0.2

        # ENHANCED SEMANTIC DOMAIN MATCHING: Check if hotspot relates to request domain
        if request_context:
            request_lower = request_context.lower()
            # Extract domain keywords from request (important nouns/verbs)
            domain_keywords = []
            for word in request_lower.split():
                if len(word) > 4 and word not in stop_words:
                    domain_keywords.append(word)

            # Expand domain keywords with synonyms
            expanded_keywords = self.expand_keywords_with_synonyms(domain_keywords)

            # Check if hotspot text contains ANY domain keywords or synonyms
            domain_match_count = 0
            fuzzy_match_scores = []

            for keyword in expanded_keywords:
                # Exact substring match
                if keyword in hotspot_text:
                    domain_match_count += 1
                else:
                    # Fuzzy matching for partial matches
                    fuzzy_score = self.fuzzy_match_score(keyword, hotspot_text)
                    if fuzzy_score > 0.7:  # High similarity threshold
                        fuzzy_match_scores.append(fuzzy_score)

            if domain_match_count > 0:
                # Big bonus for domain relevance! This helps filter out irrelevant UIs
                score += domain_match_count * 0.5  # Increased from 0.4

            # Add fuzzy match bonuses
            if fuzzy_match_scores:
                score += max(fuzzy_match_scores) * 0.3

        # ENHANCED TARGET MATCHING: Check if hotspot text matches any targets (HIGH PRIORITY)
        for target in step_keywords['targets']:
            target_lower = target.lower()
            # Exact match = very high score
            if target_lower == hotspot_text.strip():
                score += 1.2  # Increased from 1.0
            # Substring match = high score
            elif target_lower in hotspot_text or hotspot_text in target_lower:
                score += 0.7  # Increased from 0.5
            else:
                # Fuzzy match for close matches
                fuzzy_score = self.fuzzy_match_score(target_lower, hotspot_text)
                if fuzzy_score > 0.75:
                    score += fuzzy_score * 0.6  # New: fuzzy matching bonus

        # ENHANCED TYPE MATCHING: Check if hotspot type matches step actions (MEDIUM PRIORITY)
        if hotspot_type:
            if 'button' in hotspot_type and 'click' in step_keywords['actions']:
                score += 0.35  # Increased from 0.3
            if 'input' in hotspot_type or 'field' in hotspot_type or 'text_field' in hotspot_type:
                if 'enter' in step_keywords['actions']:
                    score += 0.35  # Increased from 0.3
            if 'menu' in hotspot_type and 'navigate' in step_keywords['actions']:
                score += 0.35  # Increased from 0.3

        # ENHANCED PARTIAL TEXT MATCHING: with fuzzy matching
        step_words = set(step.lower().split()) - stop_words
        hotspot_words = set(hotspot_text.split()) - stop_words
        common_words = step_words & hotspot_words

        if common_words:
            # Filter out generic terms and short words
            meaningful_common = [w for w in common_words
                               if len(w) > 3 and w not in generic_terms]
            if meaningful_common:
                # Give bonus based on word importance
                score += len(meaningful_common) * 0.15  # Increased from 0.1

        # NEW: Cross-word fuzzy matching for compound terms
        if not common_words and len(hotspot_words) > 0 and len(step_words) > 0:
            max_fuzzy = 0.0
            for step_word in step_words:
                if len(step_word) > 4:  # Only check meaningful words
                    for hotspot_word in hotspot_words:
                        if len(hotspot_word) > 4:
                            fuzzy_score = self.fuzzy_match_score(step_word, hotspot_word)
                            max_fuzzy = max(max_fuzzy, fuzzy_score)

            if max_fuzzy > 0.8:  # Very similar words
                score += max_fuzzy * 0.2

        return max(0.0, min(score, 2.0))  # Allow scores up to 2.0 for very strong matches
    
    def map_steps_to_images(
        self,
        steps: List[str],
        visual_items: List[Dict[str, Any]],
        threshold: float = 0.15,  # Lowered to 0.15 for better matching with enhanced scoring
        debug: bool = False,  # Enable debug output
        request_context: str = "",  # Original user request for semantic matching
        max_image_reuse: int = 3,  # Maximum times same image can be used
        diversity_penalty: float = 0.15  # Penalty per reuse (0.15 recommended)
    ) -> List[Dict[str, Any]]:
        """Map each step to the most relevant image and hotspot with enhanced matching.

        Args:
            steps: List of instruction steps
            visual_items: List of visual content items with hotspots
            threshold: Minimum relevance score to consider a match (0-2 scale now)
            debug: Enable debug output
            request_context: Original user request for semantic domain matching
            max_image_reuse: Maximum times same image can be reused
            diversity_penalty: Penalty multiplier per image reuse

        Returns:
            List of step-to-image mappings with relevance scores
        """
        mappings = []
        used_images = {}  # Track how many times each image is used
        
        if debug:
            print(f"\n🔍 DEBUG: Mapping {len(steps)} steps to {len(visual_items)} visual items")
            print(f"   Threshold: {threshold}")
            if request_context:
                print(f"   Request context: {request_context[:60]}...")
        
        for step_idx, step in enumerate(steps):
            if debug:
                print(f"\n--- Step {step_idx + 1}: {step[:50]}...")
            
            best_match = {
                'step_index': step_idx,
                'step': step,
                'file_id': None,
                'hotspot': None,
                'relevance_score': 0.0,
                'sequence_number': None
            }
            
            candidates = []  # Store all candidates above threshold
            
            for visual_item in visual_items:
                file_id = visual_item.get('fileId')
                hotspots = visual_item.get('hotspots', [])
                
                for hotspot in hotspots:
                    # Skip AUDIO type hotspots
                    if hotspot.get('type', '').upper() == 'AUDIO':
                        continue
                    
                    score = self.calculate_relevance_score(step, hotspot, request_context)
                    
                    if debug and score > 0:
                        hotspot_name = hotspot.get('name', 'N/A')
                        print(f"    {file_id[:20]}... | {hotspot_name[:30]:30s} | Score: {score:.2f}")
                    
                    if score >= threshold:
                        # Apply diversity penalty: penalize overused images
                        reuse_count = used_images.get(file_id, 0)
                        penalty = reuse_count * diversity_penalty
                        adjusted_score = score - penalty
                        
                        candidates.append({
                            'file_id': file_id,
                            'hotspot': self.normalize_hotspot(hotspot),
                            'score': score,
                            'adjusted_score': adjusted_score
                        })
            
            # Select best candidate based on adjusted score (with diversity)
            if candidates:
                best_candidate = max(candidates, key=lambda x: x['adjusted_score'])

                # Only use if not exceeding max reuse limit
                if used_images.get(best_candidate['file_id'], 0) < max_image_reuse:
                    best_match['file_id'] = best_candidate['file_id']
                    best_match['hotspot'] = best_candidate['hotspot']
                    best_match['relevance_score'] = best_candidate['score']

                    # Track image usage for diversity
                    used_images[best_candidate['file_id']] = used_images.get(best_candidate['file_id'], 0) + 1

                    if debug:
                        print(f"    ✅ BEST: {best_candidate['file_id'][:30]}... (score: {best_candidate['score']:.2f}, adjusted: {best_candidate['adjusted_score']:.2f})")
                else:
                    # Try second best if first exceeds limit
                    sorted_candidates = sorted(candidates, key=lambda x: x['adjusted_score'], reverse=True)
                    for candidate in sorted_candidates[1:]:
                        if used_images.get(candidate['file_id'], 0) < max_image_reuse:
                            best_match['file_id'] = candidate['file_id']
                            best_match['hotspot'] = candidate['hotspot']
                            best_match['relevance_score'] = candidate['score']
                            used_images[candidate['file_id']] = used_images.get(candidate['file_id'], 0) + 1
                            if debug:
                                print(f"    ✅ ALTERNATIVE: {candidate['file_id'][:30]}... (score: {candidate['score']:.2f})")
                            break
                    else:
                        if debug:
                            print(f"    ⚠️  Best match exceeds reuse limit")
            else:
                if debug:
                    print(f"    ❌ NO MATCH (all scores below {threshold})")
            
            mappings.append(best_match)
        
        return mappings
    
    def highlight_hotspot_on_image(
        self,
        image_path: str,
        hotspot: Dict[str, Any],
        output_path: str = None
    ) -> Image.Image:
        """Draw a highlight box around the hotspot on the image."""
        # Load image
        img = Image.open(image_path).convert('RGBA')
        
        # Create overlay
        overlay = Image.new('RGBA', img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Normalize hotspot
        norm_hotspot = self.normalize_hotspot(hotspot, img.size)
        
        # Get coordinates
        coords = norm_hotspot.get('coordinates', {})
        x = coords.get('x', 0)
        y = coords.get('y', 0)
        width = coords.get('width', 100)
        height = coords.get('height', 40)
        
        # Draw highlight box
        box = [x - 5, y - 5, x + width + 5, y + height + 5]
        draw.rectangle(box, outline=(255, 0, 0, 255), width=3)
        draw.rectangle(box, fill=(255, 255, 0, 80))
        
        # Add label
        hotspot_text = norm_hotspot.get('text', '')
        if hotspot_text:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
            except:
                font = ImageFont.load_default()
            
            text_bbox = draw.textbbox((x, y - 25), hotspot_text, font=font)
            draw.rectangle(text_bbox, fill=(255, 0, 0, 200))
            draw.text((x, y - 25), hotspot_text, fill=(255, 255, 255, 255), font=font)
        
        # Composite
        highlighted = Image.alpha_composite(img, overlay)
        
        if output_path:
            highlighted.convert('RGB').save(output_path)
        
        return highlighted
    
    def process_simulation_with_vision(
        self,
        steps: List[str],
        visual_items: List[Dict[str, Any]],
        image_directory: str = None,
        visual_items_source_path: str = None,  # Deprecated - use image_dirs instead
        image_dirs: Dict[str, str] = None,  # NEW: Map of fileId -> directory path
        request_context: str = ""  # Original user request for semantic matching
    ) -> Dict[str, Any]:
        """Complete vision mapping pipeline."""
        mappings = self.map_steps_to_images(steps, visual_items, request_context=request_context)
        
        result = {
            'total_steps': len(steps),
            'mapped_steps': sum(1 for m in mappings if m['file_id']),
            'mappings': []
        }
        
        for mapping in mappings:
            if mapping['file_id']:
                file_id = mapping['file_id']
                
                # Determine which directory to look in for this specific image
                if image_dirs and file_id in image_dirs:
                    # Use the specific directory for this image
                    base_dir = Path(image_dirs[file_id])
                elif visual_items_source_path:
                    # Fallback to source path (old behavior)
                    base_dir = Path(visual_items_source_path).parent
                elif image_directory:
                    # Fallback to global image directory
                    base_dir = Path(image_directory)
                else:
                    # Last resort - current directory
                    base_dir = Path('.')
                
                # Try all common image extensions (handles mixed format directories)
                possible_paths = [
                    base_dir / file_id,  # Try as-is first (might already have extension)
                    base_dir / f"{file_id}.JPG",   # Uppercase JPG
                    base_dir / f"{file_id}.jpg",   # Lowercase jpg
                    base_dir / f"{file_id}.PNG",   # Uppercase PNG
                    base_dir / f"{file_id}.png",   # Lowercase png
                    base_dir / f"{file_id}.JPEG",  # Uppercase JPEG
                    base_dir / f"{file_id}.jpeg",  # Lowercase jpeg
                ]
                
                image_path = None
                for path in possible_paths:
                    if path.exists():
                        image_path = path
                        break
                
                mapping_result = {
                    'step_index': mapping['step_index'],
                    'step': mapping['step'],
                    'file_id': file_id,
                    'relevance_score': mapping['relevance_score'],
                    'hotspot_text': mapping['hotspot'].get('text', 'N/A'),
                    'hotspot_type': mapping['hotspot'].get('type', 'N/A'),
                    'image_found': image_path is not None,
                    'highlighted_image': None
                }
                
                if image_path:
                    try:
                        highlighted = self.highlight_hotspot_on_image(
                            str(image_path),
                            mapping['hotspot']
                        )
                        mapping_result['highlighted_image'] = highlighted
                    except Exception as e:
                        mapping_result['error'] = str(e)
                
                result['mappings'].append(mapping_result)
            else:
                result['mappings'].append({
                    'step_index': mapping['step_index'],
                    'step': mapping['step'],
                    'file_id': None,
                    'relevance_score': 0.0,
                    'hotspot_text': 'No match found',
                    'image_found': False
                })
        
        return result


def create_mapping_report(mapping_result: Dict[str, Any]) -> str:
    """Create a text report of the vision mapping results."""
    report = []
    report.append("=" * 70)
    report.append("VISION-BASED STEP-TO-IMAGE MAPPING REPORT")
    report.append("=" * 70)
    report.append(f"Total Steps: {mapping_result['total_steps']}")
    report.append(f"Successfully Mapped: {mapping_result['mapped_steps']}")
    report.append(f"Mapping Rate: {mapping_result['mapped_steps']/mapping_result['total_steps']*100:.1f}%")
    report.append("=" * 70)
    report.append("")
    
    for mapping in mapping_result['mappings']:
        report.append(f"Step {mapping['step_index'] + 1}: {mapping['step']}")
        report.append(f"  Image: {mapping.get('file_id', 'None')}")
        report.append(f"  Hotspot: {mapping.get('hotspot_text', 'N/A')}")
        report.append(f"  Type: {mapping.get('hotspot_type', 'N/A')}")
        report.append(f"  Relevance: {mapping.get('relevance_score', 0.0):.2f}")
        report.append(f"  Image Found: {mapping.get('image_found', False)}")
        report.append("")
    
    return "\n".join(report)
