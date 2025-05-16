"""Main module for token usage analyzer."""

import json
import datetime
import os
from config import (
    DEFAULT_MODEL_COSTS,
    CALCULATION_MODE,
    DEFAULT_EXPORT_FORMAT,
    REPORT_DIRECTORY,
    EXPORT_FORMATS,
)
from loaders import load_conversations
from filters import filter_conversations_by_date, filter_conversations_by_model
from analyzers import analyze_conversation_tokens_and_costs
from reporting import generate_comprehensive_report, print_report_to_console
from message_ordering import get_message_chronological_order


def count_real_turns_in_conversation(original_conv):
    """
    Count the actual number of turns in a conversation by using the end_turn field.
    A turn ends when a message with end_turn=true is encountered.

    Args:
        original_conv: The original conversation data

    Returns:
        The number of real turns in the conversation
    """
    mapping = original_conv.get("mapping", {})
    if not mapping:
        return 0

    # Get messages in chronological order
    ordered_message_ids = get_message_chronological_order(mapping)
    if not ordered_message_ids:
        return 0

    turn_count = 0
    for msg_id in ordered_message_ids:
        msg_data = mapping.get(msg_id)
        if not msg_data or not msg_data.get("message"):
            continue

        message = msg_data["message"]

        # Check if this message ends a turn
        if message.get("end_turn") is True:
            turn_count += 1

    return turn_count


def find_conversations_with_most_turns(analysis_results, limit=10):
    """Return the conversations with the most turns, sorted in descending order."""
    # Filter out conversations with errors
    valid_results = [result for result in analysis_results if "error" not in result]

    # Sort conversations by turn count
    if valid_results and "real_turns_count" in valid_results[0]:
        # Use real turn count when available
        sorted_convs = sorted(
            valid_results, key=lambda x: x.get("real_turns_count", 0), reverse=True
        )
    elif valid_results and "assistant_messages_count" in valid_results[0]:
        # For detailed mode, fall back to assistant message count if real turns not available
        sorted_convs = sorted(
            valid_results,
            key=lambda x: x.get("assistant_messages_count", 0),
            reverse=True,
        )
    else:
        # For simple mode - use message count as proxy for turns
        sorted_convs = sorted(
            valid_results, key=lambda x: x.get("message_count", 0), reverse=True
        )

    return sorted_convs[:limit]


def find_conversations_by_title(analysis_results, title_query, case_sensitive=False):
    """
    Find conversations that match the given title query.

    Args:
        analysis_results: List of analysis results for each conversation
        title_query: String to search for in conversation titles
        case_sensitive: Whether the search should be case sensitive

    Returns:
        List of conversations that match the title query
    """
    matching_conversations = []

    for conv in analysis_results:
        title = conv.get("title", "")
        if not title:
            continue

        if case_sensitive:
            if title_query in title:
                matching_conversations.append(conv)
        else:
            if title_query.lower() in title.lower():
                matching_conversations.append(conv)

    return matching_conversations


def extract_message_content(message):
    """
    Extract the text content from a message.

    Args:
        message: Message data dictionary

    Returns:
        Extracted text content
    """
    content = message.get("content", {})

    # Handle different content types
    parts = content.get("parts", [])
    if parts:
        # Join multiple parts with newlines
        return "\n".join([str(part) for part in parts if part])

    # Handle other content types if needed
    text = content.get("text", "")
    if text:
        return text

    # Fallback for other formats
    return str(content) if content else "[No content]"


def display_conversation_text(original_conv):
    """
    Display the full text of a conversation with clear turn delineation.

    Args:
        original_conv: The original conversation data
    """
    title = original_conv.get("title", "Untitled Conversation")
    mapping = original_conv.get("mapping", {})

    if not mapping:
        print("Error: No messages found in this conversation.")
        return

    # Get messages in chronological order
    ordered_message_ids = get_message_chronological_order(mapping)

    if not ordered_message_ids:
        print("Error: Could not determine message order.")
        return

    print(f"\n{'='*80}")
    print(f"CONVERSATION: {title}")
    print(f"{'='*80}")

    current_turn = 1

    for msg_id in ordered_message_ids:
        msg_data = mapping.get(msg_id)
        if not msg_data or not msg_data.get("message"):
            continue

        message = msg_data["message"]
        author = message.get("author", {})
        role = author.get("role", "unknown")
        name = author.get("name", role.capitalize())

        # Get message content
        content = extract_message_content(message)

        # Add model information for assistant messages
        model_info = ""
        if role == "assistant":
            model = message.get("metadata", {}).get("model_slug", "")
            if model:
                model_info = f" [Model: {model}]"

        # Format role name with padding
        role_display = f"[{name}{model_info}]"

        print(f"\n{role_display}")
        print(f"{'-' * len(role_display)}")
        print(content)

        # Mark turn boundaries
        if message.get("end_turn") is True:
            print(f"\n----- End of Turn {current_turn} -----")
            current_turn += 1

    print(f"\n{'='*80}")
    print(f"Total turns: {current_turn - 1}")
    print(f"{'='*80}\n")


