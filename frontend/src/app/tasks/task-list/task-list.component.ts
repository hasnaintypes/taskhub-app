import { Component, inject, signal } from '@angular/core';
import { DatePipe, NgClass } from '@angular/common';
import { RouterLink } from '@angular/router';

import { TaskService } from '../../core/services/task.service';
import { AuthService } from '../../core/services/auth.service';
import { Task } from '../../core/models/task.model';
import { initialsOf, statusChipClasses, statusDotClasses, statusLabel } from '../../core/utils/task-status';

type ViewState = 'loading' | 'ready' | 'error';

@Component({
  selector: 'app-task-list',
  standalone: true,
  imports: [RouterLink, NgClass, DatePipe],
  templateUrl: './task-list.component.html',
})
export class TaskListComponent {
  private readonly taskService = inject(TaskService);
  readonly authService = inject(AuthService);

  readonly state = signal<ViewState>('loading');
  readonly tasks = signal<Task[]>([]);

  readonly statusLabel = statusLabel;
  readonly statusChipClasses = statusChipClasses;
  readonly statusDotClasses = statusDotClasses;
  readonly initialsOf = initialsOf;

  constructor() {
    this.load();
  }

  load(): void {
    this.state.set('loading');
    this.taskService.list().subscribe({
      next: (response) => {
        this.tasks.set(response.results);
        this.state.set('ready');
      },
      error: () => this.state.set('error'),
    });
  }
}
