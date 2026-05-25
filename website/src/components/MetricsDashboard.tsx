'use client';

import React, { useState, useEffect, useCallback } from 'react';

type ServiceStatus = { up: boolean; checks?: Record<string, boolean> };
type MetricsData = {
  ts: number;
  services: { hermes: ServiceStatus; litellm: ServiceStatus };
  metrics: {
    totalRequests: number;
    successRequests: number;
    avgLatencyMs: number | null;
    errorRatePct: number;
  };
};

function Dot({ up }: { up: boolean }) {
  return (
    <span
      style={{
        display: 'inline-block',
        width: 8,
        height: 8,
        borderRadius: '50%',
        background: up ? 'var(--success)' : '#ef4444',
        boxShadow: up ? '0 0 6px rgba(34,197,94,0.5)' : '0 0 6px rgba(239,68,68,0.5)',
        flexShrink: 0,
      }}
    />
  );
}

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div style={{
      background: 'var(--bg-elevated)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius)',
      padding: '20px 24px',
      minWidth: 140,
    }}>
      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
        {label}
      </div>
      <div style={{ fontSize: '1.8rem', fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1 }}>
        {value}
      </div>
      {sub && <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 6 }}>{sub}</div>}
    </div>
  );
}

function ServiceCard({ name, status }: { name: string; status: ServiceStatus }) {
  return (
    <div style={{
      background: 'var(--bg-elevated)',
      border: `1px solid ${status.up ? 'rgba(34,197,94,0.2)' : 'rgba(239,68,68,0.2)'}`,
      borderRadius: 'var(--radius)',
      padding: '16px 20px',
      display: 'flex',
      flexDirection: 'column',
      gap: 12,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <Dot up={status.up} />
        <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{name}</span>
        <span style={{
          marginLeft: 'auto',
          fontSize: '0.75rem',
          padding: '2px 8px',
          borderRadius: 12,
          background: status.up ? 'rgba(34,197,94,0.08)' : 'rgba(239,68,68,0.08)',
          color: status.up ? 'var(--success)' : '#ef4444',
          fontWeight: 500,
        }}>
          {status.up ? 'online' : 'offline'}
        </span>
      </div>
      {status.checks && Object.keys(status.checks).length > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          {Object.entries(status.checks).map(([k, v]) => (
            <span key={k} style={{
              fontSize: '0.7rem',
              padding: '2px 7px',
              borderRadius: 10,
              background: v ? 'rgba(34,197,94,0.06)' : 'rgba(239,68,68,0.06)',
              color: v ? 'var(--success)' : '#ef4444',
              border: `1px solid ${v ? 'rgba(34,197,94,0.15)' : 'rgba(239,68,68,0.15)'}`,
            }}>
              {k}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

export default function MetricsDashboard() {
  const [data, setData] = useState<MetricsData | null>(null);
  const [error, setError] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const fetchMetrics = useCallback(() => {
    fetch('/api/metrics')
      .then(r => r.json())
      .then((d: MetricsData) => {
        setData(d);
        setLastUpdate(new Date());
        setError(false);
      })
      .catch(() => setError(true));
  }, []);

  useEffect(() => {
    fetchMetrics();
    const id = setInterval(fetchMetrics, 10000);
    return () => clearInterval(id);
  }, [fetchMetrics]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>
      {/* Header row */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <h2 style={{ fontSize: '1.4rem', fontWeight: 700 }}>Métricas en vivo</h2>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          {error ? (
            <span style={{ color: '#ef4444' }}>Error al obtener datos</span>
          ) : lastUpdate ? (
            <>Actualizado: {lastUpdate.toLocaleTimeString('es-ES')} · refresh cada 10s</>
          ) : (
            'Cargando...'
          )}
        </div>
      </div>

      {/* Services */}
      <div>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: 12, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
          Estado de servicios
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 12 }}>
          <ServiceCard name="Hermes Agent" status={data?.services.hermes ?? { up: false }} />
          <ServiceCard name="LiteLLM Router" status={data?.services.litellm ?? { up: false }} />
        </div>
      </div>

      {/* Stats */}
      <div>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: 12, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
          Rendimiento del agente
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: 12 }}>
          <StatCard
            label="Requests"
            value={data ? data.metrics.totalRequests.toLocaleString('es-ES') : '—'}
            sub="total procesadas"
          />
          <StatCard
            label="Éxito"
            value={data ? data.metrics.successRequests.toLocaleString('es-ES') : '—'}
            sub="respuestas 200"
          />
          <StatCard
            label="Latencia"
            value={data?.metrics.avgLatencyMs != null ? `${data.metrics.avgLatencyMs}ms` : '—'}
            sub="promedio E2E"
          />
          <StatCard
            label="Error rate"
            value={data ? `${data.metrics.errorRatePct}%` : '—'}
            sub="respuestas 5xx"
          />
        </div>
      </div>

      {/* No data state */}
      {!data && !error && (
        <div style={{ textAlign: 'center', padding: 48, color: 'var(--text-muted)' }}>
          Conectando con los servicios...
        </div>
      )}
    </div>
  );
}
