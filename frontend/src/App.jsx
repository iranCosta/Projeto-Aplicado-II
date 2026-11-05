import { useCallback, useEffect, useRef, useState } from "react";
import * as api from "./api.js";
import Grafico from "./Grafico.jsx";
import { ESTILO, LIM, anomalo, hora, nomeSensor, sensorPadrao, textoModelo, POSICAO } from "./util.js";

const ATUALIZAR_MS = 10000;

// Executa `fn` já na montagem e depois a cada `ms`. Se `chave` mudar, recarrega.
function useAtualizacao(fn, ms, chave) {
  const ref = useRef(fn);
  ref.current = fn;
  useEffect(() => {
    let vivo = true;
    const rodar = () => vivo && ref.current();
    rodar();
    const id = setInterval(rodar, ms);
    return () => { vivo = false; clearInterval(id); };
  }, [ms, chave]);
}

const horaAgora = () => new Date().toISOString().slice(11, 19) + " UTC";

function Cartao({ s, desatualizado }) {
  const e = s.status_alerta ? ESTILO[s.status_alerta] : null;
  const classe = ["cartao", s.status_alerta || "SEM", s.status_alerta === "CRITICO" ? "pulso" : "", desatualizado ? "velho" : ""].join(" ");
  return (
    <div className={classe}>
      <div className="tag">{s.tag}</div>
      <div className="sub">{s.ativo} — {POSICAO[s.posicao] || s.posicao}</div>
      <div className="estado">{e ? e.rotulo : "SEM DADOS"}</div>
      <div className="valores">
        {s.leitura_id == null ? "Aguardando leituras" : `RMS ${s.rms.toFixed(2)} mm/s · Curtose ${s.curtose.toFixed(1)}`}
      </div>
      <div className="hora">{hora(s.timestamp)}</div>
      <div className="aviso-modelo" style={{ visibility: anomalo(s) ? "visible" : "hidden" }}>⚠ MODELO: PADRÃO ANÔMALO</div>
    </div>
  );
}

function Resumo({ sensores }) {
  const n = (k) => sensores.filter((s) => s.status_alerta === k).length;
  const an = sensores.filter(anomalo).length;
  return (
    <p className="resumo">
      🔴 {n("CRITICO")} crítico(s) · 🟡 {n("ATENCAO")} em atenção · 🟢 {n("NORMAL")} normal(is)
      {an > 0 && ` · ⚠ ${an} com padrão anômalo pelo modelo`}
    </p>
  );
}

function Alertas() {
  const [dados, setDados] = useState(null);
  const [erro, setErro] = useState(null);

  const carregar = useCallback(async () => {
    try { setDados(await api.alertasPendentes()); setErro(null); }
    catch (e) { setErro(e.message); }
  }, []);
  useAtualizacao(carregar, ATUALIZAR_MS);

  const reconhecer = async (id) => {
    try { await api.reconhecer(id); await carregar(); }
    catch (e) { setErro(`Não foi possível reconhecer o alerta: ${e.message}`); }
  };

  return (
    <section>
      <h2>🔔 Alertas não reconhecidos: {dados ? dados.nao_reconhecidos : "…"}</h2>
      {erro && <p className="erro">Não foi possível carregar os alertas: {erro}</p>}
      {dados && dados.nao_reconhecidos === 0 && <p className="legenda">Nenhum alerta pendente.</p>}
      {dados?.alertas.map((a) => (
        <div className="alerta" key={a.id}>
          <span className={`selo ${a.severidade}`}>{ESTILO[a.severidade].rotulo}</span>
          <div className="alerta-txt">
            <b>{nomeSensor(a)}</b> · {hora(a.timestamp)}<br />{a.mensagem}
          </div>
          <button onClick={() => reconhecer(a.id)}>Reconhecer</button>
        </div>
      ))}
      {dados && dados.nao_reconhecidos > dados.alertas.length && (
        <p className="legenda">Mostrando os {dados.alertas.length} mais recentes de {dados.nao_reconhecidos}.</p>
      )}
    </section>
  );
}

