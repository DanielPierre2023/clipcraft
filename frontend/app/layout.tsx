// frontend/app/layout.tsx
import type { Metadata } from 'next';
import { ClerkProvider } from '@clerk/nextjs';
import '@/app/globals.css';

export const metadata: Metadata = {
  title: 'ClipCraft Studio - AI Video Generator',
  description: 'Production-grade AI Video Generation Engine',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider>
      <html lang="en" className="dark">
        <body className="bg-zinc-950 text-zinc-100 antialiased selection:bg-purple-500 selection:text-white">
          {children}
        </body>
      </html>
    </ClerkProvider>
  );
}
