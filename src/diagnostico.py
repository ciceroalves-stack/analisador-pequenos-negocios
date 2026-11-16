"""Diagnóstico financeiro de pequenos negócios (foco em restaurantes/delivery)."""

def n(x, c=1):
    """Número no formato brasileiro: 1.234,5"""
    return f"{x:,.{c}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def brl(x, c=0):
    return "R$ " + n(x, c)



def diagnosticar(d: dict) -> dict:
    fat = d["faturamento_mensal"]
    pedidos = d["pedidos_mes"]
    ticket = fat / pedidos if pedidos else 0

    cmv = d["custo_insumos"] / fat * 100
    pessoal = d["custo_pessoal"] / fat * 100
    ocupacao = d["aluguel_contas"] / fat * 100
    taxas = d["taxas_plataformas"] / fat * 100
    custos = d["custo_insumos"] + d["custo_pessoal"] + d["aluguel_contas"] + d["taxas_plataformas"] + d["outros_custos"]
    lucro = fat - custos
    margem = lucro / fat * 100

    fixos = d["custo_pessoal"] + d["aluguel_contas"] + d["outros_custos"]
    margem_contrib = 1 - (d["custo_insumos"] + d["taxas_plataformas"]) / fat
    equilibrio = fixos / margem_contrib if margem_contrib > 0 else float("inf")
    caixa_meses = d["caixa_disponivel"] / fixos if fixos else 99.0

    # referências de mercado para food service (aproximadas)
    alertas = []
    if cmv > 35: alertas.append(("CMV alto", f"Insumos consomem {cmv:.0f}% do faturamento (ideal: 28 a 35%)."))
    if pessoal > 30: alertas.append(("Folha pesada", f"Pessoal em {pessoal:.0f}% (ideal: até 30%)."))
    if ocupacao > 12: alertas.append(("Custo de ocupação", f"Aluguel e contas em {ocupacao:.0f}% (ideal: até 12%)."))
    if taxas > 20: alertas.append(("Dependência de plataformas", f"Taxas de apps em {taxas:.0f}% do faturamento."))
    if fixos and caixa_meses < 1: alertas.append(("Caixa curto", f"Reserva cobre só {n(caixa_meses)} mês de custos fixos."))
    if margem < 5: alertas.append(("Margem apertada", f"Margem líquida de {n(margem)}% (saudável: acima de 10%)."))

    nota = min(100, max(0, 100 - 15 * len(alertas) + min(margem, 20)))
    status = "Saudável" if nota >= 80 else "Atenção" if nota >= 55 else "Crítico"

    return {
        "negocio": d["nome"],
        "ticket_medio": round(ticket, 2),
        "lucro_mensal": round(lucro, 2),
        "margem_liquida_pct": round(margem, 1),
        "ponto_equilibrio": round(equilibrio, 2) if equilibrio != float("inf") else 0.0,
        "folga_sobre_equilibrio_pct": round((fat / equilibrio - 1) * 100, 1) if equilibrio not in (0, float("inf")) else (100.0 if equilibrio == 0 else -100.0),
        "meses_de_caixa": round(caixa_meses, 1),
        "estrutura_custos_pct": {
            "Insumos (CMV)": round(cmv, 1),
            "Pessoal": round(pessoal, 1),
            "Ocupação": round(ocupacao, 1),
            "Taxas de apps": round(taxas, 1),
            "Lucro": round(margem, 1),
        },
        "alertas": alertas,
        "nota_saude": round(nota),
        "status": status,
    }
