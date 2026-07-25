from src.utils.exception_handling import build_problem


def test_build_problem_uses_mapped_type_and_title_for_known_status():
    problem = build_problem(status_code=409, detail="Track already exists")

    assert problem["type"] == "https://spacetune.dev/errors/conflict"
    assert problem["title"] == "Conflict"
    assert problem["status"] == 409
    assert problem["detail"] == "Track already exists"


def test_build_problem_falls_back_to_generic_type_for_unmapped_status():
    problem = build_problem(status_code=418, detail="I'm a teapot")

    assert problem["type"] == "https://spacetune.dev/errors/error"
    assert problem["title"] == "Error"
    assert problem["status"] == 418


def test_build_problem_omits_instance_when_not_provided():
    problem = build_problem(status_code=404, detail="Not found")

    assert "instance" not in problem


def test_build_problem_includes_instance_when_provided():
    problem = build_problem(
        status_code=404, detail="Not found", instance="/music/track/123"
    )

    assert problem["instance"] == "/music/track/123"
