def get_post_description_from_str(
    description_str: str,
) -> dict:
    return {
        "content": [
            {"type": "paragraph", "children": [{"text": description_str}]},
        ]
    }
