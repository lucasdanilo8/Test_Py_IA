# main.py

from langgraph.graph import StateGraph, END
import os
import warnings
from dotenv import load_dotenv
from groq import Groq

from state import AgentState
from nodes import llm_node
from executor import action_node, should_continue
from tools import search_docs, clean_code
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import DirectoryLoader

# --- SUPRIMIR WARNINGS DO TRANSFORMERS ---
warnings.filterwarnings("ignore", category=UserWarning, module="transformers")

# --- CARREGA VARIÁVEIS DE AMBIENTE ---
load_dotenv()

# --- setup LLM ---
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("⚠️ Variável de ambiente GROQ_API_KEY não configurada.")

client = Groq(api_key=api_key)


# --- RAG ---
loader = DirectoryLoader("docs/", glob="**/*.txt")
docs = loader.load()

embeddings = HuggingFaceEmbeddings()
vectorstore = FAISS.from_documents(docs, embeddings)

# Configura retriever com k baseado no número de documentos
num_docs = len(docs)
k_value = min(5, num_docs)
retriever = vectorstore.as_retriever(search_kwargs={"k": k_value})


# --- função gerar testes ---
def generate_tests(client, code, context):
    prompt = f"""
VOCÊ É UM ESPECIALISTA EM TESTES PYTEST.

TAREFA: Gere TESTES UNITÁRIOS (funções test_*) para o código abaixo.

CONTEXTO (melhores práticas):
{context}

CÓDIGO A TESTAR:
```python
{code}
```

REQUISITOS OBRIGATÓRIOS:
1. INCLUA o código a ser testado NO PRÓPRIO ARQUIVO (não use imports como 'from your_module import')
2. Defina a função fornecida PRIMEIRO
3. Defina as funções de teste (def test_*():) DEPOIS
4. Use pytest assertions (assert expressão)
5. Inclua testes para casos normais E casos edge (valores negativos, zero, None, etc)
6. SEM prints, input ou output externo
7. CÓDIGO EXECUTÁVEL DIRETAMENTE (sem dependências externas)
8. RETORNE APENAS CÓDIGO PYTHON - SEM EXPLICAÇÕES NEM COMENTÁRIOS

ESTRUTURA OBRIGATÓRIA:
```python
import pytest

# CÓDIGO A TESTAR (COPIAR DE VERDADE)
def sua_funcao():
    ...

# TESTES
def test_caso1():
    assert ...
```

RETORNE APENAS O CÓDIGO COMPLETO - INCLUA O CÓDIGO E OS TESTES:
"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2048
    )
    return clean_code(response.choices[0].message.content)


# --- criar grafo ---
builder = StateGraph(AgentState)

builder.add_node("llm", lambda s: llm_node(s, client))
builder.add_node("action", lambda s: action_node(s, client, retriever, generate_tests))


builder.set_entry_point("llm")

builder.add_edge("llm", "action")

builder.add_conditional_edges(
    "action",
    should_continue,
    {
        "continue": "llm",
        "end": END
    }
)

graph = builder.compile()


# --- rodar ---
if __name__ == "__main__":

    initial_state = {
        "code": """
def soma(a, b):
    return a + b
""",
        "context": "",
        "tests": "",
        "last_output": "",
        "step": 0,
        "done": False
    }

    result = graph.invoke(initial_state)

    print("\n=== RESULTADO FINAL ===\n")
    print(result["tests"])