import type { Metadata } from 'next';

import './globals.css';
import './dashboard.css';
import { AuthProvider } from './auth';

export const metadata: Metadata = {
 title: 'Sentinel | Banking Fraud Detection',
 description: 'Analyze banking transactions, understand risk signals, and manage fraud verification in one research workspace.',
 icons: { icon: '/favicon.svg' },
 openGraph: { title: 'Sentinel | Banking Fraud Detection', description: 'A clearer picture of every transaction.' },
 twitter: { card: 'summary_large_image', title: 'Sentinel | Banking Fraud Detection', description: 'A clearer picture of every transaction.' },
};

export default function RootLayout({children}: 
    Readonly<{children: React.ReactNode}>) {
        return <html lang="en"><body><AuthProvider>{children}</AuthProvider></body></html>;
}
