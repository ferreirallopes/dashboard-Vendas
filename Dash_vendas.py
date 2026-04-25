#1. Importa bibliotecas
import pandas as pd
import streamlit as st
import plotly.express as px

#2. Configura página
st. set_page_config(
    page_title = "Dashboard de Vendas",
    page_icon = "📊",
    layout = "wide"
)

st.title("📊 Dashboard de Vendas")
st.caption("     Análise diagnóstica e visão inicial para análise preditiva.     ")

st.markdown("""
<style>
html, body, [class*="css"]  {
    font-size: 14px;
}
</style>
""", unsafe_allow_html=True)

def formatar_real(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatar_numero(valor):
    return f"{valor:,.0f}".replace(",", ".")

def formatar_percentual(valor):
    return f"{valor:.2f}%".replace(".", ",")

#3. Lê a base CSV

@st.cache_data
def carregar_dados():
    df = pd.read_csv(r"base_vendas_lojas_pequenas.csv")
    df["DATA"] = pd.to_datetime(df["DATA"])
    df["Mês"] = df["DATA"].dt.strftime("%Y-%m")
    df["Dia da Semana"] = df["DATA"].dt.day_name()
    df["Ticket Médio"] = df["Faturamento Dia"] / df["Quantidade de Vendas"]
    return df

df = carregar_dados()

#Aqui é feita a leitura do arquivo csv
#transforma a coluna DATA em data real
#cria coluna de mês
#cria coluna de dia da semana
#calcula ticket médio



#4. Cria colunas auxiliares

#5. Cria filtros
st.sidebar.header("Filtros")

# 1. Zona
zonas = st.sidebar.multiselect(
    "Selecione a Zona",
    options=sorted(df["Zona"].unique()),
    default=sorted(df["Zona"].unique())
)

# 2. Base filtrada por zona (ESSENCIAL)
df_zona = df[df["Zona"].isin(zonas)]

# 3. Lojas dependentes da zona
lojas = st.sidebar.multiselect(
    "Selecione a Loja",
    options=sorted(df_zona["Nome da Loja"].unique()),
    default=sorted(df_zona["Nome da Loja"].unique())
)

# 4. Canal (também pode depender da zona)
canais = st.sidebar.multiselect(
    "Selecione o Canal",
    options=sorted(df_zona["Canal"].unique()),
    default=sorted(df_zona["Canal"].unique())
)

# 5. Período
data_min = df["DATA"].min()
data_max = df["DATA"].max()

periodo = st.sidebar.date_input(
    "Período",
    value=[data_min, data_max],
    min_value=data_min,
    max_value=data_max
)

# 6. Aplicação final dos filtros
df_filtrado = df[
    (df["Zona"].isin(zonas)) &
    (df["Nome da Loja"].isin(lojas)) &
    (df["Canal"].isin(canais))
]

# 7. Filtro de data
if len(periodo) == 2:
    inicio = pd.to_datetime(periodo[0])
    fim = pd.to_datetime(periodo[1])

    df_filtrado = df_filtrado[
        (df_filtrado["DATA"] >= inicio) &
        (df_filtrado["DATA"] <= fim)
    ]


#7. Filtrar por periodo

df["DATA"] = pd.to_datetime(df["DATA"])

if len(periodo) == 2:
    inicio = pd.to_datetime(periodo[0])
    fim = pd.to_datetime(periodo[1])

    df_filtrado = df_filtrado[
        (df_filtrado["DATA"] >= inicio) &
        (df_filtrado["DATA"] <= fim)
    ]
#8. calcular KPI's
    faturamento_total = df_filtrado["Faturamento Dia"].sum()
vendas_total = df_filtrado["Quantidade de Vendas"].sum()
ticket_medio = faturamento_total / vendas_total

loja_top = df_filtrado.groupby("Nome da Loja")["Faturamento Dia"].sum().idxmax()

#9. mostrar o card de indicador

col1, col2, col3, col4 = st.columns(4)

col1.metric("Faturamento Total", formatar_real(faturamento_total))
col2.metric("Total de Vendas", formatar_numero(vendas_total))
col3.metric("Ticket Médio", formatar_real(ticket_medio))
col4.metric("Loja Top", loja_top)


#10. grafico de faturamento

fat_zona = df_filtrado.groupby("Zona", as_index=False)["Faturamento Dia"].sum()


fig_zona = px.bar(
    fat_zona,
    x="Zona",
    y="Faturamento Dia",
    title="Faturamento por Zona"
)


st.plotly_chart(fig_zona, use_container_width=True)

#11. grafico de vendas por canal

st.subheader("Vendas por Canal")

vendas_canal = (
    df_filtrado
    .groupby("Canal", as_index=False)["Quantidade de Vendas"]
    .sum()
)

st.write(vendas_canal)  # teste: mostra se tem dados

fig_canal = px.pie(
    vendas_canal,
    names="Canal",
    values="Quantidade de Vendas",
    title="Distribuição de Vendas por Canal"
)

st.plotly_chart(fig_canal, use_container_width=True)


#12. Evolução diária do faturamento
fat_dia = df_filtrado.groupby("DATA", as_index=False)["Faturamento Dia"].sum()

#Agrupa o faturamento por dia.

fig_linha = px.line(
    fat_dia,
    x="DATA",
    y="Faturamento Dia",
    title="Evolução do Faturamento Dia a Dia",
    markers=True
)

#Cria linha do tempo.

#Esse gráfico é importante para análise preditiva, porque mostra tendência.

#13. Ranking de lojas
st.subheader("🏆 Ranking de Lojas")

# DEBUG (pode apagar depois)
st.write("Linhas após filtro:", len(df_filtrado))

if df_filtrado.empty:
    st.warning("Sem dados com os filtros selecionados.")
else:
    ranking = (
        df_filtrado
        .groupby(["Nome da Loja", "Zona"], as_index=False)
        .agg({
            "Faturamento Dia": "sum",
            "Quantidade de Vendas": "sum",
            "Vendas Débito": "sum",
            "Vendas Crédito": "sum",
            "Vendas Dinheiro": "sum"
        })
    )

    # Ticket médio (evita divisão por zero)
    ranking["Ticket Médio"] = ranking["Faturamento Dia"] / ranking["Quantidade de Vendas"].replace(0, 1)

    # Ordena
    ranking = ranking.sort_values("Faturamento Dia", ascending=False)

    # 👉 MOSTRAR TABELA
    st.dataframe(ranking, use_container_width=True, hide_index=True)

    # 👉 GRÁFICO TOP 10
    import plotly.express as px

    fig = px.bar(
        ranking.head(10),
        x="Faturamento Dia",
        y="Nome da Loja",
        color="Zona",
        orientation="h",
        title="Top 10 Lojas por Faturamento",
        text_auto=".2s"
    )

    fig.update_layout(yaxis={"categoryorder": "total ascending"})

    st.plotly_chart(fig, use_container_width=True)

#14 - Forma de Pagamento


st.subheader("💳 Formas de Pagamento")

pagamentos = pd.DataFrame({
    "Forma de Pagamento": ["Débito", "Crédito", "Dinheiro"],
    "Quantidade": [
        df_filtrado["Vendas Débito"].sum(),
        df_filtrado["Vendas Crédito"].sum(),
        df_filtrado["Vendas Dinheiro"].sum()
    ]
})

# Debug rápido
st.write(pagamentos)

if pagamentos["Quantidade"].sum() == 0:
    st.warning("Sem dados para exibir (verifique os filtros).")
else:
    fig_pagamento = px.bar(
        pagamentos,
        x="Forma de Pagamento",
        y="Quantidade",
        title="Volume de Vendas por Forma de Pagamento",
        text_auto=True
    )

    st.plotly_chart(fig_pagamento, use_container_width=True)