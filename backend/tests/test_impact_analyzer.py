import pytest

from app.analyzers.impact_analyzer import ImpactAnalyzer


@pytest.fixture
def analyzer():
    return ImpactAnalyzer()


def test_empty_repo_list(analyzer):
    result = analyzer.analyze([])
    assert result["total_stars"] == 0
    assert result["total_forks"] == 0
    assert result["owned_repo_count"] == 0
    assert result["forked_repo_count"] == 0
    assert result["hero_repo"] is None


def test_only_owned_repos(analyzer):
    repos = [
        {"name": "repo-a", "fork": False, "stargazers_count": 10, "forks_count": 2},
        {"name": "repo-b", "fork": False, "stargazers_count": 5, "forks_count": 1},
    ]
    result = analyzer.analyze(repos)
    assert result["total_stars"] == 15
    assert result["total_forks"] == 3
    assert result["owned_repo_count"] == 2
    assert result["forked_repo_count"] == 0


def test_forked_repos_excluded_from_totals(analyzer):
    # forked repo has huge star count but shouldn't count towards user's own totals
    repos = [
        {"name": "my-repo", "fork": False, "stargazers_count": 5, "forks_count": 0},
        {
            "name": "someone-elses-repo",
            "fork": True,
            "stargazers_count": 5000,
            "forks_count": 100,
        },
    ]
    result = analyzer.analyze(repos)
    assert result["total_stars"] == 5
    assert result["total_forks"] == 0
    assert result["owned_repo_count"] == 1
    assert result["forked_repo_count"] == 1


def test_hero_repo_is_highest_starred(analyzer):
    repos = [
        {"name": "small", "fork": False, "stargazers_count": 3},
        {"name": "big", "fork": False, "stargazers_count": 300},
        {"name": "medium", "fork": False, "stargazers_count": 50},
    ]
    result = analyzer.analyze(repos)
    assert result["hero_repo"] == {"name": "big", "stars": 300}


def test_hero_repo_none_when_all_zero_stars(analyzer):
    repos = [
        {"name": "repo-a", "fork": False, "stargazers_count": 0},
        {"name": "repo-b", "fork": False, "stargazers_count": 0},
    ]
    result = analyzer.analyze(repos)
    assert result["hero_repo"] is None


def test_hero_repo_none_when_only_forks(analyzer):
    repos = [
        {"name": "forked-repo", "fork": True, "stargazers_count": 999},
    ]
    result = analyzer.analyze(repos)
    assert result["hero_repo"] is None
    assert result["owned_repo_count"] == 0
    assert result["forked_repo_count"] == 1


def test_missing_fields_default_safely(analyzer):
    # repo dicts missing keys entirely shouldn't blow up
    repos = [{"name": "bare-repo"}]
    result = analyzer.analyze(repos)
    assert result["total_stars"] == 0
    assert result["total_forks"] == 0
    assert result["owned_repo_count"] == 1
    assert result["hero_repo"] is None


def test_mixed_owned_and_forked(analyzer):
    repos = [
        {"name": "owned-1", "fork": False, "stargazers_count": 20, "forks_count": 4},
        {"name": "fork-1", "fork": True, "stargazers_count": 100, "forks_count": 10},
        {"name": "owned-2", "fork": False, "stargazers_count": 60, "forks_count": 2},
    ]
    result = analyzer.analyze(repos)
    assert result["total_stars"] == 80
    assert result["total_forks"] == 6
    assert result["owned_repo_count"] == 2
    assert result["forked_repo_count"] == 1
    assert result["hero_repo"] == {"name": "owned-2", "stars": 60}
