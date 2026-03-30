# Demonstração de variáveis e precedência de operadores
a = 5 + 3 * 2
b = (a + 1) / 3

print("O valor de a e:", a)
print("O valor de b e:", b)

# Demonstração de estruturas de controle (if/else)
if b > 3:
    print("b e maior que 3")
else:
    print("b nao e maior que 3")

# Demonstração de listas e laços 'for'
print("--- Contagem ---")
numeros = [10.5, 20.2, 30.8, 40.1]
soma = 0

for item in numeros:
    print("Item atual:", item)
    soma = soma + item

print("A soma dos itens e:", soma)