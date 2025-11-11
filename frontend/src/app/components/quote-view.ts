import { Component, Input } from '@angular/core';
import { NgIf, NgFor, CurrencyPipe } from '@angular/common';

@Component({
  selector: 'app-quote-view',
  standalone: true,
  imports: [NgIf, NgFor, CurrencyPipe],
  templateUrl: './quote-view.html',
  styleUrl: './quote-view.css',
})
export class QuoteViewComponent {
  @Input() quote: any;
}
