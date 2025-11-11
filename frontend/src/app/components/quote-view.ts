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
  @Input() quote: any;          // the object you pass in: result.quote
}
