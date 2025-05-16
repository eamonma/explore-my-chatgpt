"""Functions for determining message order in conversations."""


def get_message_chronological_order(conversation_mapping):
    """
    Orders messages in a conversation chronologically using the parent/children links.
    Returns a list of message IDs in order.
    """
    if not conversation_mapping:
        return []

    # Find the root message (no parent or parent is 'client-created-root')
    root_id = None
    # Try to find 'client-created-root' first
    if "client-created-root" in conversation_mapping:
        root_id = "client-created-root"
    else:  # Fallback: find a message with no parent or a non-existent parent
        all_ids = set(conversation_mapping.keys())
        child_ids_with_valid_parents = set()
        for msg_id, msg_data in conversation_mapping.items():
            parent_id = msg_data.get("parent")
            if parent_id and parent_id in all_ids:
                child_ids_with_valid_parents.add(msg_id)

        possible_roots = list(all_ids - child_ids_with_valid_parents)
        if not possible_roots:
            return []  # Should not happen in valid data
        # Prefer a root that is not a typical message guid if multiple roots found without client-created-root
        non_guid_roots = [
            r for r in possible_roots if not (len(r) == 36 and r.count("-") == 4)
        ]
        if non_guid_roots:
            root_id = non_guid_roots[0]
        elif possible_roots:
            root_id = possible_roots[0]  # Pick one if all are GUID like
        else:
            return []

    ordered_message_ids = []

    current_id = root_id
    visited_for_children_expansion = set()

    # Traverse using a queue for breadth-first like expansion based on children
    # More robustly, a depth-first traversal from the root following the primary child link
    # The structure is a tree, so direct DFS from the root is usually how it's structured.

    # Let's use the create_time on messages if available, as a primary sort key within the mapping,
    # then fall back to tree traversal if times are missing or inconsistent.
    # The sample data shows some messages (system) have null create_time.
    # Tree traversal seems more robust.

    # Start with the root's first child if root is 'client-created-root' and it's just a container
    if root_id == "client-created-root" and conversation_mapping.get(root_id, {}).get(
        "children"
    ):
        # If client-created-root has multiple children, this might be tricky,
        # but typically it points to the start of the actual message chain.
        current_id = conversation_mapping[root_id]["children"][0]

    # Iterative DFS based on the 'children' array (assuming first child is the main path)
    # This assumes a linear conversation flow for the main turn-by-turn.
    # Parallel branches (multiple children) could represent alternative generation paths.
    # For this analysis, we typically follow the main accepted path.

    # We must process the actual root if it's a message, then its child.
    # If root_id is 'client-created-root', its message is null, so we start with its child.
    # Otherwise, the found root_id is the first message.

    # Let's refine the starting point
    if root_id == "client-created-root":
        children_of_root = conversation_mapping.get(root_id, {}).get("children", [])
        if not children_of_root:
            return []  # No messages after the dummy root
        # Assuming the first child of client-created-root is the actual first message node
        # This might need adjustment if there can be multiple starting branches from client-created-root
        current_id = children_of_root[0]
    else:  # The root_id itself is the first message node
        # Add the root itself if it's a message and not just a placeholder
        if conversation_mapping.get(current_id, {}).get("message"):
            ordered_message_ids.append(current_id)
        # And then prepare to process its children

    # Iteratively follow the first child to reconstruct the main conversation thread
    # This assumes that the conversation is primarily linear, and 'children[0]' represents the next message in sequence.

    visited_ids = (
        set()
    )  # To handle potential cycles or reprocessing, though not expected in clean data

    # If the current_id (derived root or its first child) has a message, add it.
    if current_id not in ordered_message_ids and conversation_mapping.get(
        current_id, {}
    ).get("message"):
        ordered_message_ids.append(current_id)
        visited_ids.add(current_id)

    while current_id:
        msg_node = conversation_mapping.get(current_id)
        if not msg_node:
            break  # Should not happen

        children = msg_node.get("children", [])
        if children:
            # We assume the first child is the continuation of the main conversation
            next_id = children[0]
            if next_id in visited_ids:
                break  # Cycle detected or already processed this path

            if conversation_mapping.get(next_id, {}).get(
                "message"
            ):  # Only add if it's a message node
                ordered_message_ids.append(next_id)

            visited_ids.add(next_id)
            current_id = next_id
        else:
            current_id = None  # End of this branch

    return ordered_message_ids
