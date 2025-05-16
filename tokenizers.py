"""Functions for token counting and message extraction."""

import tiktoken
from config import THOUGHT_CONTENT_MULTIPLIER


def get_tokenizer(model_slug=None):
    """Gets the tiktoken tokenizer based on model_slug."""
    try:
        if model_slug == "o3":
            # Assuming o3 corresponds to gpt-4o based on user example
            return tiktoken.encoding_for_model("gpt-4o")
        elif model_slug:
            # Try if model_slug itself is a direct model name tiktoken knows
            return tiktoken.encoding_for_model(model_slug)
        else:
            # Default for messages without a slug (e.g., user, system)
            return tiktoken.get_encoding("cl100k_base")
    except Exception:
        # Fallback to a general tokenizer if specific model encoding fails or is unknown
        # print(f"Warning: Could not get tokenizer for model_slug '{model_slug}'. Using cl100k_base.")
        return tiktoken.get_encoding("cl100k_base")


def count_tokens(text, tokenizer):
    """Counts tokens in a given text using the provided tokenizer.
    Handles potential disallowed special tokens like '<|endoftext|>' by allowing them as normal text.
    """
    if not text or not isinstance(text, str):
        return 0

    # Allow '<|endoftext|>' to be encoded as normal text.
    # For other special tokens, tiktoken will still raise an error if they are disallowed by default.
    disallowed_set = tokenizer.special_tokens_set
    if "<|endoftext|>" in disallowed_set:
        disallowed_set = disallowed_set - {"<|endoftext|>"}

    try:
        return len(tokenizer.encode(text, disallowed_special=disallowed_set))
    except ValueError as e:
        # This might happen if other unexpected special tokens are encountered.
        # For now, we'll print a warning and return 0 tokens for this text part.
        # A more sophisticated handling might be needed if this occurs frequently with other tokens.
        print(
            f"Warning: Tokenizer error for text: '{text[:100]}...'. Error: {e}. Returning 0 tokens for this part."
        )
        return 0


def extract_text_from_message(message_data, count_thoughts=True):
    """
    Extracts relevant text from a message object for token counting.
    If count_thoughts is True, applies a multiplier to tokens from thoughts[].content.
    Tokens are counted using a tokenizer appropriate for the message's model_slug.
    Returns a list of text pieces and their token counts.
    """
    if not message_data or not message_data.get("message"):
        return [], 0

    message = message_data["message"]
    model_slug = message.get("metadata", {}).get("model_slug")
    tokenizer = get_tokenizer(model_slug)  # Get tokenizer based on this message's slug

    content = message.get("content", {})
    content_type = content.get("content_type")

    text_parts = []
    total_tokens = 0

    if content_type == "text":
        parts = content.get("parts", [])
        if parts:
            full_text = "".join(p for p in parts if isinstance(p, str))
            text_parts.append(full_text)
            total_tokens += count_tokens(full_text, tokenizer)

    elif content_type == "thoughts" and count_thoughts:
        thoughts = content.get("thoughts", [])
        for thought in thoughts:
            summary_label = thought.get("summary", "")
            thought_content_text = thought.get("content", "")

            if summary_label:
                total_tokens += count_tokens(summary_label, tokenizer)
                text_parts.append(f"[Thought Label]: {summary_label}")

            if thought_content_text:
                content_tokens = count_tokens(thought_content_text, tokenizer)
                total_tokens += content_tokens * THOUGHT_CONTENT_MULTIPLIER
                text_parts.append(
                    f"[Thought Content (x{THOUGHT_CONTENT_MULTIPLIER})]: {thought_content_text}"
                )

    elif content_type == "user_editable_context":
        # These typically set up the conversation but might not be "active" message parts for costing each turn.
        # For now, we'll count them as they contribute to the context.
        user_profile = content.get("user_profile", "")
        user_instructions = content.get("user_instructions", "")
        if user_profile:
            total_tokens += count_tokens(user_profile, tokenizer)
            text_parts.append(f"[User Profile]: {user_profile}")
        if user_instructions:
            total_tokens += count_tokens(user_instructions, tokenizer)
            text_parts.append(f"[User Instructions]: {user_instructions}")

    # Add other content_types if necessary

    # For role and author, also include if it's not empty or default
    author_role = message.get("author", {}).get("role")
    if author_role and author_role not in [
        "system",
        "user",
        "assistant",
    ]:  # if there's a custom role name
        # This is a simple way to account for role name tokens if they are custom/long.
        # Often role names are short and fixed, so their token count is negligible or part of model's internal prompting.
        # text_parts.append(f"[Author Role]: {author_role}")
        # total_tokens += count_tokens(author_role, tokenizer)
        pass

    return text_parts, total_tokens
