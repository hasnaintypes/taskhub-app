import { AfterViewInit, Component, ElementRef, EventEmitter, HostListener, Output, ViewChild, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { UserService } from '../../core/services/user.service';
import { Role, User } from '../../core/models/user.model';

@Component({
  selector: 'app-user-form-dialog',
  standalone: true,
  imports: [ReactiveFormsModule],
  templateUrl: './user-form-dialog.component.html',
})
export class UserFormDialogComponent implements AfterViewInit {
  @Output() readonly closed = new EventEmitter<void>();
  @Output() readonly saved = new EventEmitter<User>();

  @ViewChild('usernameInput') private readonly usernameInput?: ElementRef<HTMLInputElement>;

  private readonly fb = inject(FormBuilder);
  private readonly userService = inject(UserService);

  readonly roles: Role[] = ['ADMIN', 'MANAGER', 'EMPLOYEE'];
  readonly creating = signal(false);
  readonly errorMessage = signal<string | null>(null);

  readonly form = this.fb.nonNullable.group({
    username: ['', Validators.required],
    email: ['', [Validators.required, Validators.email]],
    role: this.fb.nonNullable.control<Role>('EMPLOYEE'),
    password: ['', [Validators.required, Validators.minLength(8)]],
  });

  ngAfterViewInit(): void {
    this.usernameInput?.nativeElement.focus();
  }

  @HostListener('document:keydown.escape')
  onEscape(): void {
    this.close();
  }

  close(): void {
    this.closed.emit();
  }

  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.creating.set(true);
    this.errorMessage.set(null);
    this.userService.create(this.form.getRawValue()).subscribe({
      next: (user) => {
        this.creating.set(false);
        this.saved.emit(user);
      },
      error: () => {
        this.creating.set(false);
        this.errorMessage.set('Could not create the user. Check the fields and try again.');
      },
    });
  }
}
