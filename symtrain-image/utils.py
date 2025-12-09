"""
Utility functions for SymTrain Simulation Intelligence Assistant
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any
import openai

# Task 1: Load the dataset
def load_dataset(json_file_path: str) -> Dict[str, Any]:
    """
    Load a single JSON simulation file and extract audioContentItems.
    
    Args:
        json_file_path: Path to the JSON file
        
    Returns:
        Dictionary containing the simulation data
    """
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data

# Task 2: Merge dialogue text
def merge_dialogue(audio_content_items: List[Dict]) -> str:
    """
    Merge transcript lines into one continuous string while preserving speaker roles.
    
    Args:
        audio_content_items: List of audio content items from JSON
        
    Returns:
        Merged dialogue string
    """
    merged = []
    
    # Sort by sequence number to ensure correct order
    sorted_items = sorted(audio_content_items, key=lambda x: x.get('sequenceNumber', 0))
    
    for item in sorted_items:
        actor = item.get('actor', 'Unknown')
        transcript = item.get('fileTranscript', '').strip()
        
        if transcript:
            merged.append(f"{actor}: {transcript}")
    
    return " ".join(merged)

# Task 3: Extract call reasons and steps
def extract_call_reason_and_steps(dialogue: str, api_key: str = None) -> Dict[str, Any]:
    """
    Extract the call reason and steps from the dialogue using GPT.
    
    Args:
        dialogue: The merged dialogue string
        api_key: OpenAI API key
        
    Returns:
        Dictionary with 'reason' and 'steps'
    """
    if not api_key:
        # Fallback to simple extraction
        return {
            "reason": "Unable to determine without API key",
            "steps": ["Step extraction requires OpenAI API key"]
        }
    
    client = openai.OpenAI(api_key=api_key)
    
    prompt = f"""Analyze the following customer service dialogue and extract:
1. The reason for the customer's call (what they need help with)
2. The steps the agent provided to resolve the issue

Dialogue:
{dialogue}

