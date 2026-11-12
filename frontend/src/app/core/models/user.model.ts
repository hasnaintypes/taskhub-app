export type Role = 'ADMIN' | 'MANAGER' | 'EMPLOYEE';

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: Role;
  date_joined: string;
}
