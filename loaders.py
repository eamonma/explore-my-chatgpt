"""Functions for loading conversation data."""

import json


def load_conversations(file_path):
    """Loads conversations from a JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data