Respond in JSON format:
{{
    "reason": "brief description of why customer is calling",
    "steps": ["step 1", "step 2", ...]
}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert at analyzing customer service conversations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
    
    except Exception as e:
        return {
            "reason": f"Error: {str(e)}",
            "steps": []
        }

# Task 4: Categorize simulations
def categorize_simulation(dialogue: str, reason: str, api_key: str = None) -> str:
    """
    Categorize the simulation based on dialogue and reason.
    
    Args:
        dialogue: The merged dialogue
        reason: The extracted reason
        api_key: OpenAI API key
        
    Returns:
        Category string
    """
    if not api_key:
        return "Uncategorized"
    
    client = openai.OpenAI(api_key=api_key)
    
    prompt = f"""Categorize the following customer service interaction into ONE of these categories:
- Payment Update
- Insurance Claim
- Order Status
- Account Management
- Technical Support
- Booking/Reservation
- Returns/Refunds
- General Inquiry

Reason: {reason}

Respond with ONLY the category name, nothing else."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert at categorizing customer service requests."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        category = response.choices[0].message.content.strip()
        return category
    
    except Exception as e:
        return "Uncategorized"

def load_all_simulations(data_dir: str) -> List[Dict[str, Any]]:
    """
    Load all simulation files from the data directory and process them.
    
    Args:
        data_dir: Path to the directory containing simulation JSON files
        
    Returns:
        List of processed simulations with dialogue, reason, steps, and category
    """
    simulations = []
    data_path = Path(data_dir)
    
    # Find all JSON files recursively
    json_files = list(data_path.rglob("*.json"))
    
    for json_file in json_files:
        try:
            # Load the dataset
            data = load_dataset(str(json_file))
            
            # Extract audio content items
            audio_items = data.get('audioContentItems', [])
            
            if not audio_items:
                continue
            
            # Merge dialogue
            dialogue = merge_dialogue(audio_items)
            
            # Store simulation info
            simulation = {
                'file_path': str(json_file),
                'file_name': json_file.name,
                'company': json_file.parent.name,
                'dialogue': dialogue,
                'audio_items': audio_items,
                'visual_items': data.get('visualContentItems', [])
            }
            
            simulations.append(simulation)
        
        except Exception as e:
            print(f"Error loading {json_file}: {str(e)}")
            continue
    
    return simulations

def extract_reasons_and_categorize_all(simulations: List[Dict], api_key: str) -> List[Dict]:
    """
    Extract reasons, steps, and categories for all simulations.
    
    Args:
        simulations: List of simulation dictionaries
        api_key: OpenAI API key
        
    Returns:
        Updated list of simulations with reasons, steps, and categories
    """
    for sim in simulations:
        # Extract reason and steps
        extraction = extract_call_reason_and_steps(sim['dialogue'], api_key)
        sim['reason'] = extraction['reason']
        sim['steps'] = extraction['steps']
        
        # Categorize
        sim['category'] = categorize_simulation(
            sim['dialogue'], 
            sim['reason'], 
            api_key
        )
    
    return simulations

# Task 5: Generate steps using few-shot learning
def generate_steps_few_shot(
    user_request: str,
    simulations: List[Dict],
    api_key: str,
    n_examples: int = 3
) -> Dict[str, Any]:
    """
    Generate steps for a user request using few-shot learning with GPT.
    
    Args:
        user_request: The customer's request
        simulations: List of training simulations
        api_key: OpenAI API key
        n_examples: Number of few-shot examples to use
        
    Returns:
        Dictionary with category, reason, and steps
    """
    if not api_key:
        return {
            "category": "Error",
            "reason": "OpenAI API key required",
            "steps": []
        }
    
    client = openai.OpenAI(api_key=api_key)
    
    # First, determine the category of the user request
    category_prompt = f"""Categorize the following customer request into ONE category:
- Payment Update
- Insurance Claim
- Order Status
- Account Management
- Technical Support
- Booking/Reservation
- Returns/Refunds
- General Inquiry

Customer Request: {user_request}

Respond with ONLY the category name."""

    try:
        category_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert at categorizing customer requests."},
                {"role": "user", "content": category_prompt}
            ],
            temperature=0.1
        )
        
        predicted_category = category_response.choices[0].message.content.strip()
        
        # Get few-shot examples from the same category
        examples = []
        for sim in simulations:
            if sim.get('category') == predicted_category and 'reason' in sim and 'steps' in sim:
                examples.append({
                    'request': sim.get('dialogue', '')[:200] + "...",  # Truncate for context
                    'reason': sim['reason'],
                    'steps': sim['steps']
                })
                if len(examples) >= n_examples:
                    break
        
        # Build few-shot prompt
        few_shot_examples = ""
        for i, ex in enumerate(examples, 1):
            steps_str = json.dumps(ex['steps'])
            few_shot_examples += f"""
Example {i}:
Request: {ex['request']}
Output: {{"reason": "{ex['reason']}", "steps": {steps_str}}}
"""
        
        # Generate response for user request
        generation_prompt = f"""You are an expert customer service assistant. Based on the following examples from the '{predicted_category}' category, generate a response for the new customer request.

{few_shot_examples}

New Customer Request: {user_request}

Generate the reason and steps to help this customer. Respond ONLY with valid JSON in this exact format:
{{
    "reason": "brief description of what customer needs",
    "steps": ["step 1", "step 2", "step 3", ...]
}}"""

        generation_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert customer service assistant. Always respond with valid JSON only."},
                {"role": "user", "content": generation_prompt}
            ],
            temperature=0.3
        )
        
        #result = json.loads(generation_response.choices[0].message.content)
        #result['category'] = predicted_category

        # Get the response and clean it
        response_text = generation_response.choices[0].message.content
        
        # Remove markdown code blocks if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]
        
        # Strip whitespace
        response_text = response_text.strip()
        
        # Parse JSON
        result = json.loads(response_text)
        result['category'] = predicted_category

        return result
    
    except json.JSONDecodeError as e:
        return {
            "category": predicted_category if 'predicted_category' in locals() else "Unknown",
            "reason": "Error parsing response",
            "steps": ["Error: Could not parse GPT response as JSON"]
        }
    except Exception as e:
        return {
            "category": "Error",
            "reason": f"Error: {str(e)}",
            "steps": []
        }

def get_relevant_images(step: str, visual_items: List[Dict]) -> List[str]:
    """
    Bonus Task: Find relevant images for a given step.
    
    Args:
        step: The step description
        visual_items: List of visual content items
        
    Returns:
        List of relevant file IDs
    """
    try:
        from vision_mapper import VisionMapper
        
        mapper = VisionMapper()
        mappings = mapper.map_steps_to_images([step], visual_items, threshold=0.2)
        
        if mappings and mappings[0]['file_id']:
            return [mappings[0]['file_id']]
        return []
    except Exception as e:
        # Fallback to simple keyword matching
        relevant_images = []
        step_lower = step.lower()
        
        for item in visual_items:
            hotspots = item.get('hotspots', [])
            for hotspot in hotspots:
                hotspot_text = hotspot.get('text', '').lower()
                if any(keyword in step_lower and keyword in hotspot_text 
                       for keyword in ['click', 'button', 'enter', 'select', 'update']):
                    file_id = item.get('fileId')
                    if file_id and file_id not in relevant_images:
                        relevant_images.append(file_id)
        
        return relevant_images
