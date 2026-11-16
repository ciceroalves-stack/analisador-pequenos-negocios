"""Lê o relatório de vendas exportado do PDV ou da plataforma de delivery (CSV ou Excel)
e calcula faturamento, pedidos, ticket médio, canais e tendência."""
import pandas as pd

from .numeros import coluna_numerica

ALIASES = {
    "data": ["data", "data do pedido", "data_pedido", "dia", "date", "criado em", "data/hora"],
    "valor": ["valor", "valor total", "total", "valor_total", "valor do pedido", "faturamento", "preço", "preco"],
    "canal": ["canal", "origem", "plataforma", "app", "tipo", "forma de venda"],
}
DIAS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]


def _achar(colunas, opcoes):
    norm = {c.strip().lower(): c for c in colunas}
    for o in opcoes:
        if o in norm:
            return norm[o]
    for c_low, c in norm.items():
        if any(o in c_low for o in opcoes):
            return c
    return None


def _valor(s: pd.Series) -> pd.Series:
    return coluna_numerica(s)


def _datas(s: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(s):
        return s
    txt = s.astype(str).str.strip()
    iso = txt.str.match(r"^\d{4}-\d{2}-\d{2}")
    out = pd.Series(pd.NaT, index=s.index, dtype="datetime64[ns]")
    if iso.any():
        out[iso] = pd.to_datetime(txt[iso].str[:19], errors="coerce", format="mixed")
    if (~iso).any():
        out[~iso] = pd.to_datetime(txt[~iso], errors="coerce", dayfirst=True, format="mixed")
    return out


def ler_vendas(arquivo) -> pd.DataFrame:
    nome = getattr(arquivo, "name", str(arquivo)).lower()
    if nome.endswith((".xlsx", ".xls")):
        bruto = pd.read_excel(arquivo, dtype=str)
    else:
        bruto = pd.read_csv(arquivo, sep=None, engine="python", encoding_errors="ignore", dtype=str)

    c_data, c_valor = _achar(bruto.columns, ALIASES["data"]), _achar(bruto.columns, ALIASES["valor"])
    if not c_data or not c_valor:
        raise ValueError(f"Não encontrei as colunas de data e valor. Colunas do arquivo: {list(bruto.columns)}")
    c_canal = _achar(bruto.columns, ALIASES["canal"])

    df = pd.DataFrame({
        "data": _datas(bruto[c_data]),
        "valor": _valor(bruto[c_valor]),
        "canal": bruto[c_canal].astype(str) if c_canal else "Não informado",
    }).dropna(subset=["data", "valor"])
    if df.empty:
        raise ValueError("O arquivo não tem linhas válidas de data e valor.")
    return df


def resumo_vendas(df: pd.DataFrame) -> dict:
    df = df.assign(mes=df["data"].dt.to_period("M"))
    mensal = df.groupby("mes").agg(faturamento=("valor", "sum"), pedidos=("valor", "size"))
    ultimo = mensal.iloc[-1]
    variacao = None
    if len(mensal) > 1:
        ant = mensal.iloc[-2]["faturamento"]
        variacao = round((ultimo["faturamento"] / ant - 1) * 100, 1) if ant else None

    por_dia = df.groupby(df["data"].dt.dayofweek)["valor"].sum().reindex(range(7), fill_value=0)
    por_dia.index = DIAS
    canais = (df.groupby("canal")["valor"].sum() / df["valor"].sum() * 100).round(1).sort_values(ascending=False)

    return {
        "mes_referencia": str(mensal.index[-1]),
        "faturamento_mensal": float(ultimo["faturamento"]),
        "pedidos_mes": int(ultimo["pedidos"]),
        "variacao_mes_anterior_pct": variacao,
        "historico": mensal.assign(mes=mensal.index.astype(str)).set_index("mes")["faturamento"],
        "por_dia_semana": por_dia,
        "canais_pct": canais,
        "melhor_dia": por_dia.idxmax(),
        "pior_dia": por_dia.idxmin(),
    }
