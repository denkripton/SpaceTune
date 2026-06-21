import pytest

from src.modules.music.utils.count_avg import count_avg


def test_count_avg_returns_zero_for_empty_list():
    assert count_avg([]) == 0


def test_count_avg_returns_exact_value_for_single_element():
    assert count_avg([7]) == 7


def test_count_avg_computes_mean_of_multiple_values():
    assert count_avg([8, 9, 10]) == 9.0


@pytest.mark.parametrize(
    ("grades", "expected"),
    [
        ([1, 2], 1.5),
        ([10, 10, 10], 10.0),
        ([1, 2, 3, 4], 2.5),
        ([5, 6, 7], 6.0),
    ],
)
def test_count_avg_parametrized_cases(grades, expected):
    assert count_avg(grades) == expected


def test_count_avg_rounds_to_one_decimal_place():
    assert count_avg([1, 2, 7]) == 3.3
