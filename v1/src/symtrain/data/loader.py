"""Functions for loading and processing simulation data."""

import os
import json
import pandas as pd


def load_json_files(parent_dir: str) -> list[dict]:
    """
    Load all JSON files from subdirectories.

    Args:
        parent_dir: Path to the parent directory containing simulation folders.

    Returns:
        List of parsed JSON objects.
    """
    json_list = []

    for folder in os.listdir(parent_dir):
        folder_path = os.path.join(parent_dir, folder)

        if not os.path.isdir(folder_path):
            continue

        json_files = [f for f in os.listdir(folder_path) if f.endswith(".json")]

        if len(json_files) != 1:
            print(f"Skipping {folder}: expected 1 JSON file, found {len(json_files)}")
            continue

        json_path = os.path.join(folder_path, json_files[0])

        with open(json_path, "r") as f:
            data = json.load(f)

        json_list.append(data)

    return json_list


def create_transcript_dataframe(json_list: list[dict]) -> pd.DataFrame:
    """
    Convert JSON data to a DataFrame with name and transcript columns.

    Args:
        json_list: List of parsed JSON objects from simulations.

    Returns:
        DataFrame with 'name' and 'transcript' columns.
    """
    rows = []

    for data in json_list:
        name = data.get("name", "Unknown")
        audio_items = data.get("audioContentItems", [])

        # Combine all actor: transcript lines into one string
        lines = [f'{item["actor"]}: {item["fileTranscript"]}' for item in audio_items]
        transcript = "\n".join(lines)

        rows.append({"name": name, "transcript": transcript})

    return pd.DataFrame(rows)
