import logging
import uuid
from collections.abc import Iterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
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
    normalized_username = username.strip().lower()
    profile_data = cache.get_profile(normalized_username)
    if profile_data is None:
        raise HTTPException(
            status_code=404, detail="Profile not found. Analyze the profile first."
        )

    context = build_profile_context(profile_data)
    session_id = str(uuid.uuid4())
    chat_cache.save_session(
        session_id=session_id, username=normalized_username, context=context, history=[]
    )

    return {
        "session_id": session_id,
        "username": normalized_username,
        "message": "Chat session initialized.",
    }


@router.post("/message")
def send_message(request: ChatRequest):
    session = chat_cache.get_session(request.session_id)
    if session is None:
        raise HTTPException(
            status_code=404, detail="Chat session expired or not found."
        )

    context = session["context"]
    history = session["history"]

    def response_generator() -> Iterator[str]:
        accumulated_chunks: list[str] = []
        provider_used = None
        gemini_gen = None
        groq_gen = None

        try:
            # 1. Try Groq (Primary)
            try:
                groq_gen = GroqProvider().stream_chat(
                    context=context, history=history, message=request.message
                )
                first_chunk = next(groq_gen, None)
                if first_chunk is not None:
                    accumulated_chunks.append(first_chunk)
                    yield first_chunk
                    provider_used = "groq"
                    for chunk in groq_gen:
                        if chunk:
                            accumulated_chunks.append(chunk)
                            yield chunk
            except Exception as groq_err:  # noqa: BLE001
                logger.warning(
                    "Groq stream failed. Falling back to Gemini. Error: %s", groq_err
                )
                if provider_used == "groq":
                    error_msg = "\n\n**[Connection Interrupted]** _Groq dropped the stream. Please try asking again._"
                    accumulated_chunks.append(error_msg)
                    yield error_msg

            # 2. Fallback to Gemini (Backup)
            if provider_used is None and not chat_cache.is_gemini_disabled():
                try:
                    gemini_gen = GeminiProvider().stream_chat(
                        context=context, history=history, message=request.message
                    )
                    first_chunk = next(gemini_gen, None)
                    if first_chunk is not None:
                        accumulated_chunks.append(first_chunk)
                        yield first_chunk
                        provider_used = "gemini"
                        for chunk in gemini_gen:
                            if chunk:
                                accumulated_chunks.append(chunk)
                                yield chunk
                except Exception as gemini_err:
                    error_str = str(gemini_err).upper()
                    if any(
                        err in error_str
                        for err in [
                            "429",
                            "RESOURCE_EXHAUSTED",
                            "503",
                            "UNAVAILABLE",
                            "OVERLOADED",
                        ]
                    ):
                        logger.warning(
                            "Gemini capacity/rate limit exceeded. Disabling for 5 minutes."
                        )
                        chat_cache.disable_gemini(ttl=300)
                        if provider_used == "gemini":
                            error_msg = "\n\n**[Connection Interrupted]** _Gemini dropped the stream due to high server demand. Please try asking again._"
                            accumulated_chunks.append(error_msg)
                            yield error_msg
                    else:
                        logger.exception("Gemini stream fallback also failed.")

            # 3. Total Failure
            if provider_used is None:
                yield "All LLM providers failed to generate a response."
                return

            # 4. Save History
            full_response = "".join(accumulated_chunks).strip()
            if full_response and "All LLM providers failed" not in full_response:
                chat_cache.append_messages(
                    session_id=request.session_id,
                    user_message=request.message,
                    assistant_message=full_response,
                )
        finally:
            if gemini_gen is not None:
                gemini_gen.close()
            if groq_gen is not None:
                groq_gen.close()

    return StreamingResponse(
        response_generator(), media_type="text/plain; charset=utf-8"
    )
