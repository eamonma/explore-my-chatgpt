"""Functions for generating and exporting reports."""

import os
import json
import csv
import datetime
from collections import defaultdict
from tabulate import tabulate
from config import (
    REPORT_DIRECTORY,
    DEFAULT_EXPORT_FORMAT,
    VERBOSE_MODE,
    DEFAULT_MODEL_COSTS,
)


def generate_comprehensive_report(
    all_analysis_results,
    current_calculation_mode,
    filter_params=None,
    export_format=DEFAULT_EXPORT_FORMAT,
    verbose=VERBOSE_MODE,
):
    """
    Generates a comprehensive report based on analysis results.

    Args:
        all_analysis_results: List of analysis results for each conversation
        current_calculation_mode: The calculation mode used (detailed or simple)
        filter_params: Dictionary containing filter parameters used for the analysis
        export_format: Format to export the report (csv, json, text)
        verbose: Whether to include all details in the report

    Returns:
        Dictionary containing the report data and metadata
    """
    # Create report structure
    report = {
        "metadata": {
            "generated_at": datetime.datetime.now().isoformat(),
            "calculation_mode": current_calculation_mode,
            "filters": filter_params or {},
            "total_conversations": len(all_analysis_results),
            "verbose": verbose,
        },
        "summary": {},
        "model_breakdown": {},
        "temporal_analysis": {},
        "conversation_details": all_analysis_results,
        "errors": [],
    }

    # Extract error conversations
    error_conversations = [
        result for result in all_analysis_results if "error" in result
    ]
    report["errors"] = error_conversations

    # Get valid conversations (without errors)
    valid_results = [result for result in all_analysis_results if "error" not in result]

    # Calculate global summary
    if current_calculation_mode == "detailed":
        total_input_tokens = sum(
            result.get("total_input_tokens_across_turns", 0) for result in valid_results
        )
        total_output_tokens = sum(
            result.get("total_output_tokens_for_all_assistant_msgs", 0)
            for result in valid_results
        )
        total_cost = sum(result.get("total_cost", 0) for result in valid_results)

        # Use real turns count when available, fall back to assistant message count
        total_turns = sum(
            result.get("real_turns_count", result.get("assistant_messages_count", 0))
            for result in valid_results
        )

        # Also calculate total assistant messages for comparison
        total_assistant_messages = sum(
            result.get("assistant_messages_count", 0) for result in valid_results
        )

        report["summary"] = {
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "total_tokens": total_input_tokens + total_output_tokens,
            "total_cost": total_cost,
            "total_turns": total_turns,
            "total_assistant_messages": total_assistant_messages,
            "avg_tokens_per_conversation": (
                (total_input_tokens + total_output_tokens) / len(valid_results)
                if valid_results
                else 0
            ),
            "avg_cost_per_conversation": (
                total_cost / len(valid_results) if valid_results else 0
            ),
            "avg_turns_per_conversation": (
                total_turns / len(valid_results) if valid_results else 0
            ),
            "avg_messages_per_conversation": (
                total_assistant_messages / len(valid_results) if valid_results else 0
            ),
        }
    elif current_calculation_mode == "simple":
        total_user_tokens = sum(
            result.get("simple_total_user_tokens", 0) for result in valid_results
        )
        total_assistant_tokens = sum(
            result.get("simple_total_assistant_tokens", 0) for result in valid_results
        )
        total_system_tokens = sum(
            result.get("simple_total_system_tokens", 0) for result in valid_results
        )
        total_input_tokens = sum(
            result.get("simple_total_input_tokens", 0) for result in valid_results
        )
        total_output_tokens = sum(
            result.get("simple_total_output_tokens", 0) for result in valid_results
        )
        total_input_cost = sum(
            result.get("simple_input_cost", 0) for result in valid_results
        )
        total_output_cost = sum(
            result.get("simple_output_cost", 0) for result in valid_results
        )
        total_cost = sum(result.get("simple_total_cost", 0) for result in valid_results)

        # Use real turns count when available
        total_turns = sum(result.get("real_turns_count", 0) for result in valid_results)

        report["summary"] = {
            "total_user_tokens": total_user_tokens,
            "total_assistant_tokens": total_assistant_tokens,
            "total_system_tokens": total_system_tokens,
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "total_tokens": total_input_tokens + total_output_tokens,
            "total_input_cost": total_input_cost,
            "total_output_cost": total_output_cost,
            "total_cost": total_cost,
            "total_turns": total_turns,
            "avg_tokens_per_conversation": (
                (total_input_tokens + total_output_tokens) / len(valid_results)
                if valid_results
                else 0
            ),
            "avg_cost_per_conversation": (
                total_cost / len(valid_results) if valid_results else 0
            ),
            "avg_turns_per_conversation": (
                total_turns / len(valid_results) if valid_results else 0
            ),
        }

    # Model breakdown analysis
    model_stats = defaultdict(
        lambda: {
            "message_count": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost": 0,
            "input_cost_rate": 0.0,
            "output_cost_rate": 0.0,
        }
    )

    # Add pricing information from the cost config
    for model_name, cost_info in DEFAULT_MODEL_COSTS.items():
        if model_name in model_stats:
            model_stats[model_name]["input_cost_rate"] = cost_info.get(
                "input_cost_per_million_tokens", 0.0
            )
            model_stats[model_name]["output_cost_rate"] = cost_info.get(
                "output_cost_per_million_tokens", 0.0
            )

    for result in valid_results:
        if current_calculation_mode == "detailed":
            # For detailed mode, extract model information from each turn
            turns = result.get("turns_details", [])
            for turn in turns:
                model = turn.get("model_slug", "unknown")
                model_stats[model]["message_count"] = (
                    model_stats[model].get("message_count", 0) + 1
                )
                model_stats[model]["total_input_tokens"] = model_stats[model].get(
                    "total_input_tokens", 0
                ) + turn.get("input_tokens", 0)
                model_stats[model]["total_output_tokens"] = model_stats[model].get(
                    "total_output_tokens", 0
                ) + turn.get("output_tokens", 0)
                model_stats[model]["total_cost"] = model_stats[model].get(
                    "total_cost", 0
                ) + turn.get("turn_total_cost", 0)

                # Get model cost rates if not already set
                if (
                    model_stats[model].get("input_cost_rate", 0) == 0
                    and model in DEFAULT_MODEL_COSTS
                ):
                    model_stats[model]["input_cost_rate"] = DEFAULT_MODEL_COSTS[
                        model
                    ].get("input_cost_per_million_tokens", 0.0)
                    model_stats[model]["output_cost_rate"] = DEFAULT_MODEL_COSTS[
                        model
                    ].get("output_cost_per_million_tokens", 0.0)
        elif current_calculation_mode == "simple":
            # For simple mode, model is generally stored at conversation level
            model = result.get("simple_cost_model_key", "unknown")
            model_stats[model]["message_count"] = (
                model_stats[model].get("message_count", 0) + 1
            )
            model_stats[model]["total_input_tokens"] = model_stats[model].get(
                "total_input_tokens", 0
            ) + result.get("simple_total_input_tokens", 0)
            model_stats[model]["total_output_tokens"] = model_stats[model].get(
                "total_output_tokens", 0
            ) + result.get("simple_total_output_tokens", 0)
            model_stats[model]["total_cost"] = model_stats[model].get(
                "total_cost", 0
            ) + result.get("simple_total_cost", 0)

            # Get model cost rates if not already set
            if (
                model_stats[model].get("input_cost_rate", 0) == 0
                and model in DEFAULT_MODEL_COSTS
            ):
                model_stats[model]["input_cost_rate"] = DEFAULT_MODEL_COSTS[model].get(
                    "input_cost_per_million_tokens", 0.0
                )
                model_stats[model]["output_cost_rate"] = DEFAULT_MODEL_COSTS[model].get(
                    "output_cost_per_million_tokens", 0.0
                )

    # Calculate percentages and averages for model stats
    total_all_models_cost = sum(model["total_cost"] for model in model_stats.values())

    for model_name, stats in model_stats.items():
        stats["percentage_of_total_cost"] = (
            (stats["total_cost"] / total_all_models_cost * 100)
            if total_all_models_cost > 0
            else 0
        )
        stats["avg_tokens_per_message"] = (
            (stats["total_input_tokens"] + stats["total_output_tokens"])
            / stats["message_count"]
            if stats["message_count"] > 0
            else 0
        )
        stats["avg_cost_per_message"] = (
            stats["total_cost"] / stats["message_count"]
            if stats["message_count"] > 0
            else 0
        )
        stats["total_tokens"] = (
            stats["total_input_tokens"] + stats["total_output_tokens"]
        )

    report["model_breakdown"] = dict(model_stats)

    # Temporal analysis (by day)
    daily_stats = defaultdict(
        lambda: {
            "conversation_count": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost": 0,
            "total_turns": 0,
            "total_assistant_messages": 0,
        }
    )

    for result in valid_results:
        if result.get("create_time_ts"):
            day = datetime.datetime.fromtimestamp(result["create_time_ts"]).strftime(
                "%Y-%m-%d"
            )

            if current_calculation_mode == "detailed":
                daily_stats[day]["conversation_count"] += 1
                daily_stats[day]["total_input_tokens"] += result.get(
                    "total_input_tokens_across_turns", 0
                )
                daily_stats[day]["total_output_tokens"] += result.get(
                    "total_output_tokens_for_all_assistant_msgs", 0
                )
                daily_stats[day]["total_cost"] += result.get("total_cost", 0)
                daily_stats[day]["total_turns"] += result.get("real_turns_count", 0)
                daily_stats[day]["total_assistant_messages"] += result.get(
                    "assistant_messages_count", 0
                )
            elif current_calculation_mode == "simple":
                daily_stats[day]["conversation_count"] += 1
                daily_stats[day]["total_input_tokens"] += result.get(
                    "simple_total_input_tokens", 0
                )
                daily_stats[day]["total_output_tokens"] += result.get(
                    "simple_total_output_tokens", 0
                )
                daily_stats[day]["total_cost"] += result.get("simple_total_cost", 0)
                daily_stats[day]["total_turns"] += result.get("real_turns_count", 0)

    # Calculate daily averages
    for day, stats in daily_stats.items():
        stats["avg_tokens_per_conversation"] = (
            (stats["total_input_tokens"] + stats["total_output_tokens"])
            / stats["conversation_count"]
            if stats["conversation_count"] > 0
            else 0
        )
        stats["avg_cost_per_conversation"] = (
            stats["total_cost"] / stats["conversation_count"]
            if stats["conversation_count"] > 0
            else 0
        )
        stats["avg_turns_per_conversation"] = (
            stats["total_turns"] / stats["conversation_count"]
            if stats["conversation_count"] > 0
            else 0
        )
        stats["total_tokens"] = (
            stats["total_input_tokens"] + stats["total_output_tokens"]
        )

    # Sort by date
    report["temporal_analysis"] = {
        k: daily_stats[k] for k in sorted(daily_stats.keys())
    }

    # Export the report if requested
    if export_format:
        export_report(report, export_format)

    return report


