import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_option_menu import option_menu

st.set_page_config(page_title="Dashboard Analisis Klaster Provinsi", layout="wide")

@st.cache_data
def load_data():
    return pd.read_csv("hasil_clustering_final.csv")

df = load_data()

# 1. SIDEBAR NAVIGASI DENGAN OPTION MENU
# ... (kode import dan load_data tetap sama)

with st.sidebar:
    st.title("Navigasi Dashboard")
    halaman = option_menu(
        menu_title=None,
        options=["Overview", "Peta Klaster Provinsi", "Dinamika Temporal", "Profil & Perbandingan Provinsi", "Metodologi & Validitas Model"],
        icons=["house", "map", "graph-up", "person-badge", "info-circle"],
        default_index=0,
    )
    st.divider()
    
    # FILTER KHUSUS HALAMAN PETA (Tampil hanya jika halaman Peta dipilih)
    if halaman == "Peta Klaster Provinsi":
        st.subheader("Filter Peta")
        tahun_peta = st.slider("Tahun", 2021, 2025, 2025)
        klaster_list = df['Target_Semantic'].unique().tolist()
        selected_klaster = st.multiselect("Tampilkan Klaster", klaster_list, default=klaster_list)
        search_provinsi = st.text_input("Cari Provinsi")
        mode_peta = st.radio("Mode", ["Peta Statis", "Animasi Perubahan"])

# ... (kode if halaman == "Overview" tetap sama)

elif halaman == "Peta Klaster Provinsi":
    st.title("Peta Klaster Provinsi")
    
    # Filter data peta
    df_map = df[(df['Tahun'] == tahun_peta) & (df['Target_Semantic'].isin(selected_klaster))]
    if search_provinsi:
        df_map = df_map[df_map['Provinsi'].str.contains(search_provinsi, case=False)]
    
    import json
    try:
        with open("indonesia_provinces.geojson", "r") as f:
            geojson_data = json.load(f)
        
        # Choropleth Plot
        fig = px.choropleth(
            df_map,
            geojson=geojson_data,
            locations='Provinsi', # Pastikan kolom ini berisi nama provinsi
            featureidkey="properties.name", # SESUAIKAN dengan file geojson kamu!
            color='Target_Semantic',
            color_discrete_sequence=px.colors.qualitative.Set2,
            hover_name='Provinsi',
            projection="mercator"
        )
        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig, use_container_width=True)
        
    except FileNotFoundError:
        st.error("File 'indonesia_provinces.geojson' tidak ditemukan di folder project.")