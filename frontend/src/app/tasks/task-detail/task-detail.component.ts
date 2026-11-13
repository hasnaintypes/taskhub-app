import { Component, inject, signal } from '@angular/core';
import { DatePipe, NgClass } from '@angular/common';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { TaskService } from '../../core/services/task.service';
import { UserService } from '../../core/services/user.service';
import { AuthService } from '../../core/services/auth.service';
import { ToastService } from '../../core/services/toast.service';
import { Task, TaskStatus } from '../../core/models/task.model';
import { User } from '../../core/models/user.model';
import { initialsOf, statusChipClasses, statusDotClasses, statusLabel } from '../../core/utils/task-status';
import { TaskFormDialogComponent } from '../task-form-dialog/task-form-dialog.component';
import { ConfirmDialogComponent } from '../../core/components/confirm-dialog/confirm-dialog.component';

type ViewState = 'loading' | 'ready' | 'error' | 'not-found';

const STATUS_OPTIONS: TaskStatus[] = ['pending', 'in_progress', 'completed'];

@Component({
  selector: 'app-task-detail',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, DatePipe, NgClass, TaskFormDialogComponent, ConfirmDialogComponent],
  templateUrl: './task-detail.component.html',
})
export class TaskDetailComponent {
  private readonly fb = inject(FormBuilder);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly taskService = inject(TaskService);
  private readonly userService = inject(UserService);
  private readonly toastService = inject(ToastService);
  readonly authService = inject(AuthService);

  readonly statusOptions = STATUS_OPTIONS;
  readonly statusLabel = statusLabel;
  readonly statusChipClasses = statusChipClasses;
  readonly statusDotClasses = statusDotClasses;
  readonly initialsOf = initialsOf;

  readonly state = signal<ViewState>('loading');
  readonly task = signal<Task | null>(null);
  readonly users = signal<User[]>([]);
  readonly savingStatus = signal(false);
  readonly assigning = signal(false);
  readonly deleting = signal(false);
  readonly editDialogOpen = signal(false);
  readonly deleteDialogOpen = signal(false);

  readonly statusForm = this.fb.nonNullable.group({
    status: this.fb.nonNullable.control<TaskStatus>('pending'),
  });

  readonly assignForm = this.fb.group({
    assigned_to: this.fb.control<number | null>(null),
  });

  constructor() {
    this.load();
  }

  private load(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    this.state.set('loading');

    this.taskService.get(id).subscribe({
      next: (task) => {
        this.task.set(task);
        this.statusForm.setValue({ status: task.status });
        this.assignForm.setValue({ assigned_to: task.assigned_to });
        this.state.set('ready');

        if (this.authService.canManageTasks()) {
          this.userService.list().subscribe({ next: (res) => this.users.set(res.results) });
        }
      },
      error: (err) => this.state.set(err.status === 403 || err.status === 404 ? 'not-found' : 'error'),
    });
  }

  openEditDialog(): void {
    this.editDialogOpen.set(true);
  }

  closeEditDialog(): void {
    this.editDialogOpen.set(false);
  }

  onTaskEdited(updated: Task): void {
    this.task.set(updated);
    this.editDialogOpen.set(false);
    this.toastService.success('Changes saved.');
  }

  saveStatus(): void {
    const task = this.task();
    if (!task) return;

    this.savingStatus.set(true);
    this.taskService.updateStatus(task.id, this.statusForm.getRawValue().status).subscribe({
      next: (updated) => {
        // The status-only endpoint's response only carries {id, status} —
        // merge rather than replace, or title/description would vanish
        // from the view after a status-only save.
        this.task.update((current) => (current ? { ...current, status: updated.status } : current));
        this.savingStatus.set(false);
        this.toastService.success('Status updated.');
      },
      error: () => {
        this.savingStatus.set(false);
        this.statusForm.setValue({ status: task.status });
        this.toastService.error('Could not update status.');
      },
    });
  }

  assign(): void {
    const task = this.task();
    const assignedTo = this.assignForm.getRawValue().assigned_to;
    if (!task || !assignedTo || assignedTo === task.assigned_to) return;

    this.assigning.set(true);
    this.taskService.assign(task.id, assignedTo).subscribe({
      next: () => {
        this.assigning.set(false);
        this.toastService.success('Task assigned — notification queued.');
        this.load();
      },
      error: () => {
        this.assigning.set(false);
        this.assignForm.setValue({ assigned_to: task.assigned_to });
        this.toastService.error('Could not assign the task.');
      },
    });
  }

  openDeleteDialog(): void {
    this.deleteDialogOpen.set(true);
  }

  closeDeleteDialog(): void {
    this.deleteDialogOpen.set(false);
  }

  deleteTask(): void {
    const task = this.task();
    if (!task) return;

    this.deleting.set(true);
    this.taskService.delete(task.id).subscribe({
      next: () => {
        this.toastService.success('Task deleted.');
        this.router.navigate(['/tasks']);
      },
      error: () => {
        this.deleting.set(false);
        this.deleteDialogOpen.set(false);
        this.toastService.error('Could not delete the task.');
      },
    });
  }
}
