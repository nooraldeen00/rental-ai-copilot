// src/app/components/quote-view.ts
import { Component, Input } from '@angular/core';
import { NgIf, NgFor, DecimalPipe } from '@angular/common';

@Component({
  selector: 'app-quote-view',
  standalone: true,
  imports: [NgIf, NgFor, DecimalPipe],
  templateUrl: './quote-view.html',
  styleUrl: './quote-view.css'
})
export class QuoteViewComponent {

  // Whether the backend is still generating
  @Input() loading: boolean | null = null;

  // The full run response object returned by the API (result)
  @Input() result: any = null;

  // Error message, if any
  @Input() error: string | null = null;
}
