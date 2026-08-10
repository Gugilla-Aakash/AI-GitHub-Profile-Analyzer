from typing import Any, ClassVar


class SkillAnalyzer:
    """Analyze languages and topics to categorize a developer domain expertise and his byte share"""

    DOMAIN_MAPPING: ClassVar[dict[str, set[str]]] = {
        "Frontend": {
            "javascript",
            "typescript",
            "html",
            "css",
            "react",
            "vue",
            "next.js",
        },
        "Backend": {
            "python",
            "java",
            "ruby",
            "php",
            "go",
            "c#",
            "django",
            "fastapi",
        },
        "Systems & Core": {
            "c",
            "c++",
            "rust",
            "zig",
            "assembly",
        },
        "Data & ML": {
            "jupyter notebook",
            "r",
            "julia",
            "machine-learning",
            "data-science",
        },
        "DevOps & Cloud": {
            "dockerfile",
            "shell",
            "kubernetes",
            "aws",
            "terraform",
        },
    }

    def analyze(
        self,
        language_breakdown: dict[str, int],
        repositories: list[dict[str, Any]],
    ) -> dict[str, Any]:
        # Initialize sets and counters
        languages: set[str] = set()
        topics: set[str] = set()
        domains: set[str] = set()

        # Extracts languages
        languages.update(language_breakdown.keys())

        # Extract topics (but owned repositories only)
        for repo in repositories:
            if repo.get("fork", False):
                continue

            for topic in repo.get("topics", []):
                topics.add(topic)

        # Determines domain
        signals = {signal.lower() for signal in languages}
        signals.update(topic.lower() for topic in topics)

        for domain, keywords in self.DOMAIN_MAPPING.items():
            if signals.intersection(keywords):
                domains.add(domain)

        # Calculates per domain byte-shares
        total_bytes = sum(language_breakdown.values())

        # Ensuring every detected domain has an entry in domain_shares
        domain_shares: dict[str, float] = {domain: 0.0 for domain in domains}

        if total_bytes > 0:
            lang_bytes_lower = {
                lang.lower(): bytes_count
                for lang, bytes_count in language_breakdown.items()
            }

            # Only iterates over the domains we already identified
            for domain in domains:
                keywords = self.DOMAIN_MAPPING[domain]
                domain_bytes = sum(
                    bytes_count
                    for lang, bytes_count in lang_bytes_lower.items()
                    if lang in keywords
                )

                # If bytes exist, then update from the 0.0 default
                if domain_bytes > 0:
                    share = round((domain_bytes / total_bytes) * 100, 2)
                    domain_shares[domain] = share

        return {
            "domains": sorted(domains),
            "domain_shares": domain_shares,
            "languages": sorted(languages),
            "topics": sorted(topics),
        }
