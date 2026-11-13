import { AfterViewInit, Component, ElementRef, EventEmitter, HostListener, Input, OnInit, Output, ViewChild, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { TaskService } from '../../core/services/task.service';
import { Task } from '../../core/models/task.model';
import { User } from '../../core/models/user.model';

export type TaskFormDialogMode = 'create' | 'edit';

@Component({
  selector: 'app-task-form-dialog',
  standalone: true,
  imports: [ReactiveFormsModule],
  templateUrl: './task-form-dialog.component.html',
})
export class TaskFormDialogComponent implements OnInit, AfterViewInit {
  @Input() mode: TaskFormDialogMode = 'create';
  @Input() task: Task | null = null;
  @Input() users: User[] = [];
  @Output() readonly closed = new EventEmitter<void>();
  @Output() readonly saved = new EventEmitter<Task>();

  @ViewChild('titleInput') private readonly titleInput?: ElementRef<HTMLInputElement>;

  private readonly fb = inject(FormBuilder);
  private readonly taskService = inject(TaskService);

  readonly submitting = signal(false);
  readonly errorMessage = signal<string | null>(null);

  readonly form = this.fb.nonNullable.group({
    title: ['', Validators.required],
    description: [''],
    assigned_to: this.fb.control<number | null>(null),
  });

  ngOnInit(): void {
    if (this.mode === 'edit' && this.task) {
      this.form.patchValue({
        title: this.task.title,
        description: this.task.description,
      });
    }
  }

  ngAfterViewInit(): void {
    this.titleInput?.nativeElement.focus();
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

    this.submitting.set(true);
    this.errorMessage.set(null);
    const { title, description, assigned_to } = this.form.getRawValue();

    const request =
      this.mode === 'edit' && this.task
        ? this.taskService.updateFields(this.task.id, { title, description })
        : this.taskService.create({ title, description, assigned_to });

    request.subscribe({
      next: (task) => {
        this.submitting.set(false);
        this.saved.emit(task as Task);
      },
      error: () => {
        this.submitting.set(false);
        this.errorMessage.set(
          this.mode === 'edit' ? 'Could not save changes.' : 'Could not create the task. Check the fields and try again.',
        );
      },
    });
  }
}
