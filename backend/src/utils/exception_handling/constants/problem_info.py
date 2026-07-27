STATUS_PROBLEM_INFO: dict[int, tuple[str, str]] = {
    400: ("bad-request", "Bad Request"),
    401: ("unauthorized", "Unauthorized"),
    403: ("forbidden", "Forbidden"),
    404: ("not-found", "Not Found"),
    409: ("conflict", "Conflict"),
    422: ("unprocessable-entity", "Unprocessable Entity"),
    500: ("internal-server-error", "Internal Server Error"),
    502: ("bad-gateway", "Bad Gateway"),
}

DEFAULT_PROBLEM_INFO: tuple[str, str] = ("error", "Error")
