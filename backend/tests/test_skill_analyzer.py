import pytest

from app.analyzers.skill_analyzer import SkillAnalyzer


@pytest.fixture
def analyzer():
    return SkillAnalyzer()


def test_empty_input(analyzer):
    result = analyzer.analyze({}, [])
    assert result["domains"] == []
    assert result["domain_shares"] == {}
    assert result["languages"] == []
    assert result["topics"] == []


def test_languages_detected_from_breakdown(analyzer):
    result = analyzer.analyze({"Python": 100, "JavaScript": 50}, [])
    assert result["languages"] == ["JavaScript", "Python"]


def test_domain_detected_from_language(analyzer):
    result = analyzer.analyze({"Python": 100}, [])
    assert "Backend" in result["domains"]


def test_domain_detected_from_topic_only(analyzer):
    # repo has a domain-relevant topic but no matching language bytes at all
    repos = [{"fork": False, "topics": ["machine-learning"]}]
    result = analyzer.analyze({}, repos)
    assert "Data & ML" in result["domains"]


def test_topics_ignored_from_forked_repos(analyzer):
    repos = [{"fork": True, "topics": ["kubernetes"]}]
    result = analyzer.analyze({}, repos)
    assert result["topics"] == []
    assert "DevOps & Cloud" not in result["domains"]


def test_topics_collected_from_owned_repos(analyzer):
    repos = [{"fork": False, "topics": ["react", "web"]}]
    result = analyzer.analyze({}, repos)
    assert result["topics"] == ["react", "web"]


def test_multiple_domains_detected(analyzer):
    result = analyzer.analyze({"Python": 500, "Rust": 200, "TypeScript": 300}, [])
    assert result["domains"] == ["Backend", "Frontend", "Systems & Core"]


def test_domain_share_calculation(analyzer):
    breakdown = {"Python": 750, "JavaScript": 250}
    result = analyzer.analyze(breakdown, [])
    assert result["domain_shares"]["Backend"] == 75.0
    assert result["domain_shares"]["Frontend"] == 25.0


def test_domain_from_topic_gets_zero_share_when_no_bytes(analyzer):
    # domain shows up because of the topic, but has nothing to back it byte-wise
    repos = [{"fork": False, "topics": ["data-science"]}]
    result = analyzer.analyze({"Python": 100}, repos)
    assert "Data & ML" in result["domains"]
    assert result["domain_shares"]["Data & ML"] == 0.0
    # Backend still gets its real share from the Python bytes
    assert result["domain_shares"]["Backend"] == 100.0


def test_unmapped_language_produces_no_domain(analyzer):
    # a language that isn't in any DOMAIN_MAPPING bucket
    result = analyzer.analyze({"COBOL": 100}, [])
    assert result["domains"] == []
    assert result["domain_shares"] == {}
    assert result["languages"] == ["COBOL"]


def test_case_insensitive_matching(analyzer):
    # github sometimes returns language names capitalized differently
    result = analyzer.analyze({"PYTHON": 100}, [])
    assert "Backend" in result["domains"]


def test_topics_deduplicated_across_repos(analyzer):
    repos = [
        {"fork": False, "topics": ["react"]},
        {"fork": False, "topics": ["react", "typescript"]},
    ]
    result = analyzer.analyze({}, repos)
    assert result["topics"] == ["react", "typescript"]