def find_original_conversation(analysis_result, original_data):
    """Find the original conversation data for an analysis result."""
    conv_id = analysis_result.get("conversation_id")
    if not conv_id:
        return None

    for conv in original_data:
        if conv.get("id") == conv_id:
            return conv

    return None


def export_conversation_to_json(conversation, original_data, output_dir=None):
    """
    Export the raw conversation data to a JSON file.

    Args:
        conversation: The analyzed conversation result
        original_data: The original conversations data loaded from the input file
        output_dir: Directory to save the output file (defaults to REPORT_DIRECTORY)

    Returns:
        Path to the exported file or None if export failed
    """
    if not output_dir:
        output_dir = REPORT_DIRECTORY

    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Get conversation ID to find the original data
    conv_id = conversation.get("conversation_id")
    if not conv_id:
        print("Error: Could not find conversation ID for export.")
        return None

    # Find the original conversation data
    original_conv = None
    for conv in original_data:
        if conv.get("id") == conv_id:
            original_conv = conv
            break

    if not original_conv:
        print("Error: Could not find original conversation data for export.")
        return None

    # Create a sanitized filename from the title
    title = conversation.get("title", "untitled")
    sanitized_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in title)
    sanitized_title = sanitized_title[:50]  # Limit length

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{sanitized_title}_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)

    # Write the conversation data to file
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(original_conv, f, indent=2)
        print(f"Conversation exported to: {filepath}")
        return filepath
    except Exception as e:
        print(f"Error exporting conversation: {e}")
        return None


def print_conversation_details(conversation, mode="detailed", original_data=None):
    """Print detailed information about a single conversation."""
    title = conversation.get("title", "Untitled")
    print(f"\n=== Conversation Details: {title} ===")

    # Format create time if available
    if conversation.get("create_time_ts"):
        create_time = datetime.datetime.fromtimestamp(
            conversation.get("create_time_ts")
        ).strftime("%Y-%m-%d %H:%M:%S")
        print(f"Created: {create_time}")

    if conversation.get("update_time_ts"):
        update_time = datetime.datetime.fromtimestamp(
            conversation.get("update_time_ts")
        ).strftime("%Y-%m-%d %H:%M:%S")
        print(f"Updated: {update_time}")

    # Display turn count
    if "real_turns_count" in conversation:
        print(f"Actual Turn Count: {conversation['real_turns_count']}")

    # Print mode-specific details
    if mode == "detailed":
        assistant_msgs = conversation.get("assistant_messages_count", 0)
        input_tokens = conversation.get("total_input_tokens_across_turns", 0)
        output_tokens = conversation.get(
            "total_output_tokens_for_all_assistant_msgs", 0
        )
        total_cost = conversation.get("total_cost", 0)

        print(f"Assistant Messages: {assistant_msgs}")
        print(f"Total Messages: {conversation.get('message_count', 0)}")
        print(f"Input Tokens: {input_tokens:,}")
        print(f"Output Tokens: {output_tokens:,}")
        print(f"Total Tokens: {input_tokens + output_tokens:,}")
        print(f"Estimated Cost: ${total_cost:.4f}")

        # Print turn details if available and user wants verbose output
        turns_details = conversation.get("turns_details", [])
        if turns_details:
            print("\nAssistant Message Details:")
            for i, turn in enumerate(turns_details, 1):
                turn_marker = " (End of Turn)" if turn.get("is_turn_end") else ""
                print(f"  Message {i}{turn_marker}:")
                print(f"    Turn Index: {turn.get('turn_index', 'unknown')}")
                print(f"    Model: {turn.get('model_slug', 'unknown')}")
                print(f"    Input Tokens: {turn.get('input_tokens', 0):,}")
                print(f"    Output Tokens: {turn.get('output_tokens', 0):,}")
                print(f"    Cost: ${turn.get('turn_total_cost', 0):.4f}")
    else:  # simple mode
        user_tokens = conversation.get("simple_total_user_tokens", 0)
        assistant_tokens = conversation.get("simple_total_assistant_tokens", 0)
        system_tokens = conversation.get("simple_total_system_tokens", 0)
        total_cost = conversation.get("simple_total_cost", 0)

        print(f"Total Messages: {conversation.get('message_count', 0)}")
        print(f"User Tokens: {user_tokens:,}")
        print(f"Assistant Tokens: {assistant_tokens:,}")
        print(f"System Tokens: {system_tokens:,}")
        print(f"Total Tokens: {user_tokens + assistant_tokens + system_tokens:,}")
        print(f"Estimated Cost: ${total_cost:.4f}")

    # Options for additional actions
    if original_data:
        print("\nAdditional Options:")
        print("1. View conversation text")
        print("2. Export to JSON")
        print("3. Return to menu")

        option = input("\nEnter your choice (1-3): ")

        if option == "1":
            original_conv = find_original_conversation(conversation, original_data)
            if original_conv:
                display_conversation_text(original_conv)
            else:
                print("Error: Could not find original conversation data.")
        elif option == "2":
            export_conversation_to_json(conversation, original_data)


