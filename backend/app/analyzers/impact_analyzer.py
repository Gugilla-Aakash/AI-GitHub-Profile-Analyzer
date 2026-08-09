from typing import Any


class ImpactAnalyzer:
    """Analyze the impact of Github user original repos"""

    def analyze(self, repositories: list[dict[str, Any]]) -> dict[str, Any]:
        # Edge case guard
        if not repositories:
            return {
                "total_stars": 0,
                "total_forks": 0,
                "owned_repo_count": 0,
                "forked_repo_count": 0,
                "hero_repo": None,
            }
        # Separating owned and forked repos
        owned_repos = []
        forked_repo_count = 0

        for repo in repositories:
            if repo.get("fork", False):
                forked_repo_count += 1
            else:
                owned_repos.append(repo)

        # Calculate totals (Owned repos only)
        total_stars = sum(repo.get("stargazers_count", 0) for repo in owned_repos)
        total_forks = sum(repo.get("forks_count", 0) for repo in owned_repos)
        owned_repo_count = len(owned_repos)

        # Identify owned repos
        hero_repo = None
        if owned_repos:
            max_repo = max(
                owned_repos,
                key=lambda repo: repo.get("stargazers_count", 0),
            )
            if max_repo.get("stargazers_count", 0) > 0:
                hero_repo = {
                    "name": max_repo.get("name"),
                    "stars": max_repo.get("stargazers_count", 0),
                }

        return {
            "total_stars": total_stars,
            "total_forks": total_forks,
            "owned_repo_count": owned_repo_count,
            "forked_repo_count": forked_repo_count,
            "hero_repo": hero_repo,
        }
