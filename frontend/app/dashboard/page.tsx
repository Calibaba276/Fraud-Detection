'use client';

import { AuthGuard } from '../auth';
import Dashboard from '../dashboard';

export default function DashboardPage() {
  return <AuthGuard><Dashboard /></AuthGuard>;
}
