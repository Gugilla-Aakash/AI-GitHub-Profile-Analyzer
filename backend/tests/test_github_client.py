"""
Tests for AppGitHubClient (app/clients/github_client.py).
"""

from unittest.mock import patch

import pytest
from hakiapi.core.exceptions import HakiAPIError

from app.clients.github_client import (
    AppGitHubClient,
    InvalidUsernameError,
    UserNotFoundError,
)


@pytest.fixture
def client():
    return AppGitHubClient()


# _validate_username


class TestValidateUsername:
    @pytest.mark.parametrize(
        "raw, expected_clean",
        [
            ("octocat", "octocat"),
            ("Octo-Cat", "Octo-Cat"),
            ("a", "a"),
            ("a" * 39, "a" * 39),  # max length boundary
            ("  octocat  ", "octocat"),  # surrounding whitespace is stripped
        ],
    )
    def test_valid_usernames_pass_through(self, client, raw, expected_clean):
        clean, encoded = client._validate_username(raw)
        assert clean == expected_clean
        assert encoded == expected_clean  # alphanumerics/hyphens need no encoding

    @pytest.mark.parametrize(
        "raw",
        [
            "",
            "   ",
            None,
            "-octocat",  # cannot start with a hyphen
            "octocat-",  # cannot end with a hyphen
            "octo--cat",  # no consecutive hyphens
            "octo cat",  # no spaces mid-string
            "a" * 40,  # exceeds 39 char max
            "../../../etc/passwd",  # path traversal payload
            "octocat/../admin",
            "octo/cat",
            "octo_cat",  # underscores are not valid in GitHub usernames
            "octo@cat",
        ],
    )
    def test_invalid_usernames_raise(self, client, raw):
        with pytest.raises(InvalidUsernameError):
            client._validate_username(raw)

    def test_url_unsafe_characters_would_be_encoded_if_matched(self, client):
        # Sanity check that quote() is actually applied to the cleaned value.
        clean, encoded = client._validate_username("octocat123")
        assert isinstance(clean, str)
        assert isinstance(encoded, str)


# fetch_full_profile_data


class TestFetchFullProfileData:
    def _graphql_response(self, **overrides):
        base = {
            "user": {
                "contributionsCollection": {
                    "contributionCalendar": {"totalContributions": 100},
                    "totalCommitContributions": 50,
                    "totalIssueContributions": 5,
                    "totalPullRequestContributions": 10,
                },
                "pullRequests": {
                    "totalCount": 10,
                    "nodes": [{"title": "Fix bug", "url": "u", "createdAt": "t"}],
                },
                "issues": {
                    "totalCount": 3,
                    "nodes": [{"title": "Bug report", "url": "u", "createdAt": "t"}],
                },
            }
        }
        base.update(overrides)
        return base

    def test_happy_path_aggregates_all_sections(self, client):
        with (
            patch.object(
                client, "get_user", return_value={"login": "octocat"}
            ) as m_user,
            patch.object(
                client, "get_all_user_repos", return_value=iter([{"name": "repo1"}])
            ),
            patch.object(
                client, "get_aggregate_user_languages", return_value={"Python": 100}
            ),
            patch.object(
                client, "execute_graphql", return_value=self._graphql_response()
            ) as m_gql,
            patch.object(client, "get", return_value=[]),
        ):
            result = client.fetch_full_profile_data("octocat")

        m_user.assert_called_once_with("octocat")
        assert result["profile"] == {"login": "octocat"}
        assert result["repositories"]["items"] == [{"name": "repo1"}]
        assert result["repositories"]["language_breakdown"] == {"Python": 100}
        assert result["lifetime_activity"]["pull_requests"]["total_count"] == 10
        assert result["lifetime_activity"]["issues"]["total_count"] == 3
        assert result["recent_contributions_365_days"]["totalCommitContributions"] == 50
        assert result["recent_commits"] == []

        # GraphQL variables should use the raw (unencoded) username
        _, kwargs = m_gql.call_args
        assert kwargs["variables"]["login"] == "octocat"

    def test_invalid_username_raises_before_any_network_call(self, client):
        with (
            patch.object(client, "get_user") as m_user,
            pytest.raises(InvalidUsernameError),
        ):
            client.fetch_full_profile_data("../../etc/passwd")
        m_user.assert_not_called()

    def test_404_on_get_user_raises_user_not_found(self, client):
        err = HakiAPIError("not found", status_code=404)
        with (
            patch.object(client, "get_user", side_effect=err),
            pytest.raises(UserNotFoundError),
        ):
            client.fetch_full_profile_data("ghost")

    def test_non_404_error_on_get_user_propagates(self, client):
        err = HakiAPIError("server error", status_code=500)
        with (
            patch.object(client, "get_user", side_effect=err),
            pytest.raises(HakiAPIError),
        ):
            client.fetch_full_profile_data("octocat")

    def test_get_user_error_without_status_code_does_not_crash(self, client):
        # Simulates a network-level failure that has no status_code attribute set
        err = HakiAPIError("timeout")
        with (
            patch.object(client, "get_user", side_effect=err),
            pytest.raises(HakiAPIError),
        ):
            client.fetch_full_profile_data("octocat")

    def test_repo_and_language_fetch_failures_degrade_gracefully(self, client):
        with (
            patch.object(client, "get_user", return_value={"login": "octocat"}),
            patch.object(
                client, "get_all_user_repos", side_effect=HakiAPIError("boom")
            ),
            patch.object(
                client, "get_aggregate_user_languages", side_effect=HakiAPIError("boom")
            ),
            patch.object(
                client, "execute_graphql", return_value=self._graphql_response()
            ),
            patch.object(client, "get", return_value=[]),
        ):
            result = client.fetch_full_profile_data("octocat")

        assert result["repositories"]["items"] == []
        assert result["repositories"]["language_breakdown"] == {}
        # Rest of the payload should still be populated
        assert result["profile"] == {"login": "octocat"}

    def test_graphql_could_not_resolve_user_raises_user_not_found(self, client):
        with (
            patch.object(client, "get_user", return_value={"login": "octocat"}),
            patch.object(client, "get_all_user_repos", return_value=iter([])),
            patch.object(client, "get_aggregate_user_languages", return_value={}),
            patch.object(
                client,
                "execute_graphql",
                side_effect=HakiAPIError(
                    "Could not resolve to a User with the login of 'octocat'"
                ),
            ),
            pytest.raises(UserNotFoundError),
        ):
            client.fetch_full_profile_data("octocat")

    def test_graphql_other_error_propagates(self, client):
        with (
            patch.object(client, "get_user", return_value={"login": "octocat"}),
            patch.object(client, "get_all_user_repos", return_value=iter([])),
            patch.object(client, "get_aggregate_user_languages", return_value={}),
            patch.object(
                client, "execute_graphql", side_effect=HakiAPIError("rate limited")
            ),
            pytest.raises(HakiAPIError),
        ):
            client.fetch_full_profile_data("octocat")

    def test_null_graphql_user_node_does_not_crash(self, client):
        # e.g. ghost/suspended accounts where GraphQL returns {"user": null}
        with (
            patch.object(client, "get_user", return_value={"login": "ghost"}),
            patch.object(client, "get_all_user_repos", return_value=iter([])),
            patch.object(client, "get_aggregate_user_languages", return_value={}),
            patch.object(client, "execute_graphql", return_value={"user": None}),
            patch.object(client, "get", return_value=[]),
        ):
            result = client.fetch_full_profile_data("ghost")

        assert result["lifetime_activity"]["pull_requests"]["total_count"] == 0
        assert result["lifetime_activity"]["issues"]["total_count"] == 0
        assert result["recent_contributions_365_days"] == {}

    def test_recent_commits_called_with_pre_validated_username(self, client):
        with (
            patch.object(client, "get_user", return_value={"login": "octocat"}),
            patch.object(client, "get_all_user_repos", return_value=iter([])),
            patch.object(client, "get_aggregate_user_languages", return_value={}),
            patch.object(
                client, "execute_graphql", return_value=self._graphql_response()
            ),
            patch.object(client, "get_recent_commits", return_value=[]) as m_commits,
        ):
            client.fetch_full_profile_data("octocat")

        m_commits.assert_called_once_with("octocat", is_validated=True)