def print_top_conversations_by_turns(
    conversations, mode="detailed", original_data=None
):
    """Print information about the conversations with the most turns."""
    print("\n=== Conversations with Most Turns ===")

    for i, conv in enumerate(conversations, 1):
        title = conv.get("title", "Untitled")

        real_turns = conv.get("real_turns_count", None)

        if mode == "detailed":
            assistant_msgs = conv.get("assistant_messages_count", 0)
            total_tokens = conv.get("total_input_tokens_across_turns", 0) + conv.get(
                "total_output_tokens_for_all_assistant_msgs", 0
            )
        else:  # simple mode
            assistant_msgs = (
                conv.get("message_count", 0) // 2
            )  # Rough estimate of assistant messages
            total_tokens = conv.get("simple_total_input_tokens", 0) + conv.get(
                "simple_total_output_tokens", 0
            )

        # Format create time if available
        create_time = ""
        if conv.get("create_time_ts"):
            create_time = datetime.datetime.fromtimestamp(
                conv.get("create_time_ts")
            ).strftime("%Y-%m-%d")

        print(f"{i}. {title} ({create_time})")
        if real_turns is not None:
            print(f"   Actual Turns: {real_turns}")
        print(f"   Assistant Messages: {assistant_msgs}")
        print(f"   Total Tokens: {total_tokens:,}")
        print()


def find_and_display_conversation_by_title(
    all_analysis_results, title_query, mode="detailed", original_data=None
):
    """Find and display conversations matching the given title."""
    matching_conversations = find_conversations_by_title(
        all_analysis_results, title_query
    )

    if not matching_conversations:
        print(f"\nNo conversations found with title containing '{title_query}'")
        return

    print(
        f"\nFound {len(matching_conversations)} conversations matching '{title_query}':"
    )

    # If there's only one match, display detailed information
    if len(matching_conversations) == 1:
        print_conversation_details(matching_conversations[0], mode, original_data)
    # Otherwise show a summary list
    else:
        for i, conv in enumerate(matching_conversations, 1):
            title = conv.get("title", "Untitled")
            create_time = ""
            if conv.get("create_time_ts"):
                create_time = datetime.datetime.fromtimestamp(
                    conv.get("create_time_ts")
                ).strftime("%Y-%m-%d")

            real_turns = conv.get("real_turns_count")
            print(f"{i}. {title} ({create_time})")
            if real_turns is not None:
                print(f"   Actual Turns: {real_turns}")

        # Optionally allow user to select a conversation for detailed view
        try:
            choice = input(
                "\nEnter a number to view details (or press Enter to skip): "
            )
            if choice and choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(matching_conversations):
                    print_conversation_details(
                        matching_conversations[idx], mode, original_data
                    )
        except (ValueError, KeyboardInterrupt):
            print("Skipping detailed view.")


