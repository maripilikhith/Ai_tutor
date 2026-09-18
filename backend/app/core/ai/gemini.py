"""
AI Study Companion — Gemini AI Client

Centralized wrapper around the Google Generative AI SDK.
All AI calls go through this client, which handles:
- Text generation (streaming and non-streaming)
- Structured output (JSON mode with Pydantic validation)
- Vision (image → text for document processing)
- Automatic usage logging to ai_usage_logs table
- Retries and error handling
"""

import json
import time
import uuid
from typing import AsyncGenerator, Type

from google import genai
from google.genai import types
from pydantic import BaseModel

from app.config import get_settings
from app.core.database.supabase import get_supabase


# Module-level client cache
_client: genai.Client | None = None

FALLBACK_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
]


def _get_model_chain(requested_model: str | None = None) -> list[str]:
    """Build a list of models to try in order (primary -> fallbacks)."""
    settings = get_settings()
    primary = requested_model or settings.gemini_model
    chain = [primary]
    for fb in FALLBACK_MODELS:
        if fb not in chain:
            chain.append(fb)
    return chain


def get_gemini_client() -> genai.Client:
    """Get or create the default Gemini API client."""
    global _client
    if _client is None:
        settings = get_settings()
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


async def _get_client_for_user(user_id: str | None) -> genai.Client:
    """Get the Gemini client for a specific user (supports BYOK)."""
    if not user_id:
        return get_gemini_client()
        
    db = get_supabase()
    result = db.table("profiles").select("use_custom_key, gemini_api_key").eq("id", user_id).single().execute()
    
    if result.data and result.data.get("use_custom_key") and result.data.get("gemini_api_key"):
        # Create a new client with the user's custom key
        return genai.Client(api_key=result.data["gemini_api_key"].strip())
        
    return get_gemini_client()


async def generate_text(
    prompt: str,
    system_prompt: str = "",
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    user_id: str | None = None,
    project_id: str | None = None,
    feature: str = "general",
) -> str:
    """
    Generate text using Gemini (non-streaming).

    Args:
        prompt: The user prompt
        system_prompt: System instructions
        model: Model name (defaults to config)
        temperature: Creativity (0.0 = deterministic, 1.0 = creative)
        max_tokens: Maximum output tokens
        user_id: For usage logging
        project_id: For usage logging
        feature: Feature name for usage logging (tutor, quiz, etc.)

    Returns:
        The generated text response
    """
    models_to_try = _get_model_chain(model)
    client = await _get_client_for_user(user_id)
    request_id = str(uuid.uuid4())
    start_time = time.time()
    last_error = None

    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt if system_prompt else None,
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
            )

            result_text = response.text or ""
            latency_ms = int((time.time() - start_time) * 1000)

            # Log AI usage
            await _log_usage(
                request_id=request_id,
                feature=feature,
                model=model_name,
                input_tokens=response.usage_metadata.prompt_token_count if response.usage_metadata else 0,
                output_tokens=response.usage_metadata.candidates_token_count if response.usage_metadata else 0,
                latency_ms=latency_ms,
                status="success",
                user_id=user_id,
                project_id=project_id,
            )

            return result_text

        except Exception as e:
            last_error = e
            print(f"[Gemini] generate_text failed with model {model_name}: {e}. Trying fallback...")
            continue

    latency_ms = int((time.time() - start_time) * 1000)
    await _log_usage(
        request_id=request_id,
        feature=feature,
        model=models_to_try[0],
        latency_ms=latency_ms,
        status="error",
        error_message=str(last_error),
        user_id=user_id,
        project_id=project_id,
    )
    raise last_error


async def generate_text_stream(
    prompt: str,
    system_prompt: str = "",
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    user_id: str | None = None,
    project_id: str | None = None,
    feature: str = "tutor",
) -> AsyncGenerator[str, None]:
    """
    Generate text using Gemini with streaming.
    Yields text chunks as they arrive.

    Used by the AI Tutor for progressive response rendering.
    """
    models_to_try = _get_model_chain(model)
    client = await _get_client_for_user(user_id)
    request_id = str(uuid.uuid4())
    start_time = time.time()
    total_text = ""
    stream_started = False
    last_error = None

    for model_name in models_to_try:
        try:
            response = client.models.generate_content_stream(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt if system_prompt else None,
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
            )

            for chunk in response:
                if chunk.text:
                    stream_started = True
                    total_text += chunk.text
                    yield chunk.text

            latency_ms = int((time.time() - start_time) * 1000)

            # Estimate token usage for streaming (approx 4 chars per token)
            input_tokens = int((len(prompt) + len(system_prompt)) / 4)
            output_tokens = int(len(total_text) / 4)

            # Log usage after stream completes
            await _log_usage(
                request_id=request_id,
                feature=feature,
                model=model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                status="success",
                user_id=user_id,
                project_id=project_id,
            )
            return

        except Exception as e:
            last_error = e
            if stream_started:
                # If streaming already started and emitted chunks, cannot safely restart
                raise
            print(f"[Gemini] generate_text_stream failed with model {model_name}: {e}. Trying fallback...")
            continue

    latency_ms = int((time.time() - start_time) * 1000)
    await _log_usage(
        request_id=request_id,
        feature=feature,
        model=models_to_try[0],
        latency_ms=latency_ms,
        status="error",
        error_message=str(last_error),
        user_id=user_id,
        project_id=project_id,
    )
    raise last_error


