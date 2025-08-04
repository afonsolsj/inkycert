import streamlit as st
from translation import translations
import pandas as pd
import os
from fillpdf import fillpdfs
from unidecode import unidecode
import tempfile
import zipfile
import io
from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.generic import NameObject, ArrayObject
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

#Variaveis
if "page" not in st.session_state:
    st.session_state.page = 1
if "template_path" not in st.session_state:
    st.session_state.template_path = None
if "csv_path" not in st.session_state:
    st.session_state.csv_path = None
total_pages = 5

#Navegação
def next_page():
    st.session_state.page += 1
def prev_page():
    st.session_state.page -= 1

# Gerar certificados
def generate_certificates():
    output_zip = io.BytesIO()
    pdf_path = st.session_state.template_path
    csv_path = st.session_state.csv_path
    with zipfile.ZipFile(output_zip, 'w') as zipf:
        form_fields = list(fillpdfs.get_form_fields(pdf_path).keys())
        df = pd.read_csv(csv_path)
        for _, row in df.iterrows():
            nome = row[st.session_state.coluna_nomes]
            data_dict = {form_fields[0]: nome}
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf1, \
                 tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf2:
                fillpdfs.write_fillable_pdf(pdf_path, tmp_pdf1.name, data_dict)
                flatten_pdf(tmp_pdf1.name, tmp_pdf2.name)
                zipf.write(tmp_pdf2.name, f"{nome}_Certificado.pdf")
                os.unlink(tmp_pdf1.name)
                os.unlink(tmp_pdf2.name)
    output_zip.seek(0)
    return output_zip

# Achatar
def flatten_pdf(input_pdf, output_pdf):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()
    for page in reader.pages:
        annots = page.get("/Annots")
        if not annots:
            writer.add_page(page)
            continue
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        for annot in annots:
            obj = annot.get_object()
            val = obj.get("/V")
            rect = list(map(float, obj.get("/Rect")))
            da = obj.get("/DA", "")
            if val:
                font_name, font_size, font_color = parse_da(da)
                x1, y1, x2, y2 = rect
                y_center = y1 + (y2 - y1 - font_size) / 2
                try: can.setFont(font_name, font_size)
                except: can.setFont("Helvetica", font_size)
                can.setFillColorRGB(*font_color)
                can.drawString(x1 + 2, y_center, str(val))
        can.save()
        packet.seek(0)
        overlay = PdfReader(packet)
        page.merge_page(overlay.pages[0])
        page[NameObject("/Annots")] = ArrayObject()
        writer.add_page(page)
    with open(output_pdf, "wb") as f:
        writer.write(f)

#Parametros PDF
def parse_da(da):
    font_name, font_size = "Helvetica", 12
    font_color = (0, 0, 0)
    if not da:
        return font_name, font_size, font_color
    tokens = da.split()
    for i, t in enumerate(tokens):
        if t.startswith("/"): font_name = t[1:]
        elif t == "Tf": font_size = float(tokens[i-1])
        elif t == "g": gray = float(tokens[i-1]); font_color = (gray, gray, gray)
        elif t == "rg": font_color = tuple(map(float, tokens[i-3:i]))
    return font_name, font_size, font_color

#Tradução
lang = st.session_state.get("lang", "English")
t = translations[lang]

#Interface
st.title('InkyCert')
st.subheader(t["home_title"])
st.markdown(t["shorttext"])
st.progress(st.session_state.page / total_pages)

# Página 1 - Inicio do programa
if st.session_state.page == 1:
    st.button(t["start"], on_click=next_page, type="primary", icon=":material/chevron_forward:")

# Página 2 - Upload do PDF
elif st.session_state.page == 2:
    template = st.file_uploader(t["selectPDF"], type=["pdf"], accept_multiple_files=False)
    if template:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(template.getvalue())
            tmp_path = tmp_file.name
        form_fields = list(fillpdfs.get_form_fields(tmp_path).keys())
        if len(form_fields) == 1:
            st.success(t["successFile"])
            st.session_state.template_path = tmp_path
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                st.button(t["backbutton"], on_click=prev_page, icon=":material/chevron_backward:")
            with col2:
                st.button(t["nextbutton"], on_click=next_page, type="primary", icon=":material/chevron_forward:")
        else:
            st.error(t["errorPDF"])
    else:
        st.button(t["backbutton"], on_click=prev_page, icon=":material/chevron_backward:")

# Página 3 - Upload do CSV
elif st.session_state.page == 3:
    csv_file = st.file_uploader(t["selectSpreadsheet"], type=["csv"], accept_multiple_files=False)
    if csv_file is not None:
        if csv_file.type == "text/csv":
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_file:
                tmp_file.write(csv_file.getvalue())
                tmp_csv_path = tmp_file.name
            st.success(t["successFile"])
            st.session_state.csv_path = tmp_csv_path
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                st.button(t["backbutton"], on_click=prev_page, icon=":material/chevron_backward:")
            with col2:
                st.button(t["nextbutton"], on_click=next_page, type="primary", icon=":material/chevron_forward:")
        else:
            st.error(t["error_spreadsheet"])
    else:
        st.button(t["backbutton"], on_click=prev_page, icon=":material/chevron_backward:")

# Página 4 - Seleção da coluna
elif st.session_state.page == 4:
    if st.session_state.csv_path:
        df = pd.read_csv(st.session_state.csv_path)
        colunas = df.columns.tolist()
        coluna_selecionada = st.selectbox(t["column_name"], colunas)
        st.session_state.coluna_nomes = coluna_selecionada
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            st.button(t["backbutton"], on_click=prev_page, icon=":material/chevron_backward:")
        with col2:
            st.button(t["nextbutton"], on_click=next_page, type="primary", icon=":material/chevron_forward:")
    else:
        st.button(t["backbutton"], on_click=prev_page, icon=":material/chevron_backward:")

# Página 5 - Configuração final
if st.session_state.page == 5:
    if "generating" not in st.session_state:
        st.session_state.generating = False
    if "zip_file" not in st.session_state:
        st.session_state.zip_file = None
    if st.session_state.zip_file is None:
        if not st.session_state.generating:
            if st.button(t["generate"], type="primary", icon=":material/picture_as_pdf:"):
                st.session_state.generating = True
                st.rerun()
        else:
            st.button(t["waitbutton"], disabled=True, icon=":material/hourglass:")
            st.session_state.zip_file = generate_certificates()
            st.session_state.generating = False
            st.rerun()
    else:
        st.download_button(t["download_zip"], st.session_state.zip_file, file_name="PDFs.zip", type="primary", icon=":material/download:")
    if st.button(t["resetbutton"], icon=":material/refresh:"):
        st.session_state.page = 1
        st.session_state.zip_file = None
        st.session_state.generating = False
        st.rerun()