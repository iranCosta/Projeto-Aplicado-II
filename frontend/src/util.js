// Limiares da regra (espelham services/regras.py: ISO 10816 adaptada)
export const LIM = { rms: [4.5, 7.1], curtose: [4.0, 8.0] };

export const ESTILO = {
  NORMAL: { rotulo: "NORMAL", cor: "var(--normal)" },
  ATENCAO: { rotulo: "ATENÇÃO", cor: "var(--atencao)" },
  CRITICO: { rotulo: "CRÍTICO", cor: "var(--critico)" },
};
export const POSICAO = { LADO_ACOPLADO: "Lado acoplado", LADO_LIVRE: "Lado livre" };

export const nomeSensor = (s) => `${s.tag} · ${POSICAO[s.posicao] || s.posicao}`;
export const anomalo = (s) => Boolean(s?.modelo?.anomalia);

export function hora(ts) {
  if (!ts) return "—";
  const d = new Date(ts);
  const p = (n) => String(n).padStart(2, "0");
  return `${p(d.getUTCDate())}/${p(d.getUTCMonth() + 1)}/${d.getUTCFullYear()} ${p(d.getUTCHours())}:${p(d.getUTCMinutes())} UTC`;
}
export const horaCurta = (ms) => {
  const d = new Date(ms);
  const p = (n) => String(n).padStart(2, "0");
  return `${p(d.getUTCDate())}/${p(d.getUTCMonth() + 1)} ${p(d.getUTCHours())}:${p(d.getUTCMinutes())}`;
};

export function textoModelo(m) {
  if (!m) return "Modelo preditivo: não treinado";
  if (m.anomalia)
    return `Modelo preditivo: ⚠ PADRÃO ANÔMALO (score ${m.score.toFixed(2)}) — comportamento fora do aprendido para este sensor; possível início de degradação`;
  return `Modelo preditivo: dentro do padrão aprendido (score ${m.score.toFixed(2)})`;
}

// abre no primeiro sensor com problema: crítico, atenção, anômalo, depois o resto
export function sensorPadrao(sensores) {
  const prio = (s) => ({ CRITICO: 0, ATENCAO: 1 }[s.status_alerta] ?? (anomalo(s) ? 2 : 3));
  return sensores.reduce((m, s, i) => (prio(s) < prio(sensores[m]) ? i : m), 0);
}
