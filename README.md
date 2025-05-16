# OpenAI Chat Dump Analyzer

Absolutely no idea if this works accurately at all

## **ai generated docs below**

---

## 1. Overview

This project provides a suite of Python tools for in-depth analysis of OpenAI chat dumps, specifically focusing on token usage, API costs, conversation patterns, and model performance. It allows users to process large volumes of conversation data, extract meaningful insights, and generate detailed reports. This is particularly useful for developers, researchers, or anyone working with OpenAI's language models who need to track, understand, and optimize their usage.

## 2. Usage (How to Run)

The primary way to use the OpenAI Chat Dump Analyzer is by executing the `analyzer.py` script from your terminal.

### Prerequisites:

1.  **Prepare Data**:
    - Your OpenAI chat dump must be available as a JSON file (e.g., `conversations.json`). The script can also process a directory of JSON files.
    - By default, the script looks for `conversations.json` in the root directory. You can specify a different path using the `--input` argument.
2.  **Configure (Optional but Recommended)**:
    - Review and update `config.py`, particularly `DEFAULT_MODEL_COSTS`, to ensure accurate pricing and desired settings.
3.  **Install Dependencies**:
    - Ensure you have the necessary Python packages installed. The script will remind you if `tiktoken` (for token counting) or `tabulate` (for report formatting) are missing. You can typically install them using pip:
      ```bash
      pip install tiktoken tabulate
      ```

### Running the Analysis:

Execute the `analyzer.py` script with the path to your chat data. Additional arguments can be used to customize the analysis:

```bash
python analyzer.py --input <path_to_your_conversations.json_or_directory> [options]
```

**Key Command-Line Arguments:**

- `--input <path>`: **(Required)** Path to the input conversations JSON file or a directory containing JSON files.
- `--mode <detailed|simple>`: Sets the analysis mode.
  - `detailed`: Performs an in-depth analysis, processing each turn, identifying models per turn, and calculating costs granularly.
  - `simple`: Provides a more high-level summary, often calculating costs based on a default model for the entire conversation.
  - (Defaults to `CALCULATION_MODE` in `config.py`)
- `--format <text|csv|json>`: Specifies the export format for reports. (Defaults to `DEFAULT_EXPORT_FORMAT` in `config.py`)
- `--filter-start-date <YYYY-MM-DD>`: Filters conversations to include only those created on or after this date.
- `--filter-end-date <YYYY-MM-DD>`: Filters conversations to include only those created on or before this date.
- `--filter-model <model_slug>`: Filters conversations by the specified model slug (e.g., `gpt-4o`, `gpt-3.5-turbo`).
- `--analyze-model <model_slug>`: Performs a detailed analysis for a specific model (e.g., 'o3', 'N/A') and then exits. This bypasses the interactive menu.
- `--verbose`: Enables more detailed console output during processing.

**Example Scenarios:**

1.  **Basic analysis of `conversations.json` using default settings:**

    ```bash
    python analyzer.py --input conversations.json
    ```

2.  **Detailed analysis of conversations from May 2025 for the 'gpt-4o' model, exporting reports as CSV:**

    ```bash
    python analyzer.py --input path/to/my_chat_data.json --mode detailed --filter-start-date 2025-05-01 --filter-end-date 2025-05-31 --filter-model gpt-4o --format csv
    ```

3.  **Analyze a specific model (e.g., 'o3') directly and exit:**
    ```bash
    python analyzer.py --input conversations.json --analyze-model o3
    ```

### Interactive Menu:

After loading and initially filtering the data (based on command-line arguments), the script presents an interactive menu:

```
=== Conversation Analysis Menu ===
1. Show top conversations by turns
2. Find conversation by title
3. Export conversation by title
4. Read conversation text by title
5. Generate comprehensive report
6. Browse conversations by date
7. Exit

Enter your choice (1-7):
```

This menu allows you to:

- **View Top Conversations**: List conversations with the most turns.
- **Search by Title**: Find specific conversations by their title.
- **Export Individual Conversations**: Save the raw JSON of a specific conversation (found by title) to the `reports/` directory.
- **Read Conversation Text**: Display the full text of a conversation (found by title) in the console, including turn delineation and model information.
- **Generate Comprehensive Report**: Create a detailed report based on the current dataset and filters. The report is saved to the `reports/` directory (format based on `--format` or default) and also printed to the console.
- **Browse by Date**: Interactively explore conversations grouped by date.
- **Exit**: Terminate the analyzer.

### Viewing Reports:

- Generated reports (text, JSON, CSV) are saved in the `reports/` directory (configurable in `config.py`).
- Console output will also display summaries and requested information.

