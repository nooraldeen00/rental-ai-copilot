import { Component } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { ApiService } from '../services/api';
import { QuoteViewComponent } from '../components/quote-view';
import { TraceComponent } from '../components/trace';
import { FormsModule } from '@angular/forms';
import { NgIf } from '@angular/common';

@Component({
  selector: 'app-run',
  standalone: true,
  imports: [QuoteViewComponent, TraceComponent, FormsModule, NgIf],
  templateUrl: './run.html',
  styleUrl: './run.css',
})
export class Run {
  runId!: number;
  quote: any = null;
  trace: any[] = [];
  rating = 3;
  note = '';
  error = '';

  constructor(private route: ActivatedRoute, private api: ApiService) {}

  ngOnInit() {
    this.runId = Number(this.route.snapshot.paramMap.get('id'));
    this.api.getRun(this.runId).subscribe({
      next: (res) => {
        this.quote = res.quote;
        this.trace = res.trace || [];
      },
      error: () => this.error = 'Unable to load run.'
    });
  }

  improve() {
    this.api.sendFeedback(this.runId, this.rating, this.note).subscribe({
      next: (res) => { this.quote = res.quote; },
      error: () => this.error = 'Feedback failed.'
    });
  }
}
