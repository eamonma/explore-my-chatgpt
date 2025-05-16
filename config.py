"""Configuration settings for token analysis."""

# --- Configuration ---
DEFAULT_MODEL_COSTS = {
    "gpt-4o": {
        "input_cost_per_million_tokens": 2.5,
        "output_cost_per_million_tokens": 10.0,
    },
    "research": {
        "input_cost_per_million_tokens": 10.0,
        "output_cost_per_million_tokens": 40.0,
    },
    "o3": {
        "input_cost_per_million_tokens": 10.0,
        "output_cost_per_million_tokens": 40.0,
    },
    "o1-pro": {
        "input_cost_per_million_tokens": 150.0,
        "output_cost_per_million_tokens": 600.0,
    },
    "gpt-4-5": {
        "input_cost_per_million_tokens": 75.0,
        "output_cost_per_million_tokens": 150.0,
    },
    "o1": {
        "input_cost_per_million_tokens": 15.0,
        "output_cost_per_million_tokens": 60.0,
    },
    "o1-preview": {
        "input_cost_per_million_tokens": 15.0,
        "output_cost_per_million_tokens": 60.0,
    },
    # Add other models here if needed
}

DEFAULT_TIKTOKEN_ENCODING = (
    "cl100k_base"  # Common encoding, used by gpt-3.5-turbo, gpt-4
)
THOUGHT_CONTENT_MULTIPLIER = 1.2
CALCULATION_MODE = "detailed"  # Options: "detailed", "simple"

# --- Configuration options for reporting ---
EXPORT_FORMATS = ["csv", "json", "text"]  # Supported export formats
DEFAULT_EXPORT_FORMAT = "text"  # Default export format
REPORT_DIRECTORY = "reports"  # Directory to save reports
VERBOSE_MODE = False  # Default to concise reporting
