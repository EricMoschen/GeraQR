import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

st.set_page_config(page_title="Gerador de Etiquetas", layout="wide")

st.title("📦 Gerador de Etiquetas com QRCode")
st.write("Envie uma planilha com as colunas: **Código, Descrição, Unid**")

uploaded_file = st.file_uploader("Envie sua planilha Excel (.xlsx)", type=["xlsx"])

# ---------- FUNÇÕES ----------
def gerar_qr(texto):
    qr = qrcode.QRCode(box_size=4, border=1)
    qr.add_data(texto)
    qr.make(fit=True)
    return qr.make_image()

def gerar_etiqueta(descricao, unid, codigo):
    largura, altura = 400, 120
    imagem = Image.new("RGB", (largura, altura), "white")
    draw = ImageDraw.Draw(imagem)

    try:
        font_text = ImageFont.truetype("arial.ttf", 16)
    except:
        font_text = None  # fallback padrão

    texto_qr = f"{codigo};{descricao};{unid}"
    qr = gerar_qr(texto_qr).convert("RGB")

    imagem.paste(qr, (5, 5))

    draw.text((110, 10), f"Descrição:  {descricao}", fill="black", font=font_text)
    draw.text((110, 45), f"Unid:       {unid}", fill="black", font=font_text)
    draw.text((110, 80), f"Código:     {codigo}", fill="black", font=font_text)

    return imagem

# ---------- PROCESSAMENTO ----------
if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Limpar nomes de colunas: remove espaços extras
    df.columns = [col.strip() for col in df.columns]

    st.write("Pré-visualização da planilha enviada:")
    st.dataframe(df)

    etiquetas = []

    for idx, linha in df.iterrows():
        # Usa .get() para evitar KeyError
        codigo = str(linha.get("Código", "N/A"))
        descricao = str(linha.get("Descrição", "N/A"))
        unid = str(linha.get("Unid", "N/A"))

        img = gerar_etiqueta(descricao, unid, codigo)
        etiquetas.append(img)

    st.subheader("🖼 Prévia das Etiquetas")
    cols = st.columns(2)
    for i, etiq in enumerate(etiquetas):
        with cols[i % 2]:
            st.image(etiq)

    # ---------- GERAR PDF ----------
    if st.button("📄 Salvar como PDF"):
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)

        x, y = 20, 780
        col_width = 275

        for etiq in etiquetas:
            img_buffer = BytesIO()
            etiq.save(img_buffer, format="PNG")
            img_buffer.seek(0)
            pil_img = Image.open(img_buffer)

            pdf.drawInlineImage(pil_img, x, y, width=250, height=75)

            x += col_width
            if x > 300:  # passou da 2ª coluna
                x = 20
                y -= 90  # próxima linha

            if y < 50:
                pdf.showPage()
                x, y = 20, 780

        pdf.save()
        buffer.seek(0)

        st.download_button("⬇ Baixar PDF", buffer, "etiquetas.pdf")
