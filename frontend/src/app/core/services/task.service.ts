import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { PaginatedResponse } from '../models/paginated-response.model';
import { CreateTaskPayload, Task } from '../models/task.model';

@Injectable({ providedIn: 'root' })
export class TaskService {
  private readonly baseUrl = `${environment.apiBaseUrl}/tasks`;

  constructor(private readonly http: HttpClient) {}

  /** Pass a `next`/`previous` URL from a prior response to page through
   * results; omit it to fetch the first page. */
  list(url?: string): Observable<PaginatedResponse<Task>> {
    return this.http.get<PaginatedResponse<Task>>(url ?? `${this.baseUrl}/`);
  }

  get(id: number): Observable<Task> {
    return this.http.get<Task>(`${this.baseUrl}/${id}/`);
  }

  create(payload: CreateTaskPayload): Observable<Task> {
    return this.http.post<Task>(`${this.baseUrl}/`, payload);
  }

  /** TaskStatusUpdateSerializer on the backend only returns {id, status}
   * — the type here reflects that honestly so callers can't accidentally
   * treat it as a full Task (that caused a real bug: see task-detail
   * component's merge-not-replace comment). */
  updateStatus(id: number, status: Task['status']): Observable<Pick<Task, 'id' | 'status'>> {
    return this.http.patch<Pick<Task, 'id' | 'status'>>(`${this.baseUrl}/${id}/`, { status });
  }

  updateFields(id: number, payload: Partial<Pick<Task, 'title' | 'description' | 'status'>>): Observable<Task> {
    return this.http.patch<Task>(`${this.baseUrl}/${id}/`, payload);
  }

  assign(id: number, assignedTo: number): Observable<{ detail: string }> {
    return this.http.post<{ detail: string }>(`${this.baseUrl}/${id}/assign/`, { assigned_to: assignedTo });
  }

  delete(id: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/${id}/`);
  }
}
