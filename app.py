import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import re
import datetime
from io import BytesIO

st.set_page_config(page_title="Gerador de Planilha de Produtos", layout="centered")

st.title("🧾 Gerador de Planilha de Produtos (PDF → Excel)")

# === Funções ===

def extrair_texto_pdf(uploaded_file):
    texto_total = ""
    with fitz.open(stream=uploaded_file.read(), filetype="pdf") as pdf:
        for pagina in pdf:
            texto_total += pagina.get_text()
    return texto_total

def extrair_produtos(texto):
    """
    Extrai produtos dos relatórios ABC do Shopping do Pão
    Formato das linhas: 
    CLASSIF CODIGO NOME_PRODUTO CUSTO QUANTIDADE VALOR_TOTAL [outros dados...]
    """
    # Padrão para capturar os dados principais
    padrao = r"^(\d+)\s+(\d+)\s+([A-Z0-9\s\[\]/\-\.]{10,}?)\s+([\d,\.]+)\s+([\d,\.]+)\s+([\d\.]+,\d{2})"

    produtos = []
    linhas = texto.split('\n')

    for linha in linhas:
        # Busca apenas linhas que começam com número (classificação)
        match = re.match(padrao, linha.strip())
        if match:
            classificacao = match.group(1)
            codigo = match.group(2)
            nome = match.group(3).strip()
            custo = match.group(4)
            quantidade = float(match.group(5).replace(",", "."))
            valor_total = float(match.group(6).replace(",", "."))

            # Apenas o nome do produto (sem código)
            produtos.append((nome, quantidade, valor_total))

    return produtos

def gerar_excel(produtos, setor, mes, semana):
    df = pd.DataFrame(produtos, columns=["Produto", "Quantidade", "Valor"])
    df["Setor"] = setor
    df["Mês"] = mes
    df["Semana"] = semana
    df = df[["Produto", "Setor", "Mês", "Semana", "Quantidade", "Valor"]]
    output = BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)
    return output

# === Upload PDF ===
uploaded_pdf = st.file_uploader("📎 Envie o PDF da venda/perda", type="pdf")

if uploaded_pdf:
    texto_extraido = extrair_texto_pdf(uploaded_pdf)
    produtos_encontrados = extrair_produtos(texto_extraido)

    if produtos_encontrados:
        st.success(f"{len(produtos_encontrados)} produtos encontrados no PDF.")
        nomes_produtos = [p[0] for p in produtos_encontrados]

        # Seletor de produtos
        produtos_selecionados = st.multiselect(
            "Selecione os produtos que deseja incluir:",
            options=nomes_produtos,
            default=nomes_produtos
        )

        # Informações manuais
        col1, col2, col3 = st.columns(3)
        with col1:
            setor = st.selectbox("Setor", [
                "Padaria", 
                "Confeitaria Fina", 
                "Confeitaria Trad", 
                "Salgados",
                "Lanchonete",
                "Restaurante",
                "Frios"
            ])
        with col2:
            mes = st.selectbox("Mês", ["Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"])
        with col3:
            semana = st.selectbox("Semana", ["1", "2", "3", "4"])

        if st.button("📤 Gerar Planilha Excel"):
            produtos_filtrados = [p for p in produtos_encontrados if p[0] in produtos_selecionados]
            planilha = gerar_excel(produtos_filtrados, setor, mes, semana)
            st.download_button(
                label="📥 Baixar Planilha Excel",
                data=planilha,
                file_name="planilha_produtos.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.warning("Nenhum produto encontrado no PDF.")
