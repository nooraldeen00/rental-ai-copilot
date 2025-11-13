import { Component, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {
  protected readonly title = signal('quote-copilot');

  // Stub handlers so the (click) bindings in app.html are valid
  onGenerateQuote(): void {
    console.log(
      'Generate Quote clicked (root App). Use the Home page form to actually run quotes.'
    );
  }

  onClear(): void {
    console.log(
      'Clear clicked (root App). Use the Home page form to reset the fields.'
    );
  }
}
