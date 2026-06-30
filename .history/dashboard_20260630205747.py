import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_option_menu import option_menu
import json
import plotly.graph_objects as go

# Konfigurasi Halaman
st.set_page_config(page_title="Dashboard Analisis Klaster Provinsi", layout="wide")

# Cache Data
@st.cache_data
def load_data():
    return pd.read_csv("hasil_clustering_final.csv")

df = load_data()

# 1. SIDEBAR NAVIGASI
with st.sidebar:
    st.title("Navigasi Dashboard")
    halaman = option_menu(
        menu_title=None,
        options=[
            "Overview", 
            "Peta Klaster Provinsi", 
            "Dinamika Temporal",
            "Profil & Perbandingan Provinsi", 
            "Metodologi & Validitas Model"
        ],
        icons=["house", "map", "graph-up", "person-badge", "info-circle"],
        default_index=0,
    )
    st.divider()

# 2. HALAMAN OVERVIEW
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

    klaster_dominan, kpi1_teks = "-", "0 Prov"
    persentase_naik, persentase_turun = 0.0, 0.0
    provinsi_tertinggi, pertumbuhan_tertinggi = "-", 0.0

    if total_provinsi > 0:
        counts = df_tahun_ini['Target_Semantic'].value_counts()
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
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(f"Dominan: Klaster {klaster_dominan}", kpi1_teks)
    k2.metric("Naik Klaster", f"{persentase_naik:.1f}%", "vs Tahun Lalu")
    k3.metric("Turun Klaster", f"{persentase_turun:.1f}%", "- vs Tahun Lalu", delta_color="inverse")
    k4.metric(f"Top Growth ({provinsi_tertinggi})", f"{pertumbuhan_tertinggi:.1f}%", "Server Based")
    st.divider()

    # Visual Utama
    c1, c2 = st.columns(2)
    with c1:
            st.markdown("### Peta Klaster Provinsi")
            try:
                with open("indonesia.geojson", "r") as f:
                    geojson_overview = json.load(f)

                df_map_overview = df[df['Tahun'] == tahun]

                fig_map = px.choropleth(
                    df_map_overview, geojson=geojson_overview, locations='Provinsi',
                    featureidkey="properties.name",
                    color='Target_Semantic',
                    color_discrete_sequence=px.colors.qualitative.Set2,
                    hover_name='Provinsi',
                    projection="mercator"
                )
                fig_map.update_geos(fitbounds="locations", visible=False)
                fig_map.update_layout(
                    height=400,
                    margin=dict(l=0, r=0, t=10, b=0),
                    legend=dict(
                        bgcolor="rgba(255,255,255,0.85)",
                        bordercolor="lightgray", borderwidth=1
                    )
                )
                st.plotly_chart(fig_map, use_container_width=True)
            except FileNotFoundError:
                st.error("File GeoJSON tidak ditemukan.")
    with c2:
        st.markdown("### Tren Provinsi per Klaster")
        fig = px.bar(df.groupby(['Tahun', 'Target_Semantic']).size().reset_index(name='Jumlah'), 
                     x='Tahun', y='Jumlah', color='Target_Semantic', barmode='stack', color_discrete_sequence=px.colors.qualitative.Set2)
        st.plotly_chart(fig, use_container_width=True)

