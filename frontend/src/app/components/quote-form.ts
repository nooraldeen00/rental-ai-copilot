import { Component, EventEmitter, Output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { NgIf, NgFor } from '@angular/common';
import { LanguageService } from '../services/language.service';

// Web Speech API types
interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

interface SpeechRecognitionResultList {
  length: number;
  item(index: number): SpeechRecognitionResult;
  [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionResult {
  length: number;
  item(index: number): SpeechRecognitionAlternative;
  [index: number]: SpeechRecognitionAlternative;
  isFinal: boolean;
}

interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

// Available service locations (from database)
export interface ServiceLocation {
  id: string;
  label: string;
  zone: 'local' | 'regional' | 'extended';
  region: string;
}

export const SERVICE_LOCATIONS: ServiceLocation[] = [
  { id: 'plano-tx', label: 'Plano, TX', zone: 'local', region: 'DFW Metro' },
  { id: 'dallas-tx', label: 'Dallas, TX', zone: 'local', region: 'DFW Metro' },
  { id: 'fort-worth-tx', label: 'Fort Worth, TX', zone: 'local', region: 'DFW Metro' },
  { id: 'arlington-tx', label: 'Arlington, TX', zone: 'local', region: 'DFW Metro' },
  { id: 'southlake-tx', label: 'Southlake, TX', zone: 'local', region: 'DFW Metro' },
];

@Component({
  selector: 'app-quote-form',
  standalone: true,
  imports: [FormsModule, NgIf, NgFor],
  templateUrl: './quote-form.html',
  styleUrl: './quote-form.css',
})
export class QuoteFormComponent {
  @Output() submitted = new EventEmitter<any>();

  // Available service locations for dropdown
  serviceLocations = SERVICE_LOCATIONS;

  model = {
    request_text: 'Need 2 light towers in Dallas Fri–Sun',
    customer_tier: 'B' as 'A' | 'B' | 'C',
    location: 'Dallas',  // Legacy field - free text from request
    selectedServiceLocationId: '' as string,  // New: dropdown selection ID
    zip: '',
    start_date: '',
    end_date: '',
    seed: ''
  };

  isListening = false;
  speechSupported = false;
  private recognition: any;

  constructor(public langService: LanguageService) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      this.speechSupported = true;
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = false;
      this.recognition.interimResults = false;
      this.recognition.lang = this.langService.selectedLanguage;

      this.recognition.onresult = (event: SpeechRecognitionEvent) => {
        const transcript = event.results[0][0].transcript;
        this.model.request_text = transcript;
        this.isListening = false;
      };

      this.recognition.onerror = () => {
        this.isListening = false;
      };

      this.recognition.onend = () => {
        this.isListening = false;
      };
    }
  }

  toggleSpeechRecognition() {
    if (!this.speechSupported) return;

    if (this.isListening) {
      this.recognition.stop();
      this.isListening = false;
    } else {
      this.recognition.lang = this.langService.selectedLanguage;
      this.model.request_text = '';
      this.recognition.start();
      this.isListening = true;
    }
  }

  // Get the selected service location object
  getSelectedServiceLocation(): ServiceLocation | null {
    if (!this.model.selectedServiceLocationId) return null;
    return this.serviceLocations.find(loc => loc.id === this.model.selectedServiceLocationId) || null;
  }

  submit() {
    const payload: any = { ...this.model };
    if (payload.seed === '') delete payload.seed;

    // Add selected service location metadata
    const selectedLocation = this.getSelectedServiceLocation();
    if (selectedLocation) {
      payload.selectedServiceLocationLabel = selectedLocation.label;
      payload.selectedServiceLocationMeta = {
        zone: selectedLocation.zone,
        region: selectedLocation.region
      };
    }

    this.submitted.emit(payload);
  }
}
