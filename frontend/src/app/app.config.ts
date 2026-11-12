import { ApplicationConfig, inject, provideAppInitializer, provideZoneChangeDetection } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { firstValueFrom } from 'rxjs';

import { routes } from './app.routes';
import { apiInterceptor } from './core/interceptors/api.interceptor';
import { AuthService } from './core/services/auth.service';

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes),
    provideHttpClient(withInterceptors([apiInterceptor])),
    provideAnimationsAsync(),
    // Blocks the initial router navigation until the session-restore call
    // resolves, so authGuard never evaluates against the signal's initial
    // "unknown" state on a hard page load/reload [FE-13].
    provideAppInitializer(() => firstValueFrom(inject(AuthService).bootstrap())),
  ],
};