async def generate_structured(
    prompt: str,
    response_schema: Type[BaseModel],
    system_prompt: str = "",
    model: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 4096,
    max_retries: int = 3,
    user_id: str | None = None,
    project_id: str | None = None,
    feature: str = "structured",
) -> BaseModel:
    """
    Generate structured (JSON) output using Gemini.
    Uses Gemini's JSON mode to produce output that conforms to a Pydantic schema.
    Includes automatic retry on JSON parsing failures and model fallback.
    """
    models_to_try = _get_model_chain(model)
    client = await _get_client_for_user(user_id)
    request_id = str(uuid.uuid4())
    start_time = time.time()
    last_error = None

    for model_name in models_to_try:
        for attempt in range(max_retries):
            try:
                current_prompt = prompt
                if attempt > 0:
                    current_prompt += (
                        "\n\nIMPORTANT: Your previous response had invalid JSON format. "
                        "Please return ONLY valid JSON matching the required schema."
                    )

                response = client.models.generate_content(
                    model=model_name,
                    contents=current_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt if system_prompt else None,
                        temperature=temperature,
                        max_output_tokens=max_tokens,
                        response_mime_type="application/json",
                        response_schema=response_schema,
                    ),
                )

                result_text = response.text or ""
                latency_ms = int((time.time() - start_time) * 1000)

                # Parse and validate with Pydantic
                parsed = response_schema.model_validate_json(result_text)

                await _log_usage(
                    request_id=request_id,
                    feature=feature,
                    model=model_name,
                    input_tokens=response.usage_metadata.prompt_token_count if response.usage_metadata else 0,
                    output_tokens=response.usage_metadata.candidates_token_count if response.usage_metadata else 0,
                    latency_ms=latency_ms,
                    status="success",
                    user_id=user_id,
                    project_id=project_id,
                    metadata={"attempt": attempt + 1},
                )

                return parsed

            except Exception as e:
                last_error = e
                err_msg = str(e)
                print(f"[Gemini] generate_structured attempt {attempt + 1} with {model_name} failed: {e}")
                if "503" in err_msg or "429" in err_msg or "UNAVAILABLE" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                    print(f"[Gemini] Switching to fallback model due to service limit on {model_name}")
                    break
                continue

    # All retries across all fallback models failed
    latency_ms = int((time.time() - start_time) * 1000)
    await _log_usage(
        request_id=request_id,
        feature=feature,
        model=models_to_try[0],
        latency_ms=latency_ms,
        status="error",
        error_message=f"Failed after retries: {str(last_error)}",
        user_id=user_id,
        project_id=project_id,
    )

    from app.core.exceptions import AIServiceError
    raise AIServiceError(
        detail=f"Failed to generate valid structured output after retries: {last_error}"
    )


async def generate_vision(
    images: list[bytes],
    prompt: str,
    model: str | None = None,
    user_id: str | None = None,
    project_id: str | None = None,
) -> str:
    """
    Process images with Gemini Vision (multimodal).
    Used for document processing: page images -> extracted text + concepts.
    """
    models_to_try = _get_model_chain(model)
    client = await _get_client_for_user(user_id)
    request_id = str(uuid.uuid4())
    start_time = time.time()
    last_error = None

    contents = []
    for img_bytes in images:
        contents.append(types.Part.from_bytes(data=img_bytes, mime_type="image/png"))
    contents.append(prompt)

    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=0.2,  # Low temperature for extraction accuracy
                    max_output_tokens=8192,
                ),
            )

            result_text = response.text or ""
            latency_ms = int((time.time() - start_time) * 1000)

            await _log_usage(
                request_id=request_id,
                feature="document_processing",
                model=model_name,
                input_tokens=response.usage_metadata.prompt_token_count if response.usage_metadata else 0,
                output_tokens=response.usage_metadata.candidates_token_count if response.usage_metadata else 0,
                latency_ms=latency_ms,
                status="success",
                user_id=user_id,
                project_id=project_id,
                metadata={"image_count": len(images)},
            )

            return result_text

        except Exception as e:
            last_error = e
            print(f"[Gemini] generate_vision failed with {model_name}: {e}. Trying fallback...")
            continue

    latency_ms = int((time.time() - start_time) * 1000)
    await _log_usage(
        request_id=request_id,
        feature="document_processing",
        model=models_to_try[0],
        latency_ms=latency_ms,
        status="error",
        error_message=str(last_error),
        user_id=user_id,
        project_id=project_id,
    )
    raise last_error


# ── Private: Usage Logging ──

async def _log_usage(
    request_id: str,
    feature: str,
    model: str,
    latency_ms: int = 0,
    input_tokens: int = 0,
    output_tokens: int = 0,
    status: str = "success",
    error_message: str | None = None,
    user_id: str | None = None,
    project_id: str | None = None,
    metadata: dict | None = None,
) -> None:
    """
    Log AI usage to the ai_usage_logs table.
    Silently fails — logging should never break the main flow.
    """
    try:
        db = get_supabase()
        total_tokens = input_tokens + output_tokens

        # Rough cost estimation (Gemini 2.5 Flash pricing)
        # Input: $0.15/1M tokens, Output: $0.60/1M tokens
        estimated_cost = (input_tokens * 0.15 / 1_000_000) + (output_tokens * 0.60 / 1_000_000)

        db.table("ai_usage_logs").insert({
            "request_id": request_id,
            "user_id": user_id,
            "project_id": project_id,
            "feature": feature,
            "model": model,
            "provider": "google",
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_usd": round(estimated_cost, 6),
            "latency_ms": latency_ms,
            "status": status,
            "error_message": error_message,
            "prompt_summary": feature,  # Brief description, NOT the full prompt
            "metadata": metadata or {},
        }).execute()
    except Exception:
        # Logging failures should never crash the application
        pass
