import streamlit as st
from translation import translations
from streamlit_extras.image_selector import image_selector
import fitz
from PIL import Image
from io import BytesIO
import tempfile
import os
import io
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, Color
import uuid
from fillpdf import fillpdfs
import pdfrw

# Variáveis
if "page2" not in st.session_state:
    st.session_state.page2 = 1
if "uploaded_pdf_path" not in st.session_state:
    st.session_state.uploaded_pdf_path = None
if "field_created" not in st.session_state:
    st.session_state.field_created = False
if "temp_pdf_result" not in st.session_state:
    st.session_state.temp_pdf_result = None
total_pages2 = 3
transparent = Color(0, 0, 0, alpha=0)
random_name = str(uuid.uuid4())

# Tradução
lang = st.session_state.get("lang", "English")
t = translations[lang]

#Interface
st.title('InkyCert')
st.subheader(t["create_form"])
st.markdown(t["text_form"])
st.warning(t["warning_form"])
st.progress(st.session_state.page2 / total_pages2)

# Navegação
def next_page():
    st.session_state.page2 += 1
def prev_page():
    st.session_state.page2 -= 1

# Página 1 - Inicio do programa
if st.session_state.page2 == 1:
    st.button(t["start"], on_click=next_page, type="primary", icon=":material/chevron_forward:")

# Página 2 - Upload do PDF
elif st.session_state.page2 == 2:
    template = st.file_uploader(t["selectPDF"], type=["pdf"], accept_multiple_files=False)
    if template:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(template.getvalue())
            tmp_path = tmp_file.name
        form_fields = list(fillpdfs.get_form_fields(tmp_path).keys())
        if len(form_fields) == 0:
            st.success(t["successFile"])
            st.session_state.uploaded_pdf_path = tmp_path
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                st.button(t["backbutton"], on_click=prev_page, icon=":material/chevron_backward:")
            with col2:
                st.button(t["nextbutton"], on_click=next_page, type="primary", icon=":material/chevron_forward:")
        else:
            st.error(t["errorPDF"])
    else:
        st.button(t["backbutton"], on_click=prev_page, icon=":material/chevron_backward:")

# Página 3 - Seleção da área e criação do campo
elif st.session_state.page2 == 3:
    pdf_path = st.session_state.uploaded_pdf_path

    # Abre o PDF e gera a imagem da primeira página em 300 dpi
    doc = fitz.open(pdf_path)
    page = doc.load_page(0)  # índice 0 = primeira página
    pix = page.get_pixmap(dpi=300)
    img = Image.open(BytesIO(pix.tobytes("png")))

    # Salva temporariamente a imagem para usar no image_selector
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
        temp_path = tmp_file.name
        img.save(temp_path, "PNG")

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(t.get("selectArea", t["text_field1"]))
        sel = image_selector(image=temp_path, selection_type="box", key="sel1", width=400, height=400)
        st.button(t["backbutton"], on_click=prev_page, icon=":material/chevron_backward:")

    with col2:
        st.markdown(t.get("fieldSettings", t["text_field2"]))
        font_color = st.color_picker(t.get("fontColor", t["text_field3"]), "#000000")
        font_size = st.number_input(t.get("fontSize", t["text_field4"]), min_value=6, max_value=72, value=12)

        if not st.session_state.field_created:
            create_button = st.button(
                t.get("createField", t["text_field5"]),
                disabled=not (sel and "selection" in sel and "box" in sel["selection"] and sel["selection"]["box"])
            )
            if create_button:
                box = sel["selection"]["box"][0]
                x1_img, x2_img = box["x"]
                y1_img, y2_img = box["y"]

                img_width, img_height = img.size  # usar img.size direto

                from PyPDF2 import PdfReader as PdfReaderPyPDF2, PdfWriter
                reader = PdfReaderPyPDF2(pdf_path)
                page = reader.pages[0]
                pdf_width = float(page.mediabox.width)
                pdf_height = float(page.mediabox.height)

                # Escala das coordenadas da imagem para as do PDF
                scale_x = pdf_width / img_width
                scale_y = pdf_height / img_height

                x1_pdf = x1_img * scale_x
                x2_pdf = x2_img * scale_x
                y1_pdf = pdf_height - (y2_img * scale_y)  # atenção à inversão do eixo Y
                y2_pdf = pdf_height - (y1_img * scale_y)

                field_width = x2_pdf - x1_pdf
                field_height = y2_pdf - y1_pdf

                import io
                from reportlab.pdfgen import canvas
                from reportlab.lib.colors import HexColor, Color
                import pdfrw

                transparent = Color(0, 0, 0, alpha=0)

                packet = io.BytesIO()
                can = canvas.Canvas(packet, pagesize=(pdf_width, pdf_height))
                can._doc.acroForm = pdfrw.PdfDict(NeedAppearances=pdfrw.PdfObject('true'), Fields=pdfrw.PdfArray())
                can.acroForm.textfield(
                    name="campo1",
                    x=x1_pdf,
                    y=y1_pdf,
                    width=field_width,
                    height=field_height,
                    fillColor=transparent,
                    borderStyle='inset',
                    borderColor=transparent,
                    borderWidth=0,
                    forceBorder=True,
                    textColor=HexColor(font_color),
                    fontSize=font_size,
                )
                can.save()
                packet.seek(0)

                field_pdf = PdfReaderPyPDF2(packet)
                writer = PdfWriter()
                page.merge_page(field_pdf.pages[0])
                writer.add_page(page)

                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as output_file:
                    writer.write(output_file)

                pdf_pdfrw = pdfrw.PdfReader(output_file.name)
                if not getattr(pdf_pdfrw.Root, "AcroForm", None):
                    pdf_pdfrw.Root.AcroForm = pdfrw.PdfDict()
                if "Fields" not in pdf_pdfrw.Root.AcroForm:
                    fields = []
                    for p in pdf_pdfrw.pages:
                        if p.Annots:
                            fields.extend(p.Annots)
                    pdf_pdfrw.Root.AcroForm.update(pdfrw.PdfDict(Fields=fields))
                pdf_pdfrw.Root.AcroForm.update(pdfrw.PdfDict(NeedAppearances=pdfrw.PdfObject('true')))
                pdfrw.PdfWriter().write(output_file.name, pdf_pdfrw)

                st.session_state.temp_pdf_result = output_file.name
                st.session_state.field_created = True
                st.rerun()

        else:
            with open(st.session_state.temp_pdf_result, "rb") as f:
                st.download_button(
                    t.get("downloadPDF", t["text_field6"]),
                    f,
                    file_name="PDF_file.pdf",
                    type="primary",
                    icon=":material/download:",
                )
            if st.button(t["resetbutton"], icon=":material/refresh:"):
                st.session_state.page2 = 1
                st.session_state.field_created = False
                if st.session_state.temp_pdf_result:
                    try:
                        os.remove(st.session_state.temp_pdf_result)
                    except Exception:
                        pass
                st.session_state.temp_pdf_result = None
                st.rerun()

    # Remove imagem temporária para não acumular arquivos
    if os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except Exception:
            pass