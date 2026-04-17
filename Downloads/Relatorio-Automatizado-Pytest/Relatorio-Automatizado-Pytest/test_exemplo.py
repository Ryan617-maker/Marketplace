def soma(a, b):
    return a + b


def divisao(a, b):
    return a / b


def test_soma():
    assert soma(2, 3) == 5


def test_divisao():
    assert divisao(10, 2) == 5


def test_divisao_erro():
    try:
        divisao(10, 0)
    except ZeroDivisionError:
        assert True