def export_report(report, format_type):
    """
    Exports the report in the specified format.

    Args:
        report: The report data to export
        format_type: The format to export (csv, json, text)
    """
    # Create reports directory if it doesn't exist
    if not os.path.exists(REPORT_DIRECTORY):
        os.makedirs(REPORT_DIRECTORY)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    verbose = report["metadata"]["verbose"]

    if format_type == "json":
        filename = os.path.join(
            REPORT_DIRECTORY, f"token_analysis_report_{timestamp}.json"
        )
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"Report exported to {filename}")

    elif format_type == "csv":
        # Export summary
        summary_filename = os.path.join(
            REPORT_DIRECTORY, f"token_analysis_summary_{timestamp}.csv"
        )
        with open(summary_filename, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Metric", "Value"])
            for key, value in report["summary"].items():
                if isinstance(value, float):
                    writer.writerow([key, f"{value:.2f}"])
                else:
                    writer.writerow([key, value])

        # Export model breakdown
        model_filename = os.path.join(
            REPORT_DIRECTORY, f"token_analysis_models_{timestamp}.csv"
        )
        with open(model_filename, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)

            if verbose:
                headers = [
                    "Model",
                    "Messages",
                    "Input Tokens",
                    "Output Tokens",
                    "Total Tokens",
                    "Input Cost Rate",
                    "Output Cost Rate",
                    "Total Cost ($)",
                    "% of Total Cost",
                    "Avg Tokens/Msg",
                    "Avg Cost/Msg",
                ]
            else:
                headers = [
                    "Model",
                    "Messages",
                    "Total Tokens",
                    "Total Cost ($)",
                    "% of Total Cost",
                    "Avg Cost/Msg",
                ]

            writer.writerow(headers)

            for model, stats in report["model_breakdown"].items():
                if verbose:
                    writer.writerow(
                        [
                            model,
                            stats["message_count"],
                            stats["total_input_tokens"],
                            stats["total_output_tokens"],
                            stats["total_tokens"],
                            f"${stats['input_cost_rate']:.2f}",
                            f"${stats['output_cost_rate']:.2f}",
                            f"{stats['total_cost']:.2f}",
                            f"{stats['percentage_of_total_cost']:.2f}%",
                            f"{stats['avg_tokens_per_message']:.2f}",
                            f"{stats['avg_cost_per_message']:.2f}",
                        ]
                    )
                else:
                    writer.writerow(
                        [
                            model,
                            stats["message_count"],
                            stats["total_tokens"],
                            f"{stats['total_cost']:.2f}",
                            f"{stats['percentage_of_total_cost']:.2f}%",
                            f"{stats['avg_cost_per_message']:.2f}",
                        ]
                    )

        # Export daily stats
        daily_filename = os.path.join(
            REPORT_DIRECTORY, f"token_analysis_daily_{timestamp}.csv"
        )
        with open(daily_filename, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)

            if verbose:
                headers = [
                    "Date",
                    "Conversations",
                    "Turns",
                    "Assistant Messages",
                    "Input Tokens",
                    "Output Tokens",
                    "Total Tokens",
                    "Total Cost ($)",
                    "Avg Tokens/Conv",
                    "Avg Turns/Conv",
                    "Avg Cost/Conv",
                ]
            else:
                headers = [
                    "Date",
                    "Conversations",
                    "Turns",
                    "Total Tokens",
                    "Total Cost",
                    "Avg Turns/Conv",
                    "Avg Cost/Conv",
                ]

            writer.writerow(headers)

            for day, stats in report["temporal_analysis"].items():
                if verbose:
                    writer.writerow(
                        [
                            day,
                            stats["conversation_count"],
                            stats.get("total_turns", 0),
                            stats.get("total_assistant_messages", 0),
                            f"{stats['total_input_tokens']:,}",
                            f"{stats['total_output_tokens']:,}",
                            f"{stats['total_tokens']:,}",
                            f"${stats['total_cost']:.2f}",
                            f"{stats['avg_tokens_per_conversation']:.2f}",
                            f"{stats.get('avg_turns_per_conversation', 0):.2f}",
                            f"${stats['avg_cost_per_conversation']:.2f}",
                        ]
                    )
                else:
                    writer.writerow(
                        [
                            day,
                            stats["conversation_count"],
                            stats.get("total_turns", 0),
                            f"{stats['total_tokens']:,}",
                            f"${stats['total_cost']:.2f}",
                            f"{stats.get('avg_turns_per_conversation', 0):.2f}",
                            f"${stats['avg_cost_per_conversation']:.2f}",
                        ]
                    )

        print(f"Reports exported to {REPORT_DIRECTORY}")

    elif format_type == "text":
        filename = os.path.join(
            REPORT_DIRECTORY, f"token_analysis_report_{timestamp}.txt"
        )
        with open(filename, "w", encoding="utf-8") as f:
            # Write header
            f.write("=" * 80 + "\n")
            f.write(
                f"TOKEN USAGE ANALYSIS REPORT - {report['metadata']['generated_at']}\n"
            )
            f.write("=" * 80 + "\n\n")

            # Write metadata
            f.write("ANALYSIS PARAMETERS:\n")
            f.write(f"Calculation Mode: {report['metadata']['calculation_mode']}\n")
            f.write(
                f"Total Conversations Analyzed: {report['metadata']['total_conversations']}\n"
            )
            f.write(f"Verbose Mode: {'Enabled' if verbose else 'Disabled'}\n")

            if report["metadata"]["filters"]:
                f.write("Filters Applied:\n")
                for filter_name, filter_value in report["metadata"]["filters"].items():
                    f.write(f"  {filter_name}: {filter_value}\n")
            f.write("\n")

            # Write summary
            f.write("SUMMARY STATISTICS:\n")
            f.write("-" * 80 + "\n")

            for key, value in report["summary"].items():
                if isinstance(value, float):
                    f.write(f"{key.replace('_', ' ').title()}: {value:,.2f}\n")
                else:
                    f.write(f"{key.replace('_', ' ').title()}: {value:,}\n")
            f.write("\n")

            # Write model breakdown
            f.write("MODEL BREAKDOWN:\n")
            f.write("-" * 80 + "\n")
            f.write("Note: Model identifiers explanation:\n")
            f.write(
                "  - Standard model names (o3, gpt-4-5, etc.) are direct model identifiers\n"
            )
            f.write(
                "  - 'N/A' indicates messages where no model was specified in metadata\n"
            )
            f.write("  - 'Tool: X' indicates messages sent to tool endpoints\n")
            f.write(
                "  - Models with '(default)' suffix were not directly specified but inferred from defaults\n"
            )
            f.write("\n")

            # Create table data for models
            model_table = []
            for model, stats in report["model_breakdown"].items():
                if verbose:
                    model_table.append(
                        [
                            model,
                            stats["message_count"],
                            f"{stats['total_input_tokens']:,}",
                            f"{stats['total_output_tokens']:,}",
                            f"{stats['total_tokens']:,}",
                            f"${stats['input_cost_rate']:.2f}",
                            f"${stats['output_cost_rate']:.2f}",
                            f"${stats['total_cost']:.2f}",
                            f"{stats['percentage_of_total_cost']:.2f}%",
                            f"{stats['avg_tokens_per_message']:.2f}",
                            f"${stats['avg_cost_per_message']:.2f}",
                        ]
                    )
                else:
                    model_table.append(
                        [
                            model,
                            stats["message_count"],
                            f"{stats['total_tokens']:,}",
                            f"${stats['total_cost']:.2f}",
                            f"{stats['percentage_of_total_cost']:.2f}%",
                            f"${stats['avg_cost_per_message']:.2f}",
                        ]
                    )

            # Sort table by cost (descending)
            if verbose:
                model_table.sort(
                    key=lambda x: float(x[7].replace("$", "").replace(",", "")),
                    reverse=True,
                )
                headers = [
                    "Model",
                    "Messages",
                    "Input Tokens",
                    "Output Tokens",
                    "Total Tokens",
                    "Input$/M",
                    "Output$/M",
                    "Total Cost",
                    "% of Cost",
                    "Avg Tokens/Msg",
                    "Avg Cost/Msg",
                ]
            else:
                model_table.sort(
                    key=lambda x: float(x[3].replace("$", "").replace(",", "")),
                    reverse=True,
                )
                headers = [
                    "Model",
                    "Messages",
                    "Total Tokens",
                    "Total Cost",
                    "% of Cost",
                    "Avg Cost/Msg",
                ]

            f.write(tabulate(model_table, headers=headers, tablefmt="grid") + "\n\n")

            # Write daily breakdown
            if report["temporal_analysis"]:
                f.write("DAILY BREAKDOWN:\n")
                f.write("-" * 80 + "\n")

                # Create table data for days
                day_table = []
                for day, stats in report["temporal_analysis"].items():
                    if verbose:
                        day_table.append(
                            [
                                day,
                                stats["conversation_count"],
                                stats.get("total_turns", 0),
                                stats.get("total_assistant_messages", 0),
                                f"{stats['total_input_tokens']:,}",
                                f"{stats['total_output_tokens']:,}",
                                f"{stats['total_tokens']:,}",
                                f"${stats['total_cost']:.2f}",
                                f"{stats['avg_tokens_per_conversation']:.2f}",
                                f"{stats.get('avg_turns_per_conversation', 0):.2f}",
                                f"${stats['avg_cost_per_conversation']:.2f}",
                            ]
                        )
                    else:
                        day_table.append(
                            [
                                day,
                                stats["conversation_count"],
                                stats.get("total_turns", 0),
                                f"{stats['total_tokens']:,}",
                                f"${stats['total_cost']:.2f}",
                                f"{stats.get('avg_turns_per_conversation', 0):.2f}",
                                f"${stats['avg_cost_per_conversation']:.2f}",
                            ]
                        )

                if verbose:
                    headers = [
                        "Date",
                        "Convs",
                        "Turns",
                        "Msgs",
                        "Input Tokens",
                        "Output Tokens",
                        "Total Tokens",
                        "Total Cost",
                        "Avg Tokens/Conv",
                        "Avg Turns/Conv",
                        "Avg Cost/Conv",
                    ]
                else:
                    headers = [
                        "Date",
                        "Convs",
                        "Turns",
                        "Total Tokens",
                        "Total Cost",
                        "Avg Turns/Conv",
                        "Avg Cost/Conv",
                    ]

                # Display only top 10 days
                if len(day_table) > 10:
                    f.write(f"(Showing top 10 of {len(day_table)} days)\n")
                    day_table = sorted(
                        day_table,
                        key=lambda x: float(
                            x[7 if verbose else 4].replace("$", "").replace(",", "")
                        ),
                        reverse=True,
                    )[:10]

                f.write(tabulate(day_table, headers=headers, tablefmt="grid") + "\n\n")

            # Write errors if any
            if report["errors"]:
                f.write("ERRORS:\n")
                f.write("-" * 80 + "\n")
                for error in report["errors"]:
                    f.write(
                        f"Conversation: '{error.get('title', 'N/A')}' - Error: {error.get('error', 'Unknown error')}\n"
                    )

            f.write("\n")
            f.write("=" * 80 + "\n")
            f.write("End of Report\n")
            f.write("=" * 80 + "\n")

        print(f"Report exported to {filename}")

    else:
        print(f"Unsupported export format: {format_type}")


def print_report_to_console(report):
    """
    Prints a formatted report to the console.

    Args:
        report: The report data to print
    """
    verbose = report["metadata"]["verbose"]

    # Print header
    print("\n" + "=" * 80)
    print(f"TOKEN USAGE ANALYSIS REPORT - {report['metadata']['generated_at']}")
    print("=" * 80 + "\n")

    # Print summary
    print("SUMMARY STATISTICS:")
    print("-" * 80)

    for key, value in report["summary"].items():
        if isinstance(value, float):
            print(f"{key.replace('_', ' ').title()}: {value:,.2f}")
        else:
            print(f"{key.replace('_', ' ').title()}: {value:,}")
    print()

    # Print model breakdown
    print("MODEL BREAKDOWN:")
    print("-" * 80)
    print("Note: Model identifiers explanation:")
    print("  - Standard model names (o3, gpt-4-5, etc.) are direct model identifiers")
    print("  - 'N/A' indicates messages where no model was specified in metadata")
    print("  - 'Tool: X' indicates messages sent to tool endpoints")
    print(
        "  - Models with '(default)' suffix were not directly specified but inferred from defaults"
    )
    print()

    # Create table data for models
    model_table = []
    for model, stats in report["model_breakdown"].items():
        if verbose:
            model_table.append(
                [
                    model,
                    stats["message_count"],
                    f"{stats['total_input_tokens']:,}",
                    f"{stats['total_output_tokens']:,}",
                    f"{stats['total_tokens']:,}",
                    f"${stats['input_cost_rate']:.2f}",
                    f"${stats['output_cost_rate']:.2f}",
                    f"${stats['total_cost']:.2f}",
                    f"{stats['percentage_of_total_cost']:.2f}%",
                    f"{stats['avg_tokens_per_message']:.2f}",
                    f"${stats['avg_cost_per_message']:.2f}",
                ]
            )
        else:
            model_table.append(
                [
                    model,
                    stats["message_count"],
                    f"{stats['total_tokens']:,}",
                    f"${stats['total_cost']:.2f}",
                    f"{stats['percentage_of_total_cost']:.2f}%",
                    f"${stats['avg_cost_per_message']:.2f}",
                ]
            )

    # Sort table by cost (descending)
    if verbose:
        model_table.sort(
            key=lambda x: float(x[7].replace("$", "").replace(",", "")), reverse=True
        )
        headers = [
            "Model",
            "Messages",
            "Input Tokens",
            "Output Tokens",
            "Total Tokens",
            "Input$/M",
            "Output$/M",
            "Total Cost",
            "% of Cost",
            "Avg Tokens/Msg",
            "Avg Cost/Msg",
        ]
    else:
        model_table.sort(
            key=lambda x: float(x[3].replace("$", "").replace(",", "")), reverse=True
        )
        headers = [
            "Model",
            "Messages",
            "Total Tokens",
            "Total Cost",
            "% of Cost",
            "Avg Cost/Msg",
        ]

    print(tabulate(model_table, headers=headers, tablefmt="grid"))
    print()

    # Print daily breakdown (top 5 days by cost)
    if report["temporal_analysis"]:
        print("DAILY BREAKDOWN (Top Days by Cost):")
        print("-" * 80)

        # Create table data for days
        day_table = []
        for day, stats in report["temporal_analysis"].items():
            if verbose:
                day_table.append(
                    [
                        day,
                        stats["conversation_count"],
                        stats.get("total_turns", 0),
                        stats.get("total_assistant_messages", 0),
                        f"{stats['total_input_tokens']:,}",
                        f"{stats['total_output_tokens']:,}",
                        f"{stats['total_tokens']:,}",
                        f"${stats['total_cost']:.2f}",
                        f"{stats['avg_tokens_per_conversation']:.2f}",
                        f"{stats.get('avg_turns_per_conversation', 0):.2f}",
                        f"${stats['avg_cost_per_conversation']:.2f}",
                    ]
                )
            else:
                day_table.append(
                    [
                        day,
                        stats["conversation_count"],
                        stats.get("total_turns", 0),
                        f"{stats['total_tokens']:,}",
                        f"${stats['total_cost']:.2f}",
                        f"{stats.get('avg_turns_per_conversation', 0):.2f}",
                        f"${stats['avg_cost_per_conversation']:.2f}",
                    ]
                )

        # Sort by cost (descending)
        if verbose:
            day_table.sort(
                key=lambda x: float(x[7].replace("$", "").replace(",", "")),
                reverse=True,
            )
            headers = [
                "Date",
                "Convs",
                "Turns",
                "Msgs",
                "Input Tokens",
                "Output Tokens",
                "Total Tokens",
                "Total Cost",
                "Avg Tokens/Conv",
                "Avg Turns/Conv",
                "Avg Cost/Conv",
            ]
        else:
            day_table.sort(
                key=lambda x: float(x[4].replace("$", "").replace(",", "")),
                reverse=True,
            )
            headers = [
                "Date",
                "Convs",
                "Turns",
                "Total Tokens",
                "Total Cost",
                "Avg Turns/Conv",
                "Avg Cost/Conv",
            ]

        # Display only top 10 days
        if len(day_table) > 10:
            print(f"(Showing top 10 of {len(day_table)} days)")
            day_table = day_table[:10]

        print(tabulate(day_table, headers=headers, tablefmt="grid"))
        print()

    # Print errors if any
    if report["errors"]:
        print("ERRORS:")
        print("-" * 80)
        for error in report["errors"]:
            print(
                f"Conversation: '{error.get('title', 'N/A')}' - Error: {error.get('error', 'Unknown error')}"
            )
        print()
