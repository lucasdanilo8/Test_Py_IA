# executor.py

from tools import search_docs, run_tests, clean_code


def action_node(state, client, retriever, generate_tests_fn):

    action = state["action"]

    if "SEARCH_DOCS" in action:
        context = search_docs(retriever, state["code"])
        return {**state, "context": context, "last_output": context}

    elif "GENERATE_TESTS" in action:
        tests = generate_tests_fn(client, state["code"], state.get("context", ""))
        
        with open("test_generated.py", "w", encoding="utf-8") as f:
            f.write(tests)

        return {**state, "tests": tests, "last_output": tests}

    elif "RUN_TESTS" in action:
        result = run_tests()
        return {**state, "last_output": result}

    elif "FIX_TESTS" in action:
        fix_prompt = f"""
VOCÊ É UM ESPECIALISTA EM TESTES PYTEST.

OS TESTES FALHARAM COM ESTE ERRO:
{state['last_output']}

CÓDIGO A TESTAR:
{state['code']}

TAREFA: Gere NOVOS TESTES que funcionem com este código. Inclua o código e os testes.

REQUISITOS:
1. INCLUA o código a ser testado NO ARQUIVO (não use imports)
2. Defina a função PRIMEIRO
3. Defina testes (def test_*():) DEPOIS
4. Use pytest assertions
5. Corrija os problemas que causaram as falhas
6. SEM imports de módulos inexistentes
7. CÓDIGO EXECUTÁVEL DIRETAMENTE
8. RETORNE APENAS CÓDIGO - SEM EXPLICAÇÕES

ESTRUTURA:
```python
import pytest

# CÓDIGO A TESTAR
def sua_funcao():
    ...

# TESTES CORRIGIDOS
def test_caso():
    assert ...
```

RETORNE APENAS O CÓDIGO COMPLETO - INCLUA CÓDIGO + TESTES:
"""
        fix_response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": fix_prompt}],
            max_tokens=2048
        )
        tests = clean_code(fix_response.choices[0].message.content)

        with open("test_generated.py", "w", encoding="utf-8") as f:
            f.write(tests)

        return {**state, "tests": tests, "last_output": tests}

    elif "FINISH" in action:
        return {**state, "done": True}

    return state


def should_continue(state):
    if state.get("done"):
        return "end"

    if state["step"] > 5:
        return "end"

    return "continue"
