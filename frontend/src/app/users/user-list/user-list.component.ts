import { Component, computed, inject, signal } from '@angular/core';

import { UserService } from '../../core/services/user.service';
import { AuthService } from '../../core/services/auth.service';
import { ToastService } from '../../core/services/toast.service';
import { PaginatedResponse } from '../../core/models/paginated-response.model';
import { User } from '../../core/models/user.model';
import { initialsOf } from '../../core/utils/task-status';
import { UserFormDialogComponent } from '../user-form-dialog/user-form-dialog.component';

type ViewState = 'loading' | 'ready' | 'error';

@Component({
  selector: 'app-user-list',
  standalone: true,
  imports: [UserFormDialogComponent],
  templateUrl: './user-list.component.html',
})
export class UserListComponent {
  private readonly userService = inject(UserService);
  private readonly toastService = inject(ToastService);
  readonly authService = inject(AuthService);

  readonly state = signal<ViewState>('loading');
  readonly response = signal<PaginatedResponse<User> | null>(null);
  readonly users = computed(() => this.response()?.results ?? []);
  readonly dialogOpen = signal(false);
  readonly initialsOf = initialsOf;

  constructor() {
    this.load();
  }

  load(url?: string): void {
    this.state.set('loading');
    this.userService.list(url).subscribe({
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
    this.dialogOpen.set(true);
  }

  closeDialog(): void {
    this.dialogOpen.set(false);
  }

  onUserCreated(): void {
    this.dialogOpen.set(false);
    this.toastService.success('User created.');
    this.load();
  }
}
