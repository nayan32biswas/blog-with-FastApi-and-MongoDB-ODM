V1_URL = "/api/v1"


class Endpoints:
    # Auth endpoints
    TOKEN = f"{V1_URL}/token"
    REGISTRATION = f"{V1_URL}/registration"
    UPDATE_ACCESS_TOKEN = f"{V1_URL}/update-access-token"
    LOGOUT_FROM_ALL_DEVICES = f"{V1_URL}/logout-from-all-device"
    CHANGE_PASSWORD = f"{V1_URL}/change-password"

    # User endpoints
    ME = f"{V1_URL}/users/me"
    USER_PROFILE = f"{V1_URL}/users/details"
    USER_UPDATE = f"{V1_URL}/users/update"
    PUBLIC_PROFILE = f"{V1_URL}/users/{'{username}'}"

    # Topics endpoints
    TOPICS = f"{V1_URL}/topics"

    # Posts endpoints
    POSTS = f"{V1_URL}/posts"
    POSTS_DETAIL = f"{V1_URL}/posts/{'{slug}'}"

    # Comments endpoints
    COMMENTS = f"{V1_URL}/posts/{'{slug}'}/comments"
    COMMENTS_DETAIL = f"{V1_URL}/posts/{'{slug}'}/comments/{'{comment_id}'}"

    # Replies endpoints
    REPLIES = f"{V1_URL}/posts/{'{slug}'}/comments/{'{comment_id}'}/replies"
    REPLIES_DETAIL = (
        f"{V1_URL}/posts/{'{slug}'}/comments/{'{comment_id}'}/replies/{'{reply_id}'}"
    )

    # Reactions endpoints
    REACTIONS = f"{V1_URL}/posts/{'{slug}'}/reactions"
