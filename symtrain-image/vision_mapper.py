"""
Bonus Task: Vision-based Step-to-Image Mapping
Updated to support SymTrain JSON format
"""

import json
import re
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

class VisionMapper:
    """
    Maps generated steps to relevant UI images and highlights hotspots.
    Supports both standard format and SymTrain format.
    """
    
    def __init__(self):
        # Common UI action keywords
        self.action_keywords = {
            'click': ['click', 'press', 'tap', 'select', 'choose'],
            'enter': ['enter', 'type', 'input', 'fill', 'write'],
            'navigate': ['navigate', 'go to', 'open', 'access', 'visit'],
            'update': ['update', 'change', 'modify', 'edit', 'alter'],
            'view': ['view', 'see', 'check', 'look at', 'review'],
            'submit': ['submit', 'save', 'confirm', 'apply'],
            'search': ['search', 'find', 'lookup', 'locate']
        }
        
        # Common UI element types
        self.element_types = [
            'button', 'link', 'menu', 'dropdown', 'field', 'input',
            'checkbox', 'radio', 'tab', 'icon', 'text'
        ]
    
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
        """Calculate how relevant a hotspot is to a step.
        
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
                     'my', 'your', 'can', 'you', 'help', 'me', 'with', 'that', 'this'}
        
        score = 0.0
        
        # PENALTY: Penalize generic hotspot names (but not too harshly)
        if hotspot_text.strip() in generic_terms:
            score -= 0.2  # Reduced penalty (was -0.5)
        
        # SEMANTIC DOMAIN MATCHING: Check if hotspot relates to request domain
        if request_context:
            request_lower = request_context.lower()
            # Extract domain keywords from request (important nouns/verbs)
            domain_keywords = []
            for word in request_lower.split():
                if len(word) > 4 and word not in stop_words:
                    domain_keywords.append(word)
            
            # Check if hotspot text contains ANY domain keywords
            domain_match_count = 0
            for keyword in domain_keywords:
                if keyword in hotspot_text:
                    domain_match_count += 1
            
            if domain_match_count > 0:
                # Big bonus for domain relevance! This helps filter out irrelevant UIs
                score += domain_match_count * 0.4
        
        # Check if hotspot text matches any targets (HIGH PRIORITY)
        for target in step_keywords['targets']:
            target_lower = target.lower()
            # Exact match = high score
            if target_lower == hotspot_text.strip():
                score += 1.0
            # Substring match = medium score
            elif target_lower in hotspot_text or hotspot_text in target_lower:
                score += 0.5  # Increased from 0.6
        
        # Check if hotspot type matches step actions (MEDIUM PRIORITY)
        if hotspot_type:
            if 'button' in hotspot_type and 'click' in step_keywords['actions']:
                score += 0.3  # Increased from 0.2
            if 'input' in hotspot_type or 'field' in hotspot_type or 'text_field' in hotspot_type:
                if 'enter' in step_keywords['actions']:
                    score += 0.3  # Increased from 0.2
            if 'menu' in hotspot_type and 'navigate' in step_keywords['actions']:
                score += 0.3  # Increased from 0.2
        
        # Partial text matching (LOW PRIORITY) - only meaningful words
        step_words = set(step.lower().split()) - stop_words
        hotspot_words = set(hotspot_text.split()) - stop_words
        common_words = step_words & hotspot_words
        
        if common_words:
            # Filter out generic terms and short words
            meaningful_common = [w for w in common_words 
                               if len(w) > 3 and w not in generic_terms]
            if meaningful_common:
                # Give small bonus
                score += len(meaningful_common) * 0.1  # Increased from 0.05
        
        return max(0.0, min(score, 1.0))  # Clamp between 0 and 1
    
    def map_steps_to_images(
        self,
        steps: List[str],
        visual_items: List[Dict[str, Any]],
        threshold: float = 0.2,  # Lowered back to 0.2 for more matches
        debug: bool = False,  # Enable debug output
        request_context: str = ""  # Original user request for semantic matching
    ) -> List[Dict[str, Any]]:
        """Map each step to the most relevant image and hotspot."""
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
                        # Apply diversity bonus: penalize overused images
                        diversity_penalty = used_images.get(file_id, 0) * 0.1
                        adjusted_score = score - diversity_penalty
                        
                        candidates.append({
                            'file_id': file_id,
                            'hotspot': self.normalize_hotspot(hotspot),
                            'score': score,
                            'adjusted_score': adjusted_score
                        })
            
            # Select best candidate based on adjusted score (with diversity)
            if candidates:
                best_candidate = max(candidates, key=lambda x: x['adjusted_score'])
                best_match['file_id'] = best_candidate['file_id']
                best_match['hotspot'] = best_candidate['hotspot']
                best_match['relevance_score'] = best_candidate['score']
                
                # Track image usage for diversity
                used_images[best_candidate['file_id']] = used_images.get(best_candidate['file_id'], 0) + 1
                
                if debug:
                    print(f"    ✅ BEST: {best_candidate['file_id'][:30]}... (score: {best_candidate['score']:.2f})")
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
