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
with st.sidebar:
    st.title("Navigasi Dashboard")
    halaman = option_menu(
        menu_title=None, # Sembunyikan judul menu di dalam
        options=[
            "Overview", 
            "Peta Klaster Provinsi", 
            "Dinamika Temporal",
            "Profil & Perbandingan Provinsi", 
            "Metodologi & Validitas Model"
        ],
        icons=["house", "map", "graph-up", "person-badge", "info-circle"], # Ikon opsional
        menu_icon="cast",
        default_index=0,
    )
    st.divider()

# 2. KONTEN HALAMAN
if halaman == "Overview":
    # Header & Filter
    col_header, col_filter, col_btn = st.columns([6, 2, 3], vertical_alignment="bottom")
    with col_header:
        st.markdown("<h2 style='margin-top: 0; padding-top: 0;'>Dashboard Analisis Klaster Provinsi</h2>", unsafe_allow_html=True)
    with col_filter:
        tahun = st.selectbox("Pilih Tahun", options=[2021, 2022, 2023, 2024, 2025], index=4)
    with col_btn:
        st.button("Unduh PDF", use_container_width=True)
    st.divider()

    # Perhitungan KPI
    df_tahun_ini = df[df['Tahun'] == tahun]
    df_tahun_lalu = df[df['Tahun'] == tahun - 1]
    total_provinsi = df_tahun_ini.shape[0]

    klaster_dominan, kpi1_teks, persentase_naik, persentase_turun, provinsi_tertinggi, pertumbuhan_tertinggi = "-", "0 Prov", 0.0, 0.0, "-", 0.0

    if total_provinsi > 0:
        counts = df_tahun_ini['Cluster_raw'].value_counts()
        klaster_dominan, jumlah = counts.idxmax(), counts.max()
        kpi1_teks = f"{jumlah}/{total_provinsi} Prov"

    if not df_tahun_lalu.empty and not df_tahun_ini.empty:
        df_merged = pd.merge(
            df_tahun_ini[['Provinsi', 'Target_Semantic', 'Server_Based']], 
            df_tahun_lalu[['Provinsi', 'Target_Semantic', 'Server_Based']], 
            on='Provinsi', suffixes=('_now', '_prev')
        )
        if not df_merged.empty:
            persentase_naik = ((df_merged['Target_Semantic_now'] > df_merged['Target_Semantic_prev']).sum() / total_provinsi) * 100
            persentase_turun = ((df_merged['Target_Semantic_now'] < df_merged['Target_Semantic_prev']).sum() / total_provinsi) * 100
            df_merged['growth'] = ((df_merged['Server_Based_now'] - df_merged['Server_Based_prev']) / df_merged['Server_Based_prev']) * 100
            idx = df_merged['growth'].idxmax()
            provinsi_tertinggi, pertumbuhan_tertinggi = df_merged.loc[idx, 'Provinsi'], df_merged.loc[idx, 'growth']

    # Tampilan KPI
    st.subheader(f"KPI Tahun {tahun}")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric(f"Dominan: Klaster {klaster_dominan}", kpi1_teks)
    kpi2.metric("Naik Klaster", f"{persentase_naik:.1f}%", "vs Tahun Lalu")
    kpi3.metric("Turun Klaster", f"{persentase_turun:.1f}%", "- vs Tahun Lalu", delta_color="inverse")
    kpi4.metric(f"Top Growth ({provinsi_tertinggi})", f"{pertumbuhan_tertinggi:.1f}%", "Server Based")
    st.divider()

    # Baris Visual
    col_peta, col_grafik = st.columns(2)
    with col_peta:
        st.markdown("### Peta Klaster Provinsi")
        st.info("Visualisasi peta akan muncul di sini.")
    with col_grafik:
        st.markdown("### Tren Provinsi per Klaster")
        fig = px.bar(df.groupby(['Tahun', 'Target_Semantic']).size().reset_index(name='Jumlah'), 
                     x='Tahun', y='Jumlah', color='Target_Semantic', barmode='stack', color_discrete_sequence=px.colors.qualitative.Set2)
        st.plotly_chart(fig, use_container_width=True)

# 3. HALAMAN LAINNYA
elif halaman == "Peta Klaster Provinsi":
    st.title("Peta Klaster Provinsi")

    with st.sidebar:
        st.subheader("Filter Peta")
        tahun_peta = st.slider("Pilih Tahun", 2021, 2022, 2023, 2024, 2025)
        klaster_list = df['Target_Semantic'].unique().tolist()
        selected_klaster = st.multiselect("Tampilkan  Klaster", klaster_list, default=klaster_list)
        search_provinsi = st.text_input("Cari Provinsi")
        mode_peta = st.radio("Mode Peta", ["Berdasarkan Klaster", "Berdasarkan Provinsi"])

    df_map = df[df['Tahun'] == tahun_peta]
    df_map = df_map[df_map['Target_Semantic'].isin(selected_klaster)]
    if search_provinsi:
        df_map = df_map[df_map['Provinsi'].str.contains(search_provinsi, case=False)]
    
    import json
    try:
        with open("indonesia_provinces.geojson", "r") as f:
            geojson_data = json.load(f)
        
        if mode_peta == "Peta Statis":
            fig = px.choropleth(
                df_map,
                geojson=geojson_data,
                locations='Provinsi',
                featureidkey="properties.name",
                color='Target_Semantic',
                color_discrete_sequence=px.colors.qualitative.Set2,
                hover_name='Provinsi',
                hover_data={'Tahun': True, 'Server_Based': True, 'Cluster_raw': True},
            )
        else:
            fig = px.choropleth(
                df_map,
                geojson=geojson_data,
                locations='Provinsi',
                featureidkey="properties.name",
                color='Target_Semantic',
                color_discrete_sequence=px.colors.qualitative.Set2,
                hover_name='Provinsi',
                hover_data={'Tahun': True, 'Server_Based': True, 'Cluster_raw': True},
            )
    except FileNotFoundError:
        st.error("File geojson tidak ditemukan.")
elif halaman == "Dinamika Temporal":
    st.title("Dinamika Temporal")
elif halaman == "Profil & Perbandingan Provinsi":
    st.title("Profil & Perbandingan Provinsi")
elif halaman == "Metodologi & Validitas Model":
    st.title("Metodologi & Validitas Model")