import pandas as pd
import streamlit as st

from src.diagnostico import diagnosticar
from src.ia import plano_de_acao

st.set_page_config(page_title="Analisador de Pequenos Negócios", page_icon="🏪", layout="wide")
st.title("🏪 Analisador de Pequenos Negócios")
st.caption("Diagnóstico financeiro em linguagem simples para restaurantes e negócios de delivery.")

df = pd.read_csv("data/negocios_exemplo.csv")
nome = st.sidebar.selectbox("Negócio de exemplo", df["nome"])
d = df[df["nome"] == nome].iloc[0].to_dict()

with st.sidebar.expander("✏️ Editar números do mês"):
    for campo, rotulo in [
        ("faturamento_mensal", "Faturamento (R$)"), ("pedidos_mes", "Pedidos no mês"),
        ("custo_insumos", "Insumos (R$)"), ("custo_pessoal", "Pessoal (R$)"),
        ("aluguel_contas", "Aluguel e contas (R$)"), ("taxas_plataformas", "Taxas de apps (R$)"),
        ("outros_custos", "Outros custos (R$)"), ("caixa_disponivel", "Caixa disponível (R$)"),
    ]:
        d[campo] = st.number_input(rotulo, value=float(d[campo]), step=100.0)

r = diagnosticar(d)
cor = {"Saudável": "🟢", "Atenção": "🟡", "Crítico": "🔴"}[r["status"]]

k = st.columns(5)
k[0].metric("Saúde", f"{cor} {r['status']}", f"{r['nota_saude']}/100")
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
    st.write(f"Folga atual: **{r['folga_sobre_equilibrio_pct']}%** acima do equilíbrio.")
    st.subheader("Alertas")
    for t, txt in r["alertas"] or [("Tudo certo", "Nenhum alerta.")]:
        st.warning(f"**{t}:** {txt}")

st.subheader("🧭 Plano de ação")
if st.button("Gerar plano com IA"):
    with st.spinner("Pensando no seu negócio..."):
        st.markdown(plano_de_acao(r))
