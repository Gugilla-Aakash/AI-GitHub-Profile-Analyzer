from unittest.mock import patch

from app.tasks import (
    _exact_repositories,
    _extract_recent_items,
    analyze_profile_task,
)


class TestExactRepositories:
    def test_returns_empty_list_for_empty_input(self):
        assert _exact_repositories([]) == []

    def test_sorts_by_updated_at_or_pushed_at(self):
        repos = [
            {"name": "repo1", "updated_at": "2023-01-01T00:00:00Z"},
            {"name": "repo2", "pushed_at": "2023-02-01T00:00:00Z"},  # Most recent
            {"name": "repo3"},  # No date, goes last
        ]
        result = _exact_repositories(repos)

        assert len(result) == 3
        assert result[0]["name"] == "repo2"
        assert result[1]["name"] == "repo1"
        assert result[2]["name"] == "repo3"
        assert result[2]["updated_at"] == "unknown"

    def test_truncates_to_repos_limit(self):
        # Assuming REPOS_LIMIT = 15 from tasks.py
        repos = [
            {"name": f"repo{i}", "updated_at": f"2023-01-{i:02d}T00:00:00Z"}
            for i in range(20)
        ]
        result = _exact_repositories(repos)

        assert len(result) == 15

    def test_maps_dictionary_keys_correctly(self):
        repos = [
            {
                "name": "octo-repo",
                "description": "A cool repo",
                "stargazers_count": 42,
                "forks_count": 7,
                "language": "Python",
                "fork": True,
                "updated_at": "2023-01-01T00:00:00Z",
            }
        ]
        result = _exact_repositories(repos)[0]

        assert result["name"] == "octo-repo"
        assert result["description"] == "A cool repo"
        assert result["stars"] == 42
        assert result["forks"] == 7
        assert result["language"] == "Python"
        assert result["is_fork"] is True
        assert result["updated_at"] == "2023-01-01T00:00:00Z"


class TestExtractRecentItems:
    def test_returns_empty_structure_if_empty(self):
        expected = {"pull_requests": [], "issues": []}
        assert _extract_recent_items({}) == expected

    def test_extracts_repo_name_from_nested_repository_object(self):
        data = {
            "pull_requests": {
                "recent_items": [
                    {"title": "Fix bug", "repository": {"name": "octocat/hello-world"}}
                ]
            }
        }
        result = _extract_recent_items(data)
        assert result["pull_requests"][0]["repo"] == "octocat/hello-world"

    def test_extracts_repo_name_from_url_if_repository_object_missing(self):
        data = {
            "issues": {
                "recent_items": [
                    {
                        "title": "Bug found",
                        "url": "https://github.com/octocat/Spoon-Knife/issues/1",
                    }
                ]
            }
        }
        result = _extract_recent_items(data)
        # URL parsing splits at "/" -> parts[4] is the repo name
        assert result["issues"][0]["repo"] == "Spoon-Knife"

    def test_falls_back_to_unknown_repo_if_url_is_invalid(self):
        data = {
            "issues": {"recent_items": [{"title": "Weird Bug", "url": "invalid-url"}]}
        }
        result = _extract_recent_items(data)
        assert result["issues"][0]["repo"] == "unknown repo"

    def test_truncates_to_recent_items_limit(self):
        # Assuming RECENT_ITEMS_LIMIT = 5 from tasks.py
        data = {
            "pull_requests": {"recent_items": [{"title": f"PR {i}"} for i in range(10)]}
        }
        result = _extract_recent_items(data)
        assert len(result["pull_requests"]) == 5


class TestAnalyzeProfileTask:
    @patch("app.tasks.cache")
    @patch("app.tasks.ProfileScorer")
    @patch("app.tasks.ActivityAnalyzer")
    @patch("app.tasks.SkillAnalyzer")
    @patch("app.tasks.ImpactAnalyzer")
    @patch("app.tasks.LanguageAnalyzer")
    @patch("app.tasks.GitHubClient")
    def test_orchestrates_data_fetching_and_scoring(
        self,
        mock_github_client_cls,
        mock_lang_analyzer_cls,
        mock_impact_analyzer_cls,
        mock_skill_analyzer_cls,
        mock_activity_analyzer_cls,
        mock_scorer_cls,
        mock_cache,
    ):
        # Setup GitHub Client mock
        mock_gh = mock_github_client_cls.return_value
        mock_gh.fetch_full_profile_data.return_value = {
            "repositories": {"items": [{"name": "repo1"}], "language_breakdown": {}},
            "recent_contributions_365_days": {},
            "lifetime_activity": {},
            "readme_statuses": {"repo1": True},
        }

        # Setup Analyzer mocks
        mock_lang_analyzer_cls.return_value.analyze.return_value = {"lang_data": True}
        mock_impact_analyzer_cls.return_value.analyze.return_value = {
            "impact_data": True
        }
        mock_skill_analyzer_cls.return_value.analyze.return_value = {"skill_data": True}
        mock_activity_analyzer_cls.return_value.analyze.return_value = {
            "act_data": True
        }

        # Setup Scorer mock
        mock_scorer = mock_scorer_cls.return_value
        mock_scorer.calculate_score.return_value = {"final_score": 95, "grade": "S"}

        # Execute
        result = analyze_profile_task("octocat")

        # Assertions
        mock_gh.fetch_full_profile_data.assert_called_once_with("octocat")
        mock_scorer.calculate_score.assert_called_once_with(
            {"lang_data": True},
            {"impact_data": True},
            {"skill_data": True},
            {"act_data": True},
        )

        # Verify result compilation
        assert result["username"] == "octocat"
        assert result["final_score"] == 95
        assert result["grade"] == "S"
        assert result["language"] == {"lang_data": True}
        assert result["readme_status"] == {"repo1": True}

        # Verify caching
        mock_cache.set_profile.assert_called_once_with("octocat", result)
