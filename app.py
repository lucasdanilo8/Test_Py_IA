import streamlit as st
import subprocess
import os
import time
import warnings
from dotenv import load_dotenv
from groq import Groq

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from tools import clean_code

# --- SUPRIMIR WARNINGS DO TRANSFORMERS ---
warnings.filterwarnings("ignore", category=UserWarning, module="transformers")

# --- CARREGA VARIÁVEIS DE AMBIENTE ---
load_dotenv()

# --- CONFIGURAÇÃO DA API GROQ ---
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("⚠️ Variável de ambiente GROQ_API_KEY não configurada. Defina sua chave API antes de executar.")
    st.stop()

client = Groq(api_key=api_key)


# --- CONFIGURAÇÃO DO SISTEMA RAG (Retrieval-Augmented Generation) ---
# Carrega documentos da pasta docs/ para base de conhecimento
loader = DirectoryLoader("docs/", glob="**/*.txt")
documents = loader.load()

# Cria embeddings usando HuggingFace e armazena em FAISS
embeddings = HuggingFaceEmbeddings()
vectorstore = FAISS.from_documents(documents, embeddings)

# Configura retriever com k dinâmico baseado no número de documentos
num_docs = len(documents)
k_value = min(5, num_docs)  # Não busca mais do que existem
retriever = vectorstore.as_retriever(search_kwargs={"k": k_value})


# --- FUNÇÕES AUXILIARES ---

def search_docs(query, k=None, search_type="mmr", score_threshold=None, category=None):
    """Busca documentos relevantes no RAG usando similaridade semântica."""
    if k is None:
        k = min(5, len(documents))  # Ajusta automaticamente ao número de docs

    search_kwargs = {"k": k}
    if score_threshold:
        search_kwargs["score_threshold"] = score_threshold
    if category:
        search_kwargs["filter"] = {"category": category}

    retriever = vectorstore.as_retriever(
        search_type=search_type,  # "similarity", "mmr", ou "similarity_score_threshold"
        search_kwargs=search_kwargs
    )
    docs = retriever.invoke(query)
    return "\n".join([d.page_content for d in docs])


def search_docs_with_threshold(query, score_threshold=0.7, k=None):
    """Busca documentos relevantes filtrados por threshold de similaridade."""
    if k is None:
        k = len(documents)  # Retorna todos os documentos disponíveis

    search_kwargs = {"k": k, "score_threshold": score_threshold}

    retriever_temp = vectorstore.as_retriever(
        search_type="similarity_score_threshold",  # Filtra por score
        search_kwargs=search_kwargs
    )

    docs = retriever_temp.invoke(query)
    return "\n".join([d.page_content for d in docs])


def search_docs_with_strategy(query, strategy="Dinâmica (k automático)", k_value=None, score_threshold=0.7):
    """Busca documentos aplicando a estratégia escolhida pelo usuário."""
    if strategy == "Dinâmica (k automático)":
        # Ajusta k automaticamente
        k = min(5, len(documents)) if k_value is None else k_value
        return search_docs(query, k=k)
    
    elif strategy == "Threshold de Score":
        # Filtra por score de similaridade
        k = k_value if k_value else len(documents)
        return search_docs_with_threshold(query, score_threshold=score_threshold, k=k)
    
    elif strategy == "Todos os documentos":
        # Retorna todos disponíveis
        return search_docs(query, k=len(documents))
    
    else:
        # Padrão: dinâmica
        return search_docs(query, k=min(5, len(documents)))


def generate_tests(code, context):
    """Gera testes unitários usando Groq LLM com contexto do RAG."""
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
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048
        )
        return clean_code(response.choices[0].message.content)
    except Exception as e:
        st.error(f"⚠️ Erro ao chamar Groq: {str(e)}")
        st.stop()
        raise


def run_tests():
    """Executa os testes gerados usando pytest."""
    result = subprocess.run(
        ["pytest", "-q"],
        capture_output=True,
        text=True
    )
    return result.stdout + result.stderr


# --- UI ---

st.set_page_config(page_title="AI Test Agent", layout="wide")

st.title("🤖 Agente Gerador de Testes (ReAct + RAG)")

# --- STATUS DO RAG ---
st.subheader("📊 Status do Sistema RAG")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("📄 Documentos carregados", len(documents))

with col2:
    total_chars = sum(len(doc.page_content) for doc in documents)
    st.metric("📏 Caracteres totais", f"{total_chars:,}")

with col3:
    st.metric("🔍 Vectorstore", "FAISS ✅")

# --- EXEMPLO DE BUSCA ---
with st.expander("🔍 Exemplo de busca no RAG"):
    st.markdown("**Query:** 'pytest parametrize'")
    example_query = "pytest parametrize"
    example_results = search_docs(example_query)
    
    st.markdown("**Resultados recuperados:**")
    st.code(example_results[:500] + "..." if len(example_results) > 500 else example_results, language="markdown")

st.markdown("---")

