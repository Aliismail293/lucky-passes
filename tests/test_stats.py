import pytest

from lp import stats


def test_bootstrap_constant_data_has_zero_width():
    ci = stats.bootstrap_ci([1] * 50, resamples=200, seed=1)
    assert ci == {"value": 1.0, "lo": 1.0, "hi": 1.0, "n": 50}


def test_bootstrap_half_and_half():
    ci = stats.bootstrap_ci([1, 0] * 50, resamples=1000, seed=1)
    assert ci["value"] == 0.5
    # Normal approximation: 1.96 * sqrt(0.25 / 100) = 0.098, so the interval is about 0.40 to 0.60.
    assert 0.38 <= ci["lo"] <= 0.42 and 0.58 <= ci["hi"] <= 0.62


def test_bootstrap_is_reproducible_with_a_seed():
    data = [1, 0, 0, 1, 1, 1, 0]
    assert stats.bootstrap_ci(data, seed=7) == stats.bootstrap_ci(data, seed=7)


def test_empty_input():
    assert stats.bootstrap_ci([])["value"] is None


def test_ratio_ci():
    ci = stats.bootstrap_ratio_ci([1, 1, 0, 0], [1, 1, 1, 1], resamples=500, seed=3)
    assert ci["value"] == 0.5 and ci["n"] == 4


def test_paired_diff():
    ci = stats.paired_bootstrap_diff([1, 1, 1, 1], [0, 0, 1, 1], resamples=200, seed=1)
    assert ci["value"] == 0.5


def test_mcnemar_known_value():
    # 10 flips one way, 2 the other: exact two-sided p = 2 * P(X <= 2), X ~ Binomial(12, 1/2) = 0.0386
    a = [False] * 10 + [True] * 2 + [True] * 5
    b = [True] * 10 + [False] * 2 + [True] * 5
    result = stats.mcnemar(a, b)
    assert (result["b01"], result["b10"]) == (10, 2)
    assert result["p"] == pytest.approx(0.0386, abs=1e-4)


def test_mcnemar_no_flips():
    assert stats.mcnemar([True, False], [True, False])["p"] == 1.0


def test_clopper_pearson_known_values():
    zero = stats.clopper_pearson(0, 150)
    assert zero["lo"] == 0.0 and abs(zero["hi"] - 0.0243) < 1e-3
    mid = stats.clopper_pearson(3, 76)
    assert abs(mid["lo"] - 0.0082) < 1e-3 and abs(mid["hi"] - 0.1111) < 1e-3
    assert stats.clopper_pearson(48, 48)["hi"] == 1.0
    assert stats.clopper_pearson(0, 0)["value"] is None


def test_holm_adjusts_in_input_order():
    assert stats.holm([0.01, 0.04, 0.03, 0.5]) == [0.04, 0.09, 0.09, 0.5]
