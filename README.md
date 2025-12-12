# SymTrain Assistant

AI-powered assistant for analyzing and processing SymTrain customer service simulation data.

## Project Structure

```
symtrain-assistant/
├── symtrain-image/      # Current focus - Vision-enabled Streamlit app
│   ├── app.py           # Main Streamlit application (GPT-4o powered)
│   ├── utils.py         # Data loading and processing utilities
│   ├── vision_mapper.py # Maps steps to UI screenshots
│   └── data/            # Simulation data for the app
├── v1/                  # Phase 1 - Initial exploration & development
│   ├── app/             # Original Streamlit app (Ollama-based)
│   ├── data/            # Raw and processed simulation data
│   ├── notebooks/       # Jupyter notebooks for data exploration
│   └── src/             # Python package with embeddings & clustering
├── Dockerfile           # Container configuration
├── docker-compose.yml   # Docker orchestration
├── pyproject.toml       # Python package configuration
└── requirements.txt     # Root dependencies
```

## Quick Start

### Running the Main Application (symtrain-image)

Using Docker (recommended):

```bash
docker-compose up --build
```

The app will be available at http://localhost:8501

### Development

For working with the v1 exploration code:

```bash
# Install the package in editable mode
pip install -e .

# Run the v1 app
cd v1/app
streamlit run main.py
```

## Components

### symtrain-image (Current Focus)

- Uses OpenAI GPT-4o for intelligent processing
- Vision mapping to connect steps with UI screenshots
- Containerized deployment with Docker

### v1 (Initial Development)

- Local LLM processing with Ollama
- DistilBERT embeddings for semantic similarity
- Clustering and data exploration notebooks
- Foundation work and experimentation
