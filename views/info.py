import streamlit as st
import pandas as pd
from translation import translations

#Variaveis
df = pd.read_csv("assets/files/Modelo de Planilha.csv")
pdf_path = "assets/files/Certificado.pdf"

#Tradução
lang = st.session_state.get("lang", "en-US")
t = translations[lang]

#Interface
st.title('InkyCert')
st.subheader(t["info"])

tab1, tab2, tab3 = st.tabs([t["info1"], t["info2"], t["info3"]])

with tab1:
    st.badge("PDF", icon=":material/picture_as_pdf:", color="blue")
    st.info(t["info_pdf"])
    st.image("assets/images/image12.png")
    st.text("")
    st.badge(t["spreadsheet"], icon=":material/csv:", color="green")
    st.success(t["info_spreadsheet"])
    st.dataframe(df, use_container_width=True)

with tab2:
    st.info(t["sbs1"], icon=":material/language:")
    st.image("assets/images/image1.png")
    st.warning(t["sbs2"], icon=":material/counter_1:")
    st.image("assets/images/image2.png")
    st.warning(t["sbs3"], icon=":material/counter_2:")
    st.image("assets/images/image3.png")
    st.warning(t["sbs4"], icon=":material/counter_3:")
    st.image("assets/images/image4.png")
    st.warning(t["sbs5"], icon=":material/counter_4:")
    st.image("assets/images/image5.png")
    st.warning(t["sbs6"], icon=":material/counter_5:")
    st.image("assets/images/image6.png")
    st.warning(t["sbs7"], icon=":material/counter_6:")
    st.image("assets/images/image8.png")
    st.warning(t["sbs8"], icon=":material/counter_7:")
    st.image("assets/images/image9.png")
    st.warning(t["sbs9"], icon=":material/counter_8:")
    st.image("assets/images/image10.png")
    st.warning(t["sbs10"], icon=":material/counter_9:")
    st.image("assets/images/image11.png")

with tab3:
    st.error(t["under_construction"], icon=":material/forklift:")