def analyze_model_details(all_conversations, model_id):
    """
    Analyze details of a specific model to understand what type of messages it contains.
    Useful for understanding "N/A" or other special model identifiers.

    Args:
        all_conversations: List of all conversation data
        model_id: Model identifier to analyze

    Returns:
        None - prints analysis to console
    """
    print(f"\n{'='*80}")
    print(f"DETAILED ANALYSIS FOR MODEL: {model_id}")
    print(f"{'='*80}")

    message_count = 0
    recipient_types = {}
    content_types = {}
    author_roles = {}
    sample_messages = []

    # Loop through all conversations
    for conv in all_conversations:
        mapping = conv.get("mapping", {})
        if not mapping:
            continue

        # Get messages in chronological order
        ordered_message_ids = get_message_chronological_order(mapping)
        if not ordered_message_ids:
            continue

        for msg_id in ordered_message_ids:
            msg_data = mapping.get(msg_id)
            if not msg_data or not msg_data.get("message"):
                continue

            message = msg_data["message"]
            metadata = message.get("metadata", {})

            # Check if this message matches the model we're analyzing
            from analyzers import identify_model_from_metadata

            model_slug = identify_model_from_metadata(message)

            if model_slug == model_id:
                message_count += 1

                # Collect stats
                recipient = message.get("recipient", "none")
                recipient_types[recipient] = recipient_types.get(recipient, 0) + 1

                content = message.get("content", {})
                content_type = content.get("content_type", "unknown")
                content_types[content_type] = content_types.get(content_type, 0) + 1

                author_role = message.get("author", {}).get("role", "unknown")
                author_roles[author_role] = author_roles.get(author_role, 0) + 1

                # Collect a few sample messages
                if len(sample_messages) < 3:
                    sample_content = (
                        str(content)[:100] + "..."
                        if len(str(content)) > 100
                        else str(content)
                    )
                    sample_messages.append(
                        {
                            "conversation": conv.get("title", "Untitled"),
                            "author": author_role,
                            "recipient": recipient,
                            "content_sample": sample_content,
                        }
                    )

    # Print results
    print(f"Total messages with model '{model_id}': {message_count}")
    print("\nMessage recipients:")
    for recipient, count in sorted(
        recipient_types.items(), key=lambda x: x[1], reverse=True
    ):
        print(f"  - {recipient}: {count} messages ({count/message_count*100:.1f}%)")

    print("\nContent types:")
    for content_type, count in sorted(
        content_types.items(), key=lambda x: x[1], reverse=True
    ):
        print(f"  - {content_type}: {count} messages ({count/message_count*100:.1f}%)")

    print("\nAuthor roles:")
    for role, count in sorted(author_roles.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {role}: {count} messages ({count/message_count*100:.1f}%)")

    if sample_messages:
        print("\nSample messages:")
        for i, sample in enumerate(sample_messages, 1):
            print(f"\nSample {i}:")
            print(f"  Conversation: {sample['conversation']}")
            print(f"  Author: {sample['author']}")
            print(f"  Recipient: {sample['recipient']}")
            print(f"  Content: {sample['content_sample']}")

    print(f"\n{'='*80}")


def find_conversations_by_date(analysis_results, target_date, original_data):
    """
    Find conversations that occurred on a specific date.

    Args:
        analysis_results: List of analysis results for each conversation
        target_date: Date string in format YYYY-MM-DD
        original_data: Original conversation data

    Returns:
        List of conversations that match the date
    """
    matching_conversations = []
    target_dt = datetime.datetime.strptime(target_date, "%Y-%m-%d").date()

    for conv in analysis_results:
        # Get the original conversation data
        conv_id = conv.get("conversation_id")
        if not conv_id:
            continue

        # Find the original conversation
        original_conv = None
        for orig in original_data:
            if orig.get("id") == conv_id:
                original_conv = orig
                break

        if not original_conv:
            continue

        # Get create_time from original data
        create_time = original_conv.get("create_time")
        if not create_time:
            continue

        # Get date part only for comparison
        conv_date = datetime.datetime.fromtimestamp(create_time).date()

        # Add to results if dates match
        if conv_date == target_dt:
            matching_conversations.append(conv)

    return matching_conversations


def get_conversation_dates(analysis_results, original_data):
    """
    Get all unique dates that have conversations, sorted chronologically.

    Args:
        analysis_results: List of analysis results for each conversation
        original_data: Original conversation data

    Returns:
        List of date strings in format YYYY-MM-DD
    """
    date_dict = {}

    for conv in analysis_results:
        # Get the original conversation data
        conv_id = conv.get("conversation_id")
        if not conv_id:
            continue

        # Find the original conversation
        original_conv = None
        for orig in original_data:
            if orig.get("id") == conv_id:
                original_conv = orig
                break

        if not original_conv:
            continue

        # Get create_time from original data
        create_time = original_conv.get("create_time")
        if not create_time:
            continue

        # Get date part as string
        conv_date = datetime.datetime.fromtimestamp(create_time).date()
        date_str = conv_date.strftime("%Y-%m-%d")

        # Count conversations per date
        if date_str in date_dict:
            date_dict[date_str] += 1
        else:
            date_dict[date_str] = 1

    # Convert to list of tuples (date_str, count) and sort by date
    date_list = [(date, count) for date, count in date_dict.items()]
    date_list.sort(key=lambda x: x[0])

    return date_list


def browse_conversations_by_date(analysis_results, original_data):
    """
    Interactive date browser for conversations.

    Args:
        analysis_results: List of analysis results for each conversation
        original_data: Original conversation data
    """
    # Get all dates with conversations
    date_list = get_conversation_dates(analysis_results, original_data)

    if not date_list:
        print("\nNo conversations with date information found.")
        return

    current_index = 0
    total_dates = len(date_list)

    while True:
        # Display calendar header
        print("\n=== Conversation Calendar ===")
        print(f"Showing date {current_index + 1} of {total_dates}")

        # Get current date and count
        current_date, conv_count = date_list[current_index]

        # Display date info
        print(f"\nDate: {current_date}")
        print(f"Conversations: {conv_count}")

        # Find conversations for this date
        date_conversations = find_conversations_by_date(
            analysis_results, current_date, original_data
        )

        # Get wider terminal width information
        try:
            # Try to get terminal width
            terminal_width = os.get_terminal_size().columns
        except (AttributeError, OSError):
            # Default if unable to determine
            terminal_width = 100

        # Display conversation list in a table format
        print("\nConversations on this date:")

        # Define table headers
        headers = ["#", "Title", "Time", "Turns", "First Model", "Tokens", "Cost"]

        # Calculate column widths (adjust as needed for your typical data)
        id_width = 3
        # Limit title width to make room for other columns
        title_width = max(20, terminal_width - 80)
        time_width = 10
        turns_width = 6
        model_width = 15
        tokens_width = 10
        cost_width = 8

        # Print table header
        header_format = (
            f"{{:{id_width}}} | "
            f"{{:{title_width}.{title_width}}} | "
            f"{{:^{time_width}}} | "  # Center-align time
            f"{{:^{turns_width}}} | "  # Center-align turns
            f"{{:^{model_width}.{model_width}}} | "  # Center-align model
            f"{{:>{tokens_width}}} | "  # Right-align tokens
            f"{{:>{cost_width}}}"  # Right-align cost
        )
        print(header_format.format(*headers))

        # Print separator line
        separator = (
            "-" * id_width
            + "+"
            + "-" * (title_width + 2)
            + "+"
            + "-" * (time_width + 2)
            + "+"
            + "-" * (turns_width + 2)
            + "+"
            + "-" * (model_width + 2)
            + "+"
            + "-" * (tokens_width + 2)
            + "+"
            + "-" * cost_width
        )
        print(separator)

        # Print each conversation
        for i, conv in enumerate(date_conversations, 1):
            # Get basic info
            title = conv.get("title", "Untitled")

            # Get time (we already know the date)
            create_time = ""
            original_conv = find_original_conversation(conv, original_data)
            if original_conv and original_conv.get("create_time"):
                timestamp = datetime.datetime.fromtimestamp(
                    original_conv.get("create_time")
                )
                create_time = timestamp.strftime("%H:%M:%S")

            # Get turn count
            turn_count = conv.get("real_turns_count", "?")

            # Get first model used
            first_model = "unknown"
            if original_conv:
                first_model = get_first_model_used(original_conv)

            # Get token info
            total_tokens = 0
            if (
                "total_input_tokens_across_turns" in conv
                and "total_output_tokens_for_all_assistant_msgs" in conv
            ):
                total_tokens = conv.get(
                    "total_input_tokens_across_turns", 0
                ) + conv.get("total_output_tokens_for_all_assistant_msgs", 0)
            else:
                total_tokens = conv.get("simple_total_input_tokens", 0) + conv.get(
                    "simple_total_output_tokens", 0
                )

            # Get cost estimate
            cost = conv.get("total_cost", conv.get("simple_total_cost", 0))
            if cost is None:
                cost = 0.0

            # Format values for display
            row_format = (
                f"{{:{id_width}}} | "
                f"{{:{title_width}.{title_width}}} | "
                f"{{:^{time_width}}} | "  # Center-align time
                f"{{:^{turns_width}}} | "  # Center-align turns
                f"{{:^{model_width}.{model_width}}} | "  # Center-align model
                f"{{:>{tokens_width},}} | "  # Right-align tokens with comma separator
                f"${{:>{cost_width-1}.4f}}"  # Right-align cost with dollar sign
            )

            try:
                print(
                    row_format.format(
                        i,
                        title,
                        create_time,
                        turn_count,
                        first_model,
                        total_tokens,
                        cost,
                    )
                )
            except Exception as e:
                # Fallback for formatting errors
                print(
                    f"{i}. {title} - {first_model} - {total_tokens:,} tokens - ${cost:.4f}"
                )

        # Navigation options
        print("\nNavigation options:")
        if current_index > 0:
            print("P - Previous date")
        if current_index < total_dates - 1:
            print("N - Next date")
        print("J - Jump to specific date")
        print("V - View conversation details")
        print("R - Return to main menu")

        choice = input("\nEnter choice: ").upper()

        if choice == "P" and current_index > 0:
            current_index -= 1
        elif choice == "N" and current_index < total_dates - 1:
            current_index += 1
        elif choice == "J":
            # Jump to a specific date
            try:
                jump_date = input("Enter date (YYYY-MM-DD): ")
                # Validate date format
                datetime.datetime.strptime(jump_date, "%Y-%m-%d")

                # Find the date in our list
                found = False
                for i, (date_str, _) in enumerate(date_list):
                    if date_str == jump_date:
                        current_index = i
                        found = True
                        break

                if not found:
                    print(f"No conversations found for date {jump_date}")

                    # Suggest closest dates
                    print("Available dates:")
                    date_only = [date for date, _ in date_list]
                    # Show up to 5 dates before and after the target
                    for i, date_str in enumerate(date_only):
                        if date_str > jump_date:
                            # Show dates near the target date
                            start_idx = max(0, i - 5)
                            end_idx = min(len(date_only), i + 5)
                            for j in range(start_idx, end_idx):
                                print(f"  {date_only[j]}")
                            break
                    else:
                        # If we didn't find any dates after the target,
                        # show the last few dates
                        for date_str in date_only[-10:]:
                            print(f"  {date_str}")

            except ValueError:
                print("Invalid date format. Please use YYYY-MM-DD format.")
        elif choice == "V":
            # Let user select which conversation to display
            try:
                view_choice = input("Enter conversation number to view: ")
                if view_choice.isdigit():
                    idx = int(view_choice) - 1
                    if 0 <= idx < len(date_conversations):
                        original_conv = find_original_conversation(
                            date_conversations[idx], original_data
                        )
                        if original_conv:
                            display_conversation_text(original_conv)
                        else:
                            print("Error: Could not find original conversation data.")
                    else:
                        print("Invalid conversation number.")
            except (ValueError, KeyboardInterrupt):
                print("Viewing canceled.")
        elif choice == "R":
            return
        else:
            print("Invalid choice.")


def get_first_model_used(conversation):
    """
    Determine the first model used in a conversation.

    Args:
        conversation: Original conversation data

    Returns:
        String with the model slug/identifier or "unknown" if can't be determined
    """
    mapping = conversation.get("mapping", {})
    if not mapping:
        return "unknown"

    # Get messages in chronological order
    ordered_message_ids = get_message_chronological_order(mapping)
    if not ordered_message_ids:
        return "unknown"

    # Check messages in order
    for msg_id in ordered_message_ids:
        msg_data = mapping.get(msg_id)
        if not msg_data or not msg_data.get("message"):
            continue

        message = msg_data["message"]

        # Only interested in assistant messages that have a model
        if message.get("author", {}).get("role") != "assistant":
            continue

        # Get model information
        model = message.get("metadata", {}).get("model_slug", "")
        if model:
            return model

    return "unknown"


def main(args=None):
    """Main function to load, process, and analyze conversations."""
    if args is None:
        # For backward compatibility or direct calls
        import argparse

        parser = argparse.ArgumentParser(
            description="Analyze token usage in conversations."
        )
        parser.add_argument(
            "--mode",
            choices=["detailed", "simple"],
            default=CALCULATION_MODE,
            help="Analysis mode: 'detailed' or 'simple'",
        )
        parser.add_argument(
            "--input",
            required=True,
            help="Path to input conversations file or directory",
        )
        parser.add_argument(
            "--format",
            choices=EXPORT_FORMATS,
            default=DEFAULT_EXPORT_FORMAT,
            help=f"Export format: {', '.join(EXPORT_FORMATS)}",
        )
        parser.add_argument(
            "--verbose", action="store_true", help="Enable verbose output"
        )
        parser.add_argument(
            "--filter-start-date",
            help="Filter conversations from this date (YYYY-MM-DD)",
        )
        parser.add_argument(
            "--filter-end-date",
            help="Filter conversations until this date (YYYY-MM-DD)",
        )
        parser.add_argument("--filter-model", help="Filter conversations by model slug")
        parser.add_argument("--view-id", help="View a specific conversation by ID")
        parser.add_argument(
            "--analyze-model",
            help="Analyze details of a specific model (e.g., 'N/A', 'o3', etc.)",
        )
        args = parser.parse_args()

    # --- Process command-line arguments ---
    input_path = args.input
    current_calculation_mode = args.mode
    export_format = args.format
    verbose_output = args.verbose
    filter_start_date = args.filter_start_date
    filter_end_date = args.filter_end_date
    filter_model = args.filter_model
    view_conversation_id = args.view_id
    analyze_specific_model = args.analyze_model

    print("Starting conversation analysis...")
    print("Please ensure you have `tiktoken` installed (`pip install tiktoken`)\n")
    print(
        "For comprehensive reports, please install tabulate: `pip install tabulate`\n"
    )

    # --- Load Data ---
    print(f"Loading conversations from {input_path}...")
    try:
        conversations_data = load_conversations(input_path)
    except FileNotFoundError:
        print(f"Error: Input file {input_path} not found.")
        return
    except json.JSONDecodeError:
        print(
            f"Error: Could not decode JSON from {input_path}. Ensure it's a valid JSON file."
        )
        return
    print(f"Loaded {len(conversations_data)} conversations.")

    # --- Filter Conversations ---
    filtered_convs = conversations_data
    if filter_start_date or filter_end_date:
        print(
            f"Filtering by date: Start='{filter_start_date}', End='{filter_end_date}'"
        )
        filtered_convs = filter_conversations_by_date(
            filtered_convs, filter_start_date, filter_end_date
        )
        print(f"{len(filtered_convs)} conversations after date filtering.")

    if filter_model:
        print(f"Filtering by model: '{filter_model}'")
        filtered_convs = filter_conversations_by_model(filtered_convs, filter_model)
        print(f"{len(filtered_convs)} conversations after model filtering.")

    if not filtered_convs:
        print("No conversations match the specified filters.")
        return

    # Check if we're doing a detailed model analysis
    if analyze_specific_model:
        analyze_model_details(filtered_convs, analyze_specific_model)
        return

    # --- Analyze Conversations ---
    all_analysis_results = []
    print(
        f"\nAnalyzing {len(filtered_convs)} conversations using '{current_calculation_mode}' mode..."
    )

    for i, conv in enumerate(filtered_convs):
        analysis_result = analyze_conversation_tokens_and_costs(
            conv, DEFAULT_MODEL_COSTS, current_calculation_mode
        )
        # Add conversation ID for later reference to original data
        analysis_result["conversation_id"] = conv.get("id")
        all_analysis_results.append(analysis_result)

        # Show progress for large datasets
        if (i + 1) % 100 == 0 or i + 1 == len(filtered_convs):
            print(f"  Processed {i + 1}/{len(filtered_convs)} conversations...")

    # Interactive menu
    while True:
        print("\n=== Conversation Analysis Menu ===")
        print("1. Show top conversations by turns")
        print("2. Find conversation by title")
        print("3. Export conversation by title")
        print("4. Read conversation text by title")
        print("5. Generate comprehensive report")
        print("6. Browse conversations by date")
        print("7. Exit")

        choice = input("\nEnter your choice (1-7): ")

        if choice == "1":
            top_count = input("How many top conversations to show? (default: 10) ")
            limit = int(top_count) if top_count.isdigit() else 10
            top_conversations = find_conversations_with_most_turns(
                all_analysis_results, limit=limit
            )
            print_top_conversations_by_turns(
                top_conversations, current_calculation_mode, conversations_data
            )

        elif choice == "2":
            title_query = input("Enter title to search for: ")
            if title_query:
                find_and_display_conversation_by_title(
                    all_analysis_results,
                    title_query,
                    current_calculation_mode,
                    conversations_data,
                )

        elif choice == "3":
            title_query = input("Enter title of conversation to export: ")
            if title_query:
                matching_conversations = find_conversations_by_title(
                    all_analysis_results, title_query
                )

                if not matching_conversations:
                    print(
                        f"\nNo conversations found with title containing '{title_query}'"
                    )
                else:
                    print(
                        f"\nFound {len(matching_conversations)} conversations matching '{title_query}':"
                    )

                    # Show list of matching conversations
                    for i, conv in enumerate(matching_conversations, 1):
                        title = conv.get("title", "Untitled")
                        create_time = ""
                        if conv.get("create_time_ts"):
                            create_time = datetime.datetime.fromtimestamp(
                                conv.get("create_time_ts")
                            ).strftime("%Y-%m-%d")

                        print(f"{i}. {title} ({create_time})")

                    # Let user select which conversation to export
                    try:
                        choice = input(
                            "\nEnter a number to export (or press Enter to cancel): "
                        )
                        if choice and choice.isdigit():
                            idx = int(choice) - 1
                            if 0 <= idx < len(matching_conversations):
                                export_conversation_to_json(
                                    matching_conversations[idx], conversations_data
                                )
                    except (ValueError, KeyboardInterrupt):
                        print("Export canceled.")

        elif choice == "4":
            title_query = input("Enter title of conversation to read: ")
            if title_query:
                matching_conversations = find_conversations_by_title(
                    all_analysis_results, title_query
                )

                if not matching_conversations:
                    print(
                        f"\nNo conversations found with title containing '{title_query}'"
                    )
                else:
                    print(
                        f"\nFound {len(matching_conversations)} conversations matching '{title_query}':"
                    )

                    # Show list of matching conversations
                    for i, conv in enumerate(matching_conversations, 1):
                        title = conv.get("title", "Untitled")
                        create_time = ""
                        if conv.get("create_time_ts"):
                            create_time = datetime.datetime.fromtimestamp(
                                conv.get("create_time_ts")
                            ).strftime("%Y-%m-%d")

                        print(f"{i}. {title} ({create_time})")

                    # Let user select which conversation to display
                    try:
                        choice = input(
                            "\nEnter a number to read (or press Enter to cancel): "
                        )
                        if choice and choice.isdigit():
                            idx = int(choice) - 1
                            if 0 <= idx < len(matching_conversations):
                                original_conv = find_original_conversation(
                                    matching_conversations[idx], conversations_data
                                )
                                if original_conv:
                                    display_conversation_text(original_conv)
                                else:
                                    print(
                                        "Error: Could not find original conversation data."
                                    )
                    except (ValueError, KeyboardInterrupt):
                        print("Reading canceled.")

        elif choice == "5":
            # Generate comprehensive report
            report = generate_comprehensive_report(
                all_analysis_results,
                current_calculation_mode,
                {
                    "start_date": filter_start_date,
                    "end_date": filter_end_date,
                    "model": filter_model,
                },
                export_format,
                verbose_output,
            )
            # Print the report to the console
            print_report_to_console(report)

        elif choice == "6":
            # Browse conversations by date
            browse_conversations_by_date(all_analysis_results, conversations_data)

        elif choice == "7":
            print("Exiting...")
            break

        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
