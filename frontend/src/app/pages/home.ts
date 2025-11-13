import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { NgIf, NgFor, DecimalPipe } from '@angular/common';
import { ApiService } from '../services/api';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [FormsModule, NgIf, NgFor, DecimalPipe],
  templateUrl: './home.html',
})
export class HomeComponent {

  form: any = {
    request_text: '',
    customer_tier: 'B',
    location: '',
    seed: '',
    start_date: '',
    end_date: '',
    zip: '',
  };
  
  loading = false;
  error = '';
  result: any = null;

  constructor(private api: ApiService) {}

  onSubmit() {
    this.loading = true;
    this.error = '';
    this.result = null;

    this.api.runQuote(this.form).subscribe({
      next: (res) => {
        console.log('API result:', res);
        this.result = res;
        this.loading = false;
      },
      error: () => {
        this.error = 'Request failed.';
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
  }
}
