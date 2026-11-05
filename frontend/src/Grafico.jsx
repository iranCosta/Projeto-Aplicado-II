import { ESTILO, anomalo, horaCurta } from "./util.js";

const W = 860, H = 340, M = { t: 16, r: 16, b: 34, l: 48 };

// Gráfico em SVG: linha, pontos coloridos pelo status, anel nas leituras anômalas pelo modelo,
// e linhas tracejadas nos limiares de atenção e crítico.
export default function Grafico({ leituras, campo, titulo, limites }) {
  const dados = [...leituras]
    .reverse()
    .map((l) => ({ ...l, t: new Date(l.timestamp).getTime(), v: l[campo] }));
  if (dados.length < 1) return null;

  const t0 = dados[0].t, t1 = dados[dados.length - 1].t || t0 + 1;
  const vmax = Math.max(...dados.map((d) => d.v), limites[1]) * 1.1;
  const x = (t) => M.l + ((t - t0) / Math.max(t1 - t0, 1)) * (W - M.l - M.r);
  const y = (v) => H - M.b - (v / vmax) * (H - M.t - M.b);

  const yTicks = [0, 1, 2, 3, 4].map((i) => (vmax / 4) * i);
  const xTicks = [0, 1, 2, 3].map((i) => t0 + ((t1 - t0) / 3) * i);
  const linha = dados.map((d, i) => `${i ? "L" : "M"}${x(d.t).toFixed(1)},${y(d.v).toFixed(1)}`).join(" ");
  const nomesLim = [["Atenção", "var(--atencao)"], ["Crítico", "var(--critico)"]];

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="grafico" role="img" aria-label={`Gráfico de ${titulo}`}>
      {yTicks.map((v) => (
        <g key={v}>
          <line x1={M.l} x2={W - M.r} y1={y(v)} y2={y(v)} className="grade" />
          <text x={M.l - 8} y={y(v) + 4} textAnchor="end" className="eixo">{v.toFixed(1)}</text>
        </g>
      ))}
      {xTicks.map((t) => (
        <text key={t} x={x(t)} y={H - 10} textAnchor="middle" className="eixo">{horaCurta(t)}</text>
      ))}
      <text x={M.l} y={12} className="eixo">{titulo} · horário UTC</text>
      {limites.map((v, i) => (
        <g key={v}>
          <line x1={M.l} x2={W - M.r} y1={y(v)} y2={y(v)} stroke={nomesLim[i][1]} strokeWidth="2" strokeDasharray="6 4" />
          <text x={W - M.r} y={y(v) - 5} textAnchor="end" fill={nomesLim[i][1]} className="lim">{nomesLim[i][0]}</text>
        </g>
      ))}
      <path d={linha} className="linha" />
      {dados.map((d) => (
        <g key={d.id ?? d.t}>
          {anomalo(d) && <circle cx={x(d.t)} cy={y(d.v)} r="10" className="anel" />}
          <circle cx={x(d.t)} cy={y(d.v)} r="4.5" fill={ESTILO[d.status_alerta]?.cor}>
            <title>{`${horaCurta(d.t)} · ${titulo} ${d.v.toFixed(2)} · ${ESTILO[d.status_alerta]?.rotulo}`}</title>
          </circle>
        </g>
      ))}
    </svg>
  );
}
