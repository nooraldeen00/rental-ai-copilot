import { Component, EventEmitter, Output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { NgIf, NgFor } from '@angular/common';

@Component({
  selector: 'app-quote-form',
  standalone: true,
  imports: [FormsModule, NgIf, NgFor],
  templateUrl: './quote-form.html',
  styleUrl: './quote-form.css',
})
export class QuoteFormComponent {
  @Output() submitted = new EventEmitter<any>();

  model = {
    request_text: 'Need 2 light towers in Dallas Fri–Sun',
    customer_tier: 'B' as 'A' | 'B' | 'C',
    location: 'Dallas',
    zip: '',
    start_date: '',
    end_date: '',
    seed: ''
  };

  submit() {
    const payload: any = { ...this.model };
    if (payload.seed === '') delete payload.seed;
    this.submitted.emit(payload);
  }
}
