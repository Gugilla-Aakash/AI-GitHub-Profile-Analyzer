from typing import Any


class LanguageAnalyzer:
    """Analyze Github user language distribution"""

    def analyze(self, language_breakdown: dict[str, int]) -> dict[str, Any]:
        """
        Analyze github language byte distribution


        Returns:
            {
                "total_bytes": int,
                "primary_language": str | None,
                "percentages": dict[str, float],
                "language_count": int,
                "diversity_score": float,
            }
        """

        # If empty
        if not language_breakdown:
            return {
                "total_bytes": 0,
                "primary_language": None,
                "percentages": {},
                "language_count": 0,
                "diversity_score": 0.0,
            }
        total_bytes = sum(language_breakdown.values())

        # Avoid division by 0
        if total_bytes == 0:
            return {
                "total_bytes": 0,
                "primary_language": None,
                "percentages": {},
                "language_count": len(language_breakdown),
                "diversity_score": 0.0,
            }
        # Percentage share of each language
        percentages = {
            language: round((byte_count / total_bytes) * 100, 2)
            for language, byte_count in language_breakdown.items()
        }

        # Dominant Language
        primary_language = max(
            language_breakdown,
            key=lambda lang: language_breakdown[lang],
        )

        # Herfindahl-Hirschman Index (HHI)
        hhi = sum(
            (byte_count / total_bytes) ** 2
            for byte_count in language_breakdown.values()
        )

        # Normalize so:
        # 0.00 -> single-language profile
        # approaching 1.00 -> highly diverse profile
        diversity_score = round(1.0 - hhi, 2)

        return {
            "total_bytes": total_bytes,
            "primary_language": primary_language,
            "percentages": percentages,
            "language_count": len(language_breakdown),
            "diversity_score": diversity_score,
        }
