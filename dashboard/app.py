"""
Painel de monitoramento de vibração (Aula 07).
Rode da raiz, com a API no ar:  streamlit run dashboard/app.py

Pensado para monitor de chão de fábrica: cartões grandes, legíveis a 2 metros,
verde = normal, amarelo = atenção, vermelho = crítico.
"""
import sys
from datetime import datetime
from html import escape
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # para importar services/
import cliente  # noqa: E402
from services.regras import (LIM_CURT_ATENCAO, LIM_CURT_CRITICO,  # noqa: E402
                             LIM_RMS_ATENCAO, LIM_RMS_CRITICO)

ATUALIZAR_A_CADA = "10s"

# fundo, texto, rótulo — contraste alto (amarelo com texto escuro)
ESTILO = {
    "NORMAL": ("#15803d", "#ffffff", "NORMAL"),
    "ATENCAO": ("#facc15", "#111827", "ATENÇÃO"),
    "CRITICO": ("#b91c1c", "#ffffff", "CRÍTICO"),
    None: ("#4b5563", "#ffffff", "SEM DADOS"),
}
POSICAO = {"LADO_ACOPLADO": "Lado acoplado", "LADO_LIVRE": "Lado livre"}

CSS = """
<style>
.cartao { border-radius: 14px; padding: 18px 22px; margin-bottom: 16px; }
.cartao .tag { font-size: 2.1rem; font-weight: 800; line-height: 1.1; }
.cartao .sub { font-size: 1.05rem; opacity: .9; }
.cartao .estado { font-size: 2.6rem; font-weight: 900; letter-spacing: .04em; margin: 8px 0 4px; }
.cartao .valores { font-size: 1.25rem; font-weight: 600; }
.cartao .hora { font-size: .95rem; opacity: .85; margin-top: 4px; }
.pulso { animation: pulso 1.2s ease-in-out infinite; }
@keyframes pulso { 0%, 100% { box-shadow: 0 0 0 0 rgba(185,28,28,.8); } 50% { box-shadow: 0 0 0 12px rgba(185,28,28,0); } }
.resumo { font-size: 1.5rem; font-weight: 700; }
.diagnostico { border-radius: 14px; padding: 16px 22px; margin-bottom: 8px; }
.diagnostico .estado { font-size: 1.9rem; font-weight: 900; }
.diagnostico ul { font-size: 1.35rem; font-weight: 600; margin: 6px 0 0; }
</style>
"""


def _hora(ts: str | None) -> str:
    if not ts:
        return "—"
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).strftime("%d/%m/%Y %H:%M UTC")


def nome_sensor(s: dict) -> str:
    return f"{s['tag']} · {POSICAO.get(s['posicao'], s['posicao'])}"


def cartao_html(s: dict) -> str:
    fundo, texto, rotulo = ESTILO.get(s.get("status_alerta"), ESTILO[None])
    pulso = " pulso" if s.get("status_alerta") == "CRITICO" else ""
    if s.get("leitura_id") is None:
        valores = "Aguardando leituras"
    else:
        valores = f"RMS {s['rms']:.2f} mm/s · Curtose {s['curtose']:.1f}"
    return (
        f'<div class="cartao{pulso}" style="background:{fundo};color:{texto}">'
        f'<div class="tag">{escape(s["tag"])}</div>'
        f'<div class="sub">{escape(s["ativo"])} — {escape(POSICAO.get(s["posicao"], s["posicao"]))}</div>'
        f'<div class="estado">{rotulo}</div>'
        f'<div class="valores">{valores}</div>'
        f'<div class="hora">{_hora(s.get("timestamp"))}</div>'
        "</div>"
    )


def resumo(sensores: list[dict]) -> str:
    cont = {k: sum(s.get("status_alerta") == k for s in sensores) for k in ("CRITICO", "ATENCAO", "NORMAL")}
    return f"🔴 {cont['CRITICO']} crítico(s) &nbsp;·&nbsp; 🟡 {cont['ATENCAO']} em atenção &nbsp;·&nbsp; 🟢 {cont['NORMAL']} normal(is)"


