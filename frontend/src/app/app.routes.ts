import { Routes } from '@angular/router';

import { authGuard } from './core/guards/auth.guard';
import { roleGuard } from './core/guards/role.guard';

export const routes: Routes = [
  {
    path: 'login',
    loadComponent: () => import('./auth/login/login.component').then((m) => m.LoginComponent),
  },
  {
    path: 'dashboard',
    canActivate: [authGuard],
    loadComponent: () => import('./dashboard/dashboard.component').then((m) => m.DashboardComponent),
  },
  {
    path: 'tasks',
    canActivate: [authGuard],
    loadComponent: () => import('./tasks/task-list/task-list.component').then((m) => m.TaskListComponent),
  },
  {
    path: 'tasks/new',
    canActivate: [authGuard, roleGuard(['ADMIN', 'MANAGER'])],
    loadComponent: () =>
      import('./tasks/task-create/task-create.component').then((m) => m.TaskCreateComponent),
  },
  {
    path: 'tasks/:id',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./tasks/task-detail/task-detail.component').then((m) => m.TaskDetailComponent),
  },
  {
    path: 'users',
    canActivate: [authGuard, roleGuard(['ADMIN', 'MANAGER'])],
    loadComponent: () => import('./users/user-list/user-list.component').then((m) => m.UserListComponent),
  },
  { path: '', pathMatch: 'full', redirectTo: 'dashboard' },
  { path: '**', redirectTo: 'dashboard' },
];
