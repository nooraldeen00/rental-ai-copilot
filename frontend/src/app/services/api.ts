// frontend/src/app/services/api.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { environment } from '../../environments/environment';

export type Tier = 'A'|'B'|'C';

export type QuoteRequest = {
  request_text: string;
  customer_tier: Tier;
  location: string;
  zip?: string;
  start_date?: string;
  end_date?: string;
  seed?: number;
};

export type QuoteItem = {
  name: string;
  sku?: string;
  qty: number;
  days?: number;
  dailyRate?: number;
  unitPrice: number;
  subtotal: number;
};

// ============ Inventory Browser Types ============

/**
 * Represents a single inventory item with pricing info.
 */
export interface InventoryItem {
  sku: string;
  name: string;
  location: string;
  available: number;
  dailyRate: number;
  weeklyRate: number;
  monthlyRate: number;
  attributes?: Record<string, any>;
}

/**
 * Represents a category of inventory items.
 */
export interface InventoryCategory {
  key: string;
  name: string;
  description: string;
  icon: string;
  itemCount: number;
  items: InventoryItem[];
}

/**
 * Response from the /inventory/browse endpoint.
 */
export interface InventoryBrowseResponse {
  categories: InventoryCategory[];
}

export interface QuoteRunResponse {
  run_id: number;
  quote: {
    currency?: string;
    total?: number;
    items?: QuoteItem[];
    notes?: string[];
  };
  // Added so the template `result.completedAt` is valid
  completedAt?: string; // e.g. "2025-11-13T18:05:58Z" or formatted string
}

// API base URL from environment configuration
const BASE = environment.apiUrl;

@Injectable({ providedIn: 'root' })
export class ApiService {
  constructor(private http: HttpClient) {}

  runQuote(req: QuoteRequest): Observable<QuoteRunResponse> {
  // Map frontend model to backend payload
  const payload: any = {
    message: req.request_text,
    customer_tier: req.customer_tier,
    location: req.location,
    zip: req.zip,
    start_date: req.start_date,
    end_date: req.end_date,
    seed: req.seed,
  };

  const fixDate = (s?: string) => {
    if (!s) return undefined;
    const d = new Date(s);
    if (isNaN(d.getTime())) return undefined;
    return d.toISOString().slice(0, 10); // YYYY-MM-DD
  };

  payload.start_date = fixDate(req.start_date);
  payload.end_date   = fixDate(req.end_date);

  if (payload.seed === '' || payload.seed == null || !Number.isFinite(Number(payload.seed))) {
    delete payload.seed;
  } else {
    payload.seed = Number(payload.seed);
  }

  if (!payload.zip) delete payload.zip;
  Object.keys(payload).forEach(k => payload[k] === undefined && delete payload[k]);

  return this.http.post<QuoteRunResponse>(`${BASE}/quote/run`, payload);
}

  sendFeedback(run_id: number, rating: number, note: string) {
    return this.http.post(`${BASE}/quote/feedback`, { run_id, rating, note });
  }

  getRun(runId: number) {
    return this.http.get(`${BASE}/runs/${runId}`);
  }

  /**
   * Download the PDF quote for a given run.
   * Triggers a browser download of the PDF file.
   */
  downloadQuotePdf(runId: number): Observable<Blob> {
    return this.http.get(`${BASE}/quote/runs/${runId}/pdf`, {
      responseType: 'blob',
    }).pipe(
      tap((blob) => {
        // Create download link and trigger download
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `quote-${runId}.pdf`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      })
    );
  }

  /**
   * Fetch inventory categories and items for the browse modal.
   * Returns all equipment grouped by category with pricing information.
   */
  browseInventory(): Observable<InventoryBrowseResponse> {
    return this.http.get<InventoryBrowseResponse>(`${BASE}/inventory/browse`);
  }

  /**
   * Convert text to speech using ElevenLabs Rachel voice.
   * Returns an Observable of the audio Blob.
   */
  textToSpeech(text: string): Observable<Blob> {
    return this.http.post(`${BASE}/tts/speak`, { text }, {
      responseType: 'blob',
    });
  }

  /**
   * Check if TTS service is configured and available.
   */
  getTtsStatus(): Observable<{ configured: boolean; voice_name: string; provider: string }> {
    return this.http.get<{ configured: boolean; voice_name: string; provider: string }>(`${BASE}/tts/status`);
  }
}
