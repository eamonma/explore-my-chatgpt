"""Functions for analyzing conversations for token counts and costs."""

from message_ordering import get_message_chronological_order
from tokenizers import extract_text_from_message
from config import DEFAULT_MODEL_COSTS


def identify_model_from_metadata(message):
    """
    Identify the model from message metadata with better fallback handling.

    Args:
        message: The message object containing metadata

    Returns:
        A string identifying the model or a descriptive fallback
    """
    metadata = message.get("metadata", {})

    # First try direct model_slug
    model_slug = metadata.get("model_slug")
    if model_slug:
        return model_slug

    # Check for default_model_slug as fallback
    default_model_slug = metadata.get("default_model_slug")
    if default_model_slug:
        return f"{default_model_slug} (default)"

    # Check for other potential model identifiers in metadata
    if "finish_details" in metadata:
        return "Unknown API Model"

    # Try to identify by message recipient if it's a tool call
    recipient = message.get("recipient")
    if recipient and recipient != "all":
        return f"Tool: {recipient}"

    # Last resort fallback
    return "N/A"


def count_real_turns(mapping, ordered_message_ids):
    """
    Count the actual number of turns in a conversation by using the end_turn field.
    A turn ends when a message with end_turn=true is encountered.

    Args:
        mapping: The conversation message mapping
        ordered_message_ids: The message IDs in chronological order

    Returns:
        The number of real turns in the conversation
    """
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


