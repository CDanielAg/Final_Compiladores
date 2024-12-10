import re
from Generar_Arbol import Nodo, cargar_gramatica, cargar_tokens, cargar_no_terminales

def obtener_raiz(gramatica, tokens, no_terminales):
    contador_nodos = 0
    dot = None  # No necesitamos el objeto Digraph aquí

    def agregar_nodo(etiqueta, valor=None):
        nonlocal contador_nodos
        nodo = Nodo(etiqueta, f'N{contador_nodos}', valor)
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
                return nodo_actual, nuevo_index

        if "''" in [simbolo for produccion in gramatica[no_terminal] for simbolo in produccion]:
            return agregar_nodo(no_terminal), index

        return None, index

    def evaluar_prioridad(produccion, tokens, index):
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
    return raiz


class Simbolo:
    def __init__(self, nombre, tipo, es_funcion=False, parametros=None, valor=None, ambito="Global"):
        self.nombre = nombre
        self.tipo = tipo               # Tipo de la variable o función (int, float, etc.)
        self.es_funcion = es_funcion   # Si es una función o no
        self.parametros = parametros   # Lista de parámetros de la función, si es una función
        self.valor = valor             # Valor de la variable (si es una variable)
        self.ambito = ambito
    
    def __repr__(self):
        if self.es_funcion:
            return f"Función(nombre={self.nombre}, tipo={self.tipo}, parámetros={self.parametros}, valor={self.valor})"
        else:
            return f"Variable(nombre={self.nombre}, tipo={self.tipo}, valor={self.valor})"


class TablaDeSimbolos:
    def __init__(self):
        self.tabla = {}  # Usamos un diccionario para almacenar los símbolos con su nombre como clave
        self.ambitos = []  # Lista de ámbitos para manejo de variables locales

    def agregar_simbolo(self, nombre, tipo, es_funcion=False, parametros=None, valor=None, ambito="Global"):
        """Agrega un símbolo (variable o función) a la tabla de símbolos, si no está ya presente."""
        # Verificar si ya existe un símbolo con el mismo nombre en el mismo ámbito
        if nombre in self.tabla:
            simbolo_existente = self.tabla[nombre]
            if simbolo_existente.ambito == ambito:
                raise ValueError(f"El símbolo '{nombre}' ya está declarado en el ámbito '{ambito}'.")
        
        simbolo = Simbolo(nombre, tipo, es_funcion, parametros, valor, ambito)
        self.tabla[nombre] = simbolo

    def buscar_simbolo(self, nombre):
        """Busca un símbolo por su nombre."""
        return self.tabla.get(nombre, None)

    def declarar_ambito(self):
        """Comienza un nuevo ámbito (por ejemplo, al entrar en una función o bloque)."""
        self.ambitos.append(set())  # Un nuevo conjunto de símbolos locales

    def finalizar_ambito(self):
        """Finaliza el ámbito actual y elimina las variables locales de la tabla."""
        if self.ambitos:
            for simbolo in self.ambitos.pop():
                del self.tabla[simbolo]
        else:
            raise ValueError("No hay ámbitos abiertos para finalizar.")

    def agregar_variable_local(self, nombre, tipo, valor=None):
        """Agrega una variable en el ámbito local actual.""" 
        if not self.ambitos:
            raise ValueError("No hay un ámbito activo para declarar la variable.")
        
        if nombre in self.tabla:
            raise ValueError(f"El símbolo '{nombre}' ya está declarado.")
        
        simbolo = Simbolo(nombre, tipo, es_funcion=False, valor=valor)
        self.tabla[nombre] = simbolo
        self.ambitos[-1].add(nombre)  # Se agrega el nombre al ámbito actual

    def verificar_tipo(self, nombre, tipo_esperado):
        """Verifica que el tipo de un símbolo coincida con el tipo esperado."""
        simbolo = self.buscar_simbolo(nombre)
        if simbolo:
            if simbolo.tipo != tipo_esperado:
                raise TypeError(f"Tipo incorrecto para '{nombre}': se esperaba {tipo_esperado}, pero se encontró {simbolo.tipo}.")
        else:
            raise NameError(f"El símbolo '{nombre}' no está declarado.")

    def imprimir_tabla(self):
        """Imprime la tabla de símbolos mostrando toda la información de cada símbolo."""
        print("\n" + "="*50)
        print(f"{'Símbolos de la Tabla de Símbolos':^50}")
        print("="*50)
        
        # Recorremos la tabla y mostramos toda la información de cada símbolo
        for simbolo in self.tabla.values():
            # Imprimimos los atributos de cada símbolo
            print(f"\n{'Nombre:':<15} {simbolo.nombre}")
            print(f"{'Tipo:':<15} {simbolo.tipo}")
            print(f"{'Es función:':<15} {simbolo.es_funcion}")
            print(f"{'Parámetros:':<15} {simbolo.parametros if simbolo.parametros else 'N/A'}")
            print(f"{'Valor:':<15} {simbolo.valor if simbolo.valor is not None else 'N/A'}")
            print(f"{'Ámbito:':<15} {simbolo.ambito}")
            print("-"*50)

        print("="*50)

