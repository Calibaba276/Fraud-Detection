'use client';

import { createContext, useContext, useEffect, useState, type FormEvent, type ReactNode } from 'react';
import { usePathname, useRouter } from 'next/navigation';

const USERS_KEY = 'fraud-detection-users';
const SESSION_KEY = 'fraud-detection-session';
const MIN_PASSWORD_LENGTH = 8;

type DemoUser = { email: string; password: string };
type Session = { email: string };
type AuthResult = { success: boolean; message: string };
type AuthContextValue = {
  user: Session | null;
  loading: boolean;
  signIn: (email: string, password: string) => AuthResult;
  signUp: (email: string, password: string) => AuthResult;
  signOut: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);
const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function readUsers(): DemoUser[] {
  try {
    const saved = JSON.parse(localStorage.getItem(USERS_KEY) || '[]');
    return Array.isArray(saved)
      ? saved.filter((user): user is DemoUser => typeof user?.email === 'string' && typeof user?.password === 'string')
      : [];
  } catch { return []; }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    try {
      const saved = JSON.parse(localStorage.getItem(SESSION_KEY) || 'null');
      if (saved && typeof saved.email === 'string' && emailPattern.test(saved.email)) setUser({ email: saved.email });
    } catch {
      localStorage.removeItem(SESSION_KEY);
    } finally { setLoading(false); }
  }, []);

  function signIn(email: string, password: string): AuthResult {
    const normalizedEmail = email.trim().toLowerCase();
    if (!normalizedEmail || !password) return { success: false, message: 'Enter both your email and password.' };
    const account = readUsers().find(candidate => candidate.email === normalizedEmail && candidate.password === password);
    if (!account) return { success: false, message: 'Invalid email or password.' };
    const session = { email: account.email };
    try {
      localStorage.setItem(SESSION_KEY, JSON.stringify(session));
      setUser(session);
      return { success: true, message: 'Signed in successfully.' };
    } catch { return { success: false, message: 'Your browser could not save the demo session.' }; }
  }

  function signUp(email: string, password: string): AuthResult {
    const normalizedEmail = email.trim().toLowerCase();
    if (!emailPattern.test(normalizedEmail)) return { success: false, message: 'Enter a valid email address.' };
    if (password.length < MIN_PASSWORD_LENGTH) return { success: false, message: `Use at least ${MIN_PASSWORD_LENGTH} characters for the password.` };
    const users = readUsers();
    if (users.some(candidate => candidate.email === normalizedEmail)) return { success: false, message: 'An account with that email already exists.' };
    const session = { email: normalizedEmail };
    try {
      // Deliberately local-only demo data. Never use a real password here.
      localStorage.setItem(USERS_KEY, JSON.stringify([...users, { email: normalizedEmail, password }]));
      localStorage.setItem(SESSION_KEY, JSON.stringify(session));
      setUser(session);
      return { success: true, message: 'Demo account created. You are now signed in.' };
    } catch { return { success: false, message: 'Your browser could not save the demo account.' }; }
  }

  function signOut() {
    try { localStorage.removeItem(SESSION_KEY); } finally { setUser(null); }
  }

  return <AuthContext.Provider value={{ user, loading, signIn, signUp, signOut }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used inside AuthProvider.');
  return context;
}

export function AuthGuard({ children, guestOnly = false }: { children: ReactNode; guestOnly?: boolean }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  useEffect(() => {
    if (loading) return;
    if (!user && !guestOnly) router.replace('/signin');
    if (user && guestOnly) router.replace('/dashboard');
  }, [guestOnly, loading, pathname, router, user]);
  if (loading || (!user && !guestOnly) || (user && guestOnly)) return <AuthLoading />;
  return <>{children}</>;
}

function AuthLoading() {
  return <main className="auth-page"><p className="auth-loading" role="status">Checking local demo session…</p></main>;
}

function AuthForm({ mode }: { mode: 'signin' | 'signup' }) {
  const { signIn, signUp } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState(false);
  const isSignUp = mode === 'signup';
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const result = isSignUp ? signUp(email, password) : signIn(email, password);
    setMessage(result.message);
    setError(!result.success);
    if (result.success) router.replace('/dashboard');
  }
  return <main className="auth-page"><section className="auth-card" aria-labelledby="auth-title">
    <a className="brand auth-brand" href="/" aria-label="Sentinel home"><b className="brand-mark">S</b>Sentinel<span>.</span></a>
    <p className="eyebrow">DEMONSTRATION ACCESS</p>
    <h1 id="auth-title">{isSignUp ? 'Create a demo account' : 'Sign in to Sentinel'}</h1>
    <p className="auth-copy">{isSignUp ? 'Create a local-only account to open the fraud detection workspace.' : 'Use the local-only demo account stored in this browser.'}</p>
    <p className="auth-warning"><strong>Demo only:</strong> passwords are stored in this browser&apos;s localStorage and are not secure. Do not use a real password.</p>
    <form className="auth-form" onSubmit={submit} noValidate>
      <label>Email<input type="email" autoComplete="email" value={email} onChange={event => setEmail(event.target.value)} placeholder="analyst@example.com" /></label>
      <label>Password<input type="password" autoComplete={isSignUp ? 'new-password' : 'current-password'} value={password} onChange={event => setPassword(event.target.value)} placeholder={isSignUp ? `At least ${MIN_PASSWORD_LENGTH} characters` : 'Your demo password'} /></label>
      {message && <p className={'auth-message ' + (error ? 'error' : 'success')} role={error ? 'alert' : 'status'}>{message}</p>}
      <button className="button primary auth-submit" type="submit">{isSignUp ? 'Create demo account' : 'Sign in'} →</button>
    </form>
    <p className="auth-switch">{isSignUp ? 'Already have a demo account?' : 'Need a demo account?'} <a href={isSignUp ? '/signin' : '/signup'}>{isSignUp ? 'Sign in' : 'Create one'}</a></p>
  </section></main>;
}

export function SignInForm() { return <AuthForm mode="signin" />; }
export function SignUpForm() { return <AuthForm mode="signup" />; }

export function initials(email: string) {
  const name = email.split('@')[0].replace(/[^a-z0-9]+/gi, ' ').trim();
  const parts = name.split(' ').filter(Boolean);
  return (parts.length > 1 ? parts[0][0] + parts[1][0] : name.slice(0, 2)).toUpperCase() || 'DU';
}
