// src/app/app.routes.ts
import { Routes } from '@angular/router';
import { HomeComponent } from './pages/home';
import { RunPage } from './pages/run';

export const routes: Routes = [
  { path: '', component: HomeComponent },   // default = form page
  { path: 'run/:id', component: RunPage },  // detail page
  { path: '**', redirectTo: '' },
];
