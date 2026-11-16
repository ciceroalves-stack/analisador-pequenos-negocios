# 🏪 Analisador de Pequenos Negócios

> O dono do restaurante informa os números do mês e recebe um **diagnóstico financeiro em linguagem simples** e um **plano de ação de 30 dias gerado por IA**.

## Problema de negócio

A maioria dos pequenos restaurantes não sabe responder perguntas básicas: *qual é minha margem? quanto preciso vender para não ter prejuízo? quanto as taxas dos apps pesam?* Muitos fecham por falta de gestão financeira, não por falta de clientes.

Para uma plataforma de delivery, a saúde financeira do parceiro é saúde do ecossistema: restaurante que quebra é oferta que some.

## Solução

| Etapa | O que faz |
|---|---|
| Entrada | 8 números que o dono já sabe (faturamento, pedidos, custos, caixa) |
| Diagnóstico | Ticket médio, margem, CMV, ponto de equilíbrio, meses de caixa |
| Alertas | Compara com referências de food service (ex.: CMV ideal de 28–35%) |
| Plano de ação | LLM escreve 3 prioridades e ações de 30 dias sem jargão |

**Decisão de produto:** pedir poucos dados. Um formulário com 40 campos ninguém preenche; com 8 o dono preenche no celular entre um pedido e outro.

## Possíveis evoluções

- Ler os números direto do extrato da plataforma de delivery
- Comparar com restaurantes da mesma categoria e região (benchmark)
- Enviar o diagnóstico mensal por WhatsApp

## Como rodar

```bash
pip install -r requirements.txt
streamlit run app.py
```

IA opcional: defina `OPENAI_API_KEY` ou `ANTHROPIC_API_KEY`. Sem chave, roda em modo demonstração.

> Dados fictícios. Referências de mercado são aproximadas e servem para fins de demonstração.
