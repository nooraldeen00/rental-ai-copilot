// frontend/src/app/services/tts.service.ts
/**
 * Text-to-Speech Service using ElevenLabs API via backend.
 * Provides natural, human-like voice playback using Rachel voice.
 */
import { Injectable } from '@angular/core';
import { ApiService } from './api';

export interface TtsState {
  isSupported: boolean;
  isSpeaking: boolean;
  isLoading: boolean;
  error: string | null;
}

@Injectable({ providedIn: 'root' })
export class TtsService {
  private audio: HTMLAudioElement | null = null;
  private currentAudioUrl: string | null = null;
  private _isSupported = true; // ElevenLabs is always supported if backend is running
  private _isSpeaking = false;
  private _isLoading = false;

  constructor(private api: ApiService) {
    // Check if Audio is supported in browser
    if (typeof window !== 'undefined' && typeof Audio !== 'undefined') {
      this._isSupported = true;
    } else {
      this._isSupported = false;
    }
  }

  /**
   * Check if text-to-speech is supported.
   */
  get isSupported(): boolean {
    return this._isSupported;
  }

  /**
   * Check if speech is currently playing.
   */
  get isSpeaking(): boolean {
    return this._isSpeaking;
  }

  /**
   * Check if audio is currently loading.
   */
  get isLoading(): boolean {
    return this._isLoading;
  }

  /**
   * Get current TTS state for UI binding.
   */
  getState(): TtsState {
    return {
      isSupported: this._isSupported,
      isSpeaking: this._isSpeaking,
      isLoading: this._isLoading,
      error: null,
    };
  }

  /**
   * Speak the given text using ElevenLabs voice.
   *
   * @param text The text to speak
   * @param onEnd Callback when speech finishes
   * @param onError Callback on error
   * @param language Optional language code (e.g., 'en-US', 'es-ES', 'ar-SA', 'ja-JP')
   */
  speak(
    text: string,
    onEnd?: () => void,
    onError?: (error: string) => void,
    language?: string
  ): boolean {
    if (!this._isSupported) {
      onError?.('Audio playback is not supported in this browser.');
      return false;
    }

    // Stop any current playback
    this.stop();

    // Clean up text for better speech
    const cleanText = this.prepareTextForSpeech(text);

    if (!cleanText.trim()) {
      onError?.('No text to speak.');
      return false;
    }

    this._isLoading = true;

    // Call backend TTS API with language
    this.api.textToSpeech(cleanText, language).subscribe({
      next: (audioBlob) => {
        this._isLoading = false;

        // Create audio URL from blob
        this.currentAudioUrl = URL.createObjectURL(audioBlob);

        // Create and configure audio element
        this.audio = new Audio(this.currentAudioUrl);

        this.audio.onplay = () => {
          this._isSpeaking = true;
        };

        this.audio.onended = () => {
          this._isSpeaking = false;
          this.cleanup();
          onEnd?.();
        };

        this.audio.onerror = (event) => {
          console.error('Audio playback error:', event);
          this._isSpeaking = false;
          this._isLoading = false;
          this.cleanup();
          onError?.('Failed to play audio.');
        };

        // Start playback
        this.audio.play().catch((err) => {
          console.error('Audio play error:', err);
          this._isSpeaking = false;
          this._isLoading = false;
          this.cleanup();
          onError?.('Failed to start audio playback.');
        });
      },
      error: (err) => {
        console.error('TTS API error:', err);
        this._isLoading = false;

        // Provide more helpful error messages
        const status = err.status;
        if (status === 503) {
          onError?.('Text-to-speech not configured. Please set ELEVENLABS_API_KEY.');
        } else if (status === 504) {
          onError?.('Text-to-speech service timeout. Please try again.');
        } else if (status === 502) {
          onError?.('Text-to-speech service unavailable. Please try again later.');
        } else {
          onError?.('Failed to generate speech. Please try again.');
        }
      },
    });

    return true;
  }

  /**
   * Stop current speech playback.
   */
  stop(): void {
    if (this.audio) {
      this.audio.pause();
      this.audio.currentTime = 0;
    }
    this._isSpeaking = false;
    this._isLoading = false;
    this.cleanup();
  }

  /**
   * Clean up audio resources.
   */
  private cleanup(): void {
    if (this.currentAudioUrl) {
      URL.revokeObjectURL(this.currentAudioUrl);
      this.currentAudioUrl = null;
    }
    this.audio = null;
  }

  /**
   * Prepare text for speech synthesis.
   * Cleans up technical jargon and formats for natural reading.
   */
  private prepareTextForSpeech(text: string): string {
    return text
      // Remove emoji
      .replace(/[\u{1F300}-\u{1F9FF}]/gu, '')
      // Replace common abbreviations
      .replace(/\bpct\b/gi, 'percent')
      .replace(/\bqty\b/gi, 'quantity')
      .replace(/\bSKU\b/g, 'S K U')
      // Format currency naturally
      .replace(/\$(\d+(?:,\d{3})*(?:\.\d{2})?)/g, (match, amount) => {
        return `${amount} dollars`;
      })
      // Clean up excessive whitespace
      .replace(/\s+/g, ' ')
      .trim();
  }

  /**
   * Convert an array of notes to a single speakable string.
   */
  notesToSpeakableText(notes: string[]): string {
    if (!notes || notes.length === 0) return '';

    // Filter out technical notes and focus on the AI summary
    const humanNotes = notes.filter(note => {
      const lower = note.toLowerCase();
      // Skip technical parsing notes
      return !lower.includes('intelligent parsing') &&
             !lower.includes('rental period:') &&
             !lower.includes('identified') &&
             !lower.includes('based on your specified');
    });

    // If we filtered everything, use the first note
    const speakableNotes = humanNotes.length > 0 ? humanNotes : [notes[0]];

    return speakableNotes.join('. ');
  }
}
