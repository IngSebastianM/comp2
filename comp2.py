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
    def __init__(self):  # Agregado el método constructor
        self.code = []
        self.temp_counter = 0  # Inicialización de temp_counter

    def generate_code(self, node):
        if isinstance(node, ast.Module):
            for stmt in node.body:
                self.generate_code(stmt)

        elif isinstance(node, ast.Assign):
            target = node.targets[0].id
            value = self.generate_code(node.value)
            self.code.append(f"{target} = {value}")

        elif isinstance(node, ast.BinOp):
            left = self.generate_code(node.left)
            right = self.generate_code(node.right)
            op = self.get_operator_symbol(node.op)
            temp_var = self.new_temp()
            self.code.append(f"{temp_var} = {left} {op} {right}")
            return temp_var

        elif isinstance(node, ast.Name):
            return node.id

        elif isinstance(node, ast.Constant):
            return str(node.value)

        elif isinstance(node, ast.Expr):
            return self.generate_code(node.value)

        elif isinstance(node, ast.Call):
            func_name = node.func.id
            args = [self.generate_code(arg) for arg in node.args]
            temp_var = self.new_temp()
            self.code.append(f"{temp_var} = {func_name}({', '.join(args)})")
            return temp_var

    def get_operator_symbol(self, operator):
        operator_mapping = {
            ast.Add: '+',
            ast.Sub: '-',
            ast.Mult: '*',
            ast.Div: '/',
            ast.Mod: '%',
            ast.Pow: '**'  # Agregado símbolo para la operación de potenciación
        }
        return operator_mapping.get(type(operator), '')

    def new_temp(self):
        self.temp_counter += 1
        return f"t{self.temp_counter}"

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
            ast.Mod: '%'
        }
        return operator_mapping.get(type(operator), '')

    def hierarchical_layout(self, G, root, width=1., vert_gap=0.2, vert_loc=0, xcenter=0.5):
        pos = self._hierarchical_pos(G, root, width, vert_gap, vert_loc, xcenter)
        return pos

    def _hierarchical_pos(self, G, root=None, width=1., vert_gap=0.2, vert_loc=0, xcenter=0.5, pos=None, parent=None, parsed=[]):
        if pos is None:
            pos = {root: (xcenter, vert_loc)}
        else:
            pos[root] = (xcenter, vert_loc)

        children = list(G.successors(root))
        if not children:
            return pos

        dx = width / len(children)
        nextx = xcenter - width/2 - dx/2

        for child in children:
            nextx += dx
            pos = self._hierarchical_pos(G, child, width=dx, vert_gap=vert_gap,
                                         vert_loc=vert_loc-vert_gap, xcenter=nextx, pos=pos,
                                         parent=root, parsed=parsed)

        return pos

def main():
    def analyze_tokens():
        codigo_fuente = text_area.get("1.0", tk.END).strip()
        if codigo_fuente:
            tokens = tokenize(codigo_fuente)
            result = "\nTokens identificados agrupados por categoría:\n"
            for token_type, token_values in tokens.items():
                result += f"{token_type}: {', '.join(token_values)}\n"
            text_output.delete("1.0", tk.END)
            text_output.insert(tk.END, result)
        else:
            messagebox.showwarning("Advertencia", "Ingrese el código fuente antes de analizar.")

    def analyze_syntax():
        codigo_fuente = text_area.get("1.0", tk.END).strip()
        if codigo_fuente:
            visualizer = SyntaxTreeVisualizer(clear_texts)
            visualizer.analyze_syntax(codigo_fuente)
        else:
            messagebox.showwarning("Advertencia", "Ingrese el código fuente antes de analizar.")

    def generate_final_code():
        codigo_fuente = text_area.get("1.0", tk.END).strip()
        if codigo_fuente:
            try:
                tree = ast.parse(codigo_fuente)
                code_gen = CodeGenerator()
                code_gen.generate_code(tree)
                final_code = "\n".join(code_gen.code)
                text_output.insert(tk.END, "\n\nCódigo generado en tres direcciones:\n" + final_code)
            except SyntaxError as e:
                messagebox.showerror("Error de Sintaxis", f"Error de sintaxis: {e}")
        else:
            messagebox.showwarning("Advertencia", "Ingrese el código fuente antes de generar el código final.")

    def clear_texts():
        text_area.delete("1.0", tk.END)
        text_output.delete("1.0", tk.END)

    window = tk.Tk()
    window.title("Analizador Sintáctico")
    window.geometry("800x600")
    window.configure(bg="#ADD8E6")

    label = tk.Label(window, text="Bienvenido al Analizador de Código", font=("Times New Roman", 14), bg="#ADD8E6", fg="darkblue")
    label.pack(pady=10)

    label_input = tk.Label(window, text="Ingrese el código fuente:", bg="#ADD8E6", font=("Times New Roman", 12), fg="black")
    label_input.pack()
    text_area = scrolledtext.ScrolledText(window, wrap=tk.WORD, width=70, height=5, bg="lightgrey", fg="black")
    text_area.pack(pady=10)

    analyze_tokens_button = tk.Button(window, text="Analizar Tokens", command=analyze_tokens, bg="darkblue", fg="white", width=20)
    analyze_tokens_button.pack()

    analyze_syntax_button = tk.Button(window, text="Analizar Sintaxis", command=analyze_syntax, bg="darkblue", fg="white", width=20)
    analyze_syntax_button.pack(pady=10)

    generate_code_button = tk.Button(window, text="Generar Código Final", command=generate_final_code, bg="darkblue", fg="white", width=20)
    generate_code_button.pack()

    clear_button = tk.Button(window, text="Limpiar", command=clear_texts, bg="darkred", fg="white", width=20)
    clear_button.pack(pady=10)

    text_output = scrolledtext.ScrolledText(window, wrap=tk.WORD, width=70, height=10, bg="lightgrey", fg="black")
    text_output.pack(pady=10)

    window.mainloop()
    
if __name__ == "__main__":
    main()