# 🤖 AI Test Agent - Gerador de Testes com RAG

Um agente inteligente que gera testes unitários automaticamente usando **Retrieval-Augmented Generation (RAG)** e arquitetura **ReAct**, combinando busca semântica em base de conhecimento com geração de código via LLM.

## 🎯 Funcionalidades Principais

### ✨ Geração Inteligente de Testes
- **Análise automática** de código Python
- **Geração contextual** usando melhores práticas de testes
- **Suporte completo ao pytest** com parametrização, fixtures e asserts

### 🧠 Arquitetura ReAct (Reasoning + Acting)
- **Pensamento estruturado**: Análise → Busca → Geração → Execução
- **Observação inteligente**: Correção automática de testes que falham
- **Loop de melhoria**: Iteração até sucesso

### 📚 Sistema RAG Avançado
- **Base de conhecimento expansível** em `docs/`
- **Busca semântica** usando embeddings FAISS
- **Contexto relevante** para geração de testes

### 🎨 Interface Web Interativa
- **Dashboard em tempo real** com métricas do RAG
- **Visualização de prompts** enviados ao LLM
- **Execução passo-a-passo** com feedback visual

## 🏗️ Arquitetura do Sistema

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Interface     │    │   Agente ReAct  │    │   Sistema RAG   │
│   Streamlit     │◄──►│   (Thought →    │◄──►│   FAISS +       │
│                 │    │    Action)      │    │   Embeddings    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Código        │    │   Testes        │    │   Base de       │
│   Python        │    │   Gerados       │    │   Conhecimento  │
│   (Input)       │    │   (Output)      │    │   (docs/)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📁 Estrutura do Projeto

```
Test_Py_IA/
├── 📄 app.py              # Interface principal Streamlit
├── 📄 main.py             # Arquitetura ReAct com LangGraph
├── 📄 tools.py            # Funções utilitárias (limpeza, busca)
├── 📄 nodes.py            # Nós do grafo (LLM, decisão)
├── 📄 executor.py         # Executor de ações
├── 📄 state.py            # Definições de estado
├── 📄 requirements.txt    # Dependências Python
├── 📄 .env               # Variáveis de ambiente (API keys)
├── 📁 docs/              # Base de conhecimento RAG
│   ├── testing_best_practices.txt
│   ├── pytest_guide.txt
│   ├── test_patterns.txt
│   └── python_guidelines.txt
└── 📄 README.md          # Esta documentação
```

## 🚀 Como Usar

### 1. Pré-requisitos
```bash
# Python 3.8+
python --version

# Instalar dependências
pip install -r requirements.txt
```

### 2. Configurar API Key
```bash
# Obter chave gratuita em https://console.groq.com
# Criar arquivo .env
echo "GROQ_API_KEY=sua_chave_aqui" > .env
```

### 3. Executar o Sistema
```bash
# Iniciar interface web
streamlit run app.py

# Acessar: http://localhost:8503
```

### 4. Gerar Testes
1. **Cole código Python** na área de texto
2. **Clique "🚀 Gerar testes"**
3. **Veja o processo**: busca RAG → geração → execução → correção
4. **Testes gerados** aparecem automaticamente

## ⚙️ Configurações Avançadas

### 📚 Configuração do Sistema RAG

O sistema RAG utiliza uma base de conhecimento localizada na pasta `docs/` para fornecer contexto relevante durante a geração de testes:

- **Arquivos suportados**: Apenas arquivos `.txt` são carregados
- **Embeddings**: Utiliza `HuggingFaceEmbeddings` para converter texto em vetores semânticos
- **Banco vetorial**: FAISS armazena os embeddings para buscas rápidas
- **Busca semântica**: Retorna os 5 documentos mais relevantes por similaridade

**Para expandir a base de conhecimento:**
1. Adicione arquivos `.txt` na pasta `docs/`
2. Reinicie a aplicação para recarregar os documentos
3. Exemplos de conteúdo útil:
   - Padrões de teste específicos do domínio
   - Melhores práticas de código
   - Casos de uso comuns

