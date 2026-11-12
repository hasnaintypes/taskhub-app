import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { MatCardModule } from '@angular/material/card';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatIconModule } from '@angular/material/icon';

import { TaskService } from '../../core/services/task.service';
import { AuthService } from '../../core/services/auth.service';
import { Task } from '../../core/models/task.model';

type ViewState = 'loading' | 'ready' | 'error';

@Component({
  selector: 'app-task-list',
  standalone: true,
  imports: [
    RouterLink,
    MatTableModule,
    MatButtonModule,
    MatChipsModule,
    MatCardModule,
    MatProgressSpinnerModule,
    MatIconModule,
  ],
  templateUrl: './task-list.component.html',
  styleUrl: './task-list.component.css',
})
export class TaskListComponent {
  private readonly taskService = inject(TaskService);
  readonly authService = inject(AuthService);

  readonly state = signal<ViewState>('loading');
  readonly tasks = signal<Task[]>([]);
  readonly displayedColumns = ['title', 'status', 'assigned_to', 'actions'];

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
