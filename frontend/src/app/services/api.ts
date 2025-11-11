// frontend/src/app/services/api.ts

import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

// IMPORTANT: your forwarded 8000 url:
const BASE = 'https://psychic-bassoon-x5576x4q667x2w79-8000.app.github.dev';

@Injectable({ providedIn: 'root' })
export class ApiService {
  constructor(private http: HttpClient) {}

  runQuote(req: {
    request_text: string;
    customer_tier: 'A'|'B'|'C';
    location: string;
    zip?: string;
    start_date?: string;
    end_date?: string;
    seed?: number | string;
  }): Observable<any> {

    const payload: any = { ...req };

    // convert "02/12/2222" format to YYYY-MM-DD or drop
    const fixDate = (s?: string) => {
      if (!s) return undefined;
      const d = new Date(s);
      if (isNaN(d.getTime())) return undefined;
      return d.toISOString().slice(0, 10);
    };

    payload.start_date = fixDate(req.start_date);
    payload.end_date   = fixDate(req.end_date);

    // normalize seed → number or remove
    if (payload.seed !== undefined && payload.seed !== null && payload.seed !== '') {
      const n = Number(payload.seed);
      if (Number.isFinite(n)) payload.seed = n;
      else delete payload.seed;
    } else {
      delete payload.seed;
    }

    // remove empty zip
    if (!payload.zip) delete payload.zip;

    // remove undefined
    Object.keys(payload).forEach(k => payload[k] === undefined && delete payload[k]);

    return this.http.post(`${BASE}/quote/run`, payload);
  }

  sendFeedback(run_id: number, rating: number, note: string): Observable<any> {
    return this.http.post(`${BASE}/quote/feedback`, { run_id, rating, note });
  }

  getRun(runId: number): Observable<any> {
    return this.http.get(`${BASE}/runs/${runId}`);
  }
}
