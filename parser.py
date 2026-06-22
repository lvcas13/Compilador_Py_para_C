from lexico import AnalisadorLexico

SINCRONIZACAO = {"DOIS_PONTOS", "CHAVE_ESQ", "CHAVE_DIR",
                 "PALAVRA_CHAVE", "EOF"}

TIPOS_C = {"int", "float", "char", "void", "bool", "double"}

class Parser:

    def __init__(self, tokens: list):
        self.tokens = [t for t in tokens if t[0] not in ("ERRO", "COMENTARIO")]
        self.pos    = 0
        self.erros  = []
        self.erros_semanticos = [] #fase semantica: guarda os erros graves
        self.pilha_escopos = [{}]  #fase semantica: tabela de símbolos em forma de pilha de dicionarios
        self.warnings = []         #fase semantica: guarda os avisos

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
    
    #fase semantica: ferramenta para buscar a ficha completa de uma variavel em todos os escopos
    def _buscar_simbolo(self, nome_var):
        #procura a variavel do escopo mais interno para o mais externo
        for escopo in reversed(self.pilha_escopos):
            if nome_var in escopo:
                return escopo[nome_var] #retorna a ficha completa
        return None

    #fase semantica: ferramenta para pegar o tipo do valor que vem depois do '=' ou em chamadas de funçao, para aplicar regras de coerção
    def _pegar_tipo_valor(self) -> str:
        tipo_tok = self._tipo_atual()
        lexema = self._lexema_atual()
        
        if tipo_tok == "NUMERO":
            return "float" if "." in lexema else "int"
        if tipo_tok == "STRING":
            return "string"
        if tipo_tok == "IDENTIFICADOR":
            ficha = self._buscar_simbolo(lexema)
            return ficha["tipo"] if ficha else "desconhecido"
            
        return "desconhecido"

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

    #fase semantica: ferramenta para registrar erros semanticos
    def _erro_semantico(self, mensagem: str, tok: tuple = None):
        tok = tok or self._atual()
        linha  = tok[2]
        coluna = tok[3]
        self.erros_semanticos.append(f"[Erro Semântico] Linha {linha}, Coluna {coluna}: {mensagem}")

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
            self._erro("Encontrada chave '}' solta ou sobrando sem abrir um escopo '{'.")
            self._avanca()

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
        tipo_var = self._lexema_atual() 
        self._avanca()                 

        tok_nome = self._atual() 
        if not self._consome("IDENTIFICADOR"):
            self._sincronizar()
            return
        nome_var = tok_nome[1]
        linha_var = tok_nome[2]

        #regras semanticas para declaracao de variaveis
        #1.verifica duplicidade no escopo atual [-1]
        if nome_var in self.pilha_escopos[-1]: 
            self._erro_semantico(f"Variável '{nome_var}' já declarada neste escopo", tok_nome)
        else:
            #2.cria a ficha completa da variavel
            self.pilha_escopos[-1][nome_var] = {
                "tipo": tipo_var,
                "usada": False,
                "linha": linha_var
            }

        if self._tipo_atual() == "ATRIB":
            self._avanca()
            
            #3.verifica coerção de tipos na atribuiçao
            tipo_recebido = self._pegar_tipo_valor()
            if tipo_var == "int" and tipo_recebido == "float":
                self.warnings.append(f"[Aviso] Linha {linha_var}: Conversão implícita. Guardando 'float' em 'int' ('{nome_var}').")
                
            self._expressao()

#///////////Atribuicao ou chamada de funçao///////////
    def _atrib_ou_chamada(self):
        tok_nome = self._avanca() 
        nome_var = tok_nome[1]

        if self._tipo_atual() == "ATRIB":
            self._avanca()
            
            #regras semanticas para atribuiçao
            #verifica se a variavel existe e qual o tipo do valor que vem depois o '=' para aplicar regras de coerção
            ficha_alvo = self._buscar_simbolo(nome_var)
            if not ficha_alvo:
                self._erro_semantico(f"A variável '{nome_var}' não foi declarada antes de receber um valor.", tok_nome)
            tipo_recebido = self._pegar_tipo_valor()
            
            if ficha_alvo and tipo_recebido != "desconhecido":
                if ficha_alvo["tipo"] == "int" and tipo_recebido == "float":
                    self.warnings.append(f"[Aviso] Linha {tok_nome[2]}: Conversão implícita. Guardando 'float' em 'int' ('{nome_var}').")

            self._expressao()

        elif self._tipo_atual() == "PAREN_ESQ":
            self._args_chamada()

        else:
            self._erro(f"Esperado '=' ou '(' após '{nome_var}'", tok_nome)
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

        #fase semantica: abre um novo escopo local
        self.pilha_escopos.append({})

        def _fim_bloco():
            if self._tipo_atual() in ("CHAVE_DIR", "EOF"):
                return True
            if self._tipo_atual() == "PALAVRA_CHAVE" and self._lexema_atual() in ("else if", "else"):
                return True
            return False
            
        while not _fim_bloco():
            self._declaracao()
            
        #consome CHAVE_DIR apenas se presente
        if self._tipo_atual() == "CHAVE_DIR":
            self._avanca()
            
        #fase semantica: fecha o escopo e verifica quem morreu sem ser usado
        escopo_morto = self.pilha_escopos.pop()
        for var, ficha in escopo_morto.items():
            if not ficha["usada"]:
                self.warnings.append(f"[Aviso] Linha {ficha['linha']}: A variável '{var}' ({ficha['tipo']}) foi declarada, mas nunca utilizada.")

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
            tok_id = self._atual() 
            nome_var = tok_id[1]   
            self._avanca() 

            #regras semanticas para uso de variaveis
            if self._tipo_atual() != "PAREN_ESQ": #nao eh chamada de funcao, entao eh uso de variavel
                ficha = self._buscar_simbolo(nome_var) #busca a ficha em todos os escopos
                
                if not ficha:
                    self._erro_semantico(f"A variável '{nome_var}' não foi declarada antes do uso.", tok_id)
                else:
                    ficha["usada"] = True #atualiza a ficha para marcar que a variável foi usada

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
        
        #fase semantica: verifica o escopo global no fim do programa
        if self.pilha_escopos:
            escopo_global = self.pilha_escopos.pop()
            for var, ficha in escopo_global.items():
                if not ficha["usada"]:
                    self.warnings.append(f"[Aviso] Linha {ficha['linha']}: A variável global '{var}' ({ficha['tipo']}) foi declarada, mas nunca utilizada.")
                    
        return len(self.erros) == 0