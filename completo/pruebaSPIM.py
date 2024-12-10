import ast

class SPIMGenerator(ast.NodeVisitor):
    def __init__(self):
        self.variables = {}
        self.label_count = 0
        self.data_section = []
        self.text_section = []
        self.string_count = 0  # Contador para cadenas
        self.strings = {}  # Mapa de cadenas a etiquetas
        self.registers = [f"$t{i}" for i in range(10)]  # $t0 a $t9
        self.register_pool = self.registers.copy()
    
    def new_label(self, base):
        label = f"{base}_{self.label_count}"
        self.label_count += 1
        return label

    def new_string_label(self):
        label = f"str_{self.string_count}"
        self.string_count += 1
        return label

    def allocate_register(self):
        if not self.register_pool:
            raise RuntimeError("No hay registros disponibles.")
        return self.register_pool.pop(0)

    def free_register(self, reg):
        if reg in self.registers and reg not in self.register_pool:
            self.register_pool.insert(0, reg)

    def generate(self, code):
        tree = ast.parse(code)
        self.visit(tree)
        # Combine data and text sections
        data = "\n".join(self.data_section + list(self.strings.values()))
        text = "\n".join(self.text_section)
        full_code = f".data\n{data}\n\n.text\n.globl main\nmain:\n{text}\n    li $v0, 10\n    syscall"
        return full_code

    def visit_Module(self, node):
        for stmt in node.body:
            self.visit(stmt)

    def visit_Assign(self, node):
        # Asumimos una sola variable por asignación
        var_name = node.targets[0].id
        var_label = f"var_{var_name}"  # Prefijo para evitar colisiones
        if var_name not in self.variables:
            self.variables[var_name] = var_label
            self.data_section.append(f"{var_label}: .word 0")
        # Evaluar la expresión y obtener el registro que contiene el resultado
        result_reg = self.visit(node.value)
        # Almacenar el resultado en la variable
        self.text_section.append(f"    sw {result_reg}, {var_label}")
        # Liberar el registro temporal
        self.free_register(result_reg)

    def visit_Expr(self, node):
        self.visit(node.value)

    def visit_BinOp(self, node):
        # Evaluar el operando izquierdo
        left_reg = self.visit(node.left)
        # Evaluar el operando derecho
        right_reg = self.visit(node.right)
        # Asignar un registro para el resultado
        result_reg = self.allocate_register()
        # Generar la instrucción correspondiente
        if isinstance(node.op, ast.Add):
            self.text_section.append(f"    add {result_reg}, {left_reg}, {right_reg}")
        elif isinstance(node.op, ast.Sub):
            self.text_section.append(f"    sub {result_reg}, {left_reg}, {right_reg}")
        elif isinstance(node.op, ast.Mult):
            self.text_section.append(f"    mul {result_reg}, {left_reg}, {right_reg}")
        elif isinstance(node.op, ast.Div):
            self.text_section.append(f"    div {left_reg}, {right_reg}")
            self.text_section.append(f"    mflo {result_reg}")
        else:
            raise NotImplementedError(f"Operación {type(node.op)} no soportada")
        # Liberar los registros de los operandos
        self.free_register(left_reg)
        self.free_register(right_reg)
        return result_reg

    def visit_Num(self, node):
        reg = self.allocate_register()
        self.text_section.append(f"    li {reg}, {node.n}")
        return reg

    def visit_Name(self, node):
        var_label = f"var_{node.id}"  # Prefijo para evitar colisiones
        if node.id not in self.variables:
            self.variables[node.id] = var_label
            self.data_section.append(f"{var_label}: .word 0")
        reg = self.allocate_register()
        self.text_section.append(f"    lw {reg}, {var_label}")
        return reg

    def visit_If(self, node):
        # Generar etiquetas únicas para este bloque if-else
        label_if_true = self.new_label("if_true")
        label_if_false = self.new_label("if_false")
        label_if_end = self.new_label("if_end")
        
        # Evaluar la condición
        if isinstance(node.test, ast.Compare):
            left_reg = self.visit(node.test.left)
            right_reg = self.visit(node.test.comparators[0])
            op = node.test.ops[0]
            # Generar la comparación y salto condicional
            if isinstance(op, ast.Eq):
                self.text_section.append(f"    beq {left_reg}, {right_reg}, {label_if_true}")
            elif isinstance(op, ast.NotEq):
                self.text_section.append(f"    bne {left_reg}, {right_reg}, {label_if_true}")
            elif isinstance(op, ast.Lt):
                self.text_section.append(f"    blt {left_reg}, {right_reg}, {label_if_true}")
            elif isinstance(op, ast.LtE):
                self.text_section.append(f"    ble {left_reg}, {right_reg}, {label_if_true}")
            elif isinstance(op, ast.Gt):
                self.text_section.append(f"    bgt {left_reg}, {right_reg}, {label_if_true}")
            elif isinstance(op, ast.GtE):
                self.text_section.append(f"    bge {left_reg}, {right_reg}, {label_if_true}")
            else:
                raise NotImplementedError(f"Operador de comparación {type(op)} no soportado")
            self.text_section.append(f"    j {label_if_false}")
            # Bloque if
            self.text_section.append(f"{label_if_true}:")
            for stmt in node.body:
                self.visit(stmt)
            self.text_section.append(f"    j {label_if_end}")
            # Bloque else
            self.text_section.append(f"{label_if_false}:")
            for stmt in node.orelse:
                self.visit(stmt)
            # Fin del if
            self.text_section.append(f"{label_if_end}:")
            # Liberar los registros de la condición
            self.free_register(left_reg)
            self.free_register(right_reg)
        else:
            raise NotImplementedError("Solo se soportan comparaciones en condiciones if")

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id == 'print':
            if len(node.args) != 1:
                raise NotImplementedError("Solo se soporta print con un argumento")
            arg = node.args[0]
            if isinstance(arg, ast.Str):
                # Imprimir cadena
                label = self.get_string_label(arg.s)
                self.text_section.append(f"    la $a0, {label}")
                self.text_section.append("    li $v0, 4")
                self.text_section.append("    syscall")
                # Imprimir nueva línea
                self.text_section.append("    li $a0, 10")
                self.text_section.append("    li $v0, 11")
                self.text_section.append("    syscall")
            elif isinstance(arg, ast.Num):
                # Imprimir entero
                reg = self.visit(arg)
                self.text_section.append(f"    move $a0, {reg}")
                self.text_section.append("    li $v0, 1")
                self.text_section.append("    syscall")
                # Imprimir nueva línea
                self.text_section.append("    li $a0, 10")
                self.text_section.append("    li $v0, 11")
                self.text_section.append("    syscall")
                self.free_register(reg)
            elif isinstance(arg, ast.Name):
                # Imprimir variable
                reg = self.visit(arg)
                self.text_section.append(f"    move $a0, {reg}")
                self.text_section.append("    li $v0, 1")
                self.text_section.append("    syscall")
                # Imprimir nueva línea
                self.text_section.append("    li $a0, 10")
                self.text_section.append("    li $v0, 11")
                self.text_section.append("    syscall")
                self.free_register(reg)
            else:
                raise NotImplementedError("Tipo de argumento en print no soportado")
        else:
            raise NotImplementedError("Solo se soportan llamadas a la función print")

    def get_string_label(self, s):
        if s in self.strings:
            return self.strings[s]
        label = self.new_string_label()
        self.strings[s] = f"{label}: .asciiz \"{s}\""
        return label

# Ejemplo de uso con if-else anidados
if __name__ == "__main__":
    python_code = """
a = 20 + 2
b = 30
c = a + b
print(c)
"""
    generator = SPIMGenerator()
    spim_code = generator.generate(python_code)
    with open("output.asm", "w") as f:
        f.write(spim_code)
    print("Código SPIM generado en 'output.asm'")
