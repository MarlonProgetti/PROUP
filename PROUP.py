import os
import re
import difflib
import threading
import shutil
import pytesseract
from pdf2image import convert_from_path
import customtkinter as ctk
from PyPDF2 import PdfMerger

# -----------------------------
# Configuração global
# -----------------------------
PASTA_BOLETOS = r"C:\Renomeador_Boleto_pdf"
PASTA_NFS = r"C:\Renomeador_NF_pdf"
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
poppler_path = r"C:\poppler\poppler-25.07.0\Library\bin"

# -----------------------------
# Dicionário de CNPJs (único)
# -----------------------------
cnpj_loja = {
    "Colocar os CNPJ": "Colocar o nome da loja"
}

# -----------------------------
# Utilitários compartilhados
# -----------------------------
interromper = {
    "boleto_life": False,
    "boleto_b2": False,
    "nf_life": False,
    "nf_b2": False,
    "unificador": False
}

def normalizar_cnpj(cnpj):
    return re.sub(r'\D', '', cnpj) if cnpj else ""

def obter_nome_loja_por_cnpj(cnpj_normalizado):
    if not cnpj_normalizado:
        return None
    nome_loja = cnpj_loja.get(cnpj_normalizado)
    if not nome_loja:
        zfilled = cnpj_normalizado.zfill(14)
        nome_loja = cnpj_loja.get(zfilled)
    if not nome_loja:
        for chave in cnpj_loja.keys():
            if chave.endswith(cnpj_normalizado) or chave.startswith(cnpj_normalizado):
                return cnpj_loja[chave]
    if not nome_loja:
        poss = difflib.get_close_matches(cnpj_normalizado, cnpj_loja.keys(), n=1, cutoff=0.8)
        if poss:
            nome_loja = cnpj_loja[poss[0]]
    return nome_loja

# -----------------------------
# Programa 1: Boleto LIFE
# -----------------------------
def buscar_cnpjs_boleto_life(texto):
    sem_espaco = re.sub(r'\s+', '', texto)
    return re.findall(r'CNPJ[:\-]*([0-9]{14})', sem_espaco)

def processar_pdf_boleto_life(pdf_path):
    try:
        imagens = convert_from_path(pdf_path, poppler_path=poppler_path, dpi=300)
    except Exception:
        return f"❌ Erro ao converter {os.path.basename(pdf_path)}"

    texto_total = ""
    for img in imagens:
        texto_total += pytesseract.image_to_string(img) + "\n"

    brutos = buscar_cnpjs_boleto_life(texto_total)
    cnpj_normalizado = normalizar_cnpj(brutos[-1]) if brutos else ""
    nome_loja = obter_nome_loja_por_cnpj(cnpj_normalizado) or "Loja_desconhecida"

    base_nome = f"{nome_loja}_zBoleto.pdf"
    novo_caminho = os.path.join(PASTA_BOLETOS, base_nome)

    contador = 1
    nome_sem_ext, ext = os.path.splitext(base_nome)
    while os.path.exists(novo_caminho):
        novo_base = f"{nome_sem_ext}_{contador}{ext}"
        novo_caminho = os.path.join(PASTA_BOLETOS, novo_base)
        contador += 1

    try:
        os.rename(pdf_path, novo_caminho)
        return f"✅ {os.path.basename(pdf_path)} -> {os.path.basename(novo_caminho)}"
    except Exception as e:
        return f"❌ Erro ao renomear {pdf_path}: {e}"

def processar_todos_boleto_life(callback_progresso, callback_fim):
    interromper["boleto_life"] = False
    arquivos = [a for a in os.listdir(PASTA_BOLETOS) if a.lower().endswith(".pdf")]
    total = len(arquivos)
    if not arquivos:
        callback_fim("Nenhum PDF encontrado ❌")
        return
    for i, a in enumerate(arquivos, start=1):
        if interromper["boleto_life"]:
            callback_fim("⛔ Processo cancelado pelo usuário")
            break
        caminho = os.path.join(PASTA_BOLETOS, a)
        resultado = processar_pdf_boleto_life(caminho)
        progresso = i / total
        callback_progresso(progresso, f"{resultado} ({i}/{total})")
    if not interromper["boleto_life"]:
        callback_fim("✅ Finalizado com sucesso")

# -----------------------------
# Programa 2: Boleto B2Click
# -----------------------------
def buscar_cnpjs_boleto_b2(texto):
    return re.findall(r'\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}', texto)

