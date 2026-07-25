from src.utils.exception_handling.constants import (
    DEFAULT_PROBLEM_INFO,
    PROBLEM_TYPE_BASE,
    STATUS_PROBLEM_INFO,
)


def build_problem(status_code: int, detail: str, instance: str | None = None) -> dict:
    slug, title = STATUS_PROBLEM_INFO.get(status_code, DEFAULT_PROBLEM_INFO)
    problem = {
        "type": f"{PROBLEM_TYPE_BASE}/{slug}",
        "title": title,
        "status": status_code,
        "detail": detail,
    }
    if instance is not None:
        problem["instance"] = instance
    return problem
