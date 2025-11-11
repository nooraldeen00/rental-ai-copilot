import { Routes } from '@angular/router';
import { HomeComponent } from './pages/home';
import { Run } from './pages/run';  // <-- change this

export const routes: Routes = [
  { path: '', component: HomeComponent },
  { path: 'run/:id', component: Run }, // <-- and this
];
