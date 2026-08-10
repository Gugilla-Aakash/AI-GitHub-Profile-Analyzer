import pytest

from app.analyzers.scorer import ProfileScorer


@pytest.fixture
def scorer():
    return ProfileScorer()


def test_insufficient_data_when_no_languages_and_no_activity(scorer):
    result = scorer.calculate_score(
        {"diversity_score": 0.0, "total_bytes": 0},
        {"total_stars": 0, "total_forks": 0},
        {"languages": [], "domain_shares": {}},
        {"total_contributions_365": 0, "lifetime_prs": 0, "lifetime_issues": 0},
    )
    assert result["insufficient_data"] is True
    assert result["final_score"] == 0
    assert result["grade"] == "N/A"


def test_has_languages_but_no_activity_still_scores(scorer):
    # user has code on github but hasn't committed in the last year, should still get scored
    result = scorer.calculate_score(
        {"diversity_score": 0.5, "total_bytes": 100_000},
        {"total_stars": 0, "total_forks": 0},
        {"languages": ["Python"], "domain_shares": {"Backend": 100.0}},
        {"total_contributions_365": 0, "lifetime_prs": 0, "lifetime_issues": 0},
    )
    assert result["insufficient_data"] is False


def test_has_activity_but_no_languages_still_scores(scorer):
    result = scorer.calculate_score(
        {"diversity_score": 0.0, "total_bytes": 0},
        {"total_stars": 0, "total_forks": 0},
        {"languages": [], "domain_shares": {}},
        {"total_contributions_365": 50, "lifetime_prs": 0, "lifetime_issues": 0},
    )
    assert result["insufficient_data"] is False


def test_grade_boundaries(scorer):
    assert scorer._calculate_grade(90) == "S"
    assert scorer._calculate_grade(89) == "A"
    assert scorer._calculate_grade(75) == "A"
    assert scorer._calculate_grade(74) == "B"
    assert scorer._calculate_grade(60) == "B"
    assert scorer._calculate_grade(59) == "C"
    assert scorer._calculate_grade(40) == "C"
    assert scorer._calculate_grade(39) == "D"
    assert scorer._calculate_grade(0) == "D"


def test_clamp_never_exceeds_100(scorer):
    assert scorer._clamp(500.0) == 100.0
    assert scorer._clamp(50.0) == 50.0


def test_full_profile_high_scores_across_the_board(scorer):
    # a maxed out profile should push towards S grade
    result = scorer.calculate_score(
        {"diversity_score": 0.8, "total_bytes": 600_000},
        {"total_stars": 5000, "total_forks": 1000},
        {"languages": ["Python", "Go"], "domain_shares": {"Backend": 100.0}},
        {"total_contributions_365": 1500, "lifetime_prs": 500, "lifetime_issues": 500},
    )
    assert result["final_score"] >= 90
    assert result["grade"] == "S"


def test_activity_safety_floor_for_high_volume(scorer):
    # 1000+ recent contributions should floor activity score at 90 regardless of lifetime prs/issues
    result = scorer.calculate_score(
        {"diversity_score": 0.0, "total_bytes": 0},
        {"total_stars": 0, "total_forks": 0},
        {"languages": ["Python"], "domain_shares": {}},
        {"total_contributions_365": 1000, "lifetime_prs": 0, "lifetime_issues": 0},
    )
    assert result["breakdown"]["activity"] >= 90


def test_life_score_scales_with_lifetime_prs_and_issues(scorer):
    # zero lifetime prs/issues should not give a maxed out activity score anymore
    low = scorer.calculate_score(
        {"diversity_score": 0.0, "total_bytes": 0},
        {"total_stars": 0, "total_forks": 0},
        {"languages": ["Python"], "domain_shares": {}},
        {"total_contributions_365": 100, "lifetime_prs": 0, "lifetime_issues": 0},
    )
    high = scorer.calculate_score(
        {"diversity_score": 0.0, "total_bytes": 0},
        {"total_stars": 0, "total_forks": 0},
        {"languages": ["Python"], "domain_shares": {}},
        {"total_contributions_365": 100, "lifetime_prs": 400, "lifetime_issues": 200},
    )
    assert high["breakdown"]["activity"] > low["breakdown"]["activity"]


def test_volume_gate_suppresses_skill_and_lang_score_for_tiny_repos(scorer):
    # barely any bytes written, so skill/lang scores should get scaled way down
    result = scorer.calculate_score(
        {"diversity_score": 0.8, "total_bytes": 100},
        {"total_stars": 0, "total_forks": 0},
        {"languages": ["Python"], "domain_shares": {"Backend": 100.0}},
        {"total_contributions_365": 50, "lifetime_prs": 0, "lifetime_issues": 0},
    )
    # with basically zero bytes, the multiplier crushes these towards 0
    assert result["breakdown"]["skill"] < 5
    assert result["breakdown"]["language_diversity"] < 5


def test_volume_gate_full_effect_at_500kb(scorer):
    # at or above 500,000 bytes the multiplier should be 1.0, no suppression
    result = scorer.calculate_score(
        {"diversity_score": 0.8, "total_bytes": 500_000},
        {"total_stars": 0, "total_forks": 0},
        {"languages": ["Python"], "domain_shares": {"Backend": 15.0}},
        {"total_contributions_365": 50, "lifetime_prs": 0, "lifetime_issues": 0},
    )
    # domain share of 15 should map to full 33.33 points, undiluted by volume multiplier
    assert result["breakdown"]["skill"] == pytest.approx(33, abs=1)


def test_mastery_bypass_lets_impact_carry_skill_and_lang(scorer):
    # huge impact but no code bytes at all, skill/lang scores should get bumped
    # up to match impact instead of staying near zero
    result = scorer.calculate_score(
        {"diversity_score": 0.0, "total_bytes": 0},
        {"total_stars": 5000, "total_forks": 1000},
        {"languages": ["Python"], "domain_shares": {}},
        {"total_contributions_365": 50, "lifetime_prs": 0, "lifetime_issues": 0},
    )
    assert result["breakdown"]["skill"] == result["breakdown"]["impact"]
    assert result["breakdown"]["language_diversity"] == result["breakdown"]["impact"]


def test_domain_share_points_cap_at_33_per_domain(scorer):
    # a domain share way above 15% shouldn't give more than 33.33 points for that domain
    result = scorer.calculate_score(
        {"diversity_score": 0.0, "total_bytes": 500_000},
        {"total_stars": 0, "total_forks": 0},
        {"languages": ["Python"], "domain_shares": {"Backend": 90.0}},
        {"total_contributions_365": 50, "lifetime_prs": 0, "lifetime_issues": 0},
    )
    assert result["breakdown"]["skill"] <= 34
