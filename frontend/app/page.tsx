'use client';

import { AuthGuard } from './auth';
import Dashboard from './dashboard';

export default function HomePage() {
  return <AuthGuard><Dashboard /></AuthGuard>;
}
