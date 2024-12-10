import csv
import re

EPSILON = "''"

class LLParser:
    def __init__(self, grammar_file, tokens_file):
        self.alphabet = []
        self.nonterminals = []
        self.terminals = []
        self.rules = []
        self.tokens = []
        self.rule_table = {}

        self._load_grammar(grammar_file)
        self._load_tokens(tokens_file)
        self._collect_alphabet_and_symbols()
        self._load_rule_table()

    def _load_grammar(self, grammar_file):
        with open(grammar_file, 'r') as f:
            self.rules = [line.strip() for line in f if '->' in line]

    def _load_tokens(self, tokens_file):
        with open(tokens_file, 'r') as f:
            tokens = f.read().strip().split()
            # Guardar el tipo y valor de cada token en una tupla
            self.tokens = [(token.split(':')[0], token.split(':')[1]) for token in tokens]

    def _collect_alphabet_and_symbols(self):
        for rule in self.rules:
            lhs, rhs = rule.split('->')
            nonterminal = lhs.strip()
            development = rhs.strip().split()

            if nonterminal not in self.nonterminals:
                self.nonterminals.append(nonterminal)

            for symbol in development:
                if symbol != EPSILON:
                    if symbol not in self.alphabet:
                        self.alphabet.append(symbol)

        self.terminals = [symbol for symbol in self.alphabet if symbol not in self.nonterminals]

    def _load_rule_table(self):
        # Load the rule table from an external CSV file
        with open('ll1_table.csv', mode='r') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                nonterminal = row['Nonterminal']
                self.rule_table[nonterminal] = {}
                for terminal, rule in row.items():
                    if terminal != 'Nonterminal' and rule:
                        self.rule_table[nonterminal][terminal] = rule

    def parse_input(self):
        stack = ['$', self.nonterminals[0]]
        index = 0
        input_tokens = self.tokens + [('$', '$')]

        rows = []
        while len(stack) > 0:
            top = stack.pop()
            current_token_type, current_token_value = input_tokens[index]
            rule = self.rule_table.get(top, {}).get(current_token_type) if top in self.nonterminals else ""

            if top == current_token_type:
                # Consumir el token y avanzar
                index += 1
            elif top in self.terminals or top == '$':
                if top == current_token_type:
                    index += 1
                else:
                    rows.append(["Error: terminal mismatch."])
                    break
            elif top in self.nonterminals:
                if rule is None:
                    rows.append([f"Error: no rule for nonterminal '{top}' with token '{current_token_type}'"])
                    break
                _, rhs = rule.split('->')
                symbols = rhs.strip().split()
                if symbols != [EPSILON]:
                    stack.extend(reversed(symbols))
            else:
                rows.append(["Error: unknown symbol on stack."])
                break

            # Guardar el proceso en el rastreo, incluyendo el valor del token solo en la entrada
            rows.append([
                " ".join(stack),
                " ".join([f"{tok[0]}:{tok[1]}" for tok in input_tokens[index:]]),
                f"{top} -> {rhs.strip()}" if rule else "Accept" if top == '$' and current_token_type == '$' else ""
            ])

        self._export_parsing_process_to_csv("rastreo.csv", rows)

    def _export_parsing_process_to_csv(self, csv_filename, rows):
        with open(csv_filename, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            header = ["Stack", "Input", "Rule"]
            csv_writer.writerow(header)
            for row in rows:
                csv_writer.writerow(row)

if __name__ == "__main__":
    parser = LLParser("Gramatica.txt", "tokens.txt")
    parser.parse_input()