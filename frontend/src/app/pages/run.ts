// frontend/src/app/pages/run.ts
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule, DecimalPipe } from '@angular/common';
import { ApiService, QuoteRequest, QuoteRunResponse } from '../services/api';

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

  constructor(private api: ApiService) {}

  // alias used by the template
  get model() { return this.form; }
  onRun() { this.onGenerateQuote(); }
  reset() { this.onClear(); }

  onGenerateQuote() {
    this.loading = true;
    this.error = null;
    this.result = null;

    const payload: QuoteRequest = {
      request_text: this.form.request_text,
      customer_tier: this.form.customer_tier,
      location: this.form.location || '',
      zip: this.form.zip,
      start_date: this.form.start_date,
      end_date: this.form.end_date,
      seed: this.form.seed ?? undefined,
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
  }
}
