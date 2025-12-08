# backend/routes/tts.py
"""
Text-to-Speech route using ElevenLabs API.
Provides natural, human-like voice synthesis for quote summaries.
"""
from __future__ import annotations

import os
from typing import Any, Dict

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

# ElevenLabs configuration
ELEVENLABS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel - trustworthy, natural voice
ELEVENLABS_API_URL = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"


def get_elevenlabs_api_key() -> str | None:
    """Get the ElevenLabs API key from environment."""
    return os.getenv("ELEVENLABS_API_KEY")


class TTSRequest(BaseModel):
    """Request body for text-to-speech conversion."""
    text: str = Field(..., min_length=1, max_length=5000, description="Text to convert to speech")


@router.post("/speak")
async def text_to_speech(req: TTSRequest, request: Request) -> Response:
    """
    Convert text to speech using ElevenLabs Rachel voice.
    Returns MP3 audio stream.
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

    logger.info(
        f"TTS request received",
        extra={
            "extra_fields": {
                "request_id": request_id,
                "text_length": len(req.text),
            }
        },
    )

    # ElevenLabs API payload
    payload = {
        "text": req.text,
        "model_id": "eleven_multilingual_v2",  # Latest model, works on free tier
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
                ELEVENLABS_API_URL,
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
                        }
                    },
                )
                raise HTTPException(
                    status_code=502,
                    detail=f"TTS service error: {response.status_code}",
                )

            audio_content = response.content

            logger.info(
                f"TTS audio generated successfully",
                extra={
                    "extra_fields": {
                        "request_id": request_id,
                        "audio_size_bytes": len(audio_content),
                    }
                },
            )

            return Response(
                content=audio_content,
                media_type="audio/mpeg",
                headers={
                    "Content-Length": str(len(audio_content)),
                    "Cache-Control": "no-cache",
                },
            )

    except httpx.TimeoutException:
        logger.error(
            "ElevenLabs API timeout",
            extra={"extra_fields": {"request_id": request_id}},
        )
        raise HTTPException(
            status_code=504,
            detail="TTS service timeout. Please try again.",
        )
    except httpx.RequestError as e:
        logger.error(
            f"ElevenLabs API connection error: {str(e)}",
            extra={"extra_fields": {"request_id": request_id}},
        )
        raise HTTPException(
            status_code=502,
            detail="TTS service unavailable. Please try again later.",
        )


@router.get("/status")
async def tts_status() -> Dict[str, Any]:
    """
    Check if TTS service is configured and available.
    """
    return {
        "configured": bool(get_elevenlabs_api_key()),
        "voice_id": ELEVENLABS_VOICE_ID,
        "voice_name": "Rachel",
        "provider": "ElevenLabs",
    }
