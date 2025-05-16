"""Functions for filtering conversations based on various criteria."""

import datetime


def filter_conversations_by_date(conversations, start_date_str=None, end_date_str=None):
    """Filters conversations based on their top-level create_time."""
    if not start_date_str and not end_date_str:
        return conversations

    filtered = []
    start_dt = None
    end_dt = None

    if start_date_str:
        start_dt = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    if end_date_str:
        end_dt = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").replace(
            hour=23, minute=59, second=59, microsecond=999999
        )

    for conv in conversations:
        conv_time_ts = conv.get("create_time")  # or use 'update_time' if preferred
        if not conv_time_ts:
            # if create_time is missing, maybe include it or log a warning
            # For now, we'll include it if no date filter is strictly violated
            if (
                start_dt or end_dt
            ):  # if any date filter is active, and this one is unknown, exclude.
                # Or decide to include if it's an important conversation. For now, exclude if timestamp is missing and filtering is active.
                continue
            else:  # No date filters active, so include it
                filtered.append(conv)
                continue

        conv_dt = datetime.datetime.fromtimestamp(conv_time_ts)

        passes_filter = True
        if start_dt and conv_dt < start_dt:
            passes_filter = False
        if end_dt and conv_dt > end_dt:
            passes_filter = False

        if passes_filter:
            filtered.append(conv)

    return filtered


def filter_conversations_by_model(conversations, model_slug_filter=None):
    """
    Filters conversations where at least one ASSISTANT message used the specified model_slug.
    If model_slug_filter is None or empty, returns all conversations.
    """
    if not model_slug_filter:
        return conversations

    filtered_conversations = []
    for conv in conversations:
        mapping = conv.get("mapping", {})
        assistant_used_model = False
        for msg_id, msg_data in mapping.items():
            message = msg_data.get("message")
            if message:
                author_role = message.get("author", {}).get("role")
                if author_role == "assistant":
                    metadata = message.get("metadata", {})
                    if metadata.get("model_slug") == model_slug_filter:
                        assistant_used_model = True
                        break
        if assistant_used_model:
            filtered_conversations.append(conv)
    return filtered_conversations
