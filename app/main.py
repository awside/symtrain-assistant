import streamlit as st
import pandas as pd
import sys
import os

# Add the project root to the python path so we can import from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.symtrain.data import load_json_files, create_transcript_dataframe
from src.symtrain.embeddings import embed_dataframe_column
from src.symtrain.search import find_similar
from src.symtrain.clustering import cluster_embeddings, print_cluster_summary

# Set page configuration
st.set_page_config(
    page_title="SymTrain Assistant",
    page_icon="🤖",
    layout="wide"
)

# Title
st.title("🤖 SymTrain Assistant")

# Sidebar for navigation
st.sidebar.title("Navigation")
options = st.sidebar.radio("Go to", ["Data View", "Similarity Search", "Clustering Analysis"])

@st.cache_data
def load_data():
    """Load and process data."""
    with st.spinner('Loading data...'):
        # Adjust path to data relative to this file
        data_path = os.path.join(os.path.dirname(__file__), '../data/raw')
        json_list = load_json_files(data_path)
        df = create_transcript_dataframe(json_list)
        
        # Pre-calculate embeddings if not already done (or do it on the fly and cache)
        # For this demo, we'll do it here. In production, load pre-computed embeddings.
        if 'transcript_emb' not in df.columns:
             df = embed_dataframe_column(df, "transcript")
        
        return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

if options == "Data View":
    st.header("Data View")
    st.write(f"Total Records: {len(df)}")
    st.dataframe(df)

elif options == "Similarity Search":
    st.header("Similarity Search")
    
    query = st.text_area("Enter a transcript or query to find similar simulations:", height=100)
    
    if st.button("Search"):
        if query:
            with st.spinner('Searching...'):
                try:
                    results = find_similar(df, "transcript_emb", query, top_k=5)
                    st.subheader("Top Results")
                    
                    # Display results nicely
                    for idx, row in results.iterrows():
                        with st.expander(f"{row['name']} (Score: {row['similarity']:.4f})"):
                            st.write(f"**Transcript:** {row['transcript']}")
                except Exception as e:
                    st.error(f"Error during search: {e}")
        else:
            st.warning("Please enter a query.")

elif options == "Clustering Analysis":
    st.header("Clustering Analysis")
    
    n_clusters = st.slider("Number of Clusters", min_value=2, max_value=10, value=5)
    
    if st.button("Run Clustering"):
        with st.spinner('Clustering...'):
            try:
                clustered_df = cluster_embeddings(df, "transcript_emb", n_clusters=n_clusters)
                
                st.subheader("Cluster Summary")
                
                # We can't capture the print output easily, so let's manually display it or modify the function.
                # Since I can't modify the function easily right now without checking it, I'll implement a simple display here
                # assuming the function adds a 'transcript_emb_cluster' column.
                
                if 'transcript_emb_cluster' in clustered_df.columns:
                    for cluster_id in sorted(clustered_df['transcript_emb_cluster'].unique()):
                        st.markdown(f"### Cluster {cluster_id}")
                        cluster_items = clustered_df[clustered_df['transcript_emb_cluster'] == cluster_id]['name'].tolist()
                        for item in cluster_items:
                            st.write(f"- {item}")
                else:
                    st.warning("Clustering column not found. Check implementation.")
                    
            except Exception as e:
                st.error(f"Error during clustering: {e}")

# Footer
st.sidebar.markdown("---")
st.sidebar.info("SymTrain Assistant v0.1")
