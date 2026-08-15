import logging
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.cache.chat_cache import ChatCache
from app.cache.simple_cache import cache
from app.clients.llm.gemini_provider import GeminiProvider
from app.clients.llm.groq_provider import GroqProvider
from app.llm.profile_context import build_profile_context

logger = logging.getLogger(__name__)

router = APIRouter()

chat_cache = ChatCache()


class ChatRequest(BaseModel):
    session_id: str
    message: str


@router.post("/start/{username}")
def start_chat(username: str):
    """Initializing a chat session for an analyzed GitHub profile"""

    # Normalize username to match cache key format
    normalized_username = username.strip().lower()

    profile_data = cache.get_profile(normalized_username)

    if profile_data is None:
        raise HTTPException(
            status_code=404,
            detail="Profile not found. Analyze the profile first.",
        )

    context = build_profile_context(profile_data)

    session_id = str(uuid.uuid4())

    chat_cache.save_session(
        session_id=session_id,
        username=normalized_username,
        context=context,
        history=[],
    )

    return {
        "session_id": session_id,
        "username": normalized_username,
        "message": "Chat session initialized.",
    }


@router.post("/message")
def send_message(request: ChatRequest):
    """Send a message with automatic Gemini → Groq fallback and circuit breaking"""

    session = chat_cache.get_session(request.session_id)

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Chat session expired or not found.",
        )

    context = session["context"]
    history = session["history"]

    response_text = None
    provider_used = None

    # Try Gemini ONLY if it's not currently rate-limited/disabled
    if not chat_cache.is_gemini_disabled():
        try:
            response_text = GeminiProvider().chat(
                context=context,
                history=history,
                message=request.message,
            )
            provider_used = "gemini"

        except Exception as gemini_error:  # noqa: BLE001
            error_str = str(gemini_error)

            # Check if this was a rate limit / quota exhaustion
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                logger.warning(
                    "Gemini rate limit / quota exceeded (429). Disabling Gemini calls for 24 hours."
                )
                # Cool down Gemini for 24 hours (86400s)
                chat_cache.disable_gemini(ttl=86400)
            else:
                logger.warning(
                    "Gemini failed. Falling back to Groq. Error: %s",
                    gemini_error,
                )

    # Fallback to Groq if Gemini was disabled, failed, or came back empty
    if response_text is None or not response_text.strip():
        try:
            response_text = GroqProvider().chat(
                context=context,
                history=history,
                message=request.message,
            )
            provider_used = "groq"

        except Exception:
            logger.exception("Groq fallback also failed.")
            raise HTTPException(
                status_code=502,
                detail="All LLM providers failed to generate a response.",
            ) from None

    # Persist chat history
    chat_cache.append_messages(
        session_id=request.session_id,
        user_message=request.message,
        assistant_message=response_text,
    )

    return {
        "session_id": request.session_id,
        "provider": provider_used,
        "response": response_text,
    }