def processar_pdf_boleto_b2(pdf_path):
    try:
        imagens = convert_from_path(pdf_path, poppler_path=poppler_path, dpi=300)
    except Exception:
        return f"❌ Erro ao converter {os.path.basename(pdf_path)}"

    texto_total = ""
    for img in imagens:
        texto_total += pytesseract.image_to_string(img) + "\n"

    brutos = buscar_cnpjs_boleto_b2(texto_total)
    cnpj_normalizado = normalizar_cnpj(brutos[-1]) if brutos else ""
    nome_loja = obter_nome_loja_por_cnpj(cnpj_normalizado) or "Loja_desconhecida"

    base_nome = f"{nome_loja}_zBoleto.pdf"
    novo_caminho = os.path.join(PASTA_BOLETOS, base_nome)

    contador = 1
    nome_sem_ext, ext = os.path.splitext(base_nome)
    while os.path.exists(novo_caminho):
        novo_base = f"{nome_sem_ext}_{contador}{ext}"
        novo_caminho = os.path.join(PASTA_BOLETOS, novo_base)
        contador += 1

    try:
        os.rename(pdf_path, novo_caminho)
        return f"✅ {os.path.basename(pdf_path)} -> {os.path.basename(novo_caminho)}"
    except Exception as e:
        return f"❌ Erro ao renomear {pdf_path}: {e}"

def processar_todos_boleto_b2(callback_progresso, callback_fim):
    interromper["boleto_b2"] = False
    arquivos = [a for a in os.listdir(PASTA_BOLETOS) if a.lower().endswith(".pdf")]
    total = len(arquivos)
    if not arquivos:
        callback_fim("Nenhum PDF encontrado ❌")
        return
    for i, a in enumerate(arquivos, start=1):
        if interromper["boleto_b2"]:
            callback_fim("⛔ Processo cancelado pelo usuário")
            break
        caminho = os.path.join(PASTA_BOLETOS, a)
        resultado = processar_pdf_boleto_b2(caminho)
        progresso = i / total
        callback_progresso(progresso, f"{resultado} ({i}/{total})")
    if not interromper["boleto_b2"]:
        callback_fim("✅ Finalizado com sucesso")

# -----------------------------
# Programa 3: NF LIFE
# -----------------------------
def buscar_cnpjs_nf_life(texto):
    sem_espaco = re.sub(r'\s+', '', texto)
    cnpjs = re.findall(r'([0-9]{2}\.[0-9]{3}\.[0-9]{3}/[0-9]{4}-[0-9]{2})', sem_espaco)
    return cnpjs

def processar_pdf_nf_life(pdf_path):
    try:
        imagens = convert_from_path(pdf_path, poppler_path=poppler_path, dpi=300)
    except Exception:
        return None

    texto_total = ""
    for img in imagens:
        texto_total += pytesseract.image_to_string(img) + "\n"

    brutos = buscar_cnpjs_nf_life(texto_total)
    cnpj_normalizado = normalizar_cnpj(brutos[-1]) if brutos else ""
    nome_loja = obter_nome_loja_por_cnpj(cnpj_normalizado) or "Loja_desconhecida"

    base_nome = f"{nome_loja}_NF.pdf"
    novo_caminho = os.path.join(PASTA_NFS, base_nome)

    contador = 1
    nome_sem_ext, ext = os.path.splitext(base_nome)
    while os.path.exists(novo_caminho):
        novo_base = f"{nome_sem_ext}_{contador}{ext}"
        novo_caminho = os.path.join(PASTA_NFS, novo_base)
        contador += 1

    try:
        os.rename(pdf_path, novo_caminho)
        return f"✅ {os.path.basename(pdf_path)} -> {os.path.basename(novo_caminho)}"
    except Exception as e:
        return f"❌ Erro ao renomear {pdf_path}: {e}"

def processar_todos_nf_life(callback_progresso, callback_fim):
    interromper["nf_life"] = False
    arquivos = [a for a in os.listdir(PASTA_NFS) if a.lower().endswith(".pdf")]
    total = len(arquivos)
    if not arquivos:
        callback_fim("Nenhum PDF encontrado ❌")
        return
    for i, a in enumerate(arquivos, start=1):
        if interromper["nf_life"]:
            callback_fim("⛔ Processo cancelado pelo usuário")
            break
        caminho = os.path.join(PASTA_NFS, a)
        resultado = processar_pdf_nf_life(caminho)
        progresso = i / total
        callback_progresso(progresso, f"{resultado} ({i}/{total})")
    if not interromper["nf_life"]:
        callback_fim("✅ Finalizado com sucesso")