_(Note: The `analyze_n_a_model.sh` script mentioned in the original README suggests there might be specific, pre-configured analysis runs available via shell scripts. You can examine this script for its specific functionality.)_

## 3. Core Purpose

The primary goal of this analyzer is to provide a clear and detailed understanding of how OpenAI's language models are being used in chat interactions. This includes:

- **Cost Management:** Accurately calculating API costs based on token consumption for different models.
- **Usage Analytics:** Tracking token counts (input, output, total), number of turns, and messages per conversation.
- **Model Performance:** Analyzing usage patterns across various OpenAI models (e.g., GPT-4, GPT-4o, Claude).
- **Conversation Insights:** Identifying trends, common patterns, and outliers in chat data.
- **Data-driven Optimization:** Providing data to help optimize prompt engineering, model selection, and overall interaction strategies.

## 4. Key Features

- **Comprehensive Analysis:** Calculates detailed token counts, costs, and turn metrics for each conversation.
- **Flexible Configuration:** Allows customization of model costs, calculation modes (simple vs. detailed), and reporting options.
- **Multiple Data Sources:** Designed to work with chat data exported in JSON format (specifically `conversations.json`).
- **Advanced Filtering:** Supports filtering conversations by date range, model used, and other criteria.
- **Rich Reporting:** Generates human-readable text reports and machine-readable JSON/CSV reports, including:
  - Overall summary statistics.
  - Breakdown of usage and costs per model.
  - Temporal analysis (e.g., daily usage trends).
  - Details for individual conversations.
- **Chronological Message Ordering:** Accurately reconstructs the flow of conversation turns.
- **Turn Detection:** Identifies "real" conversation turns based on `end_turn` flags in message metadata.
- **Error Handling:** Gracefully handles conversations with missing data or errors.

## 5. Project Structure

```
.
├── .git/                  # Git repository files
├── .gitignore             # Specifies intentionally untracked files that Git should ignore
├── __pycache__/           # Python bytecode cache
├── reports/               # Directory for generated analysis reports
│   ├── token_analysis_report_YYYYMMDD_HHMMSS.txt
│   └── example_conversation_export.json
├── analyze_n_a_model.sh   # Shell script likely for specific analysis tasks
├── analyzer.py            # Main script for orchestrating the analysis
├── analyzers.py           # Core logic for token counting, cost calculation, and model identification
├── config.py              # Configuration settings (model costs, API keys, etc.)
├── conversations.json     # Primary input: Raw chat dump data (large file)
├── ebird_*.txt            # Example data files (likely unrelated to core functionality)
├── filters.py             # Functions for filtering conversation data
├── loaders.py             # Functions for loading conversation data
├── message_ordering.py    # Utilities for ordering messages chronologically
├── pretty.json            # Potentially a beautified version of conversations.json (large file)
├── README.md              # This file
├── reporting.py           # Functions for generating and exporting reports
├── test.py                # Unit tests or testing scripts
└── tokenizers.py          # Functions for text extraction and tokenization
```

## 6. Core Modules

- **`analyzer.py`**: The main entry point and orchestrator of the analysis pipeline. It handles loading data, applying filters, running analyses, and generating reports.
- **`analyzers.py`**: Contains the core algorithms for parsing individual conversations. This includes:
  - Identifying models used within messages.
  - Counting tokens for input and output.
  - Calculating costs based on configured rates.
  - Determining the number of "real" turns in a conversation.
- **`config.py`**: Stores all configurable parameters for the application. This includes:
  - `DEFAULT_MODEL_COSTS`: A dictionary defining input and output costs per million tokens for various models.
  - `CALCULATION_MODE`: Can be set to "detailed" (analyzing each turn) or "simple" (overall conversation metrics).
  - `DEFAULT_EXPORT_FORMAT`: The default format for exported reports (e.g., "text", "csv", "json").
  - `REPORT_DIRECTORY`: The directory where generated reports are saved.
- **`reporting.py`**: Responsible for generating various types of reports. It aggregates analysis results and formats them into:
  - Text-based summaries for console output or `.txt` files.
  - Structured JSON or CSV files for further processing or data visualization.
- **`loaders.py`**: Handles the loading of conversation data from input files (e.g., `conversations.json`).
- **`filters.py`**: Provides functions to filter the loaded conversation data based on criteria such as date ranges or specific models used.
- **`message_ordering.py`**: Ensures that messages within a conversation are processed in their correct chronological order, which is crucial for accurate turn analysis.
- **`tokenizers.py`**: Contains utilities for extracting relevant text content from messages and potentially interfacing with token counting libraries (though direct `tiktoken` usage might be abstracted or embedded within `analyzers.py`).

