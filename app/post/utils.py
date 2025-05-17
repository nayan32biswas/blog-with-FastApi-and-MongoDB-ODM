from typing import Any


def get_post_description_from_str(
    description_str: str,
) -> dict[Any, Any]:
    return {
        "content": [
            {"type": "paragraph", "children": [{"text": description_str}]},
        ]
    }
