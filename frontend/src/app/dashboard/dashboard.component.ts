import { Component, inject, signal } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatIconModule } from '@angular/material/icon';

import { DashboardService } from '../core/services/dashboard.service';
import { DashboardStats } from '../core/models/dashboard-stats.model';

type ViewState = 'loading' | 'ready' | 'error';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [MatCardModule, MatButtonModule, MatProgressSpinnerModule, MatIconModule],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.css',
})
export class DashboardComponent {
  private readonly dashboardService = inject(DashboardService);

  readonly state = signal<ViewState>('loading');
  readonly stats = signal<DashboardStats | null>(null);

  constructor() {
    this.load();
  }

  load(): void {
    this.state.set('loading');
    this.dashboardService.getStats().subscribe({
      next: (stats) => {
        this.stats.set(stats);
        this.state.set('ready');
      },
      error: () => this.state.set('error'),
    });
  }
}