def analyze_conversation_tokens_and_costs(conversation, costs_config, mode="detailed"):
    """
    Analyzes a single conversation for token counts and API costs.
    Mode can be "detailed" or "simple".
    """
    title = conversation.get("title", "N/A")
    conv_create_time = conversation.get("create_time")
    conv_update_time = conversation.get("update_time")

    mapping = conversation.get("mapping", {})
    if not mapping:
        return {
            "title": title,
            "create_time_ts": conv_create_time,
            "update_time_ts": conv_update_time,
            "error": "No message mapping found",
            "mode": mode,
        }

    ordered_message_ids = get_message_chronological_order(mapping)
    if not ordered_message_ids:
        return {
            "title": title,
            "create_time_ts": conv_create_time,
            "update_time_ts": conv_update_time,
            "error": "Could not determine message order or no messages",
            "mode": mode,
        }

    # Count real turns using end_turn field
    real_turns_count = count_real_turns(mapping, ordered_message_ids)

    if mode == "simple":
        simple_user_tokens = 0
        simple_assistant_tokens = 0
        simple_system_tokens = 0

        for msg_id in ordered_message_ids:
            msg_data = mapping.get(msg_id)
            if not msg_data or not msg_data.get("message"):
                continue

            message = msg_data["message"]
            author_role = message.get("author", {}).get("role", "unknown")

            if author_role == "user":
                _, tokens = extract_text_from_message(msg_data, count_thoughts=False)
                simple_user_tokens += tokens
            elif author_role == "assistant":
                _, tokens = extract_text_from_message(
                    msg_data, count_thoughts=True
                )  # Count thoughts for assistant output
                simple_assistant_tokens += tokens
            elif author_role == "system":
                _, tokens = extract_text_from_message(msg_data, count_thoughts=False)
                simple_system_tokens += tokens

        simple_total_input_tokens_val = simple_user_tokens + simple_system_tokens
        simple_total_output_tokens_val = simple_assistant_tokens

        # Calculate costs for simple mode
        simple_input_cost = 0.0
        simple_output_cost = 0.0
        simple_total_cost = 0.0
        cost_model_key_for_simple = "o3"  # Default assumption

        simple_calc_model_rates = costs_config.get(cost_model_key_for_simple)

        if not simple_calc_model_rates:
            if costs_config:  # Try first model in provided config if "o3" not there
                cost_model_key_for_simple = list(costs_config.keys())[0]
                simple_calc_model_rates = costs_config.get(cost_model_key_for_simple)

            if (
                not simple_calc_model_rates
            ):  # Fallback to global default "o3" if still no rates
                cost_model_key_for_simple = "o3"  # ensure key matches
                simple_calc_model_rates = DEFAULT_MODEL_COSTS.get(
                    cost_model_key_for_simple
                )

        if (
            simple_calc_model_rates
            and "input_cost_per_million_tokens" in simple_calc_model_rates
            and "output_cost_per_million_tokens" in simple_calc_model_rates
        ):
            simple_input_cost = (
                simple_total_input_tokens_val / 1_000_000
            ) * simple_calc_model_rates["input_cost_per_million_tokens"]
            simple_output_cost = (
                simple_total_output_tokens_val / 1_000_000
            ) * simple_calc_model_rates["output_cost_per_million_tokens"]
            simple_total_cost = simple_input_cost + simple_output_cost
        else:
            print(
                f"Warning: Could not determine valid model cost rates for simple calculation for conversation '{title}' (tried key: '{cost_model_key_for_simple}'). Costs will be zero."
            )
            cost_model_key_for_simple = (
                f"{cost_model_key_for_simple} (rates not found/incomplete)"
            )

        return {
            "title": title,
            "create_time_ts": conv_create_time,
            "update_time_ts": conv_update_time,
            "mode": "simple",
            "real_turns_count": real_turns_count,
            "message_count": len(ordered_message_ids),
            "simple_total_user_tokens": simple_user_tokens,
            "simple_total_assistant_tokens": simple_assistant_tokens,
            "simple_total_system_tokens": simple_system_tokens,
            "simple_total_input_tokens": simple_total_input_tokens_val,
            "simple_total_output_tokens": simple_total_output_tokens_val,
            "simple_input_cost": simple_input_cost,
            "simple_output_cost": simple_output_cost,
            "simple_total_cost": simple_total_cost,
            "simple_cost_model_key": cost_model_key_for_simple,
        }

    # Detailed mode (existing logic)
    conversation_total_input_tokens = 0
    conversation_total_output_tokens = 0
    conversation_total_cost = 0.0

    processed_turns = []
    assistant_message_count_in_convo = 0
    current_turn_messages = []  # To collect messages in the current turn
    turn_boundaries = []  # To track where turn boundaries occur

    # Find turn boundaries (indexes where end_turn is True)
    for i, msg_id in enumerate(ordered_message_ids):
        msg_data = mapping.get(msg_id)
        if not msg_data or not msg_data.get("message"):
            continue

        message = msg_data["message"]
        if message.get("end_turn") is True:
            turn_boundaries.append(i)

    # This list will store (message_id, role, message_text_for_tokens, token_count) for all messages up to a point
    history_for_inputs = []
    current_turn_index = 0  # To track which turn we're processing

    for i, msg_id in enumerate(ordered_message_ids):
        msg_data = mapping.get(msg_id)
        if not msg_data or not msg_data.get("message"):
            # print(f"Skipping node {msg_id} as it's not a message or is missing.")
            continue

        message = msg_data["message"]
        author_role = message.get("author", {}).get("role", "unknown")
        model_slug = message.get("metadata", {}).get(
            "model_slug"
        )  # Typically on assistant messages

        # Determine costs for the current message's model, defaulting if not found
        current_model_costs = costs_config.get(
            model_slug, costs_config.get("o3")
        )  # Fallback to o3 if specific slug not in costs
        if not current_model_costs:  # Further fallback if "o3" itself is missing
            current_model_costs = (
                list(costs_config.values())[0]
                if costs_config
                else DEFAULT_MODEL_COSTS["o3"]
            )  # Absolute fallback

        # Extract text and count tokens for the current message
        # Tokenizer is now determined within extract_text_from_message based on msg_data
        _, current_message_output_tokens = extract_text_from_message(
            msg_data, count_thoughts=True
        )
        _, current_message_tokens_for_history = extract_text_from_message(
            msg_data, count_thoughts=False
        )

        current_message_info_for_history = (
            msg_id,
            author_role,
            current_message_tokens_for_history,
        )

        # Add to history
        history_for_inputs.append(current_message_info_for_history)

        if author_role == "assistant":
            assistant_message_count_in_convo += 1

        # Check if this message ends a turn
        is_turn_end = message.get("end_turn") is True

        # Process assistant message costs (this still needs to happen for each assistant message)
        if author_role == "assistant":
            # Output tokens are from the assistant's own message (including its thoughts)
            output_tokens = current_message_output_tokens
            output_cost = (output_tokens / 1_000_000) * current_model_costs[
                "output_cost_per_million_tokens"
            ]

            # Input tokens are from all *prior* messages in history_for_inputs (where thoughts were excluded)
            # We exclude the current message from input tokens calculation
            input_tokens_for_this_msg = sum(
                tok_count
                for j, (_, _, tok_count) in enumerate(history_for_inputs)
                if j < len(history_for_inputs) - 1
            )

            input_cost_rate = current_model_costs["input_cost_per_million_tokens"]

            # Discount input costs after the first turn, not the first assistant message
            if current_turn_index > 0:
                input_cost_rate /= 2.0

            input_cost = (input_tokens_for_this_msg / 1_000_000) * input_cost_rate

            msg_cost = input_cost + output_cost

            conversation_total_output_tokens += output_tokens

            # Only add to processed_turns for reporting
            processed_turns.append(
                {
                    "assistant_message_id": msg_id,
                    "turn_index": current_turn_index,
                    "input_tokens": input_tokens_for_this_msg,
                    "output_tokens": output_tokens,
                    "input_cost": input_cost,
                    "output_cost": output_cost,
                    "turn_total_cost": msg_cost,
                    "model_slug": identify_model_from_metadata(message),
                    "input_discounted": current_turn_index > 0,
                    "is_turn_end": is_turn_end,
                }
            )

            # Add to total cost
            conversation_total_cost += msg_cost
            conversation_total_input_tokens += input_tokens_for_this_msg

        # If this message ends a turn, increment turn index
        if is_turn_end:
            current_turn_index += 1

    return {
        "title": title,
        "create_time_ts": conv_create_time,
        "update_time_ts": conv_update_time,
        "total_input_tokens_across_turns": conversation_total_input_tokens,
        "total_output_tokens_for_all_assistant_msgs": conversation_total_output_tokens,
        "total_cost": conversation_total_cost,
        "real_turns_count": real_turns_count,
        "assistant_messages_count": assistant_message_count_in_convo,
        "turns_details": processed_turns,
        "message_count": len(ordered_message_ids),
        "mode": "detailed",
    }
