import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { DashboardStats } from '../models/dashboard-stats.model';

@Injectable({ providedIn: 'root' })
export class DashboardService {
  private readonly baseUrl = `${environment.apiBaseUrl}/dashboard`;

  constructor(private readonly http: HttpClient) {}

  getStats(): Observable<DashboardStats> {
    return this.http.get<DashboardStats>(`${this.baseUrl}/stats/`);
  }
}
