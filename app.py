import pandas as pd
import streamlit as st

from src.diagnostico import diagnosticar
from src.plano import plano_de_acao
from src.vendas import ler_vendas, resumo_vendas

st.set_page_config(page_title="Analisador de Pequenos Negócios", page_icon="🏪", layout="wide")
st.title("🏪 Analisador de Pequenos Negócios")
st.caption("Diagnóstico financeiro em linguagem simples para restaurantes e negócios de delivery.")

ss = st.session_state
CAMPOS = ["faturamento_mensal", "pedidos_mes", "custo_insumos", "custo_pessoal",
          "aluguel_contas", "taxas_plataformas", "outros_custos", "caixa_disponivel"]
for c in CAMPOS:
    ss.setdefault(c, 0.0)
ss.setdefault("nome", "")
ss.setdefault("vendas", None)

with st.sidebar:
    st.caption("Quer só ver como funciona?")
    ex = pd.read_csv("data/negocios_exemplo.csv")
    escolha = st.selectbox("Negócio de exemplo", ex["nome"], index=None, placeholder="Escolha...")
    if st.button("Carregar exemplo", disabled=escolha is None):
        for k, v in ex[ex["nome"] == escolha].iloc[0].to_dict().items():
            ss[k] = float(v) if k != "nome" else v
        ss.vendas = None
        st.rerun()
    with open("data/vendas_exemplo.csv", "rb") as f:
        st.download_button("Baixar relatório de vendas de exemplo", f, "vendas_exemplo.csv")

st.text_input("Nome do negócio", key="nome")

# 1. Vendas
st.header("1 · Vendas")
st.write("Envie o relatório de vendas exportado do seu sistema ou app de delivery (CSV ou Excel). "
         "Basta ter uma coluna de **data** e uma de **valor**; a coluna de **canal** é opcional.")
arq = st.file_uploader("Relatório de vendas", type=["csv", "xlsx", "xls"])
comissao = st.slider("Comissão média dos apps de delivery (%)", 0, 35, 23)
if arq and st.button("Ler vendas"):
    try:
        v = resumo_vendas(ler_vendas(arq))
        ss.vendas = v
        ss.faturamento_mensal = v["faturamento_mensal"]
        ss.pedidos_mes = float(v["pedidos_mes"])
        app = sum(p for c, p in v["canais_pct"].items() if any(x in c.lower() for x in ("app", "ifood", "delivery", "rappi", "aiqfome")))
        if app:
            ss.taxas_plataformas = round(v["faturamento_mensal"] * app / 100 * comissao / 100, 2)
        st.rerun()
    except ValueError as e:
        st.error(str(e))

v = ss.vendas
if v:
    st.success(f"Vendas lidas. Mês de referência: **{v['mes_referencia']}** (último mês do arquivo).")
    g1, g2, g3 = st.columns(3)
    g1.write("**Faturamento por mês**"); g1.bar_chart(v["historico"])
    g2.write("**Vendas por dia da semana**"); g2.bar_chart(v["por_dia_semana"])
    g3.write("**Canais (% do faturamento)**"); g3.dataframe(v["canais_pct"].rename("%"))

# 2. Custos
st.header("2 · Números do mês")
a, b = st.columns(2)
a.number_input("Faturamento do mês (R$)", key="faturamento_mensal", step=100.0)
a.number_input("Número de pedidos", key="pedidos_mes", step=1.0)
a.number_input("Insumos e mercadorias (R$)", key="custo_insumos", step=100.0)
a.number_input("Taxas de apps de delivery (R$)", key="taxas_plataformas", step=100.0)
b.number_input("Pessoal: salários, encargos e pró-labore (R$)", key="custo_pessoal", step=100.0)
b.number_input("Aluguel, energia, água e gás (R$)", key="aluguel_contas", step=100.0)
b.number_input("Outros custos (R$)", key="outros_custos", step=100.0)
b.number_input("Dinheiro em caixa hoje (R$)", key="caixa_disponivel", step=100.0)

# Resultado
st.header("Diagnóstico")
if ss.faturamento_mensal <= 0 or ss.pedidos_mes <= 0:
    st.info("Envie as vendas ou preencha faturamento e pedidos para ver o diagnóstico.")
    st.stop()

d = {c: ss[c] for c in CAMPOS} | {"nome": ss.nome or "Seu negócio"}
r = diagnosticar(d)
cor = {"Saudável": "🟢", "Atenção": "🟡", "Crítico": "🔴"}[r["status"]]

k = st.columns(5)
k[0].metric("Saúde", f"{cor} {r['status']}", f"{r['nota_saude']}/100", delta_color="off")
k[1].metric("Lucro mensal", f"R$ {r['lucro_mensal']:,.0f}")
k[2].metric("Margem líquida", f"{r['margem_liquida_pct']}%")
k[3].metric("Ticket médio", f"R$ {r['ticket_medio']:,.2f}")
k[4].metric("Caixa", f"{r['meses_de_caixa']} meses")

c1, c2 = st.columns([3, 2])
with c1:
    st.subheader("Para onde vai cada R$ 100 faturados")
    st.bar_chart(pd.Series(r["estrutura_custos_pct"]))
with c2:
    st.subheader("Ponto de equilíbrio")
    st.write(f"Precisa faturar **R$ {r['ponto_equilibrio']:,.0f}/mês** para não ter prejuízo.")
    st.write(f"Hoje está **{r['folga_sobre_equilibrio_pct']}%** {'acima' if r['folga_sobre_equilibrio_pct'] >= 0 else 'abaixo'} do equilíbrio.")
    st.subheader("Alertas")
    for t, txt in r["alertas"] or [("Tudo certo", "Nenhum alerta.")]:
        st.warning(f"**{t}:** {txt}")

st.divider()
st.markdown(plano_de_acao(r, d, v))
