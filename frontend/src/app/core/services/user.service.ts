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

  /** Pass a `next`/`previous` URL from a prior response to page through
   * results; omit it to fetch the first page. */
  list(url?: string): Observable<PaginatedResponse<User>> {
    return this.http.get<PaginatedResponse<User>>(url ?? `${this.baseUrl}/`);
  }

  create(payload: CreateUserPayload): Observable<User> {
    return this.http.post<User>(`${this.baseUrl}/`, payload);
  }
}
