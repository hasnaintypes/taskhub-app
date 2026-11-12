import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthService } from '../services/auth.service';

/** Usability guard only — not a security boundary. The backend is the
 * sole source of authorization truth [RBAC-12]. */
export const authGuard: CanActivateFn = () => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (authService.isAuthenticated()) {
    return true;
  }
  return router.createUrlTree(['/login']);
};