# -----------------------------
# Programa 4: NF B2Click
# -----------------------------
def buscar_cnpjs_nf_b2(texto):
    bloco_match = re.search(r"TOMADOR DOS SERVIC[\s\S]*?LOGRADOURO", texto, flags=re.IGNORECASE)
    if bloco_match:
        bloco = bloco_match.group()
        cnpjs_tomador = re.findall(r'\d[\d\s./-]{13,17}', bloco)
        if cnpjs_tomador:
            return cnpjs_tomador
    return re.findall(r'\d[\d\s./-]{13,17}', texto)

def processar_pdf_nf_b2(pdf_path):
    try:
        imagens = convert_from_path(pdf_path, poppler_path=poppler_path, dpi=300)
    except Exception:
        return None

    texto_total = ""
    for img in imagens:
        texto_total += pytesseract.image_to_string(img) + "\n"

    brutos = buscar_cnpjs_nf_b2(texto_total)
    cnpj_normalizado = normalizar_cnpj(brutos[-1]) if brutos else ""
    nome_loja = obter_nome_loja_por_cnpj(cnpj_normalizado) or "Loja_desconhecida"

    base_nome = f"{nome_loja}_NF.pdf"
    novo_caminho = os.path.join(PASTA_NFS, base_nome)

    contador = 1
    nome_sem_ext, ext = os.path.splitext(base_nome)
    while os.path.exists(novo_caminho):
        novo_base = f"{nome_sem_ext}_{contador}{ext}"
        novo_caminho = os.path.join(PASTA_NFS, novo_base)
        contador += 1

    try:
        os.rename(pdf_path, novo_caminho)
        return f"✅ {os.path.basename(pdf_path)} -> {os.path.basename(novo_caminho)}"
    except Exception as e:
        return f"❌ Erro ao renomear {pdf_path}: {e}"

def processar_todos_nf_b2(callback_progresso, callback_fim):
    interromper["nf_b2"] = False
    arquivos = [a for a in os.listdir(PASTA_NFS) if a.lower().endswith(".pdf")]
    total = len(arquivos)
    if not arquivos:
        callback_fim("Nenhum PDF encontrado ❌")
        return
    for i, a in enumerate(arquivos, start=1):
        if interromper["nf_b2"]:
            callback_fim("⛔ Processo cancelado pelo usuário")
            break
        caminho = os.path.join(PASTA_NFS, a)
        resultado = processar_pdf_nf_b2(caminho)
        progresso = i / total
        callback_progresso(progresso, f"{resultado} ({i}/{total})")
    if not interromper["nf_b2"]:
        callback_fim("✅ Finalizado com sucesso")

# -----------------------------
# Programa 5: Unificador de PDFs
# -----------------------------
def extrair_numero_inicial(nome_arquivo):
    """Extrai o número inicial do nome do arquivo (ex: '141_ABC.pdf' -> 141)."""
    base = os.path.splitext(nome_arquivo)[0]
    m = re.match(r'^\s*([0-9]+)', base)
    if m:
        return int(m.group(1))
    return 10**9  # arquivos sem número vão para o final


def unir_pdfs(pasta_origem, nome_saida="PDF_Unificado.pdf"):
    """Une todos os PDFs da pasta em um único arquivo, ordenando por número inicial."""
    merger = PdfMerger()
    arquivos = [f for f in os.listdir(pasta_origem) if f.lower().endswith(".pdf")]

    if not arquivos:
        return "⚠ Nenhum arquivo PDF encontrado na pasta!"

    # Ordena pelo número inicial no nome
    arquivos.sort(key=lambda f: (extrair_numero_inicial(f), f.lower()))

    for arquivo in arquivos:
        caminho = os.path.join(pasta_origem, arquivo)
        try:
            merger.append(caminho)
        except Exception as e:
            print(f"❌ Erro ao adicionar {arquivo}: {e}")

    saida = os.path.join(pasta_origem, nome_saida)
    merger.write(saida)
    merger.close()

    return f"🎉 PDF final criado com sucesso: {saida}"


def processar_unificador(callback_progresso, callback_fim):
    interromper["unificador"] = False
    pasta_unificador = r"C:\Unificador_pdf"
    resultado = unir_pdfs(pasta_unificador)
    callback_fim(resultado)


# -----------------------------
# Funções de UI: iniciar/stop wrappers que rodam em threads
# -----------------------------
def run_threaded(target, *args):
    """Executa uma função em thread separada para não travar a interface."""
    t = threading.Thread(target=target, args=args, daemon=True)
    t.start()
    return t


# -----------------------------
# Interface principal com CustomTkinter
# -----------------------------
ctk.set_appearance_mode("dark")

app = ctk.CTk()
app.title("PROUP")
app.geometry("585x320")
app.resizable(False, False)

