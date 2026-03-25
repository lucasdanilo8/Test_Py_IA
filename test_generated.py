# -*- coding: utf-8 -*-
import pytest

# CÓDIGO A TESTAR
def calcular_desconto(preco, percentual):
    if percentual < 0 or percentual > 100:
        raise ValueError("O percentual deve estar entre 0 e 100")
    return preco - (preco * (percentual / 100))

def soma(a, b):
    resultado = a + b
    return resultado

# TESTES
def test_soma_casos_normais():
    assert soma(1, 2) == 3
    assert soma(0, 0) == 0
    assert soma(-1, 1) == 0

def test_soma_casos_edge():
    assert soma(-1, -2) == -3
    assert soma(0, -1) == -1
    assert soma(1, 0) == 1

def test_soma_valores_nulos():
    with pytest.raises(TypeError):
        soma(None, 2)

def test_soma_strings():
    with pytest.raises(TypeError):
        soma("a", 2)

def test_calcular_desconto_casos_normais():
    assert calcular_desconto(100, 10) == 90
    assert calcular_desconto(100, 0) == 100
    assert calcular_desconto(100, 100) == 0

def test_calcular_desconto_casos_edge():
    with pytest.raises(ValueError):
        calcular_desconto(100, -1)
    with pytest.raises(ValueError):
        calcular_desconto(100, 101)

def test_calcular_desconto_valores_nulos():
    with pytest.raises(TypeError):
        calcular_desconto(None, 10)
    with pytest.raises(TypeError):
        calcular_desconto(100, None)

def test_calcular_desconto_strings():
    with pytest.raises(TypeError):
        calcular_desconto("a", 10)
    with pytest.raises(TypeError):
        calcular_desconto(100, "a")

@pytest.mark.parametrize("preco, percentual, resultado", [
    (100, 10, 90),
    (100, 0, 100),
    (100, 100, 0)
])
def test_calcular_desconto_parametrizado(preco, percentual, resultado):
    assert calcular_desconto(preco, percentual) == resultado

@pytest.mark.parametrize("a, b, resultado", [
    (1, 2, 3),
    (0, 0, 0),
    (-1, 1, 0)
])
def test_soma_parametrizado(a, b, resultado):
    assert soma(a, b) == resultado