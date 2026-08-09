from typing import Any


class ActivityAnalyzer:
    """Analyze users lifetime and recent Github activity"""

    def analyze(
        self,
        recent_contributions_365_days: dict[str, Any],
        lifetime_activity: dict[str, Any],
    ) -> dict[str, Any]:
        # Trying root level first, next contribution calendar
        total_contributions_365 = (
            recent_contributions_365_days.get("totalContributions")
            or recent_contributions_365_days.get("total_contributions")
            or recent_contributions_365_days.get("contributionCalendar", {}).get(
                "totalContributions"
            )
        )
        # Calculate directly from weeks if totalContributions key is missing
        if total_contributions_365 is None or total_contributions_365 == 0:
            weeks = recent_contributions_365_days.get("weeks", [])
            if not weeks and "contributionCalendar" in recent_contributions_365_days:
                weeks = recent_contributions_365_days["contributionCalendar"].get(
                    "weeks", []
                )

            total_contributions_365 = sum(
                day.get("contributionCount", 0)
                for week in weeks
                for day in week.get("contributionDays", [])
            )

        issues_365 = recent_contributions_365_days.get("totalIssueContributions", 0)
        prs_365 = recent_contributions_365_days.get("totalPullRequestContributions", 0)

        # Collabration Ratio

        collaborative_365 = issues_365 + prs_365

        collaboration_ratio_365 = (
            round((collaborative_365 / total_contributions_365) * 100, 2)
            if total_contributions_365 > 0
            else 0.0
        )

        # Activity tier
        if total_contributions_365 <= 50:
            activity_tier = "Inactive"
        elif total_contributions_365 <= 250:
            activity_tier = "Casual"
        elif total_contributions_365 <= 1000:
            activity_tier = "Active"
        else:
            activity_tier = "Prolific"

        # Lifetime metrics
        lifetime_prs = lifetime_activity.get("pull_requests", {}).get("total_count", 0)
        lifetime_issues = lifetime_activity.get("issues", {}).get("total_count", 0)

        return {
            "total_contributions_365": total_contributions_365,
            "activity_tier": activity_tier,
            "collaboration_ratio_365": collaboration_ratio_365,
            "lifetime_prs": lifetime_prs,
            "lifetime_issues": lifetime_issues,
        }
