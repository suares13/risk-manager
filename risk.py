import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# configuração da página — deve ser a primeira chamada do streamlit
st.set_page_config(
    page_title="Risk Manager · MAGERIT",
    page_icon="🛡️",
    layout="wide"
)

# inicializa a lista de ativos na sessão.
# st.session_state persiste os dados enquanto o app está aberto.
if "ativos" not in st.session_state:
    st.session_state.ativos = []


def calcular_nivel(risco):
    """retorna o nível textual com base no valor do risco calculado."""
    if risco <= 4:
        return "🟢 Baixo"
    elif risco <= 9:
        return "🟡 Médio"
    elif risco <= 16:
        return "🟠 Alto"
    return "🔴 Crítico"


def calcular_estrategia(risco):
    """
    define a estratégia de tratamento baseada no nível de risco.
    segue as 4 estratégias da metodologia magerit.
    """
    if risco <= 4:
        return "✅ Aceitar"
    elif risco <= 9:
        return "🔄 Transferir"
    elif risco <= 16:
        return "🛠️ Mitigar"
    return "🚫 Evitar"


def gerar_matriz():
    """
    constrói a matriz de risco 5x5 (probabilidade × impacto).
    posiciona os ativos cadastrados como pontos na célula correspondente.
    """
    matriz = [[[] for _ in range(5)] for _ in range(5)]
    for i, ativo in enumerate(st.session_state.ativos):
        p = ativo["probabilidade"] - 1
        imp = ativo["impacto"] - 1
        matriz[p][imp].append(i + 1)
    return matriz


# ─────────────────────────────────────────────
# SIDEBAR — formulário de cadastro de ativos
# ─────────────────────────────────────────────

with st.sidebar:
    st.title("⚙️ Adicionar Ativo")
    st.caption("Preencha os dados do ativo a ser avaliado.")

    nome = st.text_input("Nome do ativo", placeholder="ex: Banco de dados de clientes")

    ameaca = st.selectbox("Ameaça principal", [
        "Ransomware",
        "Phishing",
        "Acesso não autorizado",
        "Erro humano",
        "Vazamento de dados",
        "Desastre natural"
    ])

    col1, col2 = st.columns(2)
    with col1:
        probabilidade = st.number_input("Probabilidade (1–5)", min_value=1, max_value=5, value=3)
    with col2:
        impacto = st.number_input("Impacto (1–5)", min_value=1, max_value=5, value=3)

    risco_preview = probabilidade * impacto
    st.info(f"Risco calculado: **{risco_preview}** — {calcular_nivel(risco_preview)}")

    if st.button("+ Adicionar à Matriz", use_container_width=True, type="primary"):
        if nome.strip():
            st.session_state.ativos.append({
                "ativo": nome.strip(),
                "ameaca": ameaca,
                "probabilidade": probabilidade,
                "impacto": impacto,
                "risco": risco_preview,
                "nivel": calcular_nivel(risco_preview),
                "estrategia": calcular_estrategia(risco_preview)
            })
            st.rerun()
        else:
            st.warning("Digite o nome do ativo.")

    st.divider()

    # exporta os dados como csv para uso externo
    if st.session_state.ativos:
        df_export = pd.DataFrame(st.session_state.ativos)
        csv = df_export.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Exportar relatório CSV",
            data=csv,
            file_name="relatorio_magerit.csv",
            mime="text/csv",
            use_container_width=True
        )

        if st.button("🗑️ Limpar todos os ativos", use_container_width=True):
            st.session_state.ativos = []
            st.rerun()


# ─────────────────────────────────────────────
# MAIN — dashboard principal
# ─────────────────────────────────────────────

st.title("🛡️ Risk Manager")
st.caption("Gestão de Riscos · Metodologia MAGERIT · Probabilidade × Impacto")
st.divider()

ativos = st.session_state.ativos

if not ativos:
    st.info("Nenhum ativo cadastrado ainda. Use o painel lateral para adicionar o primeiro.")
    st.stop()

