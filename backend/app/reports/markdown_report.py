import logging
from typing import Any

from app.clients.llm.gemini_provider import GeminiProvider
from app.clients.llm.groq_provider import GroqProvider
from app.llm.profile_context import build_profile_context

logger = logging.getLogger(__name__)


def _generate_full_report(context: str) -> str:
    """
    Single-turn LLM request (Gemini -> Groq fallback) to generate a complete,
    visually engaging, Markdown developer audit report.
    """
    print("=" * 80)
    print("LLM REPORT GENERATION STARTED")
    print("=" * 80)

    prompt = """
You are a Principal Staff Software Engineer and Technical Recruiter conducting an engineering audit on a developer's GitHub profile.

Your goal is to output an ENGAGING, VISUALLY RICH, and ACTIONABLE GitHub Developer Audit Report.

FORMAT & VISUAL STYLE INSTRUCTIONS:
- Use Markdown tables, emojis, bold badges, bulleted lists, and blockquote callouts to make the report visually appealing and scannable. Do not write dense walls of text!
- Include summary KPI tables for scores, languages, and repo assessments.
- Use section emojis (e.g., 🚀, 📊, 🎯, 🛠️, 📦, 📈, 💼, 💡, 🏁).

WRITING & TONE RULES:
- Write like a senior engineering manager evaluating a peer candidate.
- Confident, direct, natural, and evidence-backed.
- STRICTLY BANNED PHRASES: Do NOT use "This indicates...", "This demonstrates...", "There is a...", "It is worth noting that...", or "Based on the provided data...".
- Do NOT say "code quality cannot be evaluated" or "insufficient data to determine". Instead, evaluate what is visible in the architecture, READMEs, open issues, tags, and languages.
- Ground every claim strictly in the supplied profile context. Do NOT invent fake repositories or metrics.
- Keep total length between 1000 and 1400 words.

REQUIRED REPORT STRUCTURE:

# 🚀 GitHub Developer Audit Report: @<username>

> **Executive Summary:** <Write a 2-sentence high-impact snapshot of who this developer is, their top technical strength, and primary area for growth.>

---

## 📊 1. Profile At-A-Glance
| Metric | Rating / Value | Assessment |
| :--- | :--- | :--- |
| **Overall Grade** | **<Grade>** | <1-line verdict> |
| **Final Score** | **<Score> / 100** | <Overall standing> |
| **Primary Skill** | <Primary Language> | <Dominant stack> |
| **Activity Tier** | <Activity Tier> | <Contribution consistency> |

---

## 🎯 2. Technical Standing & Engineering Practices
- **Codebase Maturity:** <Discuss project structure, README documentation, license usage, and repo hygiene.>
- **Technical Depth:** <Analyze language distribution, framework usage, and domain focus.>
- **Open-Source Footprint:** <Evaluate public presence, forks, stars, and project visibility.>

---

## 🛠️ 3. Skill & Language Matrix
| Language / Domain | Share / Ratio | Repo Evidence & Usage |
| :--- | :--- | :--- |
| <Lang/Domain 1> | <Percentage%> | <Mention specific repo where used> |
| <Lang/Domain 2> | <Percentage%> | <Mention specific repo where used> |

*Key takeaway callout inside a blockquote regarding technical versatility.*

---

## 📦 4. Key Repository Highlights
For the top 3-4 repositories, provide a breakdown:

### 🔹 `<repo-name>`
- **Stack & Specs:** `<Language>` | ⭐ `<Stars>` | 🍴 `<Forks>` | 📄 README: `<Present/Missing>`
- **Architectural Purpose:** <Brief analysis of what the repo does and how it's built.>
- **Engineering Highlights & Opportunities:** <Strengths and recommended technical improvements.>

---

## 📈 5. Contribution & Collaboration Analysis
- **365-Day Consistency:** <Analyze annual commit volume and quarterly activity patterns.>
- **Collaboration Health:** <Evaluate PRs, issue participation, and cross-repo activity.>

---

## 💼 6. Career Fit & Role Alignment
| Role Profile | Fit Level | Technical Justification |
| :--- | :--- | :--- |
| **Backend Engineer** | 🟢 High / 🟡 Moderate / 🔴 Low | <Reason based on repos> |
| **Frontend Engineer** | 🟢 High / 🟡 Moderate / 🔴 Low | <Reason based on repos> |
| **Full-Stack Engineer**| 🟢 High / 🟡 Moderate / 🔴 Low | <Reason based on repos> |
| **AI / ML Engineer**   | 🟢 High / 🟡 Moderate / 🔴 Low | <Reason based on repos> |

---

## 💡 7. Actionable Improvement Roadmap
Provide 5 prioritized, concrete, and actionable recommendations using bullet points:
1. 🎯 **<Title>**: <Clear advice>
2. 📝 **<Title>**: <Clear advice>
3. 🚀 **<Title>**: <Clear advice>
4. 🔀 **<Title>**: <Clear advice>
5. 📊 **<Title>**: <Clear advice>

---

## 🏁 8. Final Verdict
<Write 2 concluding paragraphs giving a holistic summary and final hiring/collaboration perspective.>
"""

    raw_text = ""
    try:
        raw_text = GeminiProvider().chat(context=context, history=[], message=prompt)
        print("\n--- GEMINI RESPONSE (First 1000 chars) ---")
        print(raw_text[:1000] if raw_text else "(EMPTY RESPONSE)")
        print("------------------------------------------\n")
    except Exception as gemini_err:  # noqa: BLE001
        logger.warning(
            "Gemini failed for full report synthesis (%s). Trying Groq...", gemini_err
        )
        print(f"Gemini Exception: {gemini_err}")
        raw_text = ""

    # gemini can return empty text without raising too, so catch that case here
    if not (raw_text and raw_text.strip()):
        try:
            raw_text = GroqProvider().chat(context=context, history=[], message=prompt)
            print("\n--- GROQ RESPONSE (First 1000 chars) ---")
            print(raw_text[:1000] if raw_text else "(EMPTY RESPONSE)")
            print("----------------------------------------\n")
        except Exception as groq_err:  # noqa: BLE001
            logger.error("Groq also failed for full report synthesis: %s", groq_err)
            print(f"Groq Exception: {groq_err}")

    if raw_text and raw_text.strip():
        return raw_text.strip()

    return (
        "# 🚀 GitHub Developer Audit Report\n\n"
        "## ⚠️ Executive Summary\n\n"
        "Unable to synthesize the AI Developer Audit Report at this moment. "
        "Please verify your LLM API configuration and try again."
    )


def generate_markdown_report(data: dict[str, Any]) -> str:
    """
    Builds a complete AI-driven Markdown report for a GitHub profile
    """
    if data.get("insufficient_data"):
        return f"""# 🚀 GitHub Profile Audit: {data.get("username", "Unknown")}

## ⚠️ Executive Summary
Insufficient public data was found for this user. The profile has fewer than the required repositories or public activity entries to construct an in-depth audit report.
"""

    profile_context_str = build_profile_context(data)
    return _generate_full_report(profile_context_str)
