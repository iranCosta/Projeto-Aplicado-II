// Cliente HTTP da API. O front só lê dados por aqui.
export const API_URL = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
const TIMEOUT_MS = 6000;

export class ApiIndisponivel extends Error {}

async function chamar(caminho, opcoes = {}) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), TIMEOUT_MS);
  try {
    const r = await fetch(`${API_URL}${caminho}`, { ...opcoes, signal: ctrl.signal });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return await r.json();
  } catch (e) {
    throw new ApiIndisponivel(`${API_URL}${caminho}: ${e.message}`);
  } finally {
    clearTimeout(timer);
  }
}

export const statusSensores = () => chamar("/api/status").then((d) => d.sensores);
export const historico = (sensorId, limite = 200) =>
  chamar(`/api/diagnosticos?sensor_id=${sensorId}&limite=${limite}`).then((d) => d.diagnosticos);
export const alertasPendentes = (limite = 10) =>
  chamar(`/api/alertas?limite=${limite}&reconhecido=false`);
export const reconhecer = (id) => chamar(`/api/alertas/${id}/reconhecer`, { method: "POST" });
