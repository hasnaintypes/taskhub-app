import { TaskStatus } from '../models/task.model';

const LABELS: Record<TaskStatus, string> = {
  pending: 'Pending',
  in_progress: 'In Progress',
  completed: 'Completed',
};

const CHIP_CLASSES: Record<TaskStatus, string> = {
  in_progress: 'bg-primary-fixed text-on-primary-fixed-variant',
  pending: 'bg-tertiary-fixed text-on-tertiary-fixed-variant',
  completed: 'bg-surface-container-high text-on-secondary-fixed-variant',
};

const DOT_CLASSES: Record<TaskStatus, string> = {
  in_progress: 'bg-primary-container',
  pending: 'bg-tertiary-container',
  completed: 'bg-secondary',
};

export function statusLabel(status: TaskStatus): string {
  return LABELS[status];
}

export function statusChipClasses(status: TaskStatus): string {
  return CHIP_CLASSES[status];
}

export function statusDotClasses(status: TaskStatus): string {
  return DOT_CLASSES[status];
}

export function initialsOf(name: string | null | undefined): string {
  if (!name) return '—';
  return name.slice(0, 2).toUpperCase();
}