### � Opções de Busca RAG

O sistema oferece **3 estratégias de busca** otimizadas para bases pequenas (4 arquivos):

#### 1. **Busca Dinâmica (Padrão)**
- Ajusta `k` automaticamente ao número de documentos disponíveis
- Nunca busca mais do que existe (evita erros)
- Ideal para bases pequenas/médias

#### 2. **Filtragem por Threshold de Score**
- Retorna apenas documentos com similaridade > 0.7
- Qualidade sobre quantidade
- Função: `search_docs_with_threshold(query, score_threshold=0.7)`
- Útil quando nem todos os documentos são relevantes

**Como usar:**
```python
# Exemplo de uso da função
from app import search_docs_with_threshold

# Busca com threshold padrão (0.7)
contexto = search_docs_with_threshold("função de soma")

# Busca com threshold personalizado (mais rigoroso)
contexto = search_docs_with_threshold("teste unitário", score_threshold=0.8)

# Busca com threshold relaxado (mais documentos)
contexto = search_docs_with_threshold("algoritmo", score_threshold=0.5)
```

**Thresholds recomendados:**
- **0.9**: Muito rigoroso (poucos docs, alta relevância)
- **0.7**: Balanceado (padrão recomendado)
- **0.5**: Relaxado (mais docs, pode incluir irrelevantes)

#### 3. **Busca Completa**
- Retorna todos os documentos disponíveis
- Máximo contexto possível
- Melhor para bases muito pequenas
### 🤖 Integração com o Agente ReAct

As estratégias de busca podem ser **combinadas** no fluxo do agente:

1. **Primeira tentativa**: Busca dinâmica (k automático)
2. **Se contexto insuficiente**: Busca completa (todos os docs)
3. **Se muitos irrelevantes**: Busca com threshold (filtrada)

**Exemplo de uso avançado:**
```python
# No executor.py, pode-se modificar para usar diferentes estratégias
def action_node(state, client, retriever, generate_tests_fn):
    if "SEARCH_DOCS" in action:
        # Estratégia 1: Busca dinâmica
        context = search_docs(state["code"])
        
        # Se contexto vazio, tenta estratégia 2
        if not context.strip():
            context = search_docs_with_threshold(state["code"], score_threshold=0.5)
```
### �🔄 Quantidade de Retentativas de Geração

O agente tem um **limite máximo de 5 tentativas** para gerar testes válidos:

- **Tentativa 1**: Geração inicial baseada no código e contexto RAG
- **Tentativas 2-4**: Correção automática se os testes falharem na execução
- **Tentativa 5**: Última chance de correção
- **Limite atingido**: Processo para se testes não passarem após 5 iterações

**Fluxo de decisão do agente:**
1. `SEARCH_DOCS` → Busca contexto relevante
2. `GENERATE_TESTS` → Gera testes iniciais
3. `RUN_TESTS` → Executa e verifica se passam
4. `FIX_TESTS` → Corrige se houver falhas (até 5x)
5. `FINISH` → Encerra quando testes passam ou limite atingido

### 🔧 Personalização Avançada

#### Modificando o Threshold Padrão
```python
# Em app.py, alterar o valor padrão
def search_docs_with_threshold(query, score_threshold=0.8):  # Mais rigoroso
    # ...
```

#### Adicionando Novos Arquivos à Base RAG
```bash
# Adicionar arquivo de melhores práticas específicas
echo "Para testar funções matemáticas, sempre incluir casos edge como 0, números negativos e floats" > docs/math_testing_guide.txt
```

#### Monitorando Performance da RAG
- Verifique quantos documentos são retornados por busca
- Ajuste threshold se muitos/few documentos são retornados
- Monitore qualidade dos testes gerados

## 📊 Exemplo de Uso

