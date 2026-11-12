import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { PaginatedResponse } from '../models/paginated-response.model';
import { Role, User } from '../models/user.model';

export interface CreateUserPayload {
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  role: Role;
  password: string;
}

@Injectable({ providedIn: 'root' })
export class UserService {
  private readonly baseUrl = `${environment.apiBaseUrl}/users`;

  constructor(private readonly http: HttpClient) {}

  list(): Observable<PaginatedResponse<User>> {
    return this.http.get<PaginatedResponse<User>>(`${this.baseUrl}/`);
  }

  create(payload: CreateUserPayload): Observable<User> {
    return this.http.post<User>(`${this.baseUrl}/`, payload);
  }
}
