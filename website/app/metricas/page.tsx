import MetricsDashboard from '../../src/components/MetricsDashboard';
import '../../src/index.css';

export const metadata = {
  title: 'Métricas · Hermes Stack',
  description: 'Monitoreo en tiempo real del Hermes Stack',
};

export default function MetricasPage() {
  return (
    <div>
      {/* Navbar inline — misma estructura que App.tsx */}
      <nav className="navbar">
        <div className="container navbar-inner">
          <a className="navbar-brand" href="/">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
            </svg>
            <span>Hermes Stack</span>
          </a>
          <div className="navbar-links">
            <a href="/#servicios">Servicios</a>
            <a href="/#repositorio">Repositorio</a>
            <a href="/metricas" style={{ color: 'var(--text-primary)' }}>Métricas</a>
            <a href="https://github.com/erikjosehrnndz-crypto/hermes-stack" target="_blank" rel="noreferrer">GitHub</a>
          </div>
        </div>
      </nav>

      <section className="section">
        <div className="container">
          <MetricsDashboard />
        </div>
      </section>

      <footer className="footer">
        <div className="container">
          <p>© {new Date().getFullYear()} Hermes Stack · <a href="/">Inicio</a></p>
        </div>
      </footer>
    </div>
  );
}
