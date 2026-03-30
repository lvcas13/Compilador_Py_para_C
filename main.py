import sys
from lexico import AnalisadorLexico, exibir_erros, exibir_tabela


def obter_caminho() -> str:
    if len(sys.argv) < 2:
        print("Uso: python lexico.py <arquivo.py>")
        sys.exit(1)
    return sys.argv[1]


def ler_arquivo(caminho: str) -> str:
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Erro: arquivo '{caminho}' não encontrado.")
        sys.exit(1)
    except IOError as e:
        print(f"Erro ao ler o arquivo: {e}")
        sys.exit(1)


def exibir_resultado(tokens: list, erros: list):
    exibir_tabela(tokens)
    total = sum(1 for t in tokens if t[0] != "ERRO")
    print(f"\n  Total de tokens: {total}")
    if erros:
        exibir_erros(erros)
    else:
        print("  Nenhum aviso ou erro encontrado.\n")


def main():
    caminho    = obter_caminho()
    codigo     = ler_arquivo(caminho)

    print(f"\nAnalisando: {caminho}\n")

    analisador = AnalisadorLexico()
    tokens     = analisador.tokenizar(codigo)

    exibir_resultado(tokens, analisador.erros)


if __name__ == "__main__":
    main()