"""
SymTrain Simulation Intelligence Assistant
Main Streamlit Application with Vision Mapping (Bonus Task)
"""

import streamlit as st
import json
import os
from pathlib import Path
from utils import (
    load_dataset,
    merge_dialogue,
    extract_call_reason_and_steps,
    categorize_simulation,
    generate_steps_few_shot,
    load_all_simulations
)
from vision_mapper import VisionMapper, create_mapping_report

# Page configuration
st.set_page_config(
    page_title="SymTrain Intelligence Assistant",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .step-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .category-tag {
        background-color: #4CAF50;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 1rem;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'simulations' not in st.session_state:
        st.session_state.simulations = None
    if 'api_key' not in st.session_state:
        st.session_state.api_key = ""
    if 'enable_vision' not in st.session_state:
        st.session_state.enable_vision = False
    if 'image_directory' not in st.session_state:
        st.session_state.image_directory = "./data"

def main():
    # Header
    st.markdown('<h1 class="main-header">🤖 SymTrain Simulation Intelligence Assistant</h1>', 
                unsafe_allow_html=True)
    
    initialize_session_state()
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key input
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            value=st.session_state.api_key,
            help="Enter your OpenAI API key for GPT-based processing"
        )
        st.session_state.api_key = api_key
        
        # Data directory input
        data_dir = st.text_input(
            "Training Data Directory",
            value="./data",
            help="Path to the directory containing simulation JSON files"
        )
        
        # Load data button
        if st.button("📂 Load Training Data", use_container_width=True):
            if os.path.exists(data_dir):
                with st.spinner("Loading simulations..."):
                    try:
                        simulations = load_all_simulations(data_dir)
                        st.session_state.simulations = simulations
                        st.success(f"✅ Loaded {len(simulations)} simulations!")
                    except Exception as e:
                        st.error(f"❌ Error loading data: {str(e)}")
            else:
                st.error(f"❌ Directory not found: {data_dir}")
        
        # Display stats if data is loaded
        if st.session_state.simulations:
            st.divider()
            st.metric("Total Simulations", len(st.session_state.simulations))
            
            # Show categories if available
            if st.session_state.simulations:
                categories = set()
                for sim in st.session_state.simulations:
                    if 'category' in sim:
                        categories.add(sim['category'])
                if categories:
                    st.write("**Categories Found:**")
                    for cat in sorted(categories):
                        st.write(f"• {cat}")
        
        # Bonus: Vision Mapping
        st.divider()
        st.subheader("🎁 Bonus: Vision Mapping")
        enable_vision = st.checkbox(
            "Enable Vision Mapping",
            value=st.session_state.enable_vision,
            help="Map steps to UI images and highlight elements (Bonus Task)"
        )
        st.session_state.enable_vision = enable_vision
        
        if enable_vision:
            image_dir = st.text_input(
                "Image Directory",
                value=st.session_state.image_directory,
                help="Base directory for images (auto-detected from JSON location)"
            )
            st.session_state.image_directory = image_dir
            
            st.info("💡 Images are automatically found in the same folder as each simulation's JSON file. Multiple company folders are supported!")
    
    # Main content area
    st.header("💬 Customer Request Processor")
    
    # Test examples
    test_examples = {
        "Test 1: Payment Update (Detailed)": "Hi, I ordered a shirt last week and paid with my American Express card. I need to update the payment method because there is an issue with that card. Can you help me?",
        "Test 2: Payment Update (Simple)": "Hi, I need to update the payment method for one of my recent orders. Can you help me with that?",
        "Test 3: Insurance Claim (Detailed)": "Hi, I am Sam. I was in a car accident this morning and need to file an insurance claim. Can you help me?",
        "Test 4: Insurance Claim (Simple)": "Hi, can you help me file a claim?",
        "Test 5: Order Status (Simple)": "Hi, I recently ordered a book online. Can you give me an update on the order status?",
        "Test 6: Order Status (Delayed)": "Hi, I have been waiting for two weeks for the book I ordered. What is going on with it? Can you give me an update?",
        "Custom Input": ""
    }
    
    # Example selector
    selected_example = st.selectbox(
        "Select a test example or choose 'Custom Input':",
        options=list(test_examples.keys())
    )
    
    # Input text area
    if selected_example == "Custom Input":
        user_input = st.text_area(
            "Enter customer request:",
            height=100,
            placeholder="Type your customer request here..."
        )
    else:
        user_input = st.text_area(
            "Customer request:",
            value=test_examples[selected_example],
            height=100
        )
    
    # Process button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        process_button = st.button("🚀 Generate Steps", use_container_width=True)
    
    # Process the request
    if process_button and user_input:
        if not st.session_state.api_key:
            st.error("⚠️ Please enter your OpenAI API key in the sidebar.")
        elif not st.session_state.simulations:
            st.error("⚠️ Please load training data first using the sidebar.")
        else:
            with st.spinner("🔄 Processing your request..."):
                try:
                    # Generate response using few-shot learning
                    result = generate_steps_few_shot(
                        user_input,
                        st.session_state.simulations,
                        st.session_state.api_key
                    )
                    
                    # Display results
                    st.divider()
                    st.subheader("📊 Analysis Results")
                    
                    # Category
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        st.markdown("**Category:**")
                    with col2:
                        st.markdown(f'<span class="category-tag">{result["category"]}</span>', 
                                  unsafe_allow_html=True)
                    
                    st.write("")
                    
                    # Reason
                    st.markdown("**Request Reason:**")
                    st.info(result["reason"])
                    
                    st.write("")
                    
                    # Steps
                    st.markdown("**Resolution Steps:**")
                    for i, step in enumerate(result["steps"], 1):
                        st.markdown(f'<div class="step-box"><strong>Step {i}:</strong> {step}</div>', 
                                  unsafe_allow_html=True)
                    
                    # JSON output
                    with st.expander("📄 View JSON Output"):
                        st.json(result)
                    
                    # Bonus: Vision Mapping
                    if st.session_state.enable_vision:
                        st.divider()
                        st.subheader("🎁 Bonus: Vision-Based Step-to-Image Mapping")
                        
                        # Get ALL visual items from ALL simulations (don't limit by category)
                        all_visual_items = []
                        image_dirs = {}  # Map fileId to its directory
                        source_info = ""
                        
                        # Collect visual items from ALL simulations
                        for sim in st.session_state.simulations:
                            visual_items = sim.get('visual_items', [])
                            if visual_items:
                                sim_path = Path(sim.get('file_path', ''))
                                sim_dir = str(sim_path.parent)
                                
                                # Track where each image is located
                                for item in visual_items:
                                    file_id = item.get('fileId')
                                    if file_id:
                                        image_dirs[file_id] = sim_dir
                                
                                all_visual_items.extend(visual_items)
                        
                        if all_visual_items:
                            # Show info about what's being used
                            num_simulations = sum(1 for sim in st.session_state.simulations if sim.get('visual_items'))
                            source_info = f"ℹ️ Using {len(all_visual_items)} visual items from {num_simulations} simulation(s) across all categories"
                            st.info(source_info)
                            try:
                                # Create vision mapper
                                mapper = VisionMapper()
                                
                                # Debug info
                                st.write("🔍 **Debug Information:**")
                                st.write(f"- Total visual items loaded: {len(all_visual_items)}")
                                st.write(f"- From {num_simulations} different simulation(s)")
                                st.write(f"- Unique image directories: {len(set(image_dirs.values()))}")
                                if all_visual_items:
                                    sample_ids = [item.get('fileId') for item in all_visual_items[:3]]
                                    st.write(f"- Sample fileIds: {', '.join(f'`{id[:20]}...`' for id in sample_ids if id)}")
                                
                                # Semantic matching debug
                                st.write("")
                                st.write("🎯 **Semantic Matching Info:**")
                                user_keywords = [word.lower() for word in user_input.split() if len(word) > 4]
                                st.write(f"- Request domain keywords: {', '.join(f'`{k}`' for k in user_keywords[:5])}")
                                
                                # Check what hotspot names actually exist
                                sample_hotspots = []
                                for item in all_visual_items[:10]:
                                    for hotspot in item.get('hotspots', [])[:2]:
                                        name = hotspot.get('name', '')
                                        if name and name not in sample_hotspots:
                                            sample_hotspots.append(name)
                                        if len(sample_hotspots) >= 10:
                                            break
                                    if len(sample_hotspots) >= 10:
                                        break
                                
                                st.write(f"- Sample hotspot names: {', '.join(f'`{h}`' for h in sample_hotspots[:10])}")
                                
                                # Check for domain overlap
                                has_overlap = any(keyword in hotspot.lower() for keyword in user_keywords for hotspot in sample_hotspots)
                                if has_overlap:
                                    st.success("✅ Domain keywords found in training data - semantic matching active!")
                                else:
                                    st.warning("⚠️ No domain keywords found in sample hotspots - may show generic matches only")
                                
                                st.write("")
                                
                                # Map steps to images with ALL visual items
                                vision_result = mapper.process_simulation_with_vision(
                                    result['steps'],
                                    all_visual_items,
                                    image_directory=st.session_state.image_directory,
                                    image_dirs=image_dirs,  # Pass directory mapping
                                    request_context=user_input  # Pass user request for semantic matching
                                )
                                
                                # Display mapping statistics
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Total Steps", vision_result['total_steps'])
                                with col2:
                                    st.metric("Mapped Steps", vision_result['mapped_steps'])
                                with col3:
                                    mapping_rate = (vision_result['mapped_steps'] / vision_result['total_steps'] * 100) if vision_result['total_steps'] > 0 else 0
                                    st.metric("Mapping Rate", f"{mapping_rate:.1f}%")
                                
                                st.write("")
                                
                                # Display each mapping
                                for mapping in vision_result['mappings']:
                                    if mapping.get('file_id'):
                                        st.markdown(f"**Step {mapping['step_index'] + 1}:** {mapping['step']}")
                                        
                                        col1, col2 = st.columns([1, 2])
                                        
                                        with col1:
                                            st.write("**Mapping Details:**")
                                            st.write(f"📁 Image: `{mapping['file_id']}`")
                                            st.write(f"🎯 Hotspot: {mapping['hotspot_text']}")
                                            st.write(f"🏷️ Type: {mapping['hotspot_type']}")
                                            st.write(f"📊 Score: {mapping['relevance_score']:.2f}")
                                        
                                        with col2:
                                            if mapping.get('highlighted_image'):
                                                st.image(
                                                    mapping['highlighted_image'],
                                                    caption=f"UI Screenshot with highlighted element",
                                                    use_container_width=True
                                                )
                                            elif mapping.get('image_found'):
                                                st.warning("Image found but could not highlight (processing error)")
                                            else:
                                                st.info(f"💡 Image file `{mapping['file_id']}` not found in `{image_dir}`")
                                        
                                        st.divider()
                                
                                # Show full report in expander
                                with st.expander("📋 View Full Mapping Report"):
                                    report = create_mapping_report(vision_result)
                                    st.code(report, language=None)
                                
                            except Exception as e:
                                st.error(f"Vision mapping error: {str(e)}")
                                st.exception(e)
                        else:
                            st.warning("⚠️ No visual content items found in training data for this category.")
                            st.info("💡 Visual items need `fileId` and `hotspots` data in JSON files.")
                    
                except Exception as e:
                    st.error(f"❌ Error processing request: {str(e)}")
                    st.exception(e)
    
    # Footer with information
    st.divider()
    with st.expander("ℹ️ About This Application"):
        st.markdown("""
        ### SymTrain Simulation Intelligence Assistant
        
        This application uses AI to automatically generate customer assistance steps based on 
        training simulations. 
        
        **Key Features:**
        - Automatic categorization of customer requests
        - Reason extraction from customer input
        - Step-by-step resolution generation using few-shot learning
        - GPT-powered intelligent responses
        
        **How to Use:**
        1. Enter your OpenAI API key in the sidebar
        2. Load training data from your simulations directory
        3. Select a test example or enter a custom request
        4. Click "Generate Steps" to get AI-powered assistance
        
        **Project Tasks Completed:**
        - ✅ Task 1: Load dataset
        - ✅ Task 2: Merge dialogue text
        - ✅ Task 3: Extract call reasons and steps
        - ✅ Task 4: Categorize simulations
        - ✅ Task 5: Few-shot learning with GPT
        - ✅ Task 6: Streamlit application
        - ✅ Task 7: Docker packaging
        """)

if __name__ == "__main__":
    main()
