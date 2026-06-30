import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Dashboard Analisis Klaster Provinsi", 
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data
def load_data():
    df = pd.read_csv("hasil_clustering_final.csv")
    return df
df = load_data()

st.sidebar.title("Navigasi Dashboard")
halaman = st.sidebar.radio("Pilih Halaman", [
    "Overview", 
    "Peta Klaster Provinsi",
    "Dinamika Temporal",
    "Profil & Perbandingan Provinsi",
    "Metodologi & Validitas Model"
])

if halaman == "Overview":
    col_header, col_filter, col_btn = st.columns([6, 2, 3], vertical_alignment="bottom")
    with col_header:
        st.markdown("<h2 style='margin-top: 0; padding-top: 0;'>Dashboard Analisis Klaster Provinsi</h2>", unsafe_allow_html=True)
    with col_filter:
        tahun_terakhir = 2025
        tahun = st.selectbox("Pilih Tahun", options=[2021, 2022, 2023, 2024, 2025], index=4)
    with col_btn:
        st.button("Unduh PDF", use_container_width=True)
    st.divider()

    # KPI Cards
    st.subheader(f"KPI Tahun {tahun}")
    df_tahun_ini = df[df['Tahun'] == tahun]
    df_tahun_lalu = df[df['Tahun'] == tahun - 1]
    total_provinsi = df_tahun_ini.shape[0]

    klaster_dominan = "-"
    kpi1_teks = "0 Prov"
    persentase_naik = 0.0
    persentase_turun = 0.0
    provinsi_tertinggi = "-"
    pertumbuhan_tertinggi = 0.0

    if total_provinsi > 0:
        klaster_counts = df_tahun_ini['Cluster_raw'].value_counts()
        klaster_dominan = klaster_counts.idxmax()
        jumlah_klaster_dominan = klaster_counts.max()
        kpi1_teks = f"{jumlah_klaster_dominan}/{total_provinsi} Prov"

    if not df_tahun_lalu.empty and not df_tahun_ini.empty:
        df_merged = pd.merge(
            df_tahun_ini[['Provinsi', 'Cluster_raw', 'Server_Based']], 
            df_tahun_lalu[['Provinsi', 'Cluster_raw', 'Server_Based']], 
            on='Provinsi', 
            suffixes=('_now', '_prev')
        )
        total_merged = df_merged.shape[0]

        if total_merged > 0:
            naik = (df_merged['Cluster_raw_now'] > df_merged['Cluster_raw_prev']).sum()
            turun = (df_merged['Cluster_raw_now'] < df_merged['Cluster_raw_prev']).sum()
            persentase_naik = (naik / total_provinsi) * 100
            persentase_turun = (turun / total_provinsi) * 100
            
            df_merged['growth_server'] = (
                (df_merged['Server_Based_now'] - df_merged['Server_Based_prev']) / df_merged['Server_Based_prev']
            ) * 100
            
            idx_max = df_merged['growth_server'].idxmax()
            provinsi_tertinggi = df_merged.loc[idx_max, 'Provinsi']
            pertumbuhan_tertinggi = df_merged.loc[idx_max, 'growth_server']

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric(
        label=f"Dominan: Klaster {klaster_dominan}", 
        value=kpi1_teks, 
        help=f"{jumlah_klaster_dominan} dari {total_provinsi} provinsi berada di klaster {klaster_dominan}"
    )
    kpi2.metric(label="Naik Klaster", value=f"{persentase_naik:.1f}%", delta="vs Tahun Lalu", delta_color="normal")
    kpi3.metric(label="Turun Klaster", value=f"{persentase_turun:.1f}%", delta="- vs Tahun Lalu", delta_color="inverse")
    kpi4.metric(label=f"Top Growth ({provinsi_tertinggi})", value=f"{pertumbuhan_tertinggi:.1f}%", delta="Server Based")
    st.write("")

col_peta, col_grafik = st.column(2)

with col_peta:
    st.markdown("### Peta Klaster Provinsi")
    st.info("Peta ini menunjukkan distribusi klaster provinsi berdasarkan hasil clustering. Warna pada peta merepresentasikan klaster masing-masing provinsi.")
with col_grafik:
    st.markdown("### Tren Provinsi per Klaster")
    st.info("Grafik ini menampilkan perubahan klaster provinsi dari tahun ke tahun. Anda dapat melihat tren naik atau turunnya klaster provinsi seiring waktu.")
    df_trend = df.groupby(['Tahun', 'Cluster_raw']).size().reset_index(name='Jumlah Provinsi')
    fig = px.bar(df_trend, x='Tahun', y='Jumlah Provinsi', color='Cluster_raw', barmode='stack', color_discrete_sequence=px.colors.qualitative.Set2)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Insight Ringkas")
        st.info(f"Pada tahun {tahun}, sebanyak **{jumlah_klaster_dominan} provinsi** tergolong ke dalam klaster **{klaster_dominan}**. {teks_narasi_pergerakan}")

        st.divider()