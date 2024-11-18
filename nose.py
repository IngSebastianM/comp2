import re
import ast
import matplotlib.pyplot as plt
import networkx as nx
from collections import defaultdict
import tkinter as tk
from tkinter import messagebox, scrolledtext

# Definición de los tokens
TOKENS = [
    ("CLAVES", r'\b(if|else|while|for|return|break|continue|def|class|print|int|float|input)\b'),
    ("IDENTIFICADORES", r'\b[a-zA-Z_]\w*\b'),
    ("NUMEROS", r'\b\d+(\.\d+)?\b'),
    ("OPERADORES", r'[+\-*/%=<>!&|^~]'),
    ("STRING", r'"[^"\\](\\.[^"\\])*"'),
    ("SALTOS_DE_LINEA", r'\n'),
    ("ESPACIOS", r'[ \t]+'),
    ("COMENTARIOS", r'#.*'),
    ("DELIMITADORES", r'[(){}[\],.;:]'),
]

def tokenize(code):
    tokens = defaultdict(list)
    position = 0

    while position < len(code):
        match = None
        for token_type, token_regex in TOKENS:
            regex = re.compile(token_regex)
            match = regex.match(code, position)
            if match:
                tokens[token_type].append(match.group(0))
                position = match.end(0)
                break

        if not match:
            print(f"Error: Token desconocido en la posición {position}")
            break

    return tokens

class CodeGenerator:
    def __init__(self):
        self.code = []
        self.temp_counter = 0
        self.machine_code = []
        self.variables = {}

    def generate_code(self, node):
        if isinstance(node, ast.Module):
            for stmt in node.body:
                self.generate_code(stmt)

        elif isinstance(node, ast.Assign):  # Asignaciones
            target = node.targets[0].id
            value = self.generate_code(node.value)
            self.code.append(f"{target} = {value}")
            self.variables[target] = value  # Guardar el valor de la variable

        elif isinstance(node, ast.BinOp):  # Operaciones binarias
            left = self.generate_code(node.left)
            right = self.generate_code(node.right)
            op = self.get_operator_symbol(node.op)
            temp_var = self.new_temp()
            self.code.append(f"{temp_var} = {left} {op} {right}")
            return temp_var

        elif isinstance(node, ast.Name):  # Variables
            return node.id

        elif isinstance(node, ast.Constant):  # Constantes
            return str(node.value)

        elif isinstance(node, ast.Expr):  # Expresiones
            return self.generate_code(node.value)

        elif isinstance(node, ast.Call):  # Llamadas a funciones
            func_name = node.func.id
            args = [self.generate_code(arg) for arg in node.args]
            temp_var = self.new_temp()
            self.code.append(f"{temp_var} = {func_name}({', '.join(args)})")
            return temp_var

        elif isinstance(node, ast.FunctionDef):  # Definición de funciones
            func_name = node.name
            args = [arg.arg for arg in node.args.args]
            self.code.append(f"FUNC {func_name}({', '.join(args)})")
            for stmt in node.body:
                self.generate_code(stmt)
            self.code.append(f"END_FUNC {func_name}")

        elif isinstance(node, ast.If):  # Estructuras condicionales
            test = self.generate_code(node.test)
            self.code.append(f"IF {test} THEN")
            for stmt in node.body:
                self.generate_code(stmt)
            if node.orelse:
                self.code.append("ELSE")
                for stmt in node.orelse:
                    self.generate_code(stmt)
            self.code.append("END_IF")

        elif isinstance(node, ast.While):  # Ciclos While
            test = self.generate_code(node.test)
            self.code.append(f"WHILE {test} DO")
            for stmt in node.body:
                self.generate_code(stmt)
            self.code.append("END_WHILE")

        elif isinstance(node, ast.For):  # Ciclos For
            target = self.generate_code(node.target)
            iter_ = self.generate_code(node.iter)
            self.code.append(f"FOR {target} IN {iter_} DO")
            for stmt in node.body:
                self.generate_code(stmt)
            self.code.append("END_FOR")

    def get_operator_symbol(self, operator):
        operator_mapping = {
            ast.Add: '+',
            ast.Sub: '-',
            ast.Mult: '*',
            ast.Div: '/',
            ast.Mod: '%',
            ast.Pow: '**'
        }
        return operator_mapping.get(type(operator), '')

    def new_temp(self):
        self.temp_counter += 1
        return f"t{self.temp_counter}"

    def translate_to_machine_code(self):
        """Convierte el código intermedio a código máquina simulado"""
        for instruction in self.code:
            if "=" in instruction:
                target, expression = instruction.split("=", 1)
                target = target.strip()
                expression = expression.strip()
                self.machine_code.append(f"LOAD {expression}")
                self.machine_code.append(f"STORE {target}")
            elif instruction.startswith("FUNC"):
                self.machine_code.append(instruction.replace("FUNC", "DEF"))
            elif instruction.startswith("END_FUNC"):
                self.machine_code.append(instruction.replace("END_FUNC", "RET"))
            elif instruction.startswith("IF"):
                self.machine_code.append(instruction.replace("IF", "CMP"))
            elif instruction.startswith("WHILE"):
                self.machine_code.append(instruction.replace("WHILE", "LOOP_START"))
            elif instruction.startswith("END_WHILE"):
                self.machine_code.append("LOOP_END")
            elif instruction.startswith("FOR"):
                self.machine_code.append(instruction.replace("FOR", "ITER_START"))
            elif instruction.startswith("END_FOR"):
                self.machine_code.append("ITER_END")
            else:
                self.machine_code.append(f"EXEC {instruction}")

        return self.machine_code

    def execute_code(self):
        """Simula la ejecución del código con las variables definidas"""
        final_output = []
        for instruction in self.code:
            if "=" in instruction:
                target, value = instruction.split("=", 1)
                target = target.strip()
                value = value.strip()
                self.variables[target] = self.eval_expression(value)
            elif instruction.startswith("IF"):
                # Aquí puedes agregar lógica para simular ejecución de condicionales
                pass
            elif instruction.startswith("FOR") or instruction.startswith("WHILE"):
                # Agregar lógica de ejecución de ciclos
                pass
            final_output.append(f"Variables: {self.variables}")

        # Mostrar solo el resultado final después de la ejecución
        final_output.append(f"Resultado final de la ejecución: {self.variables}")
        return final_output

    def eval_expression(self, expression):
        """Evaluar la expresión en el código intermedio"""
        # Esta función debería manejar las operaciones y devolver el resultado
        try:
            return eval(expression, {}, self.variables)
        except Exception as e:
            return f"Error al evaluar: {e}"