def grafico(df: pd.DataFrame, campo: str, titulo: str, lim_atencao: float, lim_critico: float) -> alt.Chart:
    df = df.assign(estado=df["status_alerta"].map(lambda s: ESTILO[s][2]))
    base = alt.Chart(df).encode(x=alt.X("timestamp:T", title="Horário (UTC)", axis=alt.Axis(format="%d/%m %H:%M")))
    linha = base.mark_line(color="#64748b").encode(y=alt.Y(f"{campo}:Q", title=titulo))
    pontos = base.mark_circle(size=60).encode(
        y=f"{campo}:Q",
        color=alt.Color("estado:N", title="Status",
                        scale=alt.Scale(domain=[ESTILO[k][2] for k in ("NORMAL", "ATENCAO", "CRITICO")],
                                        range=[ESTILO["NORMAL"][0], "#eab308", ESTILO["CRITICO"][0]])),
        tooltip=[alt.Tooltip("timestamp:T", title="Horário", format="%d/%m %H:%M"),
                 alt.Tooltip(f"{campo}:Q", title=titulo, format=".2f"), alt.Tooltip("estado:N", title="Status")],
    )
    limites = pd.DataFrame({"valor": [lim_atencao, lim_critico], "nome": ["Atenção", "Crítico"],
                            "cor": ["#eab308", ESTILO["CRITICO"][0]]})
    regras = alt.Chart(limites).mark_rule(strokeDash=[6, 4], strokeWidth=2).encode(
        y="valor:Q", color=alt.Color("cor:N", scale=None))
    rotulos = alt.Chart(limites).mark_text(align="left", dx=4, dy=-6, fontWeight="bold").encode(
        y="valor:Q", x=alt.value(0), text=alt.Text("nome:N"), color=alt.Color("cor:N", scale=None))
    return (linha + pontos + regras + rotulos).properties(height=340)


def caixa_diagnostico(ultima: dict) -> None:
    fundo, texto, rotulo = ESTILO[ultima["status_alerta"]]
    motivos = "".join(f"<li>{escape(m)}</li>" for m in ultima["motivos"])
    st.markdown(f'<div class="diagnostico" style="background:{fundo};color:{texto}">'
                f'<div class="estado">Diagnóstico: {rotulo}</div><ul>{motivos}</ul></div>',
                unsafe_allow_html=True)
    st.caption("Diagnóstico pela regra de limiar (ISO 10816 adaptada). "
               "A detecção por Isolation Forest será integrada nas próximas etapas.")


@st.fragment(run_every=ATUALIZAR_A_CADA)
def painel_geral() -> list[dict] | None:
    try:
        sensores = cliente.status_sensores()
    except cliente.ApiIndisponivel as e:
        st.error(f"API indisponível. Suba a API com `uvicorn src.main:app` e confira API_URL.\n\n{e}")
        return None
    st.markdown(f'<div class="resumo">{resumo(sensores)}</div>', unsafe_allow_html=True)
    st.write("")
    colunas = st.columns(3)
    for i, s in enumerate(sensores):
        with colunas[i % 3]:
            st.markdown(cartao_html(s), unsafe_allow_html=True)
    return sensores


@st.fragment(run_every=ATUALIZAR_A_CADA)
def detalhe(sensor: dict) -> None:
    try:
        leituras = cliente.historico(sensor["sensor_id"])
    except cliente.ApiIndisponivel as e:
        st.error(f"Não foi possível carregar o histórico: {e}")
        return
    if not leituras:
        st.info("Este sensor ainda não tem leituras.")
        return
    caixa_diagnostico(leituras[0])
    df = pd.DataFrame(leituras)
    aba_rms, aba_curt = st.tabs(["RMS (mm/s)", "Curtose"])
    with aba_rms:
        st.altair_chart(grafico(df, "rms", "RMS (mm/s)", LIM_RMS_ATENCAO, LIM_RMS_CRITICO), width="stretch")
    with aba_curt:
        st.altair_chart(grafico(df, "curtose", "Curtose", LIM_CURT_ATENCAO, LIM_CURT_CRITICO), width="stretch")
    st.caption(f"Últimas {len(df)} leituras · atualiza a cada {ATUALIZAR_A_CADA}")


def main() -> None:
    st.set_page_config(page_title="Vibração — Tuper", page_icon="🛠️", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    st.title("Monitoramento de Vibração")

    sensores = painel_geral()
    if not sensores:
        return

    st.divider()
    st.header("Detalhe do sensor")
    # abre no primeiro sensor com problema, se houver
    ordem = {"CRITICO": 0, "ATENCAO": 1}
    padrao = min(range(len(sensores)), key=lambda i: (ordem.get(sensores[i].get("status_alerta"), 2), i))
    escolhido = st.selectbox("Sensor", sensores, index=padrao, format_func=nome_sensor)
    detalhe(escolhido)


main()
