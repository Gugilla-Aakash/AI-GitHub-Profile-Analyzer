import logging
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Response

from app.cache.simple_cache import cache
from app.reports.markdown_report import generate_markdown_report
from app.reports.pdf_report import convert_markdown_to_pdf

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Report"])


@router.get("/{username}")
def get_report(
    username: str,
    format: Literal["md", "pdf"] = Query(
        "md", description="Report format: 'md' or 'pdf'"
    ),
) -> Response:
    """
    Generate and download an audit report for a GitHub profile in Markdown or PDF format
    """
    profile_data = cache.get_profile(username.lower())

    if not profile_data:
        raise HTTPException(
            status_code=404,
            detail=f"Profile '{username}' not found in cache. Please run /api/v1/analyze/{username} first.",
        )

    # Build AI Markdown content
    markdown_str = generate_markdown_report(profile_data)

    # Return PDF binary if format=pdf
    if format == "pdf":
        try:
            pdf_bytes = convert_markdown_to_pdf(markdown_str)
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f'attachment; filename="{username}_github_audit.pdf"',
                    "Cache-Control": "no-store",
                },
            )
        except Exception as err:
            logger.error("PDF generation failed for %s: %s", username, err)
            raise HTTPException(
                status_code=500,
                detail="Failed to generate PDF report. Please try again.",
            ) from err

    # Default: Return Markdown
    return Response(
        content=markdown_str,
        media_type="text/markdown; charset=utf-8",
        headers={
            "Content-Disposition": f'inline; filename="{username}_github_audit.md"',
            "Cache-Control": "no-store",
        },
    )
