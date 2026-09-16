import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import re
import math

class HalsteadParserApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Анализатор метрик Холстеда (Scala)")
        self.root.geometry("900x600")

        self.keywords = {
            'def', 'var', 'val', 'if', 'while', 'for', 'return', 
            'object', 'class', 'new', 'Int', 'Double', 'String', 'Array', 'Unit'
        }

        self.blacklist = {'else'}
        
        self.symbols = [
            '<=', '>=', '==', '!=', '=>',
            '+', '-', '*', '/', '=', '<', '>', 
            ':', '.', ',', '(', '[', '{'
        ]

        self.setup_ui()

    def setup_ui(self):
        left_frame = tk.Frame(self.root, padx=10, pady=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(left_frame, text="Исходный код (Scala):", font=("Arial", 10, "bold")).pack(anchor="w")
        
        self.text_area = tk.Text(left_frame, wrap=tk.NONE, width=40)
        self.text_area.pack(fill=tk.BOTH, expand=True, pady=5)
        
        btn_frame = tk.Frame(left_frame)
        btn_frame.pack(fill=tk.X)
        
        tk.Button(btn_frame, text="Загрузить файл", command=self.load_file).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Анализировать", command=self.analyze_code).pack(side=tk.RIGHT, padx=5)

        right_frame = tk.Frame(self.root, padx=10, pady=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Label(right_frame, text="Базовые метрики:", font=("Arial", 10, "bold")).pack(anchor="w")

        columns = ("j", "operator", "f1j", "i", "operand", "f2i")
        self.tree = ttk.Treeview(right_frame, columns=columns, show="headings", height=15)
        
        self.tree.heading("j", text="j")
        self.tree.column("j", width=30, anchor="center")
        self.tree.heading("operator", text="Оператор")
        self.tree.column("operator", width=100, anchor="w")
        self.tree.heading("f1j", text="f1j")
        self.tree.column("f1j", width=40, anchor="center")
        
        self.tree.heading("i", text="i")
        self.tree.column("i", width=30, anchor="center")
        self.tree.heading("operand", text="Операнд")
        self.tree.column("operand", width=100, anchor="w")
        self.tree.heading("f2i", text="f2i")
        self.tree.column("f2i", width=40, anchor="center")
        
        self.tree.pack(fill=tk.BOTH, expand=True, pady=5)

        self.metrics_frame = tk.Frame(right_frame, pady=10)
        self.metrics_frame.pack(fill=tk.X)
        
        self.lbl_dict = tk.Label(self.metrics_frame, text="Словарь программы (η): -", font=("Arial", 10))
        self.lbl_dict.pack(anchor="w")
        
        self.lbl_len = tk.Label(self.metrics_frame, text="Длина программы (N): -", font=("Arial", 10))
        self.lbl_len.pack(anchor="w")
        
        self.lbl_vol = tk.Label(self.metrics_frame, text="Объем программы (V): -", font=("Arial", 10, "bold"))
        self.lbl_vol.pack(anchor="w")

    def load_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("Scala Files", "*.scala"), ("Text Files", "*.txt"), ("All Files", "*.*")])
        if filepath:
            with open(filepath, 'r', encoding='utf-8') as file:
                code = file.read()
                self.text_area.delete(1.0, tk.END)
                self.text_area.insert(tk.END, code)

    def analyze_code(self):
        code = self.text_area.get(1.0, tk.END)
        
        code = re.sub(r'//.*', ' ', code)
        code = re.sub(r'/\*.*?\*/', ' ', code, flags=re.DOTALL)

        operators_count = {}
        operands_count = {}

        strings = re.findall(r'"[^"]*"', code)
        for s in strings:
            operands_count[s] = operands_count.get(s, 0) + 1
        code = re.sub(r'"[^"]*"', ' ', code)

        for sym in self.symbols:
            count = code.count(sym)
            if count > 0:
                # Группируем скобки
                display_sym = sym
                if sym == '(': display_sym = '( )'
                elif sym == '[': display_sym = '[ ]'
                elif sym == '{': display_sym = '{ }'
                
                operators_count[display_sym] = operators_count.get(display_sym, 0) + count
                code = code.replace(sym, ' ')
        
        code = re.sub(r'[)\]}]', ' ', code)

        tokens = re.findall(r'\b\w+(?:\.\w+)?\b', code)
        
        for token in tokens:
            if not token in self.blacklist:
                if re.match(r'^\d+(\.\d+)?$', token):
                    operands_count[token] = operands_count.get(token, 0) + 1
                elif token in self.keywords:
                    operators_count[token] = operators_count.get(token, 0) + 1
                else:
                    operands_count[token] = operands_count.get(token, 0) + 1

        self.update_results(operators_count, operands_count)

    def update_results(self, opers, opnds):
        for item in self.tree.get_children():
            self.tree.delete(item)

        sorted_opers = sorted(opers.items(), key=lambda x: x[1], reverse=True)
        sorted_opnds = sorted(opnds.items(), key=lambda x: x[1], reverse=True)

        eta1 = len(sorted_opers)
        N1 = sum(count for _, count in sorted_opers)
        
        eta2 = len(sorted_opnds)
        N2 = sum(count for _, count in sorted_opnds)

        max_len = max(eta1, eta2)
        for idx in range(max_len):
            row = []
            # Операторы
            if idx < eta1:
                row.extend([idx + 1, sorted_opers[idx][0], sorted_opers[idx][1]])
            else:
                row.extend(["", "", ""])
            
            # Операнды
            if idx < eta2:
                row.extend([idx + 1, sorted_opnds[idx][0], sorted_opnds[idx][1]])
            else:
                row.extend(["", "", ""])
                
            self.tree.insert("", tk.END, values=row)

        self.tree.insert("", tk.END, values=("η1 =", eta1, f"N1 = {N1}", "η2 =", eta2, f"N2 = {N2}"))

        eta = eta1 + eta2
        N = N1 + N2
        V = N * math.log2(eta) if eta > 0 else 0

        self.lbl_dict.config(text=f"Словарь программы (η = η1 + η2): {eta}")
        self.lbl_len.config(text=f"Длина программы (N = N1 + N2): {N}")
        self.lbl_vol.config(text=f"Объем программы (V = N * log2(η)): {V:.2f} бит")

if __name__ == "__main__":
    root = tk.Tk()
    app = HalsteadParserApp(root)
    root.mainloop()