'use client';

import React, { useState, useEffect } from 'react';
import TreeView from './components/TreeView';
import { motion } from 'framer-motion';

type TreeNode = {
  name: string;
  type: 'file' | 'directory';
  children?: TreeNode[];
};

function countNodes(nodes: TreeNode[]): { files: number; dirs: number } {
  let files = 0, dirs = 0;
  for (const n of nodes) {
    if (n.type === 'directory') {
      dirs++;
      if (n.children) { const s = countNodes(n.children); files += s.files; dirs += s.dirs; }
    } else { files++; }
  }
  return { files, dirs };
}

const services = [
  { name: 'Hermes Agent', desc: 'Agente autónomo con inteligencia artificial para automatización de tareas complejas.', icon: '🤖', url: 'https://hermes.el80.space', domain: 'hermes.el80.space' },
  { name: 'LiteLLM Proxy', desc: 'Router unificado para múltiples proveedores de modelos de lenguaje (OpenRouter, Gemini).', icon: '⚡', url: 'https://litellm.el80.space', domain: 'litellm.el80.space' },
  { name: 'Grafana', desc: 'Plataforma de observabilidad y visualización de métricas en tiempo real.', icon: '📊', url: 'https://grafana.el80.space', domain: 'grafana.el80.space' },
  { name: 'Whisper STT', desc: 'Motor de transcripción de voz a texto local basado en OpenAI Whisper.', icon: '🎙️', url: '#', domain: 'localhost:9000' },
  { name: 'Prometheus', desc: 'Sistema de monitoreo y alertas con recolección de métricas time-series.', icon: '🔥', url: '#', domain: 'localhost:9090' },
  { name: 'Redis', desc: 'Cache en memoria de alto rendimiento para LiteLLM y optimización de latencia.', icon: '💾', url: '#', domain: 'interno' },
];

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  visible: (i: number) => ({ opacity: 1, y: 0, transition: { delay: i * 0.05, duration: 0.4, ease: 'easeOut' } }),
};

const App: React.FC = () => {
  const [treeData, setTreeData] = useState<TreeNode[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/tree')
      .then(r => r.json())
      .then(data => { setTreeData(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const stats = countNodes(treeData);

  return (
    <div>
      {/* ── Navbar ── */}
      <nav className="navbar">
        <div className="container navbar-inner">
          <a className="navbar-brand" href="/">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
            </svg>
            <span>Hermes Stack</span>
          </a>
          <div className="navbar-links">
            <a href="#servicios">Servicios</a>
            <a href="#repositorio">Repositorio</a>
            <a href="/metricas">Métricas</a>
            <a href="https://github.com/erikjosehrnndz-crypto/hermes-stack" target="_blank" rel="noreferrer">GitHub</a>
          </div>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section className="hero">
        <div className="container">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
            <div className="hero-badge">
              <span className="status-dot" />
              Todos los servicios operativos
            </div>
            <h1>Infraestructura<br />de IA Autónoma</h1>
            <p>
              Ecosistema de microservicios orquestado con Docker —
              modelos de lenguaje, monitoreo, transcripción de voz
              y agentes autónomos en un solo stack.
            </p>
            <div className="hero-actions">
              <a className="btn-primary" href="#repositorio">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h7a2 2 0 012 2z"/></svg>
                Explorar repositorio
              </a>
              <a className="btn-secondary" href="https://github.com/erikjosehrnndz/hermes-stack" target="_blank" rel="noreferrer">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
                GitHub
              </a>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ── Stats ── */}
      <section style={{ paddingBottom: 48 }}>
        <div className="container">
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2, duration: 0.4 }}>
            <div className="stats-row">
              <div className="stat-item">
                <div className="stat-value">{services.length}</div>
                <div className="stat-label">Servicios</div>
              </div>
              <div className="stat-item">
                <div className="stat-value">{stats.dirs}</div>
                <div className="stat-label">Directorios</div>
              </div>
              <div className="stat-item">
                <div className="stat-value">{stats.files}</div>
                <div className="stat-label">Archivos</div>
              </div>
              <div className="stat-item">
                <div className="stat-value">24/7</div>
                <div className="stat-label">Disponibilidad</div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      <div className="container"><div className="divider" /></div>

      {/* ── Servicios ── */}
      <section id="servicios" className="section">
        <div className="container">
          <div className="section-header">
            <h2>Servicios</h2>
            <p>Microservicios desplegados y orquestados con Docker Compose.</p>
          </div>
          <div className="services-grid">
            {services.map((svc, i) => (
              <motion.a
                key={svc.name}
                href={svc.url}
                target={svc.url.startsWith('http') ? '_blank' : undefined}
                rel="noreferrer"
                className="service-card"
                custom={i}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                variants={fadeUp}
              >
                <div className="service-icon-box">{svc.icon}</div>
                <div className="service-info">
                  <h3>{svc.name}</h3>
                  <p>{svc.desc}</p>
                  <span className="service-url">{svc.domain}</span>
                </div>
              </motion.a>
            ))}
          </div>
        </div>
      </section>

      <div className="container"><div className="divider" /></div>

      {/* ── Repositorio ── */}
      <section id="repositorio" className="section">
        <div className="container">
          <div className="section-header">
            <h2>Repositorio</h2>
            <p>Estructura del proyecto en tiempo real desde el servidor.</p>
          </div>
          {loading ? (
            <div style={{ textAlign: 'center', padding: 64, color: 'var(--text-muted)' }}>
              Cargando...
            </div>
          ) : treeData.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 64, color: 'var(--text-muted)' }}>
              No se encontraron archivos.
            </div>
          ) : (
            <motion.div initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.4 }}>
              <TreeView nodes={treeData} />
            </motion.div>
          )}
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="footer">
        <div className="container">
          <p>© {new Date().getFullYear()} Hermes Stack · Desarrollado por <a href="https://github.com/erikjosehrnndz" target="_blank" rel="noreferrer">Erik José Hernández</a></p>
        </div>
      </footer>
    </div>
  );
};

export default App;
