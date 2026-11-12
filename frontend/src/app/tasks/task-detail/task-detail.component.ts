import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { TaskService } from '../../core/services/task.service';
import { UserService } from '../../core/services/user.service';
import { AuthService } from '../../core/services/auth.service';
import { Task, TaskStatus } from '../../core/models/task.model';
import { User } from '../../core/models/user.model';
import { statusLabel } from '../../core/utils/task-status';

type ViewState = 'loading' | 'ready' | 'error' | 'not-found';

const STATUS_OPTIONS: TaskStatus[] = ['pending', 'in_progress', 'completed'];

@Component({
  selector: 'app-task-detail',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  templateUrl: './task-detail.component.html',
})
export class TaskDetailComponent {
  private readonly fb = inject(FormBuilder);
  private readonly route = inject(ActivatedRoute);
  private readonly taskService = inject(TaskService);
  private readonly userService = inject(UserService);
  readonly authService = inject(AuthService);

  readonly statusOptions = STATUS_OPTIONS;
  readonly statusLabel = statusLabel;
  readonly state = signal<ViewState>('loading');
  readonly task = signal<Task | null>(null);
  readonly users = signal<User[]>([]);
  readonly saving = signal(false);
  readonly assigning = signal(false);
  readonly errorMessage = signal<string | null>(null);
  readonly successMessage = signal<string | null>(null);

  readonly editForm = this.fb.nonNullable.group({
    title: ['', Validators.required],
    description: [''],
    status: this.fb.nonNullable.control<TaskStatus>('pending'),
  });

  readonly statusForm = this.fb.nonNullable.group({
    status: this.fb.nonNullable.control<TaskStatus>('pending'),
  });

  readonly assignForm = this.fb.group({
    assigned_to: this.fb.control<number | null>(null, Validators.required),
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
        this.editForm.setValue({
          title: task.title,
          description: task.description,
          status: task.status,
        });
        this.statusForm.setValue({ status: task.status });
        this.state.set('ready');

        if (this.authService.canManageTasks()) {
          this.userService.list().subscribe({ next: (res) => this.users.set(res.results) });
        }
      },
      error: (err) => this.state.set(err.status === 403 || err.status === 404 ? 'not-found' : 'error'),
    });
  }

  saveFields(): void {
    const task = this.task();
    if (!task || this.editForm.invalid) return;

    this.saving.set(true);
    this.errorMessage.set(null);
    this.successMessage.set(null);
    this.taskService.updateFields(task.id, this.editForm.getRawValue()).subscribe({
      next: (updated) => {
        this.task.set(updated);
        this.saving.set(false);
        this.successMessage.set('Changes saved.');
      },
      error: () => {
        this.saving.set(false);
        this.errorMessage.set('Could not save changes.');
      },
    });
  }

  saveStatus(): void {
    const task = this.task();
    if (!task) return;

    this.saving.set(true);
    this.errorMessage.set(null);
    this.successMessage.set(null);
    this.taskService.updateStatus(task.id, this.statusForm.getRawValue().status).subscribe({
      next: (updated) => {
        // The status-only endpoint's response only carries {id, status} —
        // merge rather than replace, or title/description would vanish
        // from the view after a status-only save.
        this.task.update((current) => (current ? { ...current, status: updated.status } : current));
        this.saving.set(false);
        this.successMessage.set('Status updated.');
      },
      error: () => {
        this.saving.set(false);
        this.errorMessage.set('Could not update status.');
      },
    });
  }

  assign(): void {
    const task = this.task();
    const assignedTo = this.assignForm.getRawValue().assigned_to;
    if (!task || !assignedTo) return;

    this.assigning.set(true);
    this.errorMessage.set(null);
    this.successMessage.set(null);
    this.taskService.assign(task.id, assignedTo).subscribe({
      next: () => {
        this.assigning.set(false);
        this.successMessage.set('Task assigned — notification queued.');
        this.load();
      },
      error: () => {
        this.assigning.set(false);
        this.errorMessage.set('Could not assign the task.');
      },
    });
  }
}
