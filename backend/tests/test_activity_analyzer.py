import pytest
from app.analyzers.activity_analyzer import ActivityAnalyzer


@pytest.fixture
def analyzer():
    return ActivityAnalyzer()


def test_total_contributions_from_root_key(analyzer):
    result = analyzer.analyze(
        {
            "totalContributions": 400,
            "totalIssueContributions": 10,
            "totalPullRequestContributions": 20,
        },
        {},
    )
    assert result["total_contributions_365"] == 400


def test_total_contributions_from_snake_case_key(analyzer):
    # some callers pass snake_case instead of the github camelCase style
    result = analyzer.analyze({"total_contributions": 150}, {})
    assert result["total_contributions_365"] == 150


def test_total_contributions_from_nested_calendar(analyzer):
    result = analyzer.analyze({"contributionCalendar": {"totalContributions": 600}}, {})
    assert result["total_contributions_365"] == 600


def test_falls_back_to_summing_weeks_when_total_missing(analyzer):
    data = {
        "weeks": [
            {"contributionDays": [{"contributionCount": 3}, {"contributionCount": 2}]},
            {"contributionDays": [{"contributionCount": 5}]},
        ]
    }
    result = analyzer.analyze(data, {})
    assert result["total_contributions_365"] == 10


def test_falls_back_to_nested_weeks_when_root_weeks_missing(analyzer):
    # totalContributions absent, weeks live inside contributionCalendar instead
    data = {
        "contributionCalendar": {
            "weeks": [
                {"contributionDays": [{"contributionCount": 7}]},
            ]
        }
    }
    result = analyzer.analyze(data, {})
    assert result["total_contributions_365"] == 7


def test_no_contributions_at_all(analyzer):
    result = analyzer.analyze({}, {})
    assert result["total_contributions_365"] == 0
    assert result["collaboration_ratio_365"] == 0.0
    assert result["activity_tier"] == "Inactive"


def test_collaboration_ratio_calculation(analyzer):
    data = {
        "totalContributions": 100,
        "totalIssueContributions": 10,
        "totalPullRequestContributions": 20,
    }
    result = analyzer.analyze(data, {})
    # 30 out of 100 contributions were issues/prs
    assert result["collaboration_ratio_365"] == 30.0


def test_activity_tier_inactive(analyzer):
    result = analyzer.analyze({"totalContributions": 50}, {})
    assert result["activity_tier"] == "Inactive"


def test_activity_tier_casual(analyzer):
    result = analyzer.analyze({"totalContributions": 250}, {})
    assert result["activity_tier"] == "Casual"


def test_activity_tier_active(analyzer):
    result = analyzer.analyze({"totalContributions": 1000}, {})
    assert result["activity_tier"] == "Active"


def test_activity_tier_prolific(analyzer):
    result = analyzer.analyze({"totalContributions": 1001}, {})
    assert result["activity_tier"] == "Prolific"


def test_lifetime_metrics_pulled_correctly(analyzer):
    lifetime = {
        "pull_requests": {"total_count": 42},
        "issues": {"total_count": 17},
    }
    result = analyzer.analyze({"totalContributions": 10}, lifetime)
    assert result["lifetime_prs"] == 42
    assert result["lifetime_issues"] == 17


def test_lifetime_metrics_default_to_zero_when_missing(analyzer):
    result = analyzer.analyze({"totalContributions": 10}, {})
    assert result["lifetime_prs"] == 0
    assert result["lifetime_issues"] == 0
