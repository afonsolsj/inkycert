import streamlit as st
from translation import translations

if "lang" not in st.session_state:
    st.session_state.lang = "English"

def update_lang():
    st.session_state.lang = st.session_state.lang_selectbox

t = translations[st.session_state.lang]
st.sidebar.selectbox(t["language"], ["English", "Português", "Espanõl", "Français", "Italiano", "Deutsch", "日本語", "中文", "한국어"], key="lang_selectbox", index=["English", "Português", "Espanõl", "Français", "Italiano", "Deutsch", "日本語", "中文", "한국어"].index(st.session_state.lang), on_change=update_lang,)
st.sidebar.markdown(f"""<div style="text-align: center; font-size: 12px;">{t["footer"]}</div>""", unsafe_allow_html=True)

main_page = st.Page(page='views/main.py', title=t["home_title"], icon=':material/home:', default=True)
kofi_page = st.Page(page='views/kofi.py', title="Ko-fi", icon=':material/coffee:')
info_page = st.Page(page='views/info.py', title=t["info"], icon=':material/help:')

pg = st.navigation(pages=[main_page, info_page, kofi_page])

pg.run()