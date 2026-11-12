import { HttpClient } from '@angular/common/http';
import { Injectable, computed, signal } from '@angular/core';
import { Observable, tap } from 'rxjs';

import { environment } from '../../../environments/environment';
import { Role, User } from '../models/user.model';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly baseUrl = environment.apiBaseUrl;

  // `null` = not yet resolved; `undefined` = resolved, no user.
  private readonly currentUserSignal = signal<User | null | undefined>(null);

  readonly currentUser = computed(() => this.currentUserSignal());
  readonly isAuthenticated = computed(() => !!this.currentUserSignal());
  readonly role = computed<Role | null>(() => this.currentUserSignal()?.role ?? null);
  readonly canManageTasks = computed(() => {
    const role = this.role();
    return role === 'ADMIN' || role === 'MANAGER';
  });
  readonly isAdmin = computed(() => this.role() === 'ADMIN');

  constructor(private readonly http: HttpClient) {}

  /** Call once on app start: sets the CSRF cookie and restores the
   * session (if any) so a page refresh doesn't force a re-login
   * [AUTH-04, AUTH-10]. */
  bootstrap(): Observable<User | null> {
    return new Observable<User | null>((subscriber) => {
      this.http.get<{ authenticated: boolean }>(`${this.baseUrl}/auth/session/`).subscribe({
        next: (res) => {
          if (!res.authenticated) {
            this.currentUserSignal.set(undefined);
            subscriber.next(null);
            subscriber.complete();
            return;
          }
          this.http.get<User>(`${this.baseUrl}/auth/me/`).subscribe({
            next: (user) => {
              this.currentUserSignal.set(user);
              subscriber.next(user);
              subscriber.complete();
            },
            error: () => {
              this.currentUserSignal.set(undefined);
              subscriber.next(null);
              subscriber.complete();
            },
          });
        },
        error: () => {
          this.currentUserSignal.set(undefined);
          subscriber.next(null);
          subscriber.complete();
        },
      });
    });
  }

  login(username: string, password: string): Observable<User> {
    return this.http
      .post<User>(`${this.baseUrl}/auth/login/`, { username, password })
      .pipe(tap((user) => this.currentUserSignal.set(user)));
  }

  logout(): Observable<void> {
    return this.http
      .post<void>(`${this.baseUrl}/auth/logout/`, {})
      .pipe(tap(() => this.currentUserSignal.set(undefined)));
  }

  /** Called by the HTTP interceptor when a request comes back
   * unauthorized so the rest of the app reflects the expired session
   * immediately, without waiting for another /me/ round trip. */
  markSessionExpired(): void {
    this.currentUserSignal.set(undefined);
  }
}
