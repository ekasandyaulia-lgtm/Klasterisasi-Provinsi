import streamlit as st
import pandas as pd

# Tab Overview: grid 12 column 
# Header bar: judul dashboard, filter tahun global (default: tahun terakhir/2025), tombol unduh ringkasan PDF.
st.set_page_config
    (page_title="Dashboard Analisis Klaster Provinsi", 
    layout="wide",
    initial_sidebar_state="expanded")
col_header, col_filter, col_btn = st.columns([7, 2, 3])

with col_header:
    st.title("Dashboard Analisis Klaster Provinsi")

with col_filter:
    tahun_terakhir = 2025
    tahun = st.selectbox("Pilih Tahun", options=[2021, 2022, 2023, 2024, 2025], index=4)

with col_btn:
    st.button("Unduh Ringkasan PDF")

# KPI Cards



# Tab Peta Klaster Provinsi

# Tab Dinamika Temporal

# Tab Profil & Perbandingan Provinsi

# Tab Metodologi & Validitas Model