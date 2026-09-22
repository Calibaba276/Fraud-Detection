'use client';

import { AuthGuard, SignUpForm } from '../auth';

export default function SignUpPage() {
  return <AuthGuard guestOnly><SignUpForm /></AuthGuard>;
}
