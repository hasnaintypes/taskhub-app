import { Component, inject } from '@angular/core';
import { RouterLink, RouterOutlet, Router } from '@angular/router';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

import { AuthService } from './core/services/auth.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, MatToolbarModule, MatButtonModule, MatIconModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css',
})
export class AppComponent {
  readonly authService = inject(AuthService);
  private readonly router = inject(Router);

  logout(): void {
    this.authService.logout().subscribe(() => this.router.navigateByUrl('/login'));
  }
}
