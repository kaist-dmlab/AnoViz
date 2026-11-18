"""Regression tests for the evaluator's reconstruction scoring modes."""
import numpy as np
import pytest

from server.utils.evaluator import _compute_anomaly_scores, evaluate, set_thresholds


@pytest.fixture
def windows():
    # Strong residuals make the mean and median differ in every window.
    x = np.array([[[-1, 1, 4], [2, -2, 5]], [[0, 2, -4], [-1, 3, 3]]])
    labels = np.array([[0, 1], [0, 0]])
    return x, labels


SCORES = [
    pytest.param("square_mean", [[6, 11], [20 / 3, 19 / 3]], [6, 8.5, 11], id="mean"),
    pytest.param("square_median", [[1, 4], [4, 9]], [1, 5, 9], id="median"),
    pytest.param("absolute", [[2, 3], [2, 7 / 3]], [2, 2.5, 3], id="absolute"),
]


def assert_result_matches_precomputed(result, x, labels, thresholds, errors):
    expected = evaluate(thresholds, x, np.array(errors), labels, is_reconstructed=False)
    np.testing.assert_allclose(result["rec_errors"], errors)
    for name in ("precision", "recall", "f1", "pr_auc", "roc_auc", "thresholds"):
        np.testing.assert_allclose(result[name], expected[name])


@pytest.mark.parametrize("mode,errors,thresholds", SCORES)
def test_scoring_formulas(windows, mode, errors, thresholds):
    x, _ = windows
    np.testing.assert_allclose(_compute_anomaly_scores(x, np.zeros_like(x), scoring=mode), errors)


@pytest.mark.parametrize("mode,errors,thresholds", SCORES)
def test_thresholds_follow_requested_mode(windows, mode, errors, thresholds):
    x, _ = windows
    actual = set_thresholds(x, np.zeros_like(x), n=2, scoring=mode)
    np.testing.assert_allclose(actual, thresholds)


@pytest.mark.parametrize("mode,errors,thresholds", SCORES)
def test_evaluation_follows_requested_mode(windows, mode, errors, thresholds):
    x, labels = windows
    # Supply correct thresholds independently so a threshold bug cannot mask
    # a scoring error in evaluate().
    result = evaluate(thresholds, x, np.zeros_like(x), labels, scoring=mode)
    assert_result_matches_precomputed(result, x, labels, thresholds, errors)


def test_default_matches_explicit_mean_and_existing_metrics(windows):
    x, labels = windows
    rec_x = np.zeros_like(x)
    thresholds = set_thresholds(x, rec_x, n=2)
    np.testing.assert_allclose(thresholds, [6, 8.5, 11])
    np.testing.assert_array_equal(thresholds, set_thresholds(x, rec_x, n=2, scoring="square_mean"))
    default = evaluate(thresholds, x, rec_x, labels)
    explicit = evaluate(thresholds, x, rec_x, labels, scoring="square_mean")
    for name in default:
        np.testing.assert_array_equal(default[name], explicit[name])
    np.testing.assert_allclose(default["rec_errors"], [[6, 11], [20 / 3, 19 / 3]])
    np.testing.assert_allclose(default["precision"], [0.5, 1, 0])
    np.testing.assert_allclose(default["recall"], [1, 1, 0])
    assert default["pr_auc"] == pytest.approx(0.5)
    assert default["roc_auc"] == pytest.approx(1)


@pytest.mark.parametrize(
    "mode,errors,thresholds",
    [
        ("square_mean", [[10, 55 / 3], [100 / 9, 95 / 9]], [10, 85 / 6, 55 / 3]),
        ("square_median", [[1, 4], [4, 9]], [1, 5, 9]),
    ],
)
def test_detector_style_multiple_reconstruction_outputs(windows, mode, errors, thresholds):
    x, labels = windows
    # As in detector.py's MS-RNN call, each output has shape
    # (windows, time steps, channels), and the list adds a leading axis.
    reconstructions = [np.zeros_like(x), x, -x]
    actual_thresholds = set_thresholds(x, reconstructions, n=2, scoring=mode)
    np.testing.assert_allclose(actual_thresholds, thresholds)
    result = evaluate(thresholds, x, reconstructions, labels, scoring=mode)
    assert_result_matches_precomputed(result, x, labels, thresholds, errors)


def test_precomputed_scores_bypass_reconstruction_scoring(windows):
    x, labels = windows
    errors = np.array([[1., 4.], [4., 9.]])
    thresholds = set_thresholds(x, errors, n=2, scoring="absolute", is_reconstructed=False)
    np.testing.assert_allclose(thresholds, [1, 5, 9])
    result = evaluate(thresholds, x, errors, labels, scoring="absolute", is_reconstructed=False)
    np.testing.assert_array_equal(result["rec_errors"], errors)
