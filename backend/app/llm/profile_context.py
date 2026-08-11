from typing import Any


def build_profile_context(data: dict[str, Any]) -> str:
    """
    Constructs highly structured text context for LLM report generators
    Shows repos metadata, contribution, statistics, and domain metrics too
    """
    username = data.get("username", "Unknown")
    final_score = data.get("final_score", 0)
    grade = data.get("grade", "N/A")
    breakdown = data.get("breakdown", {})

    activity = data.get("activity", {})
    language = data.get("language", {})
    skill = data.get("skill", {})
    repositories = data.get("repositories", [])
    readme_statuses = data.get("readme_status", {})

    # Building detailed repo profiles
    repo_details = []
    for repo in repositories:
        if not isinstance(repo, dict):
            continue

        name = repo.get("name", "Unknown")
        desc = repo.get("description") or "No description provided"
        lang = repo.get("language") or "N/A"
        stars = repo.get("stars", repo.get("stargazers_count", 0))
        forks = repo.get("forks", repo.get("forks_count", 0))
        open_issues = repo.get("open_issues_count", 0)
        size_kb = repo.get("size", 0)
        license_name = repo.get("license") or "No license"
        topics = repo.get("topics", [])
        has_readme = readme_statuses.get(name, repo.get("has_readme", False))
        is_fork = repo.get("fork", False)

        topics_str = ", ".join(topics) if topics else "None tagged"

        repo_details.append(
            f"  • Repo Name: {name} {'(Forked)' if is_fork else '(Owned)'}\n"
            f"    - Description: {desc}\n"
            f"    - Primary Language: {lang}\n"
            f"    - Stars: {stars} | Forks: {forks} | Open Issues: {open_issues}\n"
            f"    - Size: {size_kb} KB | License: {license_name}\n"
            f"    - README Documented: {'YES' if has_readme else 'NO'}\n"
            f"    - Topics/Tags: {topics_str}"
        )

    repos_formatted = (
        "\n".join(repo_details)
        if repo_details
        else "  • No public repository metadata available."
    )

    # Domain shares
    domain_shares = skill.get("domain_shares", {})
    domain_str = (
        ", ".join([f"{k}: {v}%" for k, v in domain_shares.items()])
        if domain_shares
        else "N/A"
    )

    # Laguages breakdown

    lang_percentages = language.get("percentages", {})
    lang_dist_str = (
        ", ".join([f"{k}: {v}%" for k, v in lang_percentages.items()])
        if lang_percentages
        else "N/A"
    )

    context = f"""=== GITHUB DEVELOPER EVALUATION DATA ===
Target Username: @{username}
Overall Grade: {grade}
Overall Score: {final_score} / 100

EVALUATION BREAKDOWN METRICS:
- Activity Score: {breakdown.get("activity", "N/A")} / 100
- Impact Score: {breakdown.get("impact", "N/A")} / 100
- Skill Breadth Score: {breakdown.get("skill", "N/A")} / 100
- Language Diversity Score: {breakdown.get("language_diversity", "N/A")} / 100

TECHNICAL & LANGUAGE METRICS:
- Primary Language: {language.get("primary_language", "N/A")}
- Language Diversity Ratio: {language.get("diversity_score", "N/A")}
- Language Breakdown: {lang_dist_str}
- Domain Distribution: {domain_str}

ACTIVITY & COLLABORATION METRICS (365 DAYS):
- Activity Tier: {activity.get("activity_tier", "Unknown")}
- Total Contributions (365 days): {activity.get("total_contributions_365", 0)}
- Lifetime Pull Requests: {activity.get("lifetime_prs", 0)}
- Lifetime Issues Filed: {activity.get("lifetime_issues", 0)}
- Collaboration Ratio: {activity.get("collaboration_ratio_365", 0)}%

PUBLIC REPOSITORIES ANALYZED ({len(repositories)} Total):
{repos_formatted}
"""
    return context