class SyntaxTreeVisualizer:
    def __init__(self, clear_texts_callback):
        self.clear_texts_callback = clear_texts_callback

    def analyze_syntax(self, code):
        try:
            tree = ast.parse(code)
            messagebox.showinfo("Análisis Sintáctico", "El análisis sintáctico fue exitoso.")
            self.visualize_ast(tree, code)
        except SyntaxError as e:
            messagebox.showerror("Error de Sintaxis", f"Error de sintaxis: {e}")

    def visualize_ast(self, tree, code):
        G = nx.DiGraph()
        node_counter = defaultdict(int)

        def add_edges(node, parent_name=None):
            node_label = self.get_node_label(node, code)
            if node_label:
                node_counter[node_label] += 1
                unique_node_name = f"{node_label}_{node_counter[node_label]}"
                G.add_node(unique_node_name, label=node_label)
            else:
                unique_node_name = parent_name

            if parent_name and unique_node_name != parent_name:
                G.add_edge(parent_name, unique_node_name)

            for child in ast.iter_child_nodes(node):
                add_edges(child, unique_node_name)

        add_edges(tree)

        pos = self.hierarchical_layout(G, list(G.nodes)[0])
        labels = nx.get_node_attributes(G, 'label')

        plt.figure(figsize=(12, 8))
        nx.draw(G, pos, labels=labels, with_labels=True, node_size=2000,
                node_color='lightblue', font_size=10, font_weight='bold', edge_color='gray', arrows=True)
        plt.title("Árbol Sintáctico (AST)")
        plt.gcf().canvas.mpl_connect("close_event", lambda event: self.clear_texts_callback())
        plt.show()

    def get_node_label(self, node, code):
        if isinstance(node, ast.Constant):
            return str(node.value)
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.BinOp):
            return self.get_operator_symbol(node.op)
        return ""

    def get_operator_symbol(self, operator):
        operator_mapping = {
            ast.Add: '+',
            ast.Sub: '-',
            ast.Mult: '*',
            ast.Div: '/',
            ast.Mod: '%',
            ast.Pow: '**'
        }
        return operator_mapping.get(type(operator), '')

    def hierarchical_layout(self, G, root):
        pos = nx.spring_layout(G)
        pos[root] = (0, 0)
        return pos


# Interfaz gráfica
def run_code():
    input_code = code_input.get("1.0", tk.END).strip()
    if not input_code:
        messagebox.showerror("Error", "Por favor ingrese código para analizar.")
        return

    tokenizer = tokenize(input_code)
    code_generator = CodeGenerator()
    syntax_tree_visualizer = SyntaxTreeVisualizer(clear_texts)
    syntax_tree_visualizer.analyze_syntax(input_code)


def clear_texts():
    code_input.delete('1.0', tk.END)
    machine_output_text.delete('1.0', tk.END)


# Interfaz de usuario
root = tk.Tk()
root.title("Simulador de Compilador")
root.geometry("600x500")

# Entradas de código
code_input_label = tk.Label(root, text="Ingrese el código:")
code_input_label.pack(pady=5)

code_input = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=15)
code_input.pack(pady=5)

# Botones
run_button = tk.Button(root, text="Ejecutar", command=run_code)
run_button.pack(pady=5)

clear_button = tk.Button(root, text="Limpiar", command=clear_texts)
clear_button.pack(pady=5)

# Salida de la máquina
machine_output_label = tk.Label(root, text="Salida de la máquina:")
machine_output_label.pack(pady=5)

machine_output_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=10)
machine_output_text.pack(pady=5)

root.mainloop()
