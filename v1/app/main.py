import streamlit as st
import pandas as pd
import sys
import os


os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Add src to path for local imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from symtrain.data import load_json_files, create_transcript_dataframe
from symtrain.embeddings import embed_dataframe_column
from symtrain.search import find_similar
from symtrain.llm import generate_steps_with_ollama

# Set page configuration
st.set_page_config(page_title="SymTrain Assistant", page_icon="🤖", layout="wide")

# Title
st.title("🤖 SymTrain Assistant")
st.markdown(
    "*AI-powered category prediction and step generation for customer service simulations*"
)

# Sidebar
st.sidebar.title("About")
st.sidebar.info(
    "This app accepts user input, predicts the category, "
    "and generates reasoning and recommended steps using RAG-based few-shot learning."
)


@st.cache_data
def load_data():
    """Load and process data with embeddings."""
    # Adjust path to data relative to this file
    data_path = os.path.join(os.path.dirname(__file__), "../data/raw")
    json_list = load_json_files(data_path)
    df = create_transcript_dataframe(json_list)

    # Generate embeddings for similarity search
    if "transcript_emb" not in df.columns:
        df = embed_dataframe_column(df, "transcript")

    return df


# Load data
with st.spinner("Loading simulation data and generating embeddings..."):
    try:
        df = load_data()
        st.sidebar.success(f"✅ Loaded {len(df)} simulations")
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.stop()

# Main interface
st.header("📝 Enter Customer Query")

# Example queries for user reference
with st.expander("💡 Example Queries"):
    st.markdown(
        """
    - *"Hi, I ordered a shirt last week and paid with my American Express card. I need to update the payment method because there is an issue with that card. Can you help me?"*
    - *"Hi, I am Sam. I was in a car accident this morning and need to file an insurance claim. Can you help me?"*
    - *"Hi, I recently ordered a book online. Can you give me an update on the order status?"*
    - *"Hi, I need to update the payment method for one of my recent orders. Can you help me with that?"*
    """
    )

# User input
query = st.text_area(
    "Enter the customer's message or transcript:",
    height=120,
    placeholder="Type or paste a customer query here...",
)

# Predict button
if st.button("🔮 Predict Category & Generate Steps", type="primary"):
    if query.strip():
        with st.spinner("Analyzing query and generating recommendations..."):
            try:
                # Call the few-shot learning pipeline
                result = generate_steps_with_ollama(query, df)

                st.divider()

                # Display Category
                col1, col2 = st.columns([1, 2])

                with col1:
                    st.subheader("🏷️ Predicted Category")
                    category = result.get("category", "Unknown")
                    st.success(f"**{category}**")

                with col2:
                    st.subheader("💭 Reasoning")
                    reason = result.get("reason", "No reasoning provided.")
                    st.info(reason)

                # Display Steps
                st.subheader("📋 Recommended Steps")
                steps = result.get("steps", [])

                if steps:
                    for i, step in enumerate(steps, 1):
                        st.markdown(f"**Step {i}:** {step}")
                else:
                    st.warning("No steps generated.")

                # Show raw response if parsing failed
                if "raw_response" in result:
                    with st.expander("⚠️ Raw LLM Response (parsing issue)"):
                        st.code(result["raw_response"])

                # Show similar simulations used for context
                with st.expander("🔍 Similar Simulations Used for Context"):
                    similar = find_similar(df, "transcript_emb", query, top_k=2)
                    for idx, row in similar.iterrows():
                        st.markdown(
                            f"**{row['name']}** (Similarity: {row['similarity']:.4f})"
                        )
                        # Get transcript from original df using the index
                        transcript = df.loc[idx, "transcript"]
                        st.caption(
                            transcript[:500] + "..."
                            if len(transcript) > 500
                            else transcript
                        )
                        st.divider()

            except Exception as e:
                st.error(f"Error during prediction: {e}")
                st.exception(e)
    else:
        st.warning("⚠️ Please enter a customer query.")

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("SymTrain Assistant v1.0 | DS5220 Programming")
