import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';

import { TaskService } from '../../core/services/task.service';
import { UserService } from '../../core/services/user.service';
import { User } from '../../core/models/user.model';

@Component({
  selector: 'app-task-create',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
  ],
  templateUrl: './task-create.component.html',
  styleUrl: './task-create.component.css',
})
export class TaskCreateComponent {
  private readonly fb = inject(FormBuilder);
  private readonly taskService = inject(TaskService);
  private readonly userService = inject(UserService);
  private readonly router = inject(Router);

  readonly submitting = signal(false);
  readonly errorMessage = signal<string | null>(null);
  readonly users = signal<User[]>([]);

  readonly form = this.fb.nonNullable.group({
    title: ['', Validators.required],
    description: [''],
    assigned_to: this.fb.control<number | null>(null),
  });

  constructor() {
    this.userService.list().subscribe({
      next: (response) => this.users.set(response.results),
      error: () => this.errorMessage.set('Could not load the user list for assignment.'),
    });
  }

  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.submitting.set(true);
    this.errorMessage.set(null);
    const { title, description, assigned_to } = this.form.getRawValue();

    this.taskService.create({ title, description, assigned_to }).subscribe({
      next: (task) => {
        this.submitting.set(false);
        this.router.navigate(['/tasks', task.id]);
      },
      error: () => {
        this.submitting.set(false);
        this.errorMessage.set('Could not create the task. Check the fields and try again.');
      },
    });
  }
}
