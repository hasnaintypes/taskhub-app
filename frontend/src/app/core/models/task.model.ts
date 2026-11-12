export type TaskStatus = 'pending' | 'in_progress' | 'completed';

export interface Task {
  id: number;
  title: string;
  description: string;
  status: TaskStatus;
  assigned_to: number | null;
  created_by: number;
  created_at: string;
  updated_at: string;
}

export interface CreateTaskPayload {
  title: string;
  description?: string;
  assigned_to?: number | null;
}
