import pandas as pd
import streamlit as st

from src.diagnostico import diagnosticar
from src.plano import plano_de_acao
from src.ui import aplicar, barras, cabecalho, passo, selo
from src.vendas import ler_vendas, resumo_vendas

st.set_page_config(page_title="Analisador de Pequenos Negócios", page_icon="🏪", layout="wide")
aplicar("#ea1d2c", "#f97316")
cabecalho("🏪", "Analisador de Pequenos Negócios",
          "Envie suas vendas, informe os custos do mês e receba um diagnóstico financeiro em linguagem simples.")

ss = st.session_state
CAMPOS = ["faturamento_mensal", "pedidos_mes", "custo_insumos", "custo_pessoal",
          "aluguel_contas", "taxas_plataformas", "outros_custos", "caixa_disponivel"]
for c in CAMPOS:
    ss.setdefault(c, 0.0)
ss.setdefault("nome", "")
ss.setdefault("vendas", None)
ss.setdefault("erro", None)


def brl(v, casas=0):
    s = f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


with st.sidebar:
    st.markdown("### 🧪 Conhecer a ferramenta")
    ex = pd.read_csv("data/negocios_exemplo.csv")
    escolha = st.selectbox("Negócio de demonstração", ex["nome"], index=None, placeholder="Escolha...")
    if st.button("Carregar demonstração", disabled=escolha is None, width="stretch"):
        for k, v in ex[ex["nome"] == escolha].iloc[0].to_dict().items():
            ss[k] = float(v) if k != "nome" else v
        ss.vendas = None
        st.rerun()
    with open("data/vendas_exemplo.csv", "rb") as f:
        st.download_button("Baixar relatório de vendas de teste", f, "vendas_exemplo.csv", width="stretch")
    st.divider()
    st.markdown("### ⚙️ Parâmetros")
    comissao = st.slider("Comissão média dos apps de delivery (%)", 0, 35, 23)

st.text_input("Nome do negócio", key="nome", placeholder="Ex.: Hamburgueria do Bairro")

# 1 · Vendas
passo(1, "Vendas", "relatório exportado do PDV ou do app de delivery")
u1, u2 = st.columns([3, 1], vertical_alignment="bottom")
arq = u1.file_uploader("CSV ou Excel com uma coluna de **data** e uma de **valor** (a de **canal** é opcional)",
                       type=["csv", "xlsx", "xls"])
if u2.button("📊 Ler vendas", type="primary", disabled=arq is None, width="stretch"):
    try:
        v = resumo_vendas(ler_vendas(arq))
        ss.vendas = v
        ss.faturamento_mensal = v["faturamento_mensal"]
        ss.pedidos_mes = float(v["pedidos_mes"])
        app = sum(p for c, p in v["canais_pct"].items()
                  if any(x in c.lower() for x in ("app", "ifood", "delivery", "rappi", "aiqfome", "99food", "keeta")))
        if app:
            ss.taxas_plataformas = round(v["faturamento_mensal"] * app / 100 * comissao / 100, 2)
    except Exception as e:
        ss.erro = str(e)
    st.rerun()
if ss.erro:
    st.error(ss.erro)
    ss.erro = None

v = ss.vendas
if v:
    var = v["variacao_mes_anterior_pct"]
    m = st.columns(4)
    m[0].metric(f"Faturamento · {v['mes_referencia']}", brl(v["faturamento_mensal"]),
                f"{var:+.1f}% vs mês anterior" if var is not None else None)
    m[1].metric("Pedidos no mês", f"{v['pedidos_mes']:,}".replace(",", "."))
    m[2].metric("Melhor dia", v["melhor_dia"])
    m[3].metric("Dia mais fraco", v["pior_dia"])
    g1, g2, g3 = st.columns(3)
    with g1:
        st.markdown("##### Faturamento por mês")
        barras(v["historico"], "#ea1d2c", altura=220)
    with g2:
        st.markdown("##### Vendas por dia da semana")
        barras(v["por_dia_semana"].rename(index=lambda x: x[:3]), "#f97316", altura=220)
    with g3:
        st.markdown("##### Canais de venda")
        st.dataframe(v["canais_pct"].rename("pct").reset_index().rename(columns={"canal": "Canal"}),
                     hide_index=True, width="stretch",
                     column_config={"pct": st.column_config.ProgressColumn("% do faturamento", format="%.1f%%",
                                                                           min_value=0, max_value=100)})

