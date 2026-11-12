import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatTableModule } from '@angular/material/table';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { UserService } from '../../core/services/user.service';
import { AuthService } from '../../core/services/auth.service';
import { User, Role } from '../../core/models/user.model';

type ViewState = 'loading' | 'ready' | 'error';

@Component({
  selector: 'app-user-list',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    MatTableModule,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
    MatProgressSpinnerModule,
  ],
  templateUrl: './user-list.component.html',
  styleUrl: './user-list.component.css',
})
export class UserListComponent {
  private readonly fb = inject(FormBuilder);
  private readonly userService = inject(UserService);
  readonly authService = inject(AuthService);

  readonly state = signal<ViewState>('loading');
  readonly users = signal<User[]>([]);
  readonly displayedColumns = ['username', 'email', 'role'];
  readonly creating = signal(false);
  readonly errorMessage = signal<string | null>(null);
  readonly roles: Role[] = ['ADMIN', 'MANAGER', 'EMPLOYEE'];

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
