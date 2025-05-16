# OpenAI Chat Dump Analyzer

Absolutely no idea if this works accurately at all

## **ai generated docs below**

## TL;DR

This Python script (`analyzer.py`) analyzes OpenAI chat dump JSON files. It calculates token usage, API costs, and provides insights into conversation patterns and model performance.

**Quick Start:**

1. Put your `conversations.json` in the same directory.
2. Run `pip install tiktoken tabulate`.
3. Run `python analyzer.py --input conversations.json`.

Customize analysis with command-line options or an interactive menu. Check `config.py` for cost settings.

## 1. Overview

This project provides a suite of Python tools for in-depth analysis of OpenAI chat dumps, specifically focusing on token usage, API costs, conversation patterns, and model performance. It allows users to process large volumes of conversation data, extract meaningful insights, and generate detailed reports. This is particularly useful for developers, researchers, or anyone working with OpenAI's language models who need to track, understand, and optimize their usage.

## 2. Usage (How to Run)

Get started with the OpenAI Chat Dump Analyzer by running the `analyzer.py` script from your terminal. Here's how:

### 1. Get Your Data Ready

- **Input File(s):** You'll need your OpenAI chat dump as a JSON file (e.g., `conversations.json`). You can also provide a directory containing multiple JSON files.
- **Location:** By default, the script looks for `conversations.json` in the same directory it's run from. Use the `--input` argument to specify a different file or directory.

### 2. Check Configuration (Optional, but Recommended)

- Open `config.py`.
- Review and update `DEFAULT_MODEL_COSTS` to reflect current OpenAI pricing for accurate cost calculations. Adjust other settings as needed.

### 3. Install Necessary Libraries

- Make sure you have `tiktoken` (for counting tokens) and `tabulate` (for formatting reports) installed. If not, you can install them using pip:
  ```bash
  pip install tiktoken tabulate
  ```
  The script will also prompt you if these are missing.

### 4. Run the Analyzer

Execute `analyzer.py` with the path to your chat data. You can add other arguments to customize the analysis.

**Basic Command:**

```bash
python analyzer.py --input <path_to_your_conversations.json_or_directory> [options]
```

**Key Command-Line Options:**

Use these options to tailor the analysis to your needs:

- `--input <path>`: **(Required)** Specifies the path to your input JSON file or a directory of JSON files.
- `--mode <detailed|simple>`:
  - `detailed`: Analyzes each conversation turn by turn, identifies models used, and calculates costs precisely.
  - `simple`: Provides a high-level summary. It aggregates token counts for user, assistant, and system messages across entire conversations. Costs are then estimated using a single model's pricing.
  - _Default: Uses the `CALCULATION_MODE` set in `config.py`._
- `--format <text|csv|json>`: Sets the output format for reports.
  - _Default: Uses `DEFAULT_EXPORT_FORMAT` from `config.py`._
- `--filter-start-date <YYYY-MM-DD>`: Includes conversations created on or after this date.
- `--filter-end-date <YYYY-MM-DD>`: Includes conversations created on or before this date.
- `--filter-model <model_slug>`: Filters for conversations that used a specific model (e.g., `gpt-4o`, `gpt-3.5-turbo`).
- `--analyze-model <model_slug>`: Performs a detailed analysis for only the specified model (e.g., 'o3', 'N/A') and then exits, bypassing the interactive menu.
- `--verbose`: Shows more detailed output in the console while processing.

**Example Scenarios:**

1.  **Analyze `conversations.json` with default settings:**

    ```bash
    python analyzer.py --input conversations.json
    ```

2.  **Analyze conversations from May 2025 using 'gpt-4o', export as CSV:**

    ```bash
    python analyzer.py --input path/to/my_chat_data.json --mode detailed --filter-start-date 2025-05-01 --filter-end-date 2025-05-31 --filter-model gpt-4o --format csv
    ```

3.  **Quickly analyze only the 'o3' model usage and exit:**
    ```bash
    python analyzer.py --input conversations.json --analyze-model o3
    ```

### 5. Use the Interactive Menu (Optional)

If you don't use options like `--analyze-model` that cause an immediate exit, the script will load your data (applying any command-line filters) and then present this menu:

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

**Menu Options:**

- **1. Show top conversations by turns:** Lists conversations with the highest number of turns.
- **2. Find conversation by title:** Searches for a specific conversation by its title.
- **3. Export conversation by title:** Saves the raw JSON of a found conversation to the `reports/` directory.
- **4. Read conversation text by title:** Displays the full text of a found conversation in the console, including turns and model information.
- **5. Generate comprehensive report:** Creates a detailed report based on the current data and filters. The report is saved to `reports/` (format determined by `--format` or defaults) and also shown in the console.
- **6. Browse conversations by date:** Interactively explore conversations grouped by their creation date.
- **7. Exit:** Closes the analyzer.

### 6. View Your Reports

- Reports (text, JSON, CSV) are saved in the `reports/` directory (this can be changed in `config.py`).
- Summaries and requested data will also appear in your console.

_(Note: The `analyze_n_a_model.sh` script, if present, might offer pre-configured analysis runs. Check its contents for specific details.)_

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
  - `"simple"`: Provides a high-level summary. Token counts for user, assistant, and system messages are aggregated for the entire conversation. Costs are then calculated using a single model's pricing rates applied to these totals. The cost model defaults to "o3", attempts the first model in `config.py` if "o3" is unavailable, and then uses a hardcoded "o3" fallback if needed.
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