### Código de Entrada:
```python
def calcular_desconto(preco, percentual):
    if percentual < 0 or percentual > 100:
        raise ValueError("Percentual deve estar entre 0 e 100")
    return preco - (preco * percentual / 100)
```

### Testes Gerados:
```python
import pytest

@pytest.mark.parametrize("preco,percentual,resultado", [
    (100, 0, 100),
    (100, 50, 50),
    (100, 100, 0),
])
def test_calcular_desconto(preco, percentual, resultado):
    assert calcular_desconto(preco, percentual) == resultado

def test_calcular_desconto_percentual_negativo():
    with pytest.raises(ValueError):
        calcular_desconto(100, -50)

def test_calcular_desconto_percentual_maior_que_100():
    with pytest.raises(ValueError):
        calcular_desconto(100, 150)
```

## 🛠️ Tecnologias Utilizadas

### Core
- **Python 3.8+**: Linguagem principal
- **Streamlit**: Interface web interativa
- **LangGraph**: Orquestração de agentes ReAct

### IA e RAG
- **Groq API**: LLM Llama-3.3-70b-versatile (gratuito)
- **LangChain**: Framework RAG
- **FAISS**: Vectorstore para busca semântica
- **HuggingFace Embeddings**: Geração de embeddings

### Testes
- **pytest**: Framework de testes
- **python-dotenv**: Gerenciamento de variáveis de ambiente

## 🔧 Configuração Avançada

### Personalizar Base de Conhecimento
Adicione arquivos `.txt` na pasta `docs/`:
```
docs/
├── meu_guia_testes.txt
├── melhores_praticas.txt
└── ...
```

### Alterar Modelo LLM
Em `app.py`, `main.py`, `nodes.py`, `executor.py`:
```python
# Mudar modelo
model="llama-3.1-70b-versatile"  # ou outro modelo Groq
```

### Configurar Vectorstore
```python
# Em app.py/main.py
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})  # Top 5 resultados
```

## 🐛 Troubleshooting

### Erro: "GROQ_API_KEY não configurada"
```bash
# Verificar se .env existe
cat .env

# Ou definir variável de ambiente
$env:GROQ_API_KEY = "sua_chave"
```

### Erro: "No module named 'langchain_community'"
```bash
pip install langchain langchain-community faiss-cpu
```

### Erro: "unstructured package not found"
```bash
pip install "unstructured[local-inference]"
```

### Testes não executam
- Verificar se `pytest` está instalado
- Arquivo `test_generated.py` pode ter caracteres especiais
- Função `clean_code()` remove problemas de encoding

## 📈 Métricas e Monitoramento

### Dashboard em Tempo Real
- **📄 Documentos carregados**: Quantidade de arquivos na base RAG
- **📏 Caracteres totais**: Tamanho da base de conhecimento
- **🔍 Vectorstore**: Status do FAISS (✅ carregado)

### Exemplo de Busca RAG
- Query: "pytest parametrize"
- Resultados: Trechos relevantes dos arquivos `docs/`

## 🎓 Aspectos Educacionais

Este projeto demonstra conceitos avançados de IA:

### 🤖 Agentes Autônomos
- **ReAct Pattern**: Reasoning + Acting para tomada de decisão
- **Chain-of-Thought**: Pensamento estruturado passo-a-passo

### 📚 Retrieval-Augmented Generation
- **Busca semântica**: Encontrar contexto relevante
- **Geração contextual**: Melhorar qualidade com conhecimento externo

### 🧪 Engenharia de Testes
- **Test-Driven Development**: Geração automática de testes
- **Boas práticas**: Parametrização, edge cases, tratamento de erros

## 📄 Licença

Este projeto é de uso acadêmico/educacional. Sinta-se livre para usar, modificar e distribuir.

## 🙏 Agradecimentos

- **Groq** por API gratuita e rápida
- **LangChain** por framework RAG
- **Streamlit** por interface web simples
- **HuggingFace** por modelos de embeddings

---
