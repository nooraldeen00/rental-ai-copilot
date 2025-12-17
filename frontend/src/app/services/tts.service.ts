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
  private _isSupported = true;
  private _isSpeaking = false;
  private _isLoading = false;
  private _useBrowserTts = false; // Fallback to browser TTS if ElevenLabs fails
  private browserSpeechSynthesis: SpeechSynthesis | null = null;
  private currentUtterance: SpeechSynthesisUtterance | null = null;

  constructor(private api: ApiService) {
    // Check if Audio is supported in browser
    if (typeof window !== 'undefined' && typeof Audio !== 'undefined') {
      this._isSupported = true;
    } else {
      this._isSupported = false;
    }

    // Check for browser Speech Synthesis API (fallback)
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      this.browserSpeechSynthesis = window.speechSynthesis;
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
   * Speak the given text using ElevenLabs voice (with browser TTS fallback).
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
          // Try browser TTS as fallback
          this.speakWithBrowserTts(cleanText, onEnd, onError, language);
        };

        // Start playback
        this.audio.play().catch((err) => {
          console.error('Audio play error:', err);
          this._isSpeaking = false;
          this._isLoading = false;
          this.cleanup();
          // Try browser TTS as fallback
          this.speakWithBrowserTts(cleanText, onEnd, onError, language);
        });
      },
      error: (err) => {
        console.error('TTS API error:', err);
        this._isLoading = false;

        // Try browser TTS as fallback
        console.log('Falling back to browser TTS...');
        this.speakWithBrowserTts(cleanText, onEnd, onError, language);
      },
    });

    return true;
  }

  /**
   * Fallback: Speak using browser's built-in Speech Synthesis API.
   */
  private speakWithBrowserTts(
    text: string,
    onEnd?: () => void,
    onError?: (error: string) => void,
    language?: string
  ): void {
    console.log('Using browser TTS fallback...');

    if (!this.browserSpeechSynthesis) {
      console.error('Browser speech synthesis not available');
      onError?.('Text-to-speech is not available in this browser.');
      return;
    }

    const startSpeaking = () => {
      try {
        // Cancel any ongoing speech
        this.browserSpeechSynthesis!.cancel();

        // Create utterance
        const utterance = new SpeechSynthesisUtterance(text);
        this.currentUtterance = utterance;

        // Set language
        utterance.lang = language || 'en-US';

        // Configure voice settings
        utterance.rate = 0.95;
        utterance.pitch = 1.0;
        utterance.volume = 1.0;

        // Try to find a good voice
        const voices = this.browserSpeechSynthesis!.getVoices();
        console.log(`Available voices: ${voices.length}`);

        if (voices.length > 0) {
          const langCode = (language || 'en-US').split('-')[0];
          // Prefer voices that match the language
          let matchingVoice = voices.find(v => v.lang.toLowerCase().startsWith(langCode.toLowerCase()));
          // Fallback to any English voice
          if (!matchingVoice) {
            matchingVoice = voices.find(v => v.lang.toLowerCase().startsWith('en'));
          }
          // Fallback to first available voice
          if (!matchingVoice) {
            matchingVoice = voices[0];
          }
          if (matchingVoice) {
            utterance.voice = matchingVoice;
            console.log(`Using voice: ${matchingVoice.name} (${matchingVoice.lang})`);
          }
        }

        utterance.onstart = () => {
          console.log('Browser TTS started');
          this._isSpeaking = true;
          this._isLoading = false;
        };

        utterance.onend = () => {
          console.log('Browser TTS ended');
          this._isSpeaking = false;
          this.currentUtterance = null;
          onEnd?.();
        };

        utterance.onerror = (event) => {
          console.error('Browser TTS error:', event.error);
          this._isSpeaking = false;
          this._isLoading = false;
          this.currentUtterance = null;
          // Don't show error for 'canceled' - that's intentional
          if (event.error !== 'canceled') {
            onError?.('Speech synthesis failed. Please try again.');
          }
        };

        // Start speaking
        this._isLoading = false;
        this._isSpeaking = true;
        this.browserSpeechSynthesis!.speak(utterance);
        console.log('Browser TTS speak() called');

      } catch (err) {
        console.error('Browser TTS exception:', err);
        this._isLoading = false;
        this._isSpeaking = false;
        onError?.('Speech synthesis failed. Please try again.');
      }
    };

    // Voices may not be loaded immediately - wait for them
    const voices = this.browserSpeechSynthesis.getVoices();
    if (voices.length > 0) {
      startSpeaking();
    } else {
      // Wait for voices to load
      console.log('Waiting for voices to load...');
      this.browserSpeechSynthesis.onvoiceschanged = () => {
        console.log('Voices loaded');
        startSpeaking();
      };
      // Also try after a short delay as backup
      setTimeout(() => {
        if (!this._isSpeaking && !this.currentUtterance) {
          console.log('Starting speech after timeout');
          startSpeaking();
        }
      }, 100);
    }
  }

  /**
   * Stop current speech playback.
   */
  stop(): void {
    // Stop HTML5 audio
    if (this.audio) {
      this.audio.pause();
      this.audio.currentTime = 0;
    }

    // Stop browser speech synthesis
    if (this.browserSpeechSynthesis) {
      this.browserSpeechSynthesis.cancel();
    }
    this.currentUtterance = null;

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
