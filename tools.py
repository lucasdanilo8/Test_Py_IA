# tools.py

import subprocess
import re

def clean_code(text):
    """Remove markdown formatting from code blocks and ensure UTF-8 encoding."""
    # Remove ```python ... ``` blocks
    text = re.sub(r'```python\n', '', text)
    text = re.sub(r'```\n', '', text)
    text = re.sub(r'```', '', text)
    text = text.strip()
    
    # Add UTF-8 encoding declaration if not present
    if not text.startswith('#'):
        text = '# -*- coding: utf-8 -*-\n' + text
    
    return text


def search_docs(retriever, query, k=None):
    """Busca documentos relevantes com k ajustável."""
    if k is None:
        # Retorna todos os documentos disponíveis se k não especificado
        docs = retriever.invoke(query)
    else:
        # Cria um retriever temporário com k específico
        search_kwargs = {"k": k}
        temp_retriever = retriever.search_kwargs.update(search_kwargs) if hasattr(retriever, 'search_kwargs') else retriever
        docs = temp_retriever.invoke(query)

    return "\n".join([d.page_content for d in docs])


def run_tests():
    result = subprocess.run(
        ["pytest", "-q"],
        capture_output=True,
        text=True
    )
    return result.stdout + result.stderr