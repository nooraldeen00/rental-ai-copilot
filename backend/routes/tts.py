# backend/routes/tts.py
"""
Text-to-Speech route using ElevenLabs API.
Provides natural, human-like voice synthesis for quote summaries.
Supports multiple languages with native voices.
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

from pathlib import Path
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field
import httpx

from backend.core.logging_config import get_logger

# Ensure .env is loaded from project root
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

router = APIRouter(prefix="/tts", tags=["tts"])
logger = get_logger(__name__)

# ElevenLabs voice configuration per language
# Using multilingual v2 model which supports all these languages with any voice
# but we select native speakers for best quality
ELEVENLABS_VOICES = {
    "en-US": {
        "voice_id": "21m00Tcm4TlvDq8ikWAM",  # Rachel - trustworthy, natural English voice
        "name": "Rachel",
        "native": True,
    },
    "es-ES": {
        "voice_id": "AZnzlk1XvdvUeBnXmlld",  # Domi - Spanish-accented voice
        "name": "Domi",
        "native": True,
    },
    "ar-SA": {
        "voice_id": "pMsXgVXv3BLzUgSXRplE",  # Yosef - Arabic-accented voice
        "name": "Yosef",
        "native": True,
    },
    "ja-JP": {
        "voice_id": "Xb7hH8MSUJpSbSDYk0k2",  # Alice - supports Japanese
        "name": "Alice",
        "native": True,
    },
}

# Default fallback voice (English)
DEFAULT_VOICE = ELEVENLABS_VOICES["en-US"]

ELEVENLABS_API_BASE = "https://api.elevenlabs.io/v1/text-to-speech"


def get_elevenlabs_api_key() -> str | None:
    """Get the ElevenLabs API key from environment."""
    return os.getenv("ELEVENLABS_API_KEY")


def get_voice_for_language(language: str) -> Dict[str, Any]:
    """
    Get the appropriate voice configuration for a language.
    Falls back to English if language not supported.

    Returns:
        Dict with voice_id, name, native, and fallback_used keys
    """
    if language in ELEVENLABS_VOICES:
        voice = ELEVENLABS_VOICES[language].copy()
        voice["fallback_used"] = False
        return voice
    else:
        voice = DEFAULT_VOICE.copy()
        voice["fallback_used"] = True
        voice["original_language"] = language
        return voice


class TTSRequest(BaseModel):
    """Request body for text-to-speech conversion."""
    text: str = Field(..., min_length=1, max_length=5000, description="Text to convert to speech")
    language: Optional[str] = Field(
        default="en-US",
        description="Language code (e.g., 'en-US', 'es-ES', 'ar-SA', 'ja-JP')"
    )


@router.post("/speak")
async def text_to_speech(req: TTSRequest, request: Request) -> Response:
    """
    Convert text to speech using ElevenLabs with language-specific voices.
    Returns MP3 audio stream.

    Supported languages:
    - en-US: Rachel (English)
    - es-ES: Domi (Spanish)
    - ar-SA: Yosef (Arabic)
    - ja-JP: Alice (Japanese)

    Falls back to English voice if language not supported.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    api_key = get_elevenlabs_api_key()

    if not api_key:
        logger.error(
            "ElevenLabs API key not configured",
            extra={"extra_fields": {"request_id": request_id}},
        )
        raise HTTPException(
            status_code=503,
            detail="Text-to-speech service not configured. Please set ELEVENLABS_API_KEY.",
        )

    # Get voice for requested language
    language = req.language or "en-US"
    voice = get_voice_for_language(language)

    logger.info(
        f"TTS request received",
        extra={
            "extra_fields": {
                "request_id": request_id,
                "text_length": len(req.text),
                "language": language,
                "voice_name": voice["name"],
                "fallback_used": voice.get("fallback_used", False),
            }
        },
    )

    # Build API URL with voice-specific endpoint
    api_url = f"{ELEVENLABS_API_BASE}/{voice['voice_id']}"

    # ElevenLabs API payload
    payload = {
        "text": req.text,
        "model_id": "eleven_multilingual_v2",  # Supports all languages with any voice
        "voice_settings": {
            "stability": 0.5,        # Balance between consistency and expressiveness
            "similarity_boost": 0.75, # How closely to match original voice
        },
    }

    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                api_url,
                json=payload,
                headers=headers,
            )

            if response.status_code != 200:
                error_detail = response.text
                logger.error(
                    f"ElevenLabs API error: {response.status_code}",
                    extra={
                        "extra_fields": {
                            "request_id": request_id,
                            "status_code": response.status_code,
                            "error": error_detail[:500],
                            "voice_id": voice["voice_id"],
                        }
                    },
                )
                raise HTTPException(
                    status_code=502,
                    detail=f"TTS service error: {response.status_code}",
                )

            audio_content = response.content

            # Build response headers
            response_headers = {
                "Content-Length": str(len(audio_content)),
                "Cache-Control": "no-cache",
                "X-TTS-Voice": voice["name"],
                "X-TTS-Language": language,
            }

            # Add fallback warning header if applicable
            if voice.get("fallback_used"):
                response_headers["X-TTS-Fallback"] = "true"
                response_headers["X-TTS-Original-Language"] = voice.get("original_language", "unknown")

            logger.info(
                f"TTS audio generated successfully",
                extra={
                    "extra_fields": {
                        "request_id": request_id,
                        "audio_size_bytes": len(audio_content),
                        "language": language,
                        "voice": voice["name"],
                    }
                },
            )

            return Response(
                content=audio_content,
                media_type="audio/mpeg",
                headers=response_headers,
            )

    except httpx.TimeoutException:
        logger.error(
            "ElevenLabs API timeout",
            extra={"extra_fields": {"request_id": request_id, "language": language}},
        )
        raise HTTPException(
            status_code=504,
            detail="TTS service timeout. Please try again.",
        )
    except httpx.RequestError as e:
        logger.error(
            f"ElevenLabs API connection error: {str(e)}",
            extra={"extra_fields": {"request_id": request_id, "language": language}},
        )
        raise HTTPException(
            status_code=502,
            detail="TTS service unavailable. Please try again later.",
        )


@router.get("/status")
async def tts_status() -> Dict[str, Any]:
    """
    Check if TTS service is configured and available.
    Returns configuration status and supported languages.
    """
    return {
        "configured": bool(get_elevenlabs_api_key()),
        "provider": "ElevenLabs",
        "model": "eleven_multilingual_v2",
        "default_voice": DEFAULT_VOICE["name"],
        "supported_languages": [
            {
                "code": code,
                "voice_name": voice["name"],
                "native": voice["native"],
            }
            for code, voice in ELEVENLABS_VOICES.items()
        ],
    }