# ─── métricas resumo ───
total = len(ativos)
criticos = sum(1 for a in ativos if a["risco"] > 16)
altos = sum(1 for a in ativos if 9 < a["risco"] <= 16)
cobertos = sum(1 for a in ativos if a["risco"] <= 9)
risco_medio = round(sum(a["risco"] for a in ativos) / total, 1)

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total de ativos", total)
col2.metric("Risco crítico 🔴", criticos)
col3.metric("Risco alto 🟠", altos)
col4.metric("Cobertos 🟢", cobertos)
col5.metric("Risco médio", risco_medio)

st.divider()

# ─── matriz e gráfico lado a lado ───
col_matriz, col_chart = st.columns([1.2, 1])

with col_matriz:
    st.subheader("Matriz de Risco")

    # cores de cada célula da matriz baseadas no valor probabilidade × impacto
    def cor_celula(p, i):
        r = p * i
        if r <= 4: return "#1a3a2a"
        if r <= 9: return "#3a2e00"
        if r <= 16: return "#3a1e00"
        return "#3a0a0a"

    def texto_celula(p, i):
        r = p * i
        if r <= 4: return "#21c354"
        if r <= 9: return "#ffd021"
        if r <= 16: return "#ffa421"
        return "#ff4b4b"

    matriz = gerar_matriz()

    # cabeçalho da matriz
    header_cols = st.columns([0.4] + [1] * 5)
    header_cols[0].markdown("<div style='text-align:center;font-size:11px;color:gray'>P\I</div>", unsafe_allow_html=True)
    for i in range(1, 6):
        header_cols[i].markdown(f"<div style='text-align:center;font-size:12px;color:gray'>I{i}</div>", unsafe_allow_html=True)

    # linhas da matriz (probabilidade de 5 a 1, de cima para baixo)
    for p in range(5, 0, -1):
        row_cols = st.columns([0.4] + [1] * 5)
        row_cols[0].markdown(f"<div style='text-align:center;font-size:12px;color:gray;padding-top:8px'>P{p}</div>", unsafe_allow_html=True)
        for i in range(1, 6):
            pontos = matriz[p - 1][i - 1]
            cor = cor_celula(p, i)
            txt_cor = texto_celula(p, i)
            conteudo = " ".join([f"<span style='background:#1c83e1;color:white;border-radius:50%;padding:1px 5px;font-size:10px;font-weight:700'>{n}</span>" for n in pontos])
            row_cols[i].markdown(
                f"<div style='background:{cor};border-radius:6px;height:38px;display:flex;align-items:center;justify-content:center;color:{txt_cor};font-size:10px'>{conteudo or str(p*i)}</div>",
                unsafe_allow_html=True
            )

    st.caption("Cada número representa um ativo cadastrado.")

with col_chart:
    st.subheader("Estratégias de Tratamento")

    # conta quantos ativos há em cada estratégia
    contagem = {"Aceitar": 0, "Transferir": 0, "Mitigar": 0, "Evitar": 0}
    for a in ativos:
        r = a["risco"]
        if r <= 4: contagem["Aceitar"] += 1
        elif r <= 9: contagem["Transferir"] += 1
        elif r <= 16: contagem["Mitigar"] += 1
        else: contagem["Evitar"] += 1

    fig = go.Figure(data=[go.Pie(
        labels=list(contagem.keys()),
        values=list(contagem.values()),
        hole=0.5,
        marker_colors=["#21c354", "#a78bfa", "#1c83e1", "#ff4b4b"],
        textinfo="label+percent",
        textfont_size=12
    )])
    fig.update_layout(
        showlegend=False,
        margin=dict(t=10, b=10, l=10, r=10),
        height=260,
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#fafafa"
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ─── tabela de ativos ───
st.subheader("Registro de Ativos (MAGERIT)")
st.caption(f"{total} ativo(s) cadastrado(s) · risco médio da organização: {risco_medio}")

df = pd.DataFrame(ativos)
df.index = range(1, len(df) + 1)
df.columns = ["Ativo", "Ameaça", "Probabilidade", "Impacto", "Risco", "Nível", "Estratégia"]

st.dataframe(df, use_container_width=True, height=min(400, 50 + len(ativos) * 45))