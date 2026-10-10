export type UserRole = 'Manufacturer' | 'Importer' | 'Brand Owner' | 'MSME' | 'Other';

export interface User {
  id: string;
  fullName: string;
  email: string;
  phone?: string;
  userType: UserRole;
  organisation?: string;
  createdAt?: string;
}

export interface AuthResponse {
  user: User;
  token: string;
}
