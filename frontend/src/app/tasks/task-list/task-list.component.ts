import { Component, computed, inject, signal } from '@angular/core';
import { DatePipe, NgClass } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { TaskService } from '../../core/services/task.service';
import { UserService } from '../../core/services/user.service';
import { AuthService } from '../../core/services/auth.service';
import { ToastService } from '../../core/services/toast.service';
import { PaginatedResponse } from '../../core/models/paginated-response.model';
import { Task } from '../../core/models/task.model';
import { User } from '../../core/models/user.model';
import { initialsOf, statusChipClasses, statusDotClasses, statusLabel } from '../../core/utils/task-status';
import { TaskFormDialogComponent } from '../task-form-dialog/task-form-dialog.component';

type ViewState = 'loading' | 'ready' | 'error';

@Component({
  selector: 'app-task-list',
  standalone: true,
  imports: [RouterLink, NgClass, DatePipe, TaskFormDialogComponent],
  templateUrl: './task-list.component.html',
})
export class TaskListComponent {
  private readonly taskService = inject(TaskService);
  private readonly userService = inject(UserService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly toastService = inject(ToastService);
  readonly authService = inject(AuthService);

  readonly state = signal<ViewState>('loading');
  readonly response = signal<PaginatedResponse<Task> | null>(null);
  readonly tasks = computed(() => this.response()?.results ?? []);
  readonly users = signal<User[]>([]);
  readonly dialogOpen = signal(false);

  readonly statusLabel = statusLabel;
  readonly statusChipClasses = statusChipClasses;
  readonly statusDotClasses = statusDotClasses;
  readonly initialsOf = initialsOf;

  constructor() {
    this.load();

    if (this.route.snapshot.data['openCreateDialog']) {
      this.openCreateDialog();
    }
  }

  load(url?: string): void {
    this.state.set('loading');
    this.taskService.list(url).subscribe({
      next: (response) => {
        this.response.set(response);
        this.state.set('ready');
      },
      error: () => this.state.set('error'),
    });
  }

  nextPage(): void {
    const next = this.response()?.next;
    if (next) this.load(next);
  }

  previousPage(): void {
    const previous = this.response()?.previous;
    if (previous) this.load(previous);
  }

  openCreateDialog(): void {
    if (this.users().length === 0) {
      this.userService.list().subscribe({ next: (res) => this.users.set(res.results) });
    }
    this.dialogOpen.set(true);
  }

  closeDialog(): void {
    this.dialogOpen.set(false);
    if (this.router.url === '/tasks/new') {
      this.router.navigate(['/tasks']);
    }
  }

  onTaskCreated(task: Task): void {
    this.dialogOpen.set(false);
    this.toastService.success('Task created.');
    this.router.navigate(['/tasks', task.id]);
  }
}
