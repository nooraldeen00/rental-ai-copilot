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

  constructor(private api: ApiService) {}

  
  onSubmit() {
    this.loading = true;
    this.error = '';

    // frontend-only fake data (no backend)
    // comment OUT the API call and uncomment the fake quote if you want:

    
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
    

    //  real backend
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
    this.loading = false;
  }
}