function Detalhe({ sensor }) {
  const [leituras, setLeituras] = useState(null);
  const [erro, setErro] = useState(null);
  const [aba, setAba] = useState("rms");

  useEffect(() => { setLeituras(null); }, [sensor.sensor_id]);
  const carregar = useCallback(async () => {
    try { setLeituras(await api.historico(sensor.sensor_id)); setErro(null); }
    catch (e) { setErro(e.message); }
  }, [sensor.sensor_id]);
  useAtualizacao(carregar, ATUALIZAR_MS, sensor.sensor_id);

  if (erro && !leituras) return <p className="erro">Não foi possível carregar o histórico: {erro}</p>;
  if (!leituras) return <p className="legenda">Carregando histórico…</p>;
  if (leituras.length === 0) return <p className="legenda">Este sensor ainda não tem leituras.</p>;

  const u = leituras[0];
  const e = ESTILO[u.status_alerta];
  return (
    <>
      <div className={`diagnostico ${u.status_alerta}`}>
        <div className="estado">Diagnóstico: {e.rotulo}</div>
        <ul>{u.motivos.map((m) => <li key={m}>{m}</li>)}</ul>
        <div className="modelo">{textoModelo(u.modelo)}</div>
      </div>
      <p className="legenda">
        Status (semáforo) pela regra de limiar (ISO 10816 adaptada). O modelo preditivo (Isolation Forest, um por
        sensor) aponta leituras fora do padrão aprendido, mesmo abaixo dos limiares — no gráfico, essas leituras aparecem com um anel.
      </p>
      <div className="abas" role="tablist">
        <button role="tab" aria-selected={aba === "rms"} onClick={() => setAba("rms")}>RMS (mm/s)</button>
        <button role="tab" aria-selected={aba === "curtose"} onClick={() => setAba("curtose")}>Curtose</button>
      </div>
      <Grafico leituras={leituras} campo={aba} limites={LIM[aba]} titulo={aba === "rms" ? "RMS (mm/s)" : "Curtose"} />
      <p className="legenda">Últimas {leituras.length} leituras · atualiza a cada 10 s</p>
    </>
  );
}

export default function App() {
  const [sensores, setSensores] = useState(null);
  const [falhaDesde, setFalhaDesde] = useState(null);
  const [atualizadoEm, setAtualizadoEm] = useState(null);
  const [erroInicial, setErroInicial] = useState(null);
  const [escolhido, setEscolhido] = useState(null);
  const [tema, setTema] = useState(() => document.documentElement.dataset.tema || "claro");

  const carregar = useCallback(async () => {
    try {
      const lista = await api.statusSensores();
      setSensores(lista);
      setAtualizadoEm(horaAgora());
      setFalhaDesde(null);
      setErroInicial(null);
      setEscolhido((atual) => atual ?? lista[sensorPadrao(lista)]?.sensor_id ?? null);
    } catch (e) {
      setFalhaDesde((d) => d || horaAgora());
      setErroInicial(e.message);
    }
  }, []);
  useAtualizacao(carregar, ATUALIZAR_MS);

  const alternarTema = () => {
    const novo = tema === "claro" ? "escuro" : "claro";
    document.documentElement.dataset.tema = novo;
    try { localStorage.setItem("tema", novo); } catch { /* sem armazenamento: só não persiste */ }
    setTema(novo);
  };

  const sensorAtual = sensores?.find((s) => s.sensor_id === escolhido);
  const desatualizado = Boolean(falhaDesde && sensores);

  return (
    <main>
      <header>
        <div>
          <h1>Painel de Saúde dos Ativos</h1>
          <p className="subtitulo">ArcelorMittal Tuper · motores e compressores</p>
        </div>
        <button className="tema" onClick={alternarTema} aria-label="Alternar tema">◐ Tema</button>
      </header>

      {!sensores && !erroInicial && <p className="legenda">Carregando dados da API…</p>}
      {!sensores && erroInicial && (
        <p className="erro">
          API indisponível. Suba a API (<code>uvicorn src.main:app</code>) e confira o <code>VITE_API_URL</code> (atual: {api.API_URL}).
          <br /><small>{erroInicial}</small>
        </p>
      )}

      {sensores && (
        <>
          {desatualizado ? (
            <p className="erro">
              ⚠ Sem comunicação com a API desde {falhaDesde}. Mostrando os últimos dados recebidos às {atualizadoEm}. Tentando de novo a cada 10 s.
            </p>
          ) : (
            <p className="legenda">🟢 Conectado à API · atualizado às {atualizadoEm} (a cada 10 s)</p>
          )}
          <div className={desatualizado ? "velho" : ""}><Resumo sensores={sensores} /></div>
          <div className="grade-cartoes">
            {sensores.map((s) => <Cartao key={s.sensor_id} s={s} desatualizado={desatualizado} />)}
          </div>

          <hr />
          <Alertas />

          <hr />
          <section>
            <h2>Detalhe do sensor</h2>
            <label className="seletor">
              Sensor{" "}
              <select value={escolhido ?? ""} onChange={(e) => setEscolhido(Number(e.target.value))}>
                {sensores.map((s) => <option key={s.sensor_id} value={s.sensor_id}>{nomeSensor(s)}</option>)}
              </select>
            </label>
            {sensorAtual && <Detalhe sensor={sensorAtual} />}
          </section>
        </>
      )}
    </main>
  );
}
