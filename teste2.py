# Programa de teste do analisador léxico

def fatorial(n):
    if n <= 1:
        return 1
    return n * fatorial(n - 1)

def main():
    x = 10
    y = 3.14
    nome = "compiladores"
    flag = True
    vazio = None

    # números especiais
    hexa  = 0xFF
    octal = 0o77
    binario = 0b1010
    grande  = 1_000_000

    if x >= 5 and y != 0.0:
        x += 1
        print(nome)
    elif x == 0:
        x = x - 1
    else:
        while x > 0:
            x -= 1

    for i in range(5):
        print(fatorial(i))

    resultado = x ** 2
    divisao_inteira = x // 3

    # operadores bit a bit
    a = x & 0b1111
    b = a | 8
    c = b ^ 3
    d = ~c
    e = a << 2
    f = e >> 1

main()