## 7. Data Files

- **`conversations.json`**: This is the primary input file containing the raw dump of OpenAI chat conversations. It's expected to be a large JSON file where each entry represents a conversation, and within each conversation, there's a mapping of messages.
- **`pretty.json`**: This file seems to be a "pretty-printed" or formatted version of `conversations.json`. Its exact role or necessity depends on the workflow, but it might be used for easier manual inspection.
- **`reports/` directory**: This directory stores the output of the analysis.
  - `*.txt`: Human-readable summary reports.
  - `*.json`: Detailed, structured data exports, often for specific conversations or aggregated results.

## 8. Configuration (`config.py`)

The `config.py` file is central to customizing the analyzer's behavior:

- **`DEFAULT_MODEL_COSTS`**: This dictionary is critical for accurate cost calculation. It maps model slugs (e.g., "gpt-4o", "research", "o3") to their respective input and output token costs (per million tokens). **Users should keep this updated with the latest OpenAI pricing.**
- **`DEFAULT_TIKTOKEN_ENCODING`**: Specifies the default encoding used for token counting (e.g., "cl100k_base").
- **`THOUGHT_CONTENT_MULTIPLIER`**: A factor used if "thoughts" or internal monologue tokens from the assistant are counted differently.
- **`CALCULATION_MODE`**:
  - `"detailed"`: Performs an in-depth analysis, processing each turn, identifying models per turn, and calculating costs granularly.
  - `"simple"`: Provides a more high-level summary, often calculating costs based on a default model for the entire conversation.
- **`EXPORT_FORMATS`**: Defines the supported formats for exporting reports (e.g., "csv", "json", "text").
- **`DEFAULT_EXPORT_FORMAT`**: Sets the default if no specific format is requested.
- **`REPORT_DIRECTORY`**: Specifies where the generated reports will be saved.
- **`VERBOSE_MODE`**: Toggles the level of detail in reports.

## 9. Reporting

The tool generates several types of outputs:

- **Console Output**: During execution, key statistics or progress might be printed to the console. The `print_report_to_console` function in `reporting.py` provides a summarized view.
- **Text Reports (`.txt`)**: These files (e.g., `token_analysis_report_YYYYMMDD_HHMMSS.txt`) provide a human-readable summary of the analysis, including:
  - Analysis parameters used.
  - Overall summary statistics (total tokens, cost, turns).
  - Breakdown of costs and usage by model.
  - Daily breakdown of activity (top N days).
- **JSON Reports (`.json`)**:
  - Can include aggregated statistics in a structured format.
  - Can also be used to export detailed analysis for individual conversations (e.g., `Recitation Block Solution_20250516_005423.json`), including the full message mapping and analysis results per turn. This is useful for programmatic access or deep dives.
- **CSV Reports (`.csv`)**: If implemented, CSV reports would offer a tabular format suitable for spreadsheets or further data analysis in tools like Pandas.

## 10. Dependencies

Based on the imports observed in the Python files, the primary dependencies are:

- **Python 3.x**
- **`tabulate`**: For formatting tables in text reports.
- **`tiktoken`** (implicitly, for token counting, though not directly imported in all shown snippets, it's essential for OpenAI tokenization).

A `requirements.txt` file would typically list these:

```
# requirements.txt (example)
tabulate
tiktoken
```

## 11. Potential Future Enhancements

- **GUI Interface**: A simple web interface (e.g., using Flask or Streamlit) for easier configuration and report viewing.
- **Advanced Visualization**: Integration with plotting libraries (e.g., Matplotlib, Seaborn, Plotly) to generate charts for trends and breakdowns.
- **Direct API Integration**: Option to fetch conversation data directly from OpenAI APIs (if available and permitted).
- **More Granular Filtering**: Add more filtering options (e.g., by user ID, specific keywords in conversations).
- **Automated Anomaly Detection**: Identify unusual patterns in token usage or costs.
- **User/Session-based Analysis**: If user/session identifiers are present in the data, break down usage by user.
- **Support for Other LLM Providers**: Extend to analyze dumps from other providers like Anthropic, Cohere, etc.
- **Interactive Exploration**: Tools for interactively querying and exploring the analyzed data.

## 12. Contribution

(If this were an open project, a section on how to contribute would be included here.)

---

This README aims to provide a thorough understanding of the OpenAI Chat Dump Analyzer. For specific implementation details, refer to the source code of the respective Python modules.
