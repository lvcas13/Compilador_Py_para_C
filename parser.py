from lexico import AnalisadorLexico

SINCRONIZACAO = {"DOIS_PONTOS", "CHAVE_ESQ", "CHAVE_DIR",
                 "PALAVRA_CHAVE", "EOF"}

TIPOS_C = {"int", "float", "char", "void", "bool", "double"}

class Parser:

    def __init__(self, tokens: list):
        self.tokens = [t for t in tokens if t[0] != "ERRO"]
        self.pos    = 0
        self.erros  = []

    def _atual(self) -> tuple:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return ("EOF", "EOF", -1, -1)

    def _tipo_atual(self) -> str:
        return self._atual()[0]

    def _lexema_atual(self) -> str:
        return self._atual()[1]

    def _avanca(self) -> tuple:
        tok = self._atual()
        if self.pos < len(self.tokens):
            self.pos += 1
        return tok

    def _consome(self, tipo: str, lexema: str = None) -> bool:
        tok = self._atual()
        if tok[0] == tipo and (lexema is None or tok[1] == lexema):
            self._avanca()
            return True
        esperado = f"'{lexema}'" if lexema else tipo
        self._erro(f"Esperado {esperado}, encontrado '{tok[1]}'", tok)
        return False

#////////Modo Panico////////
    def _erro(self, mensagem: str, tok: tuple = None):
        tok = tok or self._atual()
        linha  = tok[2]
        coluna = tok[3]
        self.erros.append(f"[Erro Sintático] Linha {linha}, Coluna {coluna}: {mensagem}")

    def _sincronizar(self):
        while self._tipo_atual() != "EOF":
            if self._tipo_atual() in SINCRONIZACAO:
                return
            self._avanca()

#/////////Regras da gramatica/////////
    def programa(self):
        while self._tipo_atual() != "EOF":
            self._declaracao()

    def _declaracao(self):
        tipo   = self._tipo_atual()
        lexema = self._lexema_atual()

        if tipo == "PALAVRA_CHAVE" and lexema == "Função":
            self._def_funcao()

        elif tipo == "PALAVRA_CHAVE" and lexema in ("if", "while", "for"):
            self._estrutura_controle()

        elif tipo == "IDENTIFICADOR" and lexema in TIPOS_C:
            self._decl_variavel()

        elif tipo == "PALAVRA_CHAVE" and lexema == "return":
            self._avanca()
            if self._tipo_atual() not in ("DOIS_PONTOS", "CHAVE_DIR", "EOF"):
                self._expressao()

        elif tipo == "IDENTIFICADOR":
            self._atrib_ou_chamada()

        elif tipo == "PALAVRA_CHAVE" and lexema in ("printf", "scanf"):
            self._avanca()
            self._args_chamada()

        elif tipo == "CHAVE_DIR":
            return

        else:
            self._erro(f"Declaração inválida: '{lexema}'")
            self._avanca()
            self._sincronizar()

#/////////Definicao de funcao//////////
    def _def_funcao(self):
        self._avanca()                                 
        self._consome("IDENTIFICADOR")                  
        self._consome("PAREN_ESQ", "(")
        if self._tipo_atual() == "IDENTIFICADOR":
            self._params()
        self._consome("PAREN_DIR", ")")
        self._consome("DOIS_PONTOS", ":")
        self._bloco()

    def _params(self):
        self._avanca()                                  
        while self._tipo_atual() == "VIRGULA":
            self._avanca()                            
            if not self._consome("IDENTIFICADOR"):
                self._sincronizar()
                return
            
#///////////Declaracao de variavel///////////
    def _decl_variavel(self):
        self._avanca()                                  
        if not self._consome("IDENTIFICADOR"):
            self._sincronizar()
            return
        if self._tipo_atual() == "ATRIB":
            self._avanca()                              
            self._expressao()

