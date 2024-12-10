import ply.lex as lex
import json  # Importar json para serializar las cadenas

# Lista de tokens
tokens = (
    'ENTERO', 'FLOTANTE', 'BOOLEANO', 'CADENA',
    'MAS', 'MENOS', 'POR', 'ENTRE', 'IGUAL', 'IGUAL_IGUAL', 'DISTINTO',
    'MENOR', 'MAYOR', 'MENOR_IGUAL', 'MAYOR_IGUAL',
    'PARENTESIS_ABRIR', 'PARENTESIS_CERRAR', 'CORCHETE_ABRIR', 'CORCHETE_CERRAR',
    'LLAVE_ABRIR', 'LLAVE_CERRAR', 'AT',
    'COMA', 'PUNTO',
    'Y', 'O', 'NO', 'COMENTARIO', 'IDENTIFICADOR', 'IMPRIMIR',
    'SI', 'SINO', 'MIENTRAS', 'PARA', 'DEF', 'RETORNAR',
    'LISTA_ABRIR', 'LISTA_CERRAR', 'DICCIONARIO_ABRIR', 'DICCIONARIO_CERRAR',
    'ROMPER', 'CONTINUAR', 'COMENTAR','SINOSI'
)

# Palabras reservadas
reserved = {
    'if': 'SI',
    'else': 'SINO',
    'while': 'MIENTRAS',
    'for': 'PARA',
    'def': 'DEF',
    'return': 'RETORNAR',
    'break': 'ROMPER',
    'continue': 'CONTINUAR',
    'int': 'ENTERO',
    'float': 'FLOTANTE',
    'boolean': 'BOOLEANO',
    'cadena': 'CADENA',
    'and': 'Y',
    'or': 'O',
    'not': 'NO',
    'True': 'BOOLEANO',
    'False': 'BOOLEANO',
    'print': 'IMPRIMIR',
    'elif' : 'SINOSI'
}

# Reglas de expresiones regulares para tokens simples
t_AT = r'@'
t_MAS = r'\+'
t_MENOS = r'-'
t_POR = r'\*'
t_ENTRE = r'/'
t_IGUAL = r'='
t_IGUAL_IGUAL = r'=='
t_DISTINTO = r'!='
t_MENOR = r'<'
t_MAYOR = r'>'
t_MENOR_IGUAL = r'<='
t_MAYOR_IGUAL = r'>='
t_PARENTESIS_ABRIR = r'\('
t_PARENTESIS_CERRAR = r'\)'
t_CORCHETE_ABRIR = r'\['
t_CORCHETE_CERRAR = r'\]'
t_LLAVE_ABRIR = r'\{'
t_LLAVE_CERRAR = r'\}'
t_LISTA_ABRIR = r'\['
t_LISTA_CERRAR = r'\]'
t_DICCIONARIO_ABRIR = r'\{'
t_DICCIONARIO_CERRAR = r'\}'
t_COMA = r','
t_PUNTO = r'\.'

# Operadores lógicos
t_Y = r'y'
t_O = r'o'
t_NO = r'no'

# Definición de las reglas de los tokens más complejos
def t_FLOTANTE(t):
    r'-?\d+\.\d+'
    t.value = float(t.value)
    return t

def t_ENTERO(t):
    r'-?\d+'
    t.value = int(t.value)
    return t

def t_BOOLEANO(t):
    r'True|False'
    t.value = True if t.value == 'True' else False
    return t

def t_CADENA(t):
    r'\'([^\\\']|(\\.))*\'|\"([^\\\"]|(\\.))*\"'
    t.value = t.value[1:-1]  # Mantiene el valor sin comillas
    return t

def t_IDENTIFICADOR(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value, 'IDENTIFICADOR')
    return t

def t_COMENTARIO(t):
    r'\#.*'
    pass

def t_newline(t):
    r'\n'
    t.lexer.lineno += 1

t_ignore = ' \t'

def t_error(t):
    print(f"Carácter ilegal: {t.value[0]}")
    t.lexer.skip(1)

# Construir el lexer
lexer = lex.lex()

# Leer el archivo de entrada
def leer_archivo_entrada(nombre_archivo):
    with open(nombre_archivo, "r") as file:
        return file.read()

# Prueba del lexer con data desde un archivo de texto
nombre_archivo = "codigo.txt"
data = leer_archivo_entrada(nombre_archivo)

lexer.input(data)

# Tokenizar e imprimir los tipos de tokens junto con sus valores
tokens_list = []
tokens_only_list = []

while True:
    tok = lexer.token()
    if not tok:
        break
    if tok.type == 'CADENA':
        # Utiliza json.dumps para serializar la cadena con dobles comillas
        tokens_list.append(f"{tok.type}:{json.dumps(tok.value)}")
    else:
        tokens_list.append(f"{tok.type}:{tok.value}")
    tokens_only_list.append(f"{tok.type}")

# Guardar los tokens en un archivo tokens.txt
with open("tokens.txt", "w") as file:
    file.write(" ".join(tokens_list))

# Guardar solo los tipos de tokens en un archivo tokens_only.txt
with open("tokens_only.txt", "w") as file:
    file.write(" ".join(tokens_only_list))
