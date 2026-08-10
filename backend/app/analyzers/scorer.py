import math
from typing import Any


class ProfileScorer:
    """Calculate overall score of a develper and gives grade"""

    def _clamp(self, value: float) -> float:
        """Ensure subscore never exceeds 100"""
        return min(100.0, value)

    def _calculate_grade(self, score: int) -> str:
        if score >= 90:
            return "S"
        elif score >= 75:
            return "A"
        elif score >= 60:
            return "B"
        elif score >= 40:
            return "C"
        else:
            return "D"

    def calculate_score(
        self,
        language_data: dict[str, Any],
        impact_data: dict[str, Any],
        skill_data: dict[str, Any],
        activity_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Calculate overall profile score tier and breakdown"""
        has_languages = len(skill_data.get("languages", [])) > 0
        has_recent_activity = activity_data.get("total_contributions_365", 0) > 0

        if not has_languages and not has_recent_activity:
            return {
                "insufficient_data": True,
                "final_score": 0,
                "grade": "N/A",
                "message": "Not enough public data to produce a meaningful rating.",
                "breakdown": {
                    "activity": 0,
                    "impact": 0,
                    "skill": 0,
                    "language_diversity": 0,
                },
            }

        # Language score (15% weight)
        diversity = language_data.get("diversity_score", 0.0)
        raw_lang_score = self._clamp((diversity / 0.80) * 100)

        # Impact score (40% weight)
        stars = impact_data.get("total_stars", 0)
        forks = impact_data.get("total_forks", 0)

        star_score = self._clamp(math.log10(1 + stars) / math.log10(5001) * 100)
        fork_score = self._clamp(math.log10(1 + forks) / math.log10(1001) * 100)

        impact_score = (star_score * 0.7) + (fork_score * 0.3)

        # Skill score (15% weight)
        domain_shares = skill_data.get("domain_shares", {})
        raw_skill_score = 0.0

        for share in domain_shares.values():
            points = min(33.33, (share / 15.0) * 33.33)
            raw_skill_score += points

        skill_score = self._clamp(raw_skill_score)

        # Activity score (30% weight)
        lifetime_prs = activity_data.get("lifetime_prs", 0)
        lifetime_issues = activity_data.get("lifetime_issues", 0)
        recent_contributions = activity_data.get("total_contributions_365", 0)

        life_total = lifetime_prs + lifetime_issues
        life_score = self._clamp((math.log10(1 + life_total) / math.log10(1001)) * 100)
        recent_score = self._clamp((recent_contributions / 500) * 100)

        # 70% for recent activity and 30 for lifetime prs/issues
        activity_score = (recent_score * 0.70) + (life_score * 0.30)

        # Safety floor for high volume maintainers
        if recent_contributions >= 1000:
            activity_score = max(activity_score, 90.0)
        activity_score = self._clamp(activity_score)

        # Volume gates
        total_bytes = language_data.get("total_bytes", 0)

        # Log scale upto 500kb (~500,000 bytes)
        volume_multipler = min(1.0, total_bytes / 500_000.0)

        skill_score = self._clamp(raw_skill_score * volume_multipler)
        lang_score = self._clamp(raw_lang_score * volume_multipler)

        # Mastery bypass (Depth over breadth)
        skill_score = max(skill_score, impact_score)
        lang_score = max(lang_score, impact_score)

        final_score_raw = (
            (activity_score * 0.30)
            + (impact_score * 0.40)
            + (skill_score * 0.15)
            + (lang_score * 0.15)
        )

        final_score_rounded = round(final_score_raw)
        grade = self._calculate_grade(final_score_rounded)

        return {
            "insufficient_data": False,
            "final_score": final_score_rounded,
            "grade": grade,
            "breakdown": {
                "activity": round(activity_score),
                "impact": round(impact_score),
                "skill": round(skill_score),
                "language_diversity": round(lang_score),
            },
        }