#///////////Atribuicao ou chamada de funcao///////////
    def _atrib_ou_chamada(self):
        nome = self._avanca()                           

        if self._tipo_atual() == "ATRIB":
            self._avanca()                              
            self._expressao()

        elif self._tipo_atual() == "PAREN_ESQ":
            self._args_chamada()

        else:
            self._erro(f"Esperado '=' ou '(' após '{nome[1]}'", nome)
            self._sincronizar()

    def _args_chamada(self):
        self._consome("PAREN_ESQ", "(")
        if self._tipo_atual() != "PAREN_DIR":
            self._expressao()
            while self._tipo_atual() == "VIRGULA":
                self._avanca()
                self._expressao()
        self._consome("PAREN_DIR", ")")

#///////////Estruturas de controle///////////
    def _estrutura_controle(self):
        lexema = self._lexema_atual()
        if lexema == "if":
            self._if_stmt()
        elif lexema == "while":
            self._while_stmt()
        elif lexema == "for":
            self._for_stmt()

    def _if_stmt(self):
        self._avanca()                                  
        self._expressao()
        self._consome("DOIS_PONTOS", ":")
        self._bloco()

        # else if / else
        while self._tipo_atual() == "PALAVRA_CHAVE" and self._lexema_atual() == "else if":
            self._avanca()                              
            self._expressao()
            self._consome("DOIS_PONTOS", ":")
            self._bloco()

        if self._tipo_atual() == "PALAVRA_CHAVE" and self._lexema_atual() == "else":
            self._avanca()                           
            self._consome("DOIS_PONTOS", ":")
            self._bloco()

    def _while_stmt(self):
        self._avanca()                                 
        self._expressao()
        self._consome("DOIS_PONTOS", ":")
        self._bloco()

    def _for_stmt(self):
        self._avanca()                                  
        self._consome("IDENTIFICADOR")                  
        self._consome("PALAVRA_CHAVE", "in")
        self._expressao()                               
        self._consome("DOIS_PONTOS", ":")
        self._bloco()

#///////////Bloco (declaracoes)///////////
    def _bloco(self):
        if not self._consome("CHAVE_ESQ", "{"):
            self._sincronizar()
            return

        def _fim_bloco():
            if self._tipo_atual() in ("CHAVE_DIR", "EOF"):
                return True
            if self._tipo_atual() == "PALAVRA_CHAVE" and self._lexema_atual() in ("else if", "else"):
                return True
            return False
        while not _fim_bloco():
            self._declaracao()
        # consome CHAVE_DIR apenas se presente
        if self._tipo_atual() == "CHAVE_DIR":
            self._avanca()
#///////////Expressao///////////
    def _expressao(self):
        self._expr_logica()

    def _expr_logica(self):
        self._expr_relacional()
        while (self._tipo_atual() in ("E_LOGICO", "OU_LOGICO") or
               (self._tipo_atual() == "PALAVRA_CHAVE" and
                self._lexema_atual() in ("&&", "||"))):
            self._avanca()
            self._expr_relacional()

    def _expr_relacional(self):
        self._expr_aditiva()
        while self._tipo_atual() in ("IGUAL", "DIFERENTE", "MENOR",
                                     "MAIOR", "MENOR_IGUAL", "MAIOR_IGUAL"):
            self._avanca()
            self._expr_aditiva()

    def _expr_aditiva(self):
        self._termo()
        while self._tipo_atual() in ("MAIS", "MENOS"):
            self._avanca()
            self._termo()

    def _termo(self):
        self._fator()
        while self._tipo_atual() in ("MULT", "DIV", "MOD"):
            self._avanca()
            self._fator()

    def _fator(self):
        tipo   = self._tipo_atual()
        lexema = self._lexema_atual()

        if tipo in ("MENOS", "NAO"):
            self._avanca()
            self._fator()

        elif tipo == "PAREN_ESQ":
            self._avanca()
            self._expressao()
            self._consome("PAREN_DIR", ")")

        elif tipo == "IDENTIFICADOR":
            self._avanca()
            if self._tipo_atual() == "PAREN_ESQ":
                self._args_chamada()

        elif tipo in ("NUMERO", "STRING"):
            self._avanca()

        elif tipo == "PALAVRA_CHAVE" and lexema in ("1", "0", "NULL"):
            self._avanca()

        else:
            self._erro(f"Expressão inválida: '{lexema}'")
            self._avanca()
            self._sincronizar()
#///////////Entrada//////////////
    def analisar(self) -> bool:
        self.programa()
        return len(self.erros) == 0
