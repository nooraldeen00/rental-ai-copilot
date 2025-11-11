import { Component } from '@angular/core';
import { QuoteFormComponent } from '../components/quote-form';
import { QuoteViewComponent } from '../components/quote-view';
import { RouterLink } from '@angular/router';
import { NgIf } from '@angular/common';
import { ApiService } from '../services/api';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [QuoteFormComponent, QuoteViewComponent, RouterLink, NgIf],
  templateUrl: './home.html'
})
export class HomeComponent {
  loading = false;
  error = '';
  result: any = null;

  constructor(private api: ApiService) {}

  onSubmit(formValue: any) {
    this.loading = true;
    this.error = '';
    this.result = null;
    this.api.runQuote(formValue).subscribe({
      next: (res) => { this.result = res; this.loading = false; },
      error: () => { this.error = 'Request failed.'; this.loading = false; }
    });
  }
}
