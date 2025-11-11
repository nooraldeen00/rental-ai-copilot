// frontend/src/app/services/api.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

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
  qty: number;
  unitPrice: number;
  subtotal: number;
};

export interface QuoteRunResponse {
  run_id: number;
  quote: {
    currency?: string;
    total?: number;
    items?: QuoteItem[];
    notes?: string[];
  };
}

// IMPORTANT: your forwarded 8000 url
const BASE = 'https://psychic-bassoon-x5576x4q667x2w79-8000.app.github.dev';

@Injectable({ providedIn: 'root' })
export class ApiService {
  constructor(private http: HttpClient) {}

  runQuote(req: QuoteRequest): Observable<QuoteRunResponse> {
    const payload: any = { ...req };

    const fixDate = (s?: string) => {
      if (!s) return undefined;
      const d = new Date(s);
      if (isNaN(d.getTime())) return undefined;
      return d.toISOString().slice(0, 10);
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
}
