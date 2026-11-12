import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { UserService } from '../../core/services/user.service';
import { AuthService } from '../../core/services/auth.service';
import { User, Role } from '../../core/models/user.model';
import { initialsOf } from '../../core/utils/task-status';

type ViewState = 'loading' | 'ready' | 'error';

@Component({
  selector: 'app-user-list',
  standalone: true,
  imports: [ReactiveFormsModule],
  templateUrl: './user-list.component.html',
})
export class UserListComponent {
  private readonly fb = inject(FormBuilder);
  private readonly userService = inject(UserService);
  readonly authService = inject(AuthService);

  readonly state = signal<ViewState>('loading');
  readonly users = signal<User[]>([]);
  readonly creating = signal(false);
  readonly errorMessage = signal<string | null>(null);
  readonly roles: Role[] = ['ADMIN', 'MANAGER', 'EMPLOYEE'];
  readonly initialsOf = initialsOf;

  readonly createForm = this.fb.nonNullable.group({
    username: ['', Validators.required],
    email: ['', [Validators.required, Validators.email]],
    role: this.fb.nonNullable.control<Role>('EMPLOYEE'),
    password: ['', [Validators.required, Validators.minLength(8)]],
  });

  constructor() {
    this.load();
  }

  load(): void {
    this.state.set('loading');
    this.userService.list().subscribe({
      next: (response) => {
        this.users.set(response.results);
        this.state.set('ready');
      },
      error: () => this.state.set('error'),
    });
  }

  createUser(): void {
    if (this.createForm.invalid) {
      this.createForm.markAllAsTouched();
      return;
    }

    this.creating.set(true);
    this.errorMessage.set(null);
    this.userService.create(this.createForm.getRawValue()).subscribe({
      next: () => {
        this.creating.set(false);
        this.createForm.reset({ role: 'EMPLOYEE' });
        this.load();
      },
      error: () => {
        this.creating.set(false);
        this.errorMessage.set('Could not create the user. Check the fields and try again.');
      },
    });
  }
}
