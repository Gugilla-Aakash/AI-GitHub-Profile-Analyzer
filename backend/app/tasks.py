from typing import Any

from hakiapi.clients.github import GitHubClient

from app.analyzers.activity_analyzer import ActivityAnalyzer
from app.analyzers.impact_analyzer import ImpactAnalyzer
from app.analyzers.language_analyzer import LanguageAnalyzer
from app.analyzers.scorer import ProfileScorer
from app.analyzers.skill_analyzer import SkillAnalyzer
from app.cache.simple_cache import cache
from app.config import settings

RECENT_ITEMS_LIMIT = 5
REPOS_LIMIT = 15

def _exact_repositories(repos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extracts top and recent repos for llm's context"""
    if not repos:
        return []

    sorted_repos = sorted(
            repos,
            key = lambda r: r.get("updated_at") or r.get("pushed_at") or "",
            reverse=True,
            )

    extracted = []

    for r in sorted_repos[:REPOS_LIMIT]:
        extracted.append(
                {
                    "name": r.get("name"),
                    "description": r.get("description"),
                    "stars": r.get("stargazers_count", 0),
                    "forks": r.get("forks_count", 0),
                    "language": r.get("language"),
                    "is_fork": r.get("fork", False),
                    "updated_at": r.get("updated_at") or r.get("pushed_at", "unknown"), 
                    }
                )
    return extracted
def _extract_recent_items(
    lifetime_activity: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    """Trim lifetime PR or issues recent items with including repository names"""
    if not lifetime_activity:
        return {"pull_requests": [], "issues": []}

    pull_requests = lifetime_activity.get("pull_requests", {}).get("recent_items", [])
    issues = lifetime_activity.get("issues", {}).get("recent_items", [])

    def _shape(item: dict[str, Any]) -> dict[str, Any]:
        repo_name = None
        repo_obj = item.get("repository")
        if isinstance(repo_obj, dict):
            repo_name = repo_obj.get("name")

        if not repo_name and item.get("url"):
            parts = item["url"].split("/")
            if len(parts) >= 5:
                repo_name = parts[4]

        return {
            "title": item.get("title"),
            "url": item.get("url"),
            "created_at": item.get("createdAt"),
            "repo": repo_name or "unknown repo",
        }

    return {
        "pull_requests": [_shape(item) for item in pull_requests[:RECENT_ITEMS_LIMIT]],
        "issues": [_shape(item) for item in issues[:RECENT_ITEMS_LIMIT]],
    }
def analyze_profile_task(username: str) -> dict[str, Any]:
    """
    Background worker task: fetch profile data, run analyzers, calculate
    the score, and cache a combined payload
    """
    client = GitHubClient(token=settings.GITHUB_TOKEN)

    data = client.fetch_full_profile_data(username)

    repos_data = data.get("repositories", {})
    repo_items = repos_data.get("items", [])
    lang_breakdown = repos_data.get("language_breakdown", {})
    recent_contribs = data.get("recent_contributions_365_days", {})
    lifetime_act = data.get("lifetime_activity", {})

    lang_result = LanguageAnalyzer().analyze(lang_breakdown)
    impact_result = ImpactAnalyzer().analyze(repo_items)
    skill_result = SkillAnalyzer().analyze(lang_breakdown, repo_items)
    activity_result = ActivityAnalyzer().analyze(recent_contribs, lifetime_act)

    score_result = ProfileScorer().calculate_score(
        lang_result, impact_result, skill_result, activity_result
    )

    combined_result: dict[str, Any] = {
        **score_result,
        "username": username,
        "language": lang_result,
        "impact": impact_result,
        "skill": skill_result,
        "activity": activity_result,
        "repositories": _exact_repositories(repo_items),
        "recent_activity": _extract_recent_items(lifetime_act),
        "recent_contributions_365_days": recent_contribs,
        "readme_status": data.get("readme_statuses", {}),
    }

    cache.set_profile(username, combined_result)

    return combined_result
