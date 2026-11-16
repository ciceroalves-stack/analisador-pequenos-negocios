"""Gera um plano de ação em linguagem simples para o dono do negócio."""
import json
import os

PROMPT = """Você é um consultor financeiro que atende pequenos restaurantes.
O dono não é da área financeira: use linguagem simples, sem jargão.
Com base no diagnóstico abaixo, escreva:
1. Como está o negócio em uma frase
2. Os 3 problemas mais importantes, em ordem de impacto
3. Um plano de ação para os próximos 30 dias (ações concretas e baratas)
4. Quanto o lucro pode melhorar se as ações derem certo (estimativa conservadora)
Use apenas os números fornecidos.

Diagnóstico:
{dados}
"""


def plano_de_acao(diag: dict) -> str:
    prompt = PROMPT.format(dados=json.dumps(diag, ensure_ascii=False, indent=2))
    if os.getenv("ANTHROPIC_API_KEY"):
        import anthropic
        m = anthropic.Anthropic().messages.create(
            model=os.getenv("LLM_MODEL", "claude-sonnet-4-5"), max_tokens=900,
            messages=[{"role": "user", "content": prompt}])
        return m.content[0].text
    if os.getenv("OPENAI_API_KEY"):
        from openai import OpenAI
        r = OpenAI().chat.completions.create(
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt}])
        return r.choices[0].message.content
    return _offline(diag)


DICAS = {
    "CMV alto": "Revise a ficha técnica dos 5 pratos mais vendidos e renegocie com 2 fornecedores.",
    "Folha pesada": "Ajuste a escala aos horários de pico usando o histórico de pedidos.",
    "Custo de ocupação": "Audite contas de energia e gás; avalie equipamentos mais eficientes.",
    "Dependência de plataformas": "Crie um canal próprio (WhatsApp/cardápio digital) com cupom para recompra.",
    "Caixa curto": "Separe um percentual fixo do faturamento semanal para reserva.",
    "Margem apertada": "Reprecifique itens com margem baixa e crie combos com itens de alta margem.",
}


def _offline(d: dict) -> str:
    linhas = [f"**Situação:** o negócio está em **{d['status']}** (nota {d['nota_saude']}/100), "
              f"com lucro de R$ {d['lucro_mensal']:,.2f} por mês.\n", "**Plano de 30 dias:**"]
    if not d["alertas"]:
        linhas.append("- Nenhum alerta crítico. Foque em aumentar o ticket médio com combos e sobremesas.")
    for titulo, texto in d["alertas"][:3]:
        linhas.append(f"- **{titulo}** — {texto} → {DICAS[titulo]}")
    linhas.append("\n_Plano gerado em modo demonstração (sem chave de API)._")
    return "\n".join(linhas)
