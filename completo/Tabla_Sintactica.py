import csv
import os

# Definir el simbolo EPSILON, que representa una produccion vacia
epsilon = "''"

# Leer la gramatica desde un archivo y almacenar las reglas en una lista
def read_grammar(file_path):
    rules = []
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line:
                rules.append(line)
    return rules

# Recopilar el alfabeto, los no terminales y los terminales de la gramatica
def collect_alphabet_and_nonterminals(rules):
    alphabet = set()
    nonterminals = set()
    for rule in rules:
        left, right = rule.split('->')
        nonterminal = left.strip()
        nonterminals.add(nonterminal)
        symbols = right.strip().split()
        alphabet.update(symbols)
    terminals = alphabet - nonterminals
    return list(alphabet), list(nonterminals), list(terminals)

# Calcular los conjuntos FIRST para cada no terminal
def collect_firsts(rules, nonterminals, terminals):
    firsts = {nt: set() for nt in nonterminals}
    not_done = True
    while not_done:
        not_done = False
        for rule in rules:
            left, right = rule.split('->')
            nonterminal = left.strip()
            symbols = right.strip().split()
            if symbols[0] == epsilon:
                not_done |= epsilon not in firsts[nonterminal]
                firsts[nonterminal].add(epsilon)
            else:
                for symbol in symbols:
                    if symbol in terminals or symbol == epsilon:
                        not_done |= symbol not in firsts[nonterminal]
                        firsts[nonterminal].add(symbol)
                        break
                    else:
                        old_size = len(firsts[nonterminal])
                        firsts[nonterminal].update(firsts[symbol] - {epsilon})
                        not_done |= len(firsts[nonterminal]) > old_size
                        if epsilon not in firsts[symbol]:
                            break
    return firsts

# Calcular los conjuntos FOLLOW para cada no terminal
def collect_follows(rules, nonterminals, firsts):
    follows = {nt: set() for nt in nonterminals}
    # Agregar el simbolo de fin de cadena ('$') al conjunto FOLLOW del simbolo inicial
    follows[rules[0].split('->')[0].strip()].add('$')
    not_done = True
    while not_done:
        not_done = False
        for rule in rules:
            left, right = rule.split('->')
            nonterminal = left.strip()
            symbols = right.strip().split()
            for i, symbol in enumerate(symbols):
                if symbol in nonterminals:
                    follows_set = follows[symbol]
                    if i + 1 < len(symbols):
                        next_symbol = symbols[i + 1]
                        if next_symbol in nonterminals:
                            follows_set.update(firsts[next_symbol] - {epsilon})
                        else:
                            follows_set.add(next_symbol)
                    # Si es el ultimo simbolo o tiene epsilon en su FIRST, agregar FOLLOW del no terminal
                    if i + 1 == len(symbols) or epsilon in firsts.get(next_symbol, []):
                        old_size = len(follows_set)
                        follows_set.update(follows[nonterminal])
                        not_done |= len(follows_set) > old_size
    return follows

# Generar la tabla de analisis sintactico LL(1)
def make_rule_table(rules, nonterminals, terminals, firsts, follows):
    rule_table = {nt: {t: '' for t in terminals + ['$']} for nt in nonterminals}
    for rule in rules:
        left, right = rule.split('->')
        nonterminal = left.strip()
        symbols = right.strip().split()
        development_firsts = collect_firsts_for_development(symbols, firsts, terminals)
        for symbol in development_firsts:
            if symbol != epsilon:
                rule_table[nonterminal][symbol] = f"{nonterminal} -> {right.strip()}"
        # Agregar la produccion a los FOLLOW si epsilon esta en FIRST
        if epsilon in development_firsts:
            for follow_symbol in follows[nonterminal]:
                rule_table[nonterminal][follow_symbol] = f"{nonterminal} -> {right.strip()}"
    return rule_table

# Calcular el conjunto FIRST para una secuencia de simbolos (produccion)
def collect_firsts_for_development(development, firsts, terminals):
    result = set()
    for symbol in development:
        if symbol in terminals:
            result.add(symbol)
            break
        result.update(firsts[symbol] - {epsilon})
        if epsilon not in firsts[symbol]:
            break
    else:
        result.add(epsilon)
    return result

# Escribir la tabla de analisis en un archivo CSV
def write_csv(rule_table, output_file):
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        header = ['Nonterminal'] + list(rule_table[next(iter(rule_table))].keys())
        writer.writerow(header)
        for nonterminal, rules in rule_table.items():
            row = [nonterminal] + [rules[terminal] for terminal in header[1:]]
            writer.writerow(row)

# Escribir los no terminales en un archivo de texto
def write_nonterminals(nonterminals, output_file):
    with open(output_file, 'w') as file:
        for nonterminal in nonterminals:
            file.write(nonterminal + '\n')

# Funcion principal para ejecutar el programa
def main():
    grammar_file = 'Gramatica.txt'  # Nombre del archivo con la gramática
    output_file = 'll1_table.csv'  # Nombre del archivo de salida CSV
    nonterminals_file = 'no_terminales.txt'  # Nombre del archivo de salida para no terminales

    # Verificar si el archivo de gramatica existe
    if not os.path.exists(grammar_file):
        print(f"Error: El archivo {grammar_file} no existe.")
        return

    # Leer la gramatica y calcular los conjuntos FIRST y FOLLOW
    rules = read_grammar(grammar_file)
    alphabet, nonterminals, terminals = collect_alphabet_and_nonterminals(rules)
    firsts = collect_firsts(rules, nonterminals, terminals)
    follows = collect_follows(rules, nonterminals, firsts)
    # Generar la tabla LL(1) y escribirla en un archivo CSV
    rule_table = make_rule_table(rules, nonterminals, terminals, firsts, follows)
    write_csv(rule_table, output_file)
    # Escribir los no terminales en un archivo de texto
    write_nonterminals(nonterminals, nonterminals_file)
    print(f"Tabla LL(1) generada y guardada en {output_file}")
    print(f"No terminales guardados en {nonterminals_file}")

if __name__ == '__main__':
    main()
