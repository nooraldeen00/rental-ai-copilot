// frontend/src/app/services/language.service.ts
import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

export interface Language {
  code: string;
  label: string;
  flag: string;
}

@Injectable({ providedIn: 'root' })
export class LanguageService {
  readonly languages: Language[] = [
    { code: 'en-US', label: 'English', flag: '🇺🇸' },
    { code: 'es-ES', label: 'Spanish', flag: '🇪🇸' },
    { code: 'ar-SA', label: 'Arabic', flag: '🇸🇦' },
    { code: 'ja-JP', label: 'Japanese', flag: '🇯🇵' }
  ];

  private _selectedLanguage = new BehaviorSubject<string>('en-US');
  selectedLanguage$ = this._selectedLanguage.asObservable();

  get selectedLanguage(): string {
    return this._selectedLanguage.value;
  }

  set selectedLanguage(code: string) {
    this._selectedLanguage.next(code);
  }

  getLanguageLabel(code: string): string {
    const lang = this.languages.find(l => l.code === code);
    return lang ? lang.label : 'English';
  }

  getLanguageFlag(code: string): string {
    const lang = this.languages.find(l => l.code === code);
    return lang ? lang.flag : '🇺🇸';
  }
}
