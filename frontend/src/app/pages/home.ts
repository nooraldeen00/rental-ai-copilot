import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { NgIf, NgFor, DecimalPipe } from '@angular/common';
import { ApiService } from '../services/api';
import { TtsService } from '../services/tts.service';
import { InventoryBrowserComponent } from '../components/inventory-browser';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [FormsModule, NgIf, NgFor, DecimalPipe, InventoryBrowserComponent],
  templateUrl: './home.html',
})
export class HomeComponent {
  // Form model used by the template
  form: any = {
    request_text: '',
    customer_tier: 'B',
    location: '',
    seed: '',
    start_date: '',
    end_date: '',
    zip: '',
  };

  // UI state used by the template
  loading = false;
  error = '';
  result: any = null;

  // PDF download state
  downloadingPdf = false;
  pdfError: string | null = null;

  // TTS state
  isSpeaking = false;
  ttsLoading = false;
  ttsError: string | null = null;

  // Inventory browser state
  showInventoryBrowser = false;

  constructor(private api: ApiService, private tts: TtsService) {}

  get ttsSupported(): boolean {
    return this.tts.isSupported;
  }

  
  onSubmit() {
     this.loading = true;
     this.error = '';
     this.result = null;

    // frontend-only fake data (no backend)
    // comment OUT the API call and uncomment the fake quote if you want:

    /*
    this.result = {
      totals: {
        subtotal: 540,
        tax: 44.55,
        grand_total: 584.55,
        fees: [{ name: 'Environmental fee', amount: 15 }],
      },
      items: [
        { name: 'Light Tower – LED', qty: 2, rate: 180, total: 360 },
        { name: 'Delivery & Pickup', qty: 1, rate: 180, total: 180 },
      ],
      ai_notes:
        'Customer needs 2 light towers for Fri–Sun in Dallas. Suggested LED towers with weekend rate and standard delivery.',
    };
    this.loading = false;
    return;
    */

    //  real backend
    this.api.runQuote(this.form).subscribe({
      next: (res) => {
        console.log('API result:', res);
        this.result = res;
        this.loading = false;
      },
      error: () => {
        this.error = 'Quote engine connection failed. Please verify service availability.';
        this.loading = false;
      },
    });
  }

  onClear() {
    this.form = {
      request_text: '',
      customer_tier: 'B',
      location: '',
      seed: '',
      start_date: '',
      end_date: '',
      zip: '',
    };
    this.error = '';
    this.result = null;
    this.loading = false;
  }

  // Helper to calculate total fees
  calculateFees(fees: any[]): number {
    if (!fees || !fees.length) return 0;
    return fees.reduce((sum, fee) => sum + (fee.amount || fee.price || 0), 0);
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
   * Play/stop the AI quote summary using ElevenLabs text-to-speech.
   */
  onPlaySummary() {
    if (!this.result?.quote?.notes?.length) {
      this.ttsError = 'No AI notes available to read.';
      return;
    }

    // If currently speaking or loading, stop
    if (this.isSpeaking || this.ttsLoading) {
      this.tts.stop();
      this.isSpeaking = false;
      this.ttsLoading = false;
      return;
    }

    this.ttsError = null;
    this.ttsLoading = true;

    // Convert notes array to speakable text
    const text = this.tts.notesToSpeakableText(this.result.quote.notes);

    this.tts.speak(
      text,
      () => {
        // On end
        this.isSpeaking = false;
        this.ttsLoading = false;
      },
      (error) => {
        // On error
        this.ttsError = error;
        this.isSpeaking = false;
        this.ttsLoading = false;
      }
    );

    // Update speaking state when audio starts playing
    // The TTS service will set isSpeaking to true when audio plays
    setTimeout(() => {
      if (this.tts.isSpeaking) {
        this.isSpeaking = true;
        this.ttsLoading = false;
      }
    }, 100);
  }

  /**
   * Open the inventory browser modal.
   * Allows users to browse available equipment before creating a quote.
   */
  openInventoryBrowser(): void {
    this.showInventoryBrowser = true;
  }

  /**
   * Close the inventory browser modal.
   */
  closeInventoryBrowser(): void {
    this.showInventoryBrowser = false;
  }
}