# 3. HALAMAN PETA
elif halaman == "Peta Klaster Provinsi":
    st.title("Peta Klaster Provinsi")

    col_kontrol, col_peta = st.columns([3, 9])

    with col_kontrol:
        st.subheader("Filter Peta")
        tahun_peta = st.slider("Tahun", 2021, 2025, 2025)

        klaster_list = sorted(df['Target_Semantic'].unique().tolist())
        selected_klaster = st.multiselect(
            "Tampilkan Klaster", klaster_list, default=klaster_list
        )

        cari_provinsi = st.text_input("Cari Provinsi", placeholder="Ketik nama provinsi...")

        mode_tampilan = st.radio(
            "Mode Tampilan",
            ["Peta Statis", "Animasi Perubahan 2021→2025"],
            index=0
        )

    if mode_tampilan == "Peta Statis":
        df_map = df[(df['Tahun'] == tahun_peta) & (df['Target_Semantic'].isin(selected_klaster))].copy()
    else:
        df_map = df[(df['Tahun'].between(2021, 2025)) & (df['Target_Semantic'].isin(selected_klaster))].copy()

    if cari_provinsi:
        df_map = df_map[df_map['Provinsi'].str.contains(cari_provinsi, case=False, na=False)]

    with col_kontrol:
        st.markdown("**Legenda**")
        df_legenda = df[(df['Tahun'] == tahun_peta) & (df['Target_Semantic'].isin(selected_klaster))]
        warna_klaster = dict(zip(klaster_list, px.colors.qualitative.Set2))
        for k in klaster_list:
            jml = (df_legenda['Target_Semantic'] == k).sum()
            warna = warna_klaster.get(k, "#999999")
            st.markdown(
                f"<div style='display:flex;align-items:center;gap:8px;margin-bottom:4px;'>"
                f"<div style='width:14px;height:14px;background:{warna};border-radius:3px;'></div>"
                f"<span>Klaster {k} — {jml} provinsi</span></div>",
                unsafe_allow_html=True
            )

    with col_peta:
        try:
            with open("indonesia.geojson", "r") as f:
                geojson = json.load(f)

            hover_cols = ['Target_Semantic']
            for kolom in ['Server_Based', 'Mobile_Based', 'Web_Based', 'Cloud_Based']:
                if kolom in df.columns:
                    hover_cols.append(kolom)

            if mode_tampilan == "Peta Statis":
                fig = px.choropleth(
                    df_map, geojson=geojson, locations='Provinsi',
                    featureidkey="properties.name",
                    color='Target_Semantic',
                    color_discrete_sequence=px.colors.qualitative.Set2,
                    hover_name='Provinsi',
                    hover_data=hover_cols,
                    projection="mercator"
                )
            else:
                fig = px.choropleth(
                    df_map, geojson=geojson, locations='Provinsi',
                    featureidkey="properties.name",
                    color='Target_Semantic',
                    color_discrete_sequence=px.colors.qualitative.Set2,
                    hover_name='Provinsi',
                    hover_data=hover_cols,
                    projection="mercator",
                    animation_frame='Tahun'
                )

            fig.update_geos(fitbounds="locations", visible=False)
            fig.update_layout(
                height=750,
                margin=dict(l=0, r=0, t=20, b=0),
                legend=dict(
                    title="Klaster",
                    orientation="v",
                    yanchor="top", y=0.98,
                    xanchor="left", x=0.01,
                    bgcolor="rgba(255,255,255,0.85)",
                    bordercolor="lightgray", borderwidth=1
                )
            )

            klik = st.plotly_chart(fig, use_container_width=True, on_select="rerun", key="peta_klaster")

        except FileNotFoundError:
            st.error("File GeoJSON tidak ditemukan.")

    if klik and klik.get("selection") and klik["selection"].get("points"):
        nama_terpilih = klik["selection"]["points"][0].get("location")
        if nama_terpilih:
            st.divider()
            st.subheader(f"Detail: {nama_terpilih}")
            detail = df[(df['Provinsi'] == nama_terpilih) & (df['Tahun'] == tahun_peta)]
            if not detail.empty:
                detail = detail.iloc[0]
                dkol = st.columns(5)
                dkol[0].metric("Klaster", detail['Target_Semantic'])
                for i, kolom in enumerate(['Server_Based', 'Mobile_Based', 'Web_Based', 'Cloud_Based']):
                    if kolom in detail and i + 1 < len(dkol):
                        dkol[i + 1].metric(kolom, detail[kolom])

# Halaman Dinamika Temporal
elif halaman == "Dinamika Temporal":
    st.title("Dinamika Temporal")

    st.subheader("Alur Perpindahan Klaster Provinsi (Sankey Diagram)")
    try:
        with open("indonesia.geojson", "r") as f:
            geojson_temporal = json.load(f)

        sankey_data = []
        for provinsi in df['Provinsi'].unique():
            prov_data = df[df['Provinsi'] == provinsi].sort_values('Tahun')
            for i in range(len(prov_data) - 1):
                source = f"{prov_data.iloc[i]['Tahun']} - {prov_data.iloc[i]['Target_Semantic']}"
                target = f"{prov_data.iloc[i + 1]['Tahun']} - {prov_data.iloc[i + 1]['Target_Semantic']}"
                sankey_data.append((source, target))

        sankey_df = pd.DataFrame(sankey_data, columns=['source', 'target'])
        sankey_counts = sankey_df.groupby(['source', 'target']).size().reset_index(name='count')

        # Membuat label unik untuk node
        unique_labels = sorted(list(set(sankey_counts['source']).union(set(sankey_counts['target']))))
        label_indices = {label: idx for idx, label in enumerate(unique_labels)}
        source_indices = [label_indices[src] for src in sankey_counts['source']]
        target_indices = [label_indices[tgt] for tgt in sankey_counts['target']]
        values = sankey_counts['count'].tolist()
        
        list_tahun = sorted(list(set([int(label.split(" - ")[0]) for label in unique_labels])))
        jarak_tahun = len(list_tahun) - 1 if len(list_tahun) > 1 else 1
        tahun_ke_x = {tahun: (idx/jarak_tahun) for idx, tahun in enumerate(list_tahun)}
        x_positions = [tahun_ke_x[int(label.split(" - ")[0])] for label in unique_labels]
        node_colors = ["#636EFA"] * len(unique_labels)
        
        fig_sankey = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=unique_labels,
                color=node_colors,
                x=x_positions
            ),
            link=dict(
                source=source_indices, 
                target=target_indices, 
                value=values)
                )])
        fig_sankey.update_layout(
            title_text="Sankey Diagram Perpindahan Klaster Provinsi", 
            font=dict(size=13, color="black")
            margin=dict(l=40, r=40, t=50, b=40),
            height=600
        )
        st.plotly_chart(fig_sankey, use_container_width=True)
    except FileNotFoundError:
        st.error("File GeoJSON tidak ditemukan.")

elif halaman == "Profil & Perbandingan Provinsi":
    st.title("Profil & Perbandingan Provinsi")
elif halaman == "Metodologi & Validitas Model":
    st.title("Metodologi & Validitas Model")