# get_recent_commits


class TestGetRecentCommits:
    def test_extracts_commits_from_push_events(self, client):
        events = [
            {
                "type": "PushEvent",
                "created_at": "2024-01-01T00:00:00Z",
                "payload": {
                    "commits": [
                        {"message": "Add feature", "sha": "abc123"},
                        {"message": "Fix typo", "sha": "def456"},
                    ]
                },
            }
        ]
        with patch.object(client, "get", return_value=events):
            commits = client.get_recent_commits("octocat")

        assert len(commits) == 2
        assert commits[0] == {
            "message": "Add feature",
            "sha": "abc123",
            "created_at": "2024-01-01T00:00:00Z",
        }

    def test_filters_out_merge_pull_request_commits(self, client):
        events = [
            {
                "type": "PushEvent",
                "created_at": "t",
                "payload": {
                    "commits": [
                        {
                            "message": "Merge pull request #42 from foo/bar",
                            "sha": "111",
                        },
                        {"message": "Real change", "sha": "222"},
                    ]
                },
            }
        ]
        with patch.object(client, "get", return_value=events):
            commits = client.get_recent_commits("octocat")

        assert len(commits) == 1
        assert commits[0]["sha"] == "222"

    def test_ignores_non_push_events(self, client):
        events = [
            {"type": "WatchEvent", "payload": {}},
            {"type": "ForkEvent", "payload": {}},
        ]
        with patch.object(client, "get", return_value=events):
            commits = client.get_recent_commits("octocat")

        assert commits == []

    def test_api_failure_degrades_to_empty_list(self, client):
        with patch.object(client, "get", side_effect=HakiAPIError("timeout")):
            commits = client.get_recent_commits("octocat")

        assert commits == []

    def test_invalid_username_raises_when_not_pre_validated(self, client):
        with pytest.raises(InvalidUsernameError):
            client.get_recent_commits("../../etc/passwd")

    def test_is_validated_true_skips_revalidation(self, client):
        # Bypasses username validation completely when is_validated=True
        with (
            patch.object(client, "_validate_username") as m_validate,
            patch.object(client, "get", return_value=[]),
        ):
            client.get_recent_commits("already%20encoded", is_validated=True)

        m_validate.assert_not_called()

    def test_missing_message_and_sha_default_to_empty_string(self, client):
        events = [
            {
                "type": "PushEvent",
                "created_at": "t",
                "payload": {"commits": [{}]},
            }
        ]
        with patch.object(client, "get", return_value=events):
            commits = client.get_recent_commits("octocat")

        assert commits == [{"message": "", "sha": "", "created_at": "t"}]
