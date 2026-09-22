'use client';

import { AuthGuard, SignInForm } from '../auth';

export default function SignInPage() {
  return <AuthGuard guestOnly><SignInForm /></AuthGuard>;
}
