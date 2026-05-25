import type { Metadata } from 'next';
import '../src/index.css';

export const metadata: Metadata = {
  title: 'Hermes Stack',
  description: 'Infraestructura de IA Autónoma',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