# 2 · Custos
passo(2, "Números do mês", "valores em R$")
a, b = st.columns(2)
a.number_input("Faturamento do mês", key="faturamento_mensal", step=100.0, min_value=0.0)
a.number_input("Número de pedidos", key="pedidos_mes", step=1.0, min_value=0.0)
a.number_input("Insumos e mercadorias", key="custo_insumos", step=100.0, min_value=0.0)
a.number_input("Taxas de apps de delivery", key="taxas_plataformas", step=100.0, min_value=0.0,
               help="Preenchido automaticamente a partir das vendas por app e da comissão definida na barra lateral.")
b.number_input("Pessoal: salários, encargos e pró-labore", key="custo_pessoal", step=100.0, min_value=0.0)
b.number_input("Aluguel, energia, água e gás", key="aluguel_contas", step=100.0, min_value=0.0)
b.number_input("Outros custos", key="outros_custos", step=100.0, min_value=0.0)
b.number_input("Dinheiro em caixa hoje", key="caixa_disponivel", step=100.0, min_value=0.0)

# Resultado
passo("✓", "Diagnóstico")
if ss.faturamento_mensal <= 0 or ss.pedidos_mes <= 0:
    st.info("Envie o relatório de vendas ou preencha **faturamento** e **pedidos** para ver o diagnóstico.")
    st.stop()
if ss.custo_insumos + ss.custo_pessoal + ss.aluguel_contas + ss.outros_custos <= 0:
    st.info("Agora preencha os **custos do mês** (insumos, pessoal, aluguel e contas) para ver o diagnóstico.")
    st.stop()

d = {c: ss[c] for c in CAMPOS} | {"nome": ss.nome or "Seu negócio"}
r = diagnosticar(d)
tipo = {"Saudável": "ok", "Atenção": "at", "Crítico": "ru"}[r["status"]]
st.markdown(f'<div class="cartao" style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">'
            f'<div><span style="color:#6b7280">Saúde financeira de {d["nome"]}</span><br>'
            f'<span style="font-size:1.4rem;font-weight:800">Nota {r["nota_saude"]}/100</span></div>'
            f'{selo(r["status"], tipo)}</div>', unsafe_allow_html=True)

k = st.columns(4)
k[0].metric("Lucro do mês", brl(r["lucro_mensal"]))
k[1].metric("Margem líquida", f"{r['margem_liquida_pct']:.1f}%".replace(".", ","))
k[2].metric("Ticket médio", brl(r["ticket_medio"], 2))
k[3].metric("Caixa cobre", "12+ meses" if r["meses_de_caixa"] >= 12 else f"{r['meses_de_caixa']:.1f} meses".replace(".", ","))

c1, c2 = st.columns([3, 2])
with c1:
    st.markdown("##### Para onde vai cada R$ 100 faturados")
    barras(pd.Series(r["estrutura_custos_pct"]), "#ea1d2c", horizontal=True, altura=230, fmt=".1f")
with c2:
    st.markdown("##### Ponto de equilíbrio")
    folga = r["folga_sobre_equilibrio_pct"]
    if r["ponto_equilibrio"] == 0 and folga < 0:
        st.error("Os custos variáveis (insumos + taxas) já são maiores que o faturamento: "
                 "cada venda dá prejuízo. Revise preços antes de tudo.")
    elif r["ponto_equilibrio"] == 0:
        st.markdown("Sem custos fixos informados: qualquer venda já cobre os custos.")
    else:
        st.markdown(f"Precisa faturar **{brl(r['ponto_equilibrio'])}/mês** para não ter prejuízo. "
                    f"Hoje está **{str(round(abs(folga), 1)).replace('.', ',')}% {'acima' if folga >= 0 else 'abaixo'}** desse valor.")
    st.markdown("##### Alertas")
    if not r["alertas"]:
        st.success("Nenhum alerta. Os custos estão dentro das referências do setor.")
    for t, txt in r["alertas"]:
        st.warning(f"**{t}:** {txt}")

with st.container(border=True):
    st.markdown(plano_de_acao(r, d, v))
