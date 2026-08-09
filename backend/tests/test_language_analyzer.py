import pytest

from app.analyzers.language_analyzer import LanguageAnalyzer


@pytest.fixture
def analyzer():
    return LanguageAnalyzer()


def test_empty_breakdown(analyzer):
    result = analyzer.analyze({})
    assert result["total_bytes"] == 0
    assert result["primary_language"] is None
    assert result["percentages"] == {}
    assert result["language_count"] == 0
    assert result["diversity_score"] == 0.0


def test_all_zero_bytes(analyzer):
    # edge case, repo exists but somehow reports 0 bytes for every language
    result = analyzer.analyze({"Python": 0, "JavaScript": 0})
    assert result["total_bytes"] == 0
    assert result["primary_language"] is None
    assert result["percentages"] == {}
    assert result["language_count"] == 2
    assert result["diversity_score"] == 0.0


def test_single_language(analyzer):
    # one language only, should be 100% and zero diversity
    result = analyzer.analyze({"Python": 1000})
    assert result["total_bytes"] == 1000
    assert result["primary_language"] == "Python"
    assert result["percentages"] == {"Python": 100.0}
    assert result["language_count"] == 1
    assert result["diversity_score"] == 0.0


def test_two_equal_languages(analyzer):
    result = analyzer.analyze({"Python": 500, "JavaScript": 500})
    assert result["total_bytes"] == 1000
    assert result["percentages"] == {"Python": 50.0, "JavaScript": 50.0}
    assert result["language_count"] == 2
    # HHI here is 0.5 + 0.5 squared = 0.5, so diversity is 0.5
    assert result["diversity_score"] == 0.5
    # tie on bytes, just make sure it picks one of them and doesn't blow up
    assert result["primary_language"] in ("Python", "JavaScript")


def test_primary_language_picks_the_biggest(analyzer):
    result = analyzer.analyze({"Python": 100, "JavaScript": 900, "HTML": 50})
    assert result["primary_language"] == "JavaScript"


def test_percentages_sum_to_roughly_100(analyzer):
    breakdown = {"Python": 333, "JavaScript": 333, "Go": 334}
    result = analyzer.analyze(breakdown)
    total_pct = sum(result["percentages"].values())
    # rounding means it won't be exact, but should be very close
    assert total_pct == pytest.approx(100.0, abs=0.1)


def test_percentages_rounded_to_two_decimals(analyzer):
    result = analyzer.analyze({"Python": 1, "JavaScript": 2})
    # 1/3 and 2/3 as percentages, want 2 decimal places not full float garbage
    assert result["percentages"]["Python"] == 33.33
    assert result["percentages"]["JavaScript"] == 66.67


def test_more_languages_means_more_diversity(analyzer):
    focused = analyzer.analyze({"Python": 900, "JavaScript": 100})
    spread_out = analyzer.analyze(
        {"Python": 250, "JavaScript": 250, "Go": 250, "Rust": 250}
    )
    assert spread_out["diversity_score"] > focused["diversity_score"]


def test_language_count_matches_input_keys(analyzer):
    breakdown = {"Python": 10, "JavaScript": 20, "Go": 30, "Rust": 40}
    result = analyzer.analyze(breakdown)
    assert result["language_count"] == len(breakdown)
