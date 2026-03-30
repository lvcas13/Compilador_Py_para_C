import tokenize
import sys
from io import BytesIO

KEYWORD_MAP = {
    "print":    "printf",
    "and":      "&&",
    "or":       "||",
    "not":      "!",
    "True":     "1",
    "False":    "0",
    "None":     "NULL",
    "def":      "Função",
    "if":       "if",
    "for":      "for",
    "else":     "else",
    "elif":     "else if",
    "while":    "while",
    "return":   "return",
    "in":       "in",
}

OPERATOR_MAP = {
    "+":  ("MAIS",          "+"),
    "-":  ("MENOS",         "-"),
    "*":  ("MULT",          "*"),
    "/":  ("DIV",           "/"),
    "%":  ("MOD",           "%"),
    "**": ("POTENCIA",      "pow()"),
    "//": ("DIV_INTEIRA",   "/"),
    "=":  ("ATRIB",         "="),
    "==": ("IGUAL",         "=="),
    "!=": ("DIFERENTE",     "!="),
    "<":  ("MENOR",         "<"),
    ">":  ("MAIOR",         ">"),
    "<=": ("MENOR_IGUAL",   "<="),
    ">=": ("MAIOR_IGUAL",   ">="),
    "&&": ("E_LOGICO",      "&&"),
    "||": ("OU_LOGICO",     "||"),
    "!":  ("NAO",           "!"),
    "(":  ("PAREN_ESQ",     "("),
    ")":  ("PAREN_DIR",     ")"),
    "{":  ("CHAVE_ESQ",     "{"),
    "}":  ("CHAVE_DIR",     "}"),
    "[":  ("COLCH_ESQ",     "["),
    "]":  ("COLCH_DIR",     "]"),
    ":":  ("DOIS_PONTOS",   ":"),
    ",":  ("VIRGULA",       ","),
    ";":  ("PONTO_VIRG",    ";"),
}

IGNORAR = {"ENCODING", "ENDMARKER", "NL", "NEWLINE"}


class AnalisadorLexico:

    def __init__(self):
        self.tokens = []
        self.erros  = []

    def _proc_comment(self, valor, linha, coluna):
        self.tokens.append(("COMENTARIO", "//" + valor[1:], linha, coluna))

    def _proc_indent(self, valor, linha, coluna):
        self.tokens.append(("CHAVE_ESQ", "{", linha, coluna))

    def _proc_dedent(self, valor, linha, coluna):
        if valor.strip():
            self.tokens.append(("CHAVE_DIR", "}", linha, coluna))

    def _proc_name(self, valor, linha, coluna):
        if valor in KEYWORD_MAP:
            self.tokens.append(("PALAVRA_CHAVE", KEYWORD_MAP[valor], linha, coluna))
        else:
            self.tokens.append(("IDENTIFICADOR", valor, linha, coluna))

    def _proc_number(self, valor, linha, coluna):
        self.tokens.append(("NUMERO", valor, linha, coluna))

    def _proc_string(self, valor, linha, coluna):
        # normaliza aspas simples para duplas (padrão C)
        if valor.startswith("'") and valor.endswith("'"):
            valor = '"' + valor[1:-1] + '"'
        self.tokens.append(("STRING", valor, linha, coluna))

    def _proc_op(self, valor, linha, coluna):
        if valor in OPERATOR_MAP:
            tipo_c, lexema_c = OPERATOR_MAP[valor]
            self.tokens.append((tipo_c, lexema_c, linha, coluna))
        else:
            self.erros.append((f"Operador sem equivalente em C: '{valor}'", linha, coluna))
            self.tokens.append(("ERRO", valor, linha, coluna))

    def tokenizar(self, codigo: str) -> list:
        self.tokens, self.erros = [], []

        if not codigo.endswith("\n"):
            codigo += "\n"

        HANDLERS = {
            "COMMENT": self._proc_comment,
            "INDENT":  self._proc_indent,
            "DEDENT":  self._proc_dedent,
            "NAME":    self._proc_name,
            "NUMBER":  self._proc_number,
            "STRING":  self._proc_string,
            "OP":      self._proc_op,
        }

        try:
            for tok in tokenize.tokenize(BytesIO(codigo.encode("utf-8")).readline):
                tipo = tokenize.tok_name[tok.type]
                if tipo in IGNORAR:
                    continue
                handler = HANDLERS.get(tipo)
                if handler:
                    handler(tok.string, *tok.start)
                else:
                    self.erros.append((f"Token não reconhecido: '{tipo}'", *tok.start))
                    self.tokens.append(("ERRO", tok.string, *tok.start))
        except tokenize.TokenError as e:
            msg, pos = e.args
            self.erros.append((f"Erro de tokenização: {msg}", *pos))

        return self.tokens

def exibir_tabela(tokens: list):
    if not tokens:
        print("  Nenhum token gerado.")
        return

    col_t = max(max(len(t[0]) for t in tokens), 15)
    col_l = max(max(len(t[1]) for t in tokens), 12)
    sep   = f"+{'-'*(col_t+2)}+{'-'*(col_l+2)}+{'-'*8}+{'-'*8}+"

    print(sep)
    print(f"| {'TIPO':<{col_t}} | {'LEXEMA (C)':<{col_l}} | {'LINHA':^6} | {'COLUNA':^6} |")
    print(sep)
    for tipo, lexema, linha, coluna in tokens:
        print(f"| {tipo:<{col_t}} | {lexema:<{col_l}} | {linha:^6} | {coluna:^6} |")
    print(sep)


def exibir_erros(erros: list):
    print(f"\n{'='*55}")
    print(f"  AVISOS / ERROS ({len(erros)})")
    print(f"{'='*55}")
    for i, (msg, linha, coluna) in enumerate(erros, 1):
        print(f"  [{i}] Linha {linha}, Coluna {coluna}: {msg}")
