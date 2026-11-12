import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';

import { environment } from '../../../environments/environment';
import { AuthService } from '../services/auth.service';

function readCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

const UNSAFE_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE'];

/** Attaches session credentials + the CSRF header to every API request,
 * and redirects to /login with a clear message on a 401 (session expired
 * or never authenticated) [FE-08, FE-13]. */
export const apiInterceptor: HttpInterceptorFn = (req, next) => {
  if (!req.url.startsWith(environment.apiBaseUrl)) {
    return next(req);
  }

  const authService = inject(AuthService);
  const router = inject(Router);

  let authedReq = req.clone({ withCredentials: true });

  if (UNSAFE_METHODS.includes(req.method)) {
    const csrfToken = readCookie('csrftoken');
    if (csrfToken) {
      authedReq = authedReq.clone({ setHeaders: { 'X-CSRFToken': csrfToken } });
    }
  }

  return next(authedReq).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status === 401 && !req.url.endsWith('/auth/login/')) {
        authService.markSessionExpired();
        router.navigate(['/login'], { queryParams: { expired: '1' } });
      }
      return throwError(() => error);
    })
  );
};