# título
label_titulo = ctk.CTkLabel(app, text="Painel de Controle - PROUP", font=("Arial", 20))
label_titulo.grid(row=0, column=0, columnspan=2, pady=(16, 8))

# Status / barra de progresso
barra = ctk.CTkProgressBar(app, width=420)
barra.set(0)
barra.grid(row=1, column=0, columnspan=2, pady=(4, 12))

label_status = ctk.CTkLabel(app, text="Aguardando ação...", font=("Arial", 12))
label_status.grid(row=2, column=0, columnspan=2, pady=(0, 12))

# Botões: tamanho reduzido, grid conforme pedido
BTN_WIDTH = 140
BTN_HEIGHT = 36

def atualizar_progresso(valor, texto):
    try:
        barra.set(valor)
        label_status.configure(text=texto)
    except Exception:
        pass

def finalizar(mensagem):
    try:
        barra.set(1)
        label_status.configure(text=mensagem)
    except Exception:
        pass

# wrappers que chamam os processadores e atualizam UI
def iniciar_boleto_life():
    def run():
        processar_todos_boleto_life(atualizar_progresso, finalizar)
    run_threaded(run)

def cancelar_boleto_life():
    interromper["boleto_life"] = True

def iniciar_boleto_b2click():
    def run():
        processar_todos_boleto_b2(atualizar_progresso, finalizar)
    run_threaded(run)

def cancelar_boleto_b2click():
    interromper["boleto_b2"] = True

def iniciar_nf_life():
    def run():
        processar_todos_nf_life(atualizar_progresso, finalizar)
    run_threaded(run)

def cancelar_nf_life():
    interromper["nf_life"] = True

def iniciar_nf_b2click():
    def run():
        processar_todos_nf_b2(atualizar_progresso, finalizar)
    run_threaded(run)

def cancelar_nf_b2click():
    interromper["nf_b2"] = True

def iniciar_unificador():
    def run():
        processar_unificador(atualizar_progresso, finalizar)
    run_threaded(run)

# Layout dos botões
btn_boleto_life = ctk.CTkButton(app, text="Boleto LIFE", command=iniciar_boleto_life, width=BTN_WIDTH, height=BTN_HEIGHT)
btn_boleto_life.grid(row=3, column=0, padx=20, pady=6)

btn_nf_life = ctk.CTkButton(app, text="NF LIFE", command=iniciar_nf_life, width=BTN_WIDTH, height=BTN_HEIGHT)
btn_nf_life.grid(row=3, column=1, padx=10, pady=6, sticky="w")

btn_boleto_b2 = ctk.CTkButton(app, text="Boleto B2Click", command=iniciar_boleto_b2click, width=BTN_WIDTH, height=BTN_HEIGHT)
btn_boleto_b2.grid(row=4, column=0, padx=20, pady=6)

btn_nf_b2 = ctk.CTkButton(app, text="NF B2Click", command=iniciar_nf_b2click, width=BTN_WIDTH, height=BTN_HEIGHT)
btn_nf_b2.grid(row=4, column=1, padx=10, pady=6, sticky="w")

btn_unificador = ctk.CTkButton(app, text="Unificador de PDFs", command=iniciar_unificador, width=320, height=BTN_HEIGHT)
btn_unificador.grid(row=5, column=0, columnspan=2, pady=(14, 8))

# Pequenos botões de cancelar (opcionais), alinhados abaixo de cada botão principal
btn_cancel_boleto_life = ctk.CTkButton(app, text="⛔", command=cancelar_boleto_life, fg_color='red', hover_color="#cc0000", width=36, height=28)
btn_cancel_boleto_life.grid(row=3, column=0, sticky="e", padx=(0, 30))

btn_cancel_nf_life = ctk.CTkButton(app, text="⛔", command=cancelar_nf_life, fg_color='red', hover_color="#cc0000", width=36, height=28)
btn_cancel_nf_life.grid(row=3, column=1, sticky="e", padx=(0, 85))

btn_cancel_boleto_b2 = ctk.CTkButton(app, text="⛔", command=cancelar_boleto_b2click, fg_color='red', hover_color="#cc0000", width=36, height=28)
btn_cancel_boleto_b2.grid(row=4, column=0, sticky="e", padx=(0, 30))

btn_cancel_nf_b2 = ctk.CTkButton(app, text="⛔", command=cancelar_nf_b2click, fg_color='red', hover_color="#cc0000", width=36, height=28)
btn_cancel_nf_b2.grid(row=4, column=1, sticky="e", padx=(0, 85))

# Centraliza as colunas
app.grid_columnconfigure(0, weight=1)
app.grid_columnconfigure(1, weight=1)

# Inicializa a UI
if __name__ == "__main__":
    app.mainloop()