TablaSimbolos = TablaDeSimbolos()

def buscarNodo(nodo, nombre):
    if nodo is None:
        return None
    if nodo.etiqueta == nombre:
        return nodo
    for hijo in nodo.hijos:
        encontrado = buscarNodo(hijo, nombre)
        if encontrado:
            return encontrado
    return None  # Si no se encuentra el valor, retornamos None

def buscarValor(nodo):
    # Imprimimos la etiqueta del nodo para depuración
    #print(f"Revisando nodo: {nodo.etiqueta}")

    # Si encontramos un nodo RETORNAR, regresamos el valor
    if nodo.etiqueta == "RETORNAR":
        #print(f"Encontrado RETORNAR en el nodo: {nodo.etiqueta}")
        return obtener_hermanos(nodo)  # Obtener los valores de los hermanos siguientes

    # Si el nodo tiene hijos, buscamos recursivamente en cada uno de ellos
    for hijo in nodo.hijos:
        resultado = buscarValor(hijo)
        if resultado:  # Si encontramos algo, lo regresamos inmediatamente
            return resultado

    return None  # Si no se encuentra el nodo RETORNAR en este camino, regresamos None

def obtener_hermanos(nodo):
    hermanos = []
    
    if nodo.padre:
        # Obtener la posición del nodo en los hijos del padre
        index = nodo.padre.hijos.index(nodo)
        # Obtener los nodos que siguen al nodo actual (hermanos)
        hermanos = nodo.padre.hijos[index + 1:]  # Los nodos después del nodo actual
    
    # Ahora recorremos todos los descendientes de cada hermano
    valores_hijos = []
    for hermano in hermanos:
        # Obtenemos los valores de los hijos (y sus descendientes)
        valores_hijos.extend(obtener_descendientes(hermano))
    
    # Concatenar los valores de los descendientes de los hermanos, excluyendo "@"
    hermanos_con_valor = ''.join([str(valor) for valor in valores_hijos if valor is not None and valor != '@'])
    
    #print(f"Hermanos y sus descendientes encontrados (sin '@'): {hermanos_con_valor}")  # Para depurar
    return hermanos_con_valor  # Devolvemos la cadena concatenada de valores


def obtener_descendientes(nodo):
    """Recorre todos los descendientes de un nodo, es decir, hijos, nietos, etc."""
    valores = []

    if nodo.valor is not None and nodo.valor != '@':  # Excluimos "@" aquí
        valores.append(nodo.valor)  # Agregar el valor del nodo actual
    
    # Recursión para buscar los valores de los hijos del nodo
    for hijo in nodo.hijos:
        valores.extend(obtener_descendientes(hijo))  # Recorremos todos los hijos
    
    return valores


def recorrer_nodos(nodo, parametros, valor, nombre=None, ambito="Global", simbolos_agregados=None):
    if simbolos_agregados is None:
        simbolos_agregados = set()  # Conjunto para rastrear símbolos ya agregados

    if nodo.etiqueta != nombre:
        for hijo in nodo.hijos:
            recorrer_nodos(hijo, parametros, valor, nombre, ambito, simbolos_agregados)
    else:
        if nodo.valor not in simbolos_agregados:
            TablaSimbolos.agregar_simbolo(nodo.valor, "Function", True, parametros, valor, ambito)
            simbolos_agregados.add(nodo.valor)  # Marca el parámetro como agregado

def BuscarParametros(nodo):
    parametros = []  # Lista que almacenará los identificadores encontrados

    if nodo is None:
        return parametros
    
    if nodo.etiqueta == "IDENTIFICADOR":
        parametros.append(nodo.valor)  # Agregamos el valor del identificador a la lista
    
    for hijo in nodo.hijos:
        parametros.extend(BuscarParametros(hijo))  # Extendemos la lista con los identificadores encontrados en los hijos

    return parametros  # Devolvemos la lista de identificadores encontrados

def buscar_valores_asignacion(nodo):
    # Esta función devolverá la concatenación de los valores de los nodos después de un nodo IGUAL.
    valores = []

    # Verificar si el nodo actual es una asignación
    if nodo.etiqueta == "ASIGNACION":
        igual = buscarNodo(nodo, "IGUAL")  # Buscar el nodo IGUAL en la asignación
        if igual and igual.padre:
            # Encontramos el padre del nodo IGUAL (que es el nodo ASIGNACION)
            padre = igual.padre
            
            # Encontrar los hermanos del nodo IGUAL, que son los nodos después de IGUAL
            index_igual = padre.hijos.index(igual)
            hermanos_despues_igual = padre.hijos[index_igual + 1:]  # Tomamos los nodos después del IGUAL

            # Ahora, buscamos los valores de estos hermanos
            for hermano in hermanos_despues_igual:
                # Obtener los descendientes de cada hermano (es decir, valores dentro de cada nodo hermano)
                valores.extend(obtener_descendientes(hermano))
    
    # Concatenamos los valores encontrados en una sola cadena (sin "@")
    return ''.join([str(valor) for valor in valores if valor is not None and valor != '@'])


def agregarSimbolos(nodo, ambito="Global"):
    if nodo.etiqueta == "FUNCION":
        # Procesamos la función
        valor = buscarValor(nodo)
        parametros = BuscarParametros(buscarNodo(nodo, "PARAMETROS"))
        nombre = buscarNodo(nodo, "IDENTIFICADOR")
        
        # Agregar la función a la tabla de símbolos
        if TablaSimbolos.buscar_simbolo(nombre.valor) is None:
            TablaSimbolos.agregar_simbolo(nombre.valor, "Function", True, parametros, valor, ambito)
        
        # Agregar los parámetros solo en el ámbito de la función
        ambito_funcion = nombre.valor  # Usamos el nombre de la función como ámbito local
        for parametro in parametros:
            if TablaSimbolos.buscar_simbolo(parametro) is None:
                TablaSimbolos.agregar_simbolo(parametro, "Variable", False, None, None, ambito_funcion)
        
        # Procesar las instrucciones dentro de la función
        instrucciones = buscarNodo(nodo, "INSTRUCCIONES")
        if instrucciones:
            for hijo in instrucciones.hijos:
                agregarSimbolos(hijo, ambito_funcion)  # Llamada recursiva dentro del ámbito local

    elif nodo.etiqueta == "ASIGNACION":
        # Si encontramos una asignación, la agregamos como variable global
        identificador = buscarNodo(nodo, "IDENTIFICADOR")
        if identificador:
            # Usamos la función buscar_valores_asignacion para obtener los valores de la asignación
            valor = buscar_valores_asignacion(nodo)
            
            # Si el identificador no está en la tabla de símbolos, lo agregamos
            if TablaSimbolos.buscar_simbolo(identificador.valor) is None:
                TablaSimbolos.agregar_simbolo(identificador.valor, "Variable", False, None, valor, ambito)
            else:
                # Si el identificador ya existe, actualizamos su valor
                simbolo = TablaSimbolos.buscar_simbolo(identificador.valor)
                simbolo.valor = valor

    # Recursión sobre los hijos
    for hijo in nodo.hijos:
        agregarSimbolos(hijo, ambito)  # Llamada recursiva para cada hijo

def imprimirNodos(nodo):
    for hijo in nodo.hijos:
        print(hijo.etiqueta, f" valor: {hijo.valor}")
        imprimirNodos(hijo)

def main():
    nombre_archivo_gramatica = 'Gramatica.txt'
    nombre_archivo_tokens = 'tokens.txt'
    nombre_archivo_no_terminales = 'no_terminales.txt'

    # Cargar gramática, tokens y no terminales desde los archivos
    gramatica = cargar_gramatica(nombre_archivo_gramatica)
    tokens = cargar_tokens(nombre_archivo_tokens)
    no_terminales = cargar_no_terminales(nombre_archivo_no_terminales)
    
    # Obtener el nodo raíz
    raiz = obtener_raiz(gramatica, tokens, no_terminales)

    if raiz:
        print("Raíz del árbol sintáctico:", raiz.etiqueta)
    else:
        print("No se pudo generar el árbol sintáctico")

    # Agregar los símbolos a la tabla
    agregarSimbolos(raiz)

    # Imprimir la tabla de símbolos después de agregar todos los símbolos
    TablaSimbolos.imprimir_tabla()  # Este método ya imprime la tabla de símbolos
    imprimirNodos(raiz)


if __name__ == "__main__":
    main()
