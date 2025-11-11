import { Component, Input } from '@angular/core';
import { NgIf, NgFor } from '@angular/common';

@Component({
  selector: 'app-trace',
  standalone: true,
  imports: [NgIf, NgFor],
  templateUrl: './trace.html',
  styleUrl: './trace.css',
})
export class TraceComponent {
  @Input() items: any[] = [];
}
