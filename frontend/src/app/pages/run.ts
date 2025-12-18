// frontend/src/app/pages/run.ts
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule, DecimalPipe } from '@angular/common';
import { ApiService, QuoteRequest, QuoteRunResponse } from '../services/api';
import { TtsService } from '../services/tts.service';
import { LanguageService } from '../services/language.service';

type Tier = 'A' | 'B' | 'C';

interface RunForm {
  request_text: string;
  customer_tier: Tier;
  location?: string;
  seed?: number | null;
  start_date?: string;
  end_date?: string;
  zip?: string;
}

@Component({
  selector: 'app-run',
  standalone: true,
  imports: [CommonModule, FormsModule, DecimalPipe],
  templateUrl: './run.html',
})
export class RunPage {
  form: RunForm = {
    request_text: '',
    customer_tier: 'B',
    location: '',
    seed: null,
    start_date: '',
    end_date: '',
    zip: '',
  };

  loading = false;
  error: string | null = null;
  result: QuoteRunResponse | null = null;

  // PDF download state
  downloadingPdf = false;
  pdfError: string | null = null;

  // TTS state
  isSpeaking = false;
  ttsError: string | null = null;

  constructor(
    private api: ApiService,
    private tts: TtsService,
    public langService: LanguageService
  ) {}

  /**
   * Check if TTS is supported in the browser.
   */
  get ttsSupported(): boolean {
    return this.tts.isSupported;
  }

  // alias used by the template
  get model() { return this.form; }
  onRun() { this.onGenerateQuote(); }
  reset() { this.onClear(); }

  onGenerateQuote() {
    this.loading = true;
    this.error = null;
    this.result = null;
    this.pdfError = null;
    this.ttsError = null;
    this.tts.stop(); // Stop any playing audio

    const payload: QuoteRequest = {
      request_text: this.form.request_text,
      customer_tier: this.form.customer_tier,
      location: this.form.location || '',
      zip: this.form.zip,
      start_date: this.form.start_date,
      end_date: this.form.end_date,
      seed: this.form.seed ?? undefined,
      language: this.langService.selectedLanguage, // Pass selected language for AI summary
    };

    this.api.runQuote(payload).subscribe({
      next: (res: QuoteRunResponse) => {
        this.result = res;
        this.loading = false;
      },
      error: (err: unknown) => {
        console.error(err);
        this.error = 'Failed to run quote';
        this.loading = false;
      },
    });
  }

  onClear() {
    this.form = {
      request_text: '',
      customer_tier: 'B',
      location: '',
      seed: null,
      start_date: '',
      end_date: '',
      zip: '',
    };
    this.error = null;
    this.result = null;
    this.pdfError = null;
    this.ttsError = null;
    this.tts.stop();
    this.isSpeaking = false;
  }

  /**
   * Download the current quote as a PDF
   */
  onDownloadPdf() {
    if (!this.result?.run_id) return;

    this.downloadingPdf = true;
    this.pdfError = null;

    this.api.downloadQuotePdf(this.result.run_id).subscribe({
      next: () => {
        this.downloadingPdf = false;
      },
      error: (err: unknown) => {
        console.error('PDF download failed:', err);
        this.pdfError = 'Failed to download PDF. Please try again.';
        this.downloadingPdf = false;
      },
    });
  }

  /**
   * Play/stop the AI quote summary using text-to-speech.
   * If already speaking, stops and restarts from the beginning.
   */
  onPlaySummary() {
    console.log('Play Summary clicked, notes:', this.result?.quote?.notes);

    if (!this.result?.quote?.notes?.length) {
      this.ttsError = 'No AI notes available to read.';
      return;
    }

    // If currently speaking, stop first
    if (this.isSpeaking) {
      this.tts.stop();
      this.isSpeaking = false;
      return;
    }

    this.ttsError = null;

    // Convert notes array to speakable text
    const text = this.tts.notesToSpeakableText(this.result.quote.notes);
    console.log('Speakable text:', text);

    if (!text || !text.trim()) {
      this.ttsError = 'No speakable content found in notes.';
      return;
    }

    const success = this.tts.speak(
      text,
      () => {
        // On end
        console.log('TTS ended');
        this.isSpeaking = false;
      },
      (error) => {
        // On error
        console.error('TTS error:', error);
        this.ttsError = error;
        this.isSpeaking = false;
      },
      this.langService.selectedLanguage // Pass the selected language
    );

    console.log('TTS speak() returned:', success);
    if (success) {
      this.isSpeaking = true;
    }
  }
}
