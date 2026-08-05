import re
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import quote

from hakiapi.clients import GitHubClient
from hakiapi.core.exceptions import HakiAPIError

# GitHub allows alphanumeric chars and single hyphens, max 39 chars.
GITHUB_USERNAME_REGEX = re.compile(
    r"^[a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38}$"
)


class UserNotFoundError(HakiAPIError):
    """Raised when the requested GitHub user or organization profile isn't found."""


class InvalidUsernameError(ValueError):
    """Raised when the input username violates GitHub's naming conventions."""


class AppGitHubClient(GitHubClient):
    """Application-specific GitHub API client built for AI profile reviews."""

    def _validate_username(self, username: str) -> tuple[str, str]:
        """
        Validates username structure. Returns a tuple of:
        (clean_username, url_encoded_username)
        """
        cleaned = username.strip() if username else ""
        if not cleaned or not GITHUB_USERNAME_REGEX.match(cleaned):
            raise InvalidUsernameError(
                f"Invalid GitHub username structure: '{username}'."
            )
        return cleaned, quote(cleaned, safe="")

    def fetch_full_profile_data(self, username: str, **kwargs: Any) -> dict[str, Any]:
        """Aggregates REST and GraphQL profile data into a single payload."""
        clean_username, safe_username = self._validate_username(username)

        # 1. Fetch REST Profile
        try:
            profile = self.get_user(safe_username)
        except HakiAPIError as exc:
            # Defensive check in case exc doesn't carry status_code (e.g. network timeouts)
            if getattr(exc, "status_code", None) == 404:
                raise UserNotFoundError(
                    f"GitHub user '{username}' was not found."
                ) from exc
            raise

        # Catch transient REST errors so the profile fetch doesn't fail completely
        try:
            repositories = list(self.get_all_user_repos(safe_username))
        except HakiAPIError:
            repositories = []

        try:
            language_breakdown = self.get_aggregate_user_languages(safe_username)
        except HakiAPIError:
            language_breakdown = {}

        # 2. Query GraphQL for 1-year activity window
        now = datetime.now(timezone.utc)
        one_year_ago = now - timedelta(days=365)

        # GraphQL expects raw string literals, so pass clean_username instead of URL-quoted string
        variables = {
            "login": clean_username,
            "from": one_year_ago.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "to": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

        query = """
        query($login: String!, $from: DateTime!, $to: DateTime!) {
          user(login: $login) {
            contributionsCollection(from: $from, to: $to) {
              contributionCalendar {
                totalContributions
              }
              totalCommitContributions
              totalIssueContributions
              totalPullRequestContributions
            }

            pullRequests(
              first: 5,
              orderBy: {field: CREATED_AT, direction: DESC}
            ) {
              totalCount
              nodes {
                title
                url
                createdAt
              }
            }

            issues(
              first: 5,
              orderBy: {field: CREATED_AT, direction: DESC}
            ) {
              totalCount
              nodes {
                title
                url
                createdAt
              }
            }
          }
        }
        """

        try:
            response = self.execute_graphql(query, variables=variables)
        except HakiAPIError as e:
            if "Could not resolve to a User" in str(e):
                raise UserNotFoundError(
                    f"User '{username}' not found or is an Organization account."
                ) from e
            raise

        user_data = response.get("user") or {}
        pull_requests = user_data.get("pullRequests") or {}
        issues = user_data.get("issues") or {}

        lifetime_activity = {
            "pull_requests": {
                "total_count": pull_requests.get("totalCount", 0),
                "recent_items": pull_requests.get("nodes", []),
            },
            "issues": {
                "total_count": issues.get("totalCount", 0),
                "recent_items": issues.get("nodes", []),
            },
        }

        recent_contributions = user_data.get("contributionsCollection", {})
        recent_commits = self.get_recent_commits(safe_username, is_validated=True)

        return {
            "profile": profile,
            "repositories": {
                "items": repositories,
                "language_breakdown": language_breakdown,
            },
            "lifetime_activity": lifetime_activity,
            "recent_contributions_365_days": recent_contributions,
            "recent_commits": recent_commits,
        }

    def get_recent_commits(
        self, username: str, is_validated: bool = False
    ) -> list[dict[str, Any]]:
        """
        Retrieves recent public commits.
        Note: Commit messages are untrusted user input—sanitize down the line before LLM prompt injection.
        """
        if is_validated:
            safe_username = username
        else:
            _, safe_username = self._validate_username(username)

        try:
            events = self.get(f"users/{safe_username}/events/public")
        except HakiAPIError:
            return []

        commits = []
        for event in events:
            if event.get("type") == "PushEvent":
                payload = event.get("payload", {})

                for commit in payload.get("commits", []):
                    commit_msg = commit.get("message", "")

                    # Filter out automated merge noise
                    if not commit_msg.startswith("Merge pull request"):
                        commits.append(
                            {
                                "message": commit_msg,
                                "sha": commit.get("sha", ""),
                                "created_at": event.get("created_at"),
                            }
                        )
        return commits
