"""Monta o plano de ação de 30 dias a partir do diagnóstico, sem depender de API externa."""

ACOES = {
    "CMV alto": ("Revise a ficha técnica dos 5 pratos mais vendidos e renegocie com 2 fornecedores.", "custo_insumos", 0.05),
    "Folha pesada": ("Ajuste a escala da equipe aos horários e dias de pico.", "custo_pessoal", 0.05),
    "Custo de ocupação": ("Audite contas de energia e gás; desligue equipamentos fora do horário.", "aluguel_contas", 0.08),
    "Dependência de plataformas": ("Crie um canal próprio (WhatsApp/cardápio digital) com cupom de recompra.", "taxas_plataformas", 0.10),
    "Caixa curto": ("Separe 5% do faturamento semanal numa conta de reserva.", None, 0),
    "Margem apertada": ("Reprecifique itens com margem baixa e crie combos com itens de alta margem.", None, 0),
}


def plano_de_acao(diag: dict, dados: dict, vendas: dict | None = None) -> str:
    t = [f"### Plano de ação — {diag['negocio']}",
         f"**Como está:** {diag['status']} (nota {diag['nota_saude']}/100). "
         f"Lucro de **R$ {diag['lucro_mensal']:,.2f}** no mês, margem de {diag['margem_liquida_pct']}%."]
    if diag["folga_sobre_equilibrio_pct"] < 0:
        t.append(f"⚠️ O faturamento está **abaixo do ponto de equilíbrio** (R$ {diag['ponto_equilibrio']:,.0f}).")

    ganho_total = 0.0
    t.append("\n**Prioridades para os próximos 30 dias**")
    if not diag["alertas"]:
        t.append("- Nenhum alerta crítico. Foque em aumentar o ticket médio com combos e sobremesas.")
    for i, (titulo, texto) in enumerate(diag["alertas"][:3], 1):
        acao, campo, corte = ACOES[titulo]
        ganho = dados[campo] * corte if campo else 0
        ganho_total += ganho
        extra = f" Economia estimada: **R$ {ganho:,.0f}/mês**." if ganho else ""
        t.append(f"{i}. **{titulo}** — {texto} {acao}{extra}")

    if vendas:
        t.append("\n**O que as suas vendas mostram**")
        t.append(f"- Seu dia mais forte é **{vendas['melhor_dia']}** e o mais fraco é **{vendas['pior_dia']}**: "
                 f"faça uma promoção ou um combo exclusivo na {vendas['pior_dia'].lower()}.")
        if vendas["variacao_mes_anterior_pct"] is not None:
            sentido = "subiu" if vendas["variacao_mes_anterior_pct"] >= 0 else "caiu"
            t.append(f"- O faturamento {sentido} {abs(vendas['variacao_mes_anterior_pct'])}% em relação ao mês anterior.")
        topo = vendas["canais_pct"]
        if len(topo) > 1:
            t.append(f"- {topo.index[0]} responde por {topo.iloc[0]}% das vendas.")

    if ganho_total:
        t.append(f"\n**Potencial:** se as ações derem certo, o lucro pode melhorar cerca de **R$ {ganho_total:,.0f} por mês** (estimativa conservadora).")
    return "\n".join(t)
