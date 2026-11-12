import { Component, computed, inject, signal } from '@angular/core';
import { DatePipe, NgClass } from '@angular/common';
import { RouterLink } from '@angular/router';

import { DashboardService } from '../core/services/dashboard.service';
import { TaskService } from '../core/services/task.service';
import { DashboardStats } from '../core/models/dashboard-stats.model';
import { Task } from '../core/models/task.model';
import { initialsOf, statusChipClasses, statusDotClasses, statusLabel } from '../core/utils/task-status';

type ViewState = 'loading' | 'ready' | 'error';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [RouterLink, NgClass, DatePipe],
  templateUrl: './dashboard.component.html',
})
export class DashboardComponent {
  private readonly dashboardService = inject(DashboardService);
  private readonly taskService = inject(TaskService);

  readonly state = signal<ViewState>('loading');
  readonly stats = signal<DashboardStats | null>(null);
  readonly recentTasks = signal<Task[]>([]);

  readonly completionRate = computed(() => {
    const stats = this.stats();
    if (!stats || stats.total_tasks === 0) return 0;
    return Math.round((stats.completed_tasks / stats.total_tasks) * 100);
  });

  readonly statusLabel = statusLabel;
  readonly statusChipClasses = statusChipClasses;
  readonly statusDotClasses = statusDotClasses;
  readonly initialsOf = initialsOf;

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
    this.taskService.list().subscribe({
      next: (response) => this.recentTasks.set(response.results.slice(0, 5)),
    });
  }
}
