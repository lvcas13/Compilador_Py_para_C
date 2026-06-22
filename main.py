import sys
from lexico import AnalisadorLexico, exibir_erros, exibir_tabela
from parser import Parser


def obter_caminho() -> str:
    if len(sys.argv) < 2:
        print("Uso: python main.py <arquivo.txt>")
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


def exibir_resultado_lexico(tokens: list, erros: list):
    exibir_tabela(tokens)
    total = sum(1 for t in tokens if t[0] != "ERRO")
    print(f"\n  Total de tokens: {total}")
    if erros:
        exibir_erros(erros)
    else:
        print("  Nenhum aviso ou erro léxico encontrado.\n")


def exibir_resultado_parser(sucesso: bool, erros_sintaticos: list, erros_semanticos: list, warnings: list):
    print(f"\n{'='*55}")
    print("  ANÁLISE SINTÁTICA E SEMÂNTICA")
    print(f"{'='*55}")
    
    #se nao houver erros sintaticos ou semanticos
    if sucesso and not erros_semanticos:
        print("  Análise concluída com sucesso! Nenhum erro encontrado.")
    else:
        #fase sintatica
        if erros_sintaticos:
            print(f"  Encontrado(s) {len(erros_sintaticos)} erro(s) sintático(s):\n")
            for erro in erros_sintaticos:
                print(f"  {erro}")
        
        #fase semantica
        if erros_semanticos:
            if erros_sintaticos:
                print() 
            print(f"  Encontrado(s) {len(erros_semanticos)} erro(s) semântico(s):\n")
            for erro in erros_semanticos:
                print(f"  {erro}")

    #exibiçao dos warnings
    if warnings:
        print(f"\n{'-'*55}")
        print(f"  Gerado(s) {len(warnings)} aviso(s) (Warnings):\n")
        for aviso in warnings:
            print(f"  {aviso}")
                
    print(f"{'='*55}\n")

def main():
    caminho = obter_caminho()
    codigo  = ler_arquivo(caminho)

    print(f"\nAnalisando: {caminho}\n")

    #fase 1 — analise lexica
    lexico  = AnalisadorLexico()
    tokens  = lexico.tokenizar(codigo)
    exibir_resultado_lexico(tokens, lexico.erros)

    #fase 2 — analise sintatica e semantica*
    parser  = Parser(tokens)
    sucesso = parser.analisar()
    exibir_resultado_parser(sucesso, parser.erros, parser.erros_semanticos, parser.warnings)
    


if __name__ == "__main__":
    main()
