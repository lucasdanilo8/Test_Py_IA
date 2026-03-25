# nodes.py

def llm_node(state, client):

    prompt = f"""
Você é um agente ReAct.

Estado atual:
- step: {state['step']}
- código: {state['code']}
- contexto: {state.get('context', '')}
- saída anterior: {state.get('last_output', '')}

Decida a próxima ação:

Opções:
1. SEARCH_DOCS
2. GENERATE_TESTS
3. RUN_TESTS
4. FIX_TESTS
5. FINISH

Responda no formato:
ACTION: <ação>
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=512
    ).choices[0].message.content.strip()

    return {
        **state,
        "action": response
    }