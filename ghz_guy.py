# ghz_gui.py
import customtkinter as ctk
from tkinter import filedialog, messagebox
from ghz_core import gerar_hosts

# Configurações visuais
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Janela principal
app = ctk.CTk()
app.title("GHZ - Gerador de Hosts Zabbix")
app.geometry("520x360")

modo = ctk.StringVar(value="site")

# ===== Funções =====
def selecionar_planilha():
    arquivo = filedialog.askopenfilename(
        filetypes=[("Planilhas Excel", "*.xlsx")]
    )
    entrada.delete(0, "end")
    entrada.insert(0, arquivo)

def executar():
    fonte = entrada.get().strip()
    if not fonte:
        messagebox.showerror("Erro", "Informe a URL ou planilha")
        return

    # Pergunta onde salvar o YAML
    salvar_em = filedialog.asksaveasfilename(
        defaultextension=".yaml",
        filetypes=[("Arquivos YAML", "*.yaml")],
        title="Salvar arquivo YAML como"
    )
    if not salvar_em:  # Usuário cancelou
        return

    try:
        nome = gerar_hosts(modo.get(), fonte, caminho_saida=salvar_em)
        messagebox.showinfo("Sucesso", f"YAML gerado:\n{nome}")
    except Exception as e:
        messagebox.showerror("Erro", str(e))

# ===== UI =====
ctk.CTkLabel(app, text="GHZ", font=("Segoe UI", 28, "bold")).pack(pady=10)

frame = ctk.CTkFrame(app)
frame.pack(pady=10, padx=20, fill="x")

ctk.CTkRadioButton(frame, text="Site (CityCam)", variable=modo, value="site").pack(anchor="w", pady=5)
ctk.CTkRadioButton(frame, text="Planilha DVR", variable=modo, value="planilha").pack(anchor="w", pady=5)

entrada = ctk.CTkEntry(app, placeholder_text="URL do site ou planilha .xlsx")
entrada.pack(padx=20, fill="x")

ctk.CTkButton(app, text="Selecionar Planilha", command=selecionar_planilha).pack(pady=5)
ctk.CTkButton(app, text="Gerar Hosts", command=executar).pack(pady=20)

app.mainloop()
