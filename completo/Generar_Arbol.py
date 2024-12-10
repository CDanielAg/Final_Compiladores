import re
from graphviz import Digraph

class Nodo:
    def __init__(self, etiqueta, identificador, valor=None):
        self.etiqueta = etiqueta
        self.identificador = identificador
        self.valor = valor
        self.hijos = []
        self.padre = None  # Atributo para almacenar el nodo padre

    def agregar_hijo(self, hijo):
        self.hijos.append(hijo)
        hijo.padre = self  # Asigna el nodo actual como el padre del hijo

    def es_hoja(self):
        return len(self.hijos) == 0

def cargar_gramatica(nombre_archivo):
    gramatica = {}
    with open(nombre_archivo, 'r') as archivo:
        for linea in archivo:
            if '->' in linea:
                cabeza, produccion = linea.split('->')
                cabeza = cabeza.strip()
                simbolos_produccion = [simbolo.strip() for simbolo in produccion.strip().split()]
                if cabeza in gramatica:
                    gramatica[cabeza].append(simbolos_produccion)
                else:
                    gramatica[cabeza] = [simbolos_produccion]
    return gramatica

def cargar_tokens(nombre_archivo):
    tokens = []
    with open(nombre_archivo, 'r') as archivo:
        for linea in archivo:
            tokens.extend(linea.strip().split())
    return tokens

def cargar_no_terminales(nombre_archivo):
    no_terminales = set()
    with open(nombre_archivo, 'r') as archivo:
        for linea in archivo:
            no_terminales.add(linea.strip())
    return no_terminales

def generar_arbol_sintactico(gramatica, tokens, no_terminales):
    dot = Digraph(comment='Arbol Sintactico')
    contador_nodos = 0
    nodos = {}

    def agregar_nodo(etiqueta, valor=None):
        nonlocal contador_nodos
        nodo = Nodo(etiqueta, f'N{contador_nodos}', valor)
        dot.node(nodo.identificador, f'{etiqueta}\n{valor}' if valor else etiqueta)
        contador_nodos += 1
        return nodo

    def parser(no_terminal, tokens, index):
        if no_terminal not in gramatica:
            print(f"No se encuentra el no terminal: {no_terminal}")
            return None, index

        producciones = sorted(gramatica[no_terminal], key=lambda p: evaluar_prioridad(p, tokens, index), reverse=True)
        for produccion in producciones:
            hijos = []
            nuevo_index = index
            exito = True
            for simbolo in produccion:
                if simbolo in gramatica:
                    nodo_hijo, nuevo_index = parser(simbolo, tokens, nuevo_index)
                    if nodo_hijo is None:
                        exito = False
                        break
                    hijos.append(nodo_hijo)
                else:
                    if simbolo == "''":
                        continue
                    if nuevo_index < len(tokens) and re.match(f'{simbolo}:.*', tokens[nuevo_index]):
                        token_tipo, token_valor = tokens[nuevo_index].split(':')
                        nodo_hijo = agregar_nodo(token_tipo, token_valor)
                        hijos.append(nodo_hijo)
                        nuevo_index += 1
                    else:
                        exito = False
                        break

            if exito:
                nodo_actual = agregar_nodo(no_terminal)
                for hijo in hijos:
                    nodo_actual.agregar_hijo(hijo)
                    dot.edge(nodo_actual.identificador, hijo.identificador)
                return nodo_actual, nuevo_index

        # Si ninguna producción tiene éxito, aceptar cadena vacía si es posible
        if "''" in [simbolo for produccion in gramatica[no_terminal] for simbolo in produccion]:
            return agregar_nodo(no_terminal), index

        return None, index

    def evaluar_prioridad(produccion, tokens, index):
        # Evaluar cuántos tokens coinciden con la producción desde el índice actual
        coincidencias = 0
        for simbolo in produccion:
            if index + coincidencias < len(tokens):
                token = tokens[index + coincidencias]
                if simbolo in gramatica or re.match(f'{simbolo}:.*', token):
                    coincidencias += 1
                else:
                    break
            else:
                break
        return coincidencias

    raiz, _ = parser('PROGRAMA', tokens, 0)
    if raiz:
        agregar_epsilon_a_hojas(raiz, dot, no_terminales)
        dot.render('arbol_sintactico', format='png', cleanup=True)
        print("Árbol sintáctico generado con éxito y guardado en arbol_sintactico.png")
        return raiz
    else:
        print("No se pudo generar el árbol sintáctico")
        return None

def agregar_epsilon_a_hojas(nodo, dot, no_terminales):
    if nodo.es_hoja() and nodo.etiqueta in no_terminales:
        epsilon_nodo = Nodo("ε", f'N{nodo.identificador}_epsilon')
        dot.node(epsilon_nodo.identificador, "ε")
        nodo.agregar_hijo(epsilon_nodo)
        dot.edge(nodo.identificador, epsilon_nodo.identificador)
    else:
        for hijo in nodo.hijos:
            agregar_epsilon_a_hojas(hijo, dot, no_terminales)

def main():
    nombre_archivo_gramatica = 'Gramatica.txt'
    nombre_archivo_tokens = 'tokens.txt'
    nombre_archivo_no_terminales = 'no_terminales.txt'

    gramatica = cargar_gramatica(nombre_archivo_gramatica)
    tokens = cargar_tokens(nombre_archivo_tokens)
    no_terminales = cargar_no_terminales(nombre_archivo_no_terminales)
    raiz = generar_arbol_sintactico(gramatica, tokens, no_terminales)
    
if __name__ == "__main__":
    main()