# --- CONFIGURAÇÕES DO RAG ---
with st.expander("⚙️ Configurações Avançadas do RAG", expanded=False):
    st.markdown("### 🔍 Opções de Busca Semântica")
    
    col_strategy, col_k, col_threshold = st.columns(3)
    
    with col_strategy:
        search_strategy = st.selectbox(
            "Estratégia de busca",
            ["Dinâmica (k automático)", "Threshold de Score", "Todos os documentos"],
            help="Dinâmica: ajusta k ao número de docs | Threshold: filtra por relevância | Todos: retorna tudo"
        )
    
    with col_k:
        k_value = st.slider(
            "Máximo de documentos (k)",
            min_value=1,
            max_value=len(documents),
            value=min(5, len(documents)),
            help="Número máximo de documentos a retornar na busca"
        )
    
    with col_threshold:
        score_threshold = st.slider(
            "Threshold de Score",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.05,
            help="Similaridade mínima para incluir documento (0.0 a 1.0)"
        )
    
    st.session_state.search_strategy = search_strategy
    st.session_state.k_value = k_value
    st.session_state.score_threshold = score_threshold

st.markdown("---")

# --- ENTRADA DO USUÁRIO ---
st.header("📝 Gerar Testes para seu Código")

st.markdown("Cole o código Python que deseja testar abaixo. O agente irá analisar e gerar testes automaticamente.")

col_input, col_button = st.columns([4, 1])

with col_input:
    code = st.text_area("Código Python", height=300, placeholder="def soma(a, b):\n    return a + b")

with col_button:
    st.write("")  # Espaço
    generate_button = st.button("🚀 Gerar Testes", use_container_width=True)

if generate_button:

    if not code.strip():
        st.warning("⚠️ Insira um código primeiro.")
    else:
        # Mostrar configuração do RAG sendo usada
        strategy = getattr(st.session_state, 'search_strategy', 'Dinâmica (k automático)')
        k_val = getattr(st.session_state, 'k_value', min(5, len(documents)))
        threshold = getattr(st.session_state, 'score_threshold', 0.7)
        
        config_msg = f"🔍 Estratégia: **{strategy}** | 📊 k máximo: **{k_val}** | ⚖️ Threshold: **{threshold:.2f}**"
        st.info(config_msg)
        
        # Barra de progresso
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Step 1: Buscar contexto
        status_text.text("🔍 Buscando contexto relevante...")
        progress_bar.progress(25)
        
        context = search_docs_with_strategy(code, strategy=strategy, k_value=k_val, score_threshold=threshold)
        
        with st.expander("📚 Contexto encontrado", expanded=True):
            st.code(context[:1000] + "..." if len(context) > 1000 else context, language="markdown")

        # Step 2: Gerar testes
        status_text.text("🧠 Gerando testes com IA...")
        progress_bar.progress(50)
        
        tests = generate_tests(code, context)

        with st.expander("🧪 Testes gerados", expanded=True):
            st.code(tests, language="python")

        # Salvar testes
        with open("test_generated.py", "w", encoding="utf-8") as f:
            f.write(tests)

        # Step 3: Executar testes
        status_text.text("⚙️ Executando testes...")
        progress_bar.progress(75)
        result = run_tests()

        with st.expander("📊 Resultados da execução", expanded=True):
            st.code(result, language="text")

        # Step 4: Correção automática se necessário
        if "failed" in result.lower() or "error" in result.lower():
            status_text.text("🔧 Corrigindo testes automaticamente...")
            progress_bar.progress(90)
            
            fix_prompt = f"""
VOCÊ É UM ESPECIALISTA EM TESTES PYTEST.

OS TESTES FALHARAM COM ESTE ERRO:
{result}

CÓDIGO ORIGINAL:
```python
{code}
```

TAREFA: Gere NOVOS TESTES que funcionem com este código. Inclua o código e os testes.

REQUISITOS:
1. INCLUA o código a ser testado NO ARQUIVO
2. Defina a função PRIMEIRO
3. Defina testes (def test_*():) DEPOIS
4. Use pytest assertions
5. SEM imports de módulos inexistentes
6. CÓDIGO EXECUTÁVEL DIRETAMENTE (sem dependências)
7. SEM explicações ou markdown
8. Corrija os problemas que causaram falhas

ESTRUTURA OBRIGATÓRIA:
```python
import pytest

# CÓDIGO A TESTAR
def sua_funcao():
    ...

# TESTES CORRIGIDOS
def test_caso1():
    assert ...
```

RETORNE APENAS O CÓDIGO COMPLETO - INCLUA CÓDIGO + TESTES CORRIGIDOS:
"""
            fixed_response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": fix_prompt}],
                max_tokens=2048
            )
            fixed_tests = clean_code(fixed_response.choices[0].message.content)

            with open("test_generated.py", "w", encoding="utf-8") as f:
                f.write(fixed_tests)

            with st.expander("🔄 Testes corrigidos", expanded=True):
                st.code(fixed_tests, language="python")

            status_text.text("🔁 Reexecutando testes...")
            result = run_tests()
            progress_bar.progress(100)

            with st.expander("📈 Resultados finais", expanded=True):
                st.code(result, language="text")
        else:
            progress_bar.progress(100)
            status_text.text("✅ Testes executados com sucesso!")

        # Limpar barra e status
        progress_bar.empty()
        status_text.empty()


st.markdown("---")
st.caption("🚀 Projeto Acadêmico: Agente ReAct com RAG para Geração Inteligente de Testes Unitários")
st.markdown("**Desenvolvido com:** Streamlit, LangChain, FAISS, Groq AI")