import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from streamlit_option_menu import option_menu
import json
import io   
import plotly.graph_objects as go

# Unduh PDF
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# Konfigurasi Halaman
st.set_page_config(page_title="Dashboard Analisis Klaster Provinsi", layout="wide")

# Cache Data
@st.cache_data
def load_data():
    return pd.read_csv("final clustering.csv"), pd.read_csv("metrics_results.csv")

df, df_metrics = load_data()

palet_warna = {
            "Digital Maju": "#00B871",
            "Digital Menengah": "#FFB000",
            "Digital Rendah": "#E8352F",
            "Digital Spesialis Non-Tunai": "#8B2FE0",
}
warna_default = "#95A5A6"

# Generator PDF Placeholder

def generate_overview_pdf(tahun, total_provinsi, klaster_dominan, kpi1_teks,
                           persentase_naik, persentase_turun,
                           provinsi_tertinggi, pertumbuhan_tertinggi,
                           cluster_counts_dict):
    """Membuat PDF ringkasan KPI halaman Overview secara nyata (bukan placeholder)."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 2.5 * cm
 
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2 * cm, y, f"Laporan Overview Dashboard - Tahun {tahun}")
    y -= 1.2 * cm
 
    c.setFont("Helvetica", 11)
    baris = [
        f"Total Provinsi Tercatat: {total_provinsi}",
        f"Klaster Dominan: {klaster_dominan} ({kpi1_teks})",
        f"Provinsi Naik Klaster (vs tahun lalu): {persentase_naik:.1f}%",
        f"Provinsi Turun Klaster (vs tahun lalu): {persentase_turun:.1f}%",
        f"Pertumbuhan Server Based Tertinggi: {provinsi_tertinggi} ({pertumbuhan_tertinggi:.1f}%)",
    ]
    for teks in baris:
        c.drawString(2 * cm, y, teks)
        y -= 0.7 * cm
 
    y -= 0.5 * cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2 * cm, y, "Distribusi Provinsi per Klaster:")
    y -= 0.7 * cm
 
    c.setFont("Helvetica", 10)
    if cluster_counts_dict:
        for klaster, jumlah in cluster_counts_dict.items():
            c.drawString(2.5 * cm, y, f"- {klaster}: {jumlah} provinsi")
            y -= 0.55 * cm
    else:
        c.drawString(2.5 * cm, y, "Tidak ada data untuk tahun ini.")
        y -= 0.55 * cm
 
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(2 * cm, 1.5 * cm, "Dokumen dihasilkan otomatis oleh Dashboard Analisis Klaster Provinsi.")
 
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()
 
 
def _nb_markdown_cell(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(keepends=True)}
 
 
def _nb_code_cell(text):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": text.splitlines(keepends=True),
    }
 
 
def generate_notebook_bytes():
    """Membuat file .ipynb yang valid (JSON sesuai skema nbformat v4), bukan teks biasa."""
    cells = [
        _nb_markdown_cell("# K-Means Clustering - Analisis Klaster Provinsi\n\nRingkasan alur pemodelan yang digunakan pada dashboard ini."),
        _nb_code_cell(
            "import pandas as pd\n"
            "import numpy as np\n"
            "from sklearn.preprocessing import RobustScaler\n"
            "from sklearn.cluster import KMeans\n"
            "from sklearn.decomposition import PCA\n"
            "from scipy.optimize import linear_sum_assignment\n"
        ),
        _nb_markdown_cell("## 1. Muat & Agregasi Data Tahunan"),
        _nb_code_cell(
            "df_mentah = pd.read_csv('data_mentah_bulanan.csv')\n"
            "df_tahunan = df_mentah.groupby(['Provinsi', 'Tahun']).mean().reset_index()\n"
        ),
        _nb_markdown_cell("## 2. Transformasi log1p & RobustScaler"),
        _nb_code_cell(
            "fitur = ['outflow_tunai', 'kartu_atm_debet', 'Server_Based', 'SKNBI_Asal']\n"
            "X = np.log1p(df_tahunan[fitur])\n"
            "scaler = RobustScaler()\n"
            "X_scaled = scaler.fit_transform(X)\n"
        ),
        _nb_markdown_cell("## 3. K-Means (k=4) dengan Elbow Method"),
        _nb_code_cell(
            "kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)\n"
            "labels = kmeans.fit_predict(X_scaled)\n"
            "df_tahunan['Cluster'] = labels\n"
        ),
        _nb_markdown_cell("## 4. PCA untuk Visualisasi 2D"),
        _nb_code_cell(
            "pca = PCA(n_components=2)\n"
            "coords = pca.fit_transform(X_scaled)\n"
            "df_tahunan[['PCA1', 'PCA2']] = coords\n"
        ),
        _nb_markdown_cell("## 5. Pelabelan Semantik (Linear Sum Assignment) & Simpan Hasil"),
        _nb_code_cell(
            "# Pemetaan label klaster numerik ke label semantik dilakukan di sini\n"
            "df_tahunan.to_csv('final clustering.csv', index=False)\n"
        ),
    ]
    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.10"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    return json.dumps(notebook, indent=2, ensure_ascii=False).encode("utf-8")
 
 
def generate_metodologi_pdf(param_df, df_metrics_tampil):
    """Membuat PDF dokumen metodologi & validitas model secara nyata (bukan placeholder)."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm,
                             leftMargin=2 * cm, rightMargin=2 * cm)
    styles = getSampleStyleSheet()
    story = []
 
    story.append(Paragraph("Dokumen Metodologi &amp; Validitas Model", styles["Title"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Dokumen ini menyajikan ringkasan teknis metodologi klasterisasi K-Means yang digunakan "
        "dalam analisis adopsi digital antar provinsi, termasuk konfigurasi parameter, metrik "
        "evaluasi, serta batasan model.",
        styles["BodyText"]
    ))
    story.append(Spacer(1, 14))
 
    story.append(Paragraph("1. Konfigurasi Parameter Model", styles["Heading2"]))
    tabel_param = [list(param_df.columns)] + param_df.astype(str).values.tolist()
    t1 = Table(tabel_param, colWidths=[7 * cm, 9.5 * cm])
    t1.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f6f7")]),
    ]))
    story.append(t1)
    story.append(Spacer(1, 16))
 
    story.append(Paragraph("2. Metrik Evaluasi Model per Tahun", styles["Heading2"]))
    df_metrik_str = df_metrics_tampil.copy()
    for kol in df_metrik_str.select_dtypes(include="number").columns:
        df_metrik_str[kol] = df_metrik_str[kol].round(4)
    tabel_metrik = [list(df_metrik_str.columns)] + df_metrik_str.astype(str).values.tolist()
    t2 = Table(tabel_metrik)
    t2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f6f7")]),
    ]))
    story.append(t2)
    story.append(Spacer(1, 16))
 
    story.append(Paragraph("3. Batasan Teknis &amp; Keterbatasan Model", styles["Heading2"]))
    batasan = [
        "Granularitas Temporal Makro: data diagregasi berbasis rata-rata tahunan sehingga variasi "
        "musiman (mis. lonjakan transaksi tunai menjelang Idul Fitri) tidak sepenuhnya tertangkap.",
        "Anomali Struktural Ibu Kota: klaster 'Digital Spesialis Non-Tunai' mencerminkan profil unik "
        "DKI Jakarta sebagai pusat kliring nasional dan tidak dapat digeneralisasi ke wilayah lain.",
        "Karakteristik Skala RobustScaler: tahan terhadap outlier namun tidak menghilangkan "
        "kesenjangan ekonomi riil antarprovinsi.",
    ]
    for item in batasan:
        story.append(Paragraph(f"&bull; {item}", styles["BodyText"]))
        story.append(Spacer(1, 6))
 
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# Sidebar
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

# Overview Page
if halaman == "Overview":
    col_header, col_filter, col_btn = st.columns([6, 2, 3], vertical_alignment="bottom")
    with col_header:
        st.markdown("<h2 style='margin-top: 0; padding-top: 0;'>Dashboard Analisis Klaster Provinsi</h2>", unsafe_allow_html=True)
    with col_filter:
        tahun = st.selectbox("Pilih Tahun", options=[2021, 2022, 2023, 2024, 2025], index=4)
    with col_btn:
            pdf_placeholder = st.empty()
    st.divider()

    # Perhitungan KPI
    df_tahun_ini = df[df['Tahun'] == tahun]
    df_tahun_lalu = df[df['Tahun'] == tahun - 1]
    total_provinsi = df_tahun_ini.shape[0]

    klaster_dominan, kpi1_teks = "-", "0 Prov"
    persentase_naik, persentase_turun = 0, 0
    provinsi_tertinggi, pertumbuhan_tertinggi = "-", 0

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
            persentase_naik = (df_merged['Target_Semantic_now'] > df_merged['Target_Semantic_prev']).sum()
            persentase_turun = (df_merged['Target_Semantic_now'] < df_merged['Target_Semantic_prev']).sum()
            df_merged['growth'] = ((df_merged['Server_Based_now'] - df_merged['Server_Based_prev']) / df_merged['Server_Based_prev']) * 100
            idx = df_merged['growth'].idxmax()
            provinsi_tertinggi, pertumbuhan_tertinggi = df_merged.loc[idx, 'Provinsi'], df_merged.loc[idx, 'growth']

            df_valid = df_merged[df_merged['Server_Based_prev'] > 1.0]
            if not df_valid.empty:
                row = df_valid.nlargest(1, 'growth').iloc[0]
            else:
                row = df_merged.nlargest(1, 'growth').iloc[0]
            provinsi_tertinggi = row['Provinsi']
            pertumbuhan_tertinggi = row['growth']
    
    # Perhitungan KPI
    df_tahun_ini = df[df['Tahun'] == tahun]
    df_tahun_lalu = df[df['Tahun'] == tahun - 1]
    total_provinsi = df_tahun_ini.shape[0]
 
    klaster_dominan, kpi1_teks = "-", "0 Prov"
    persentase_naik, persentase_turun = 0.0, 0.0
    provinsi_tertinggi, pertumbuhan_tertinggi = "-", 0.0
    cluster_counts_dict = {}

    if total_provinsi > 0:
        counts = df_tahun_ini['Target_Semantic'].value_counts()
        klaster_dominan, jumlah = counts.idxmax(), counts.max()
        kpi1_teks = f"{jumlah}/{total_provinsi} Prov"
        cluster_counts_dict = counts.to_dict()
 
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
 
            df_valid = df_merged[df_merged['Server_Based_prev'] > 1.0]
            if not df_valid.empty:
                row = df_valid.nlargest(1, 'growth').iloc[0]
            else:
                row = df_merged.nlargest(1, 'growth').iloc[0]
            provinsi_tertinggi = row['Provinsi']
            pertumbuhan_tertinggi = row['growth']
    pdf_bytes = generate_overview_pdf(
        tahun, total_provinsi, klaster_dominan, kpi1_teks,
        persentase_naik, persentase_turun,
        provinsi_tertinggi, pertumbuhan_tertinggi,
        cluster_counts_dict
    )
    pdf_placeholder.download_button(
        label="Unduh PDF",
        data=pdf_bytes,
        file_name=f"Laporan_Overview_{tahun}.pdf",
        mime="application/pdf",
        use_container_width=True,
        help="Klik untuk mengunduh rekap laporan tahun ini dalam format PDF"
    )

    # Tampilan KPI
    st.subheader(f"KPI Tahun {tahun}")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(f"Dominan: Klaster {klaster_dominan}", kpi1_teks)
    k2.metric("Naik Klaster", f"{persentase_naik:.1f}%", "vs Tahun Lalu")
    k3.metric("Turun Klaster", f"{persentase_turun:.1f}%", "- vs Tahun Lalu", delta_color="inverse")
    k4.metric(label=f"Top Growth Server Based ({provinsi_tertinggi})", value=f"{pertumbuhan_tertinggi:.1f}%")
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
                    color_discrete_map=palet_warna,
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
                st.plotly_chart(fig_map, width='stretch')
            except FileNotFoundError:
                st.error("File GeoJSON tidak ditemukan.")
    with c2:
        st.markdown("### Tren Provinsi per Klaster")
        fig = px.bar(df.groupby(['Tahun', 'Target_Semantic']).size().reset_index(name='Jumlah'), 
                     x='Tahun', y='Jumlah', color='Target_Semantic', barmode='stack', color_discrete_map=palet_warna)
        st.plotly_chart(fig, width='stretch')

# HALAMAN PETA
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

        provinsi_list_peta = sorted(df['Provinsi'].unique().tolist())
        cari_provinsi = st.multiselect(
            "Cari Provinsi", 
            options = provinsi_list_peta, 
            default=[],
            placeholder = "kosongkan untuk menampilkan semua provinsi"
        )

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
        df_map = df_map[df_map["Provinsi"].isin(cari_provinsi)]

    with col_kontrol:
        st.markdown("**Legenda**")
        df_legenda = df[(df['Tahun'] == tahun_peta) & (df['Target_Semantic'].isin(selected_klaster))]
        for k in klaster_list:
            jml = (df_legenda['Target_Semantic'] == k).sum()
            warna = palet_warna.get(k, warna_default)
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
                    color_discrete_map=palet_warna,
                    hover_name='Provinsi',
                    hover_data=hover_cols,
                    projection="mercator"
                )
            else:
                fig = px.choropleth(
                    df_map, geojson=geojson, locations='Provinsi',
                    featureidkey="properties.name",
                    color='Target_Semantic',
                    color_discrete_map={klaster: palet_warna.get(klaster, warna_default) for klaster in df_map['Target_Semantic'].unique()},
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

            klik = st.plotly_chart(fig, width='stretch', on_select="rerun", key="peta_klaster")

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
    st.title("Dinamika Temporal (2021–2025)")

    st.subheader("Alur Perpindahan Klaster Provinsi (Sankey Diagram)")
    try:
        sankey_data = []
        for provinsi in df['Provinsi'].unique():
            prov_data = df[df['Provinsi'] == provinsi].sort_values('Tahun')
            for i in range(len(prov_data) - 1):
                source = f"{prov_data.iloc[i]['Tahun']} - {prov_data.iloc[i]['Target_Semantic']}"
                target = f"{prov_data.iloc[i + 1]['Tahun']} - {prov_data.iloc[i + 1]['Target_Semantic']}"
                sankey_data.append((source, target))

        sankey_df = pd.DataFrame(sankey_data, columns=['source', 'target'])
        sankey_counts = sankey_df.groupby(['source', 'target']).size().reset_index(name='count')

        unique_labels = sorted(
            set(sankey_counts['source']) | set(sankey_counts['target']),
            key=lambda s: (int(s.split(" - ")[0]), s.split(" - ", 1)[1])
        )
        label_indices = {label: idx for idx, label in enumerate(unique_labels)}
        source_indices = [label_indices[src] for src in sankey_counts['source']]
        target_indices = [label_indices[tgt] for tgt in sankey_counts['target']]
        values = sankey_counts['count'].tolist()

        list_tahun = sorted({int(label.split(" - ")[0]) for label in unique_labels})
        jarak_tahun = len(list_tahun) - 1 if len(list_tahun) > 1 else 1
        tahun_ke_x = {tahun: idx / jarak_tahun for idx, tahun in enumerate(list_tahun)}
        x_positions = [tahun_ke_x[int(label.split(" - ")[0])] for label in unique_labels]
        x_positions = [min(max(x, 0.001), 0.999) for x in x_positions]

        label_klaster_pendek = [label.split(" - ", 1)[1] for label in unique_labels]


        node_colors = [palet_warna.get(klaster, warna_default) for klaster in label_klaster_pendek]

        def hex_ke_rgba(hex_color, alpha=0.45):
            hex_color = hex_color.lstrip("#")
            r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            return f"rgba({r},{g},{b},{alpha})"

        link_colors = [hex_ke_rgba(node_colors[src]) for src in source_indices]

        fig_sankey = go.Figure(data=[go.Sankey(
            node=dict(
                pad=8,
                thickness=15,
                line=dict(color="black", width=0.3),
                label=label_klaster_pendek,
                color=node_colors,
                x=x_positions,
            ),
            link=dict(
                source=source_indices,
                target=target_indices,
                value=values,
                color=link_colors,
            )
        )])

        fig_sankey.update_traces(textfont=dict(size=1, color="rgba(0,0,0,0)"))
        for tahun, x in tahun_ke_x.items():
            fig_sankey.add_annotation(
                x=x, y=1.08, xref="paper", yref="paper",
                text=f"<b>{tahun}</b>", showarrow=False,
                font=dict(size=13, color="#333"),
            )

        st.plotly_chart(fig_sankey, use_container_width=True)

        st.markdown(
            "<div style='font-size:13px; color:#555;'>"
            "Warna node: 🟢 Digital Maju · 🟡 Digital Menengah · 🔴 Digital Rendah · 🔵 Digital Spesialis Non-Tunai. "
            "Ketebalan alur menunjukkan jumlah provinsi yang berpindah klaster antar tahun."
            "</div>",
            unsafe_allow_html=True
        )

    except Exception as e:
        st.error(f"Gagal membuat Sankey diagram: {e}")
        
    st.divider()

    col_tabel, col_tren = st.columns(2)
    
    with col_tabel:
        st.subheader("Daftar Perubahan Klaster")
        st.markdown("Provinsi yang mengalami perpindahan klaster dari tahun ke tahun:")
        
        change_records = []
        years = sorted(df['Tahun'].unique())
        
        for i in range(len(years) - 1):
            y1, y2 = years[i], years[i + 1]
            df_y1 = df[df['Tahun'] == y1].set_index('Provinsi')['Target_Semantic']
            df_y2 = df[df['Tahun'] == y2].set_index('Provinsi')['Target_Semantic']
            
            for prov in df_y1.index:
                if prov in df_y2.index and df_y1[prov] != df_y2[prov]:
                    change_records.append({
                        'Provinsi': prov,
                        'Tahun Awal': y1,
                        'Klaster Awal': df_y1[prov],
                        'Tahun Akhir': y2,
                        'Klaster Akhir': df_y2[prov]
                    })
        
        if change_records:
            df_changes = pd.DataFrame(change_records)
            st.dataframe(df_changes, use_container_width=True, hide_index=True)
        else:
            st.info("Tidak ada perubahan klaster antar tahun.")

    with col_tren:
        st.subheader("Tren Makro Adopsi Digital")
        st.markdown("Nilai rata-rata indikator transaksi nasional (2021-2025):")
        
        indikator_cols = ['outflow_tunai', 'kartu_atm_debet', 'Server_Based', 'SKNBI_Asal']
        avail_cols = [col for col in indikator_cols if col in df.columns]
        
        if avail_cols:
            df_trend = df.groupby('Tahun')[avail_cols].mean().reset_index()
            df_trend_melted = df_trend.melt(id_vars='Tahun', value_vars=avail_cols, 
                                            var_name='Indikator', value_name='Nilai Rata-rata')
            fig_trend = px.line(df_trend_melted, x='Tahun', y='Nilai Rata-rata', color='Indikator', 
                                markers=True)
            fig_trend.update_layout(
                height=350,
                margin=dict(l=0, r=0, t=10, b=0),
                legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1)
            )
            fig_trend.update_xaxes(dtick=1)
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.warning("Data indikator tidak ditemukan.")

    st.divider()

    with st.expander("Evaluasi Stabilitas Klaster per Tahun (Metodologi)", expanded=False):
        st.markdown("Metrik evaluasi model K-Means (k=4) dari 2021 hingga 2025 untuk melihat konsistensi segmentasi klaster:") 
        
        if 'Tahun' in df_metrics.columns:
            df_metrics = df_metrics.set_index('Tahun')
        
        fig = plt.figure(figsize=(15, 10))
        metrics_to_plot = df_metrics.columns
        
        for i, metric in enumerate(metrics_to_plot, 1):
            plt.subplot(len(metrics_to_plot), 1, i)
            sns.lineplot(data=df_metrics, x=df_metrics.index, y=metric, markers=True, marker = 'o')
            plt.title(f'{metric} per Tahun', fontsize=12)
            plt.xlabel('Tahun', fontsize=10)
            plt.ylabel(metric, fontsize=10)
            plt.grid(True, linestyle='--', alpha=0.7)  
            plt.xticks(df_metrics.index)

            for x, y in zip(df_metrics.index, df_metrics[metric]):
                plt.text(x, y, f'{y:.2f}', fontsize=8, ha='right', va='bottom')
        
        plt.suptitle("Evaluasi Stabilitas Klaster k=4 per Tahun", fontsize=16, y=1.02)
        plt.tight_layout(rect=[0, 0, 1, 0.98])

        st.pyplot(fig)

elif halaman == "Profil & Perbandingan Provinsi":
    st.title("Profil & Perbandingan Provinsi")
    st.markdown(
        "Halaman ini memungkinkan analisis mendalam untuk membandingkan profil adopsi digital "
        "serta tren historis antar provinsi."
    )
    st.divider()

    provinsi_list = sorted(df['Provinsi'].unique().tolist())
    default_prov = provinsi_list[:3] if len(provinsi_list) >= 3 else provinsi_list

    selected_provinsi = st.multiselect(
        "Pilih Provinsi untuk Dibandingkan (Disarankan maksimal 5 provinsi):",
        options=provinsi_list,
        default=default_prov
    )

    if len(selected_provinsi) > 5:
        st.warning("⚠️ Memilih lebih dari 5 provinsi dapat membuat grafik visualisasi menjadi padat dan sulit dibaca.")

    if not selected_provinsi:
        st.info("💡 Silakan pilih minimal satu provinsi pada selektor di atas untuk menampilkan analisis.")
    else:
        indikator_cols = ['outflow_tunai', 'kartu_atm_debet', 'Server_Based', 'SKNBI_Asal']
        ind_labels = {
            'outflow_tunai': 'Outflow Tunai',
            'kartu_atm_debet': 'Kartu ATM/Debet',
            'Server_Based': 'Server Based',
            'SKNBI_Asal': 'SKNBI Asal'
        }

        df_norm = df.copy()
        for col in indikator_cols:
            min_val = df[col].min()
            max_val = df[col].max()
            if max_val != min_val:
                df_norm[col] = ((df[col] - min_val) / (max_val - min_val)) * 100
            else:
                df_norm[col] = 0

        st.divider()

        col_radar, col_line = st.columns(2)
        
        # Heatmap Chart
        with col_radar:
            st.subheader("Profil Kekuatan Indikator (Heatmap)")
            
            tahun_radar = st.selectbox(
                "Pilih Tahun Analisis Kinerja:", 
                options=sorted(df['Tahun'].unique(), reverse=True),
                key="tahun_radar_profil"
            )
            
            st.markdown(
                f"<small><i>Warna yang lebih gelap menunjukkan nilai indikator yang lebih tinggi/kuat pada skala 0-100 untuk tahun {tahun_radar}.</i></small>",
                unsafe_allow_html=True
            )

            df_radar_filtered = df_norm[
                (df_norm['Provinsi'].isin(selected_provinsi)) & 
                (df_norm['Tahun'] == tahun_radar)
            ]

            if not df_radar_filtered.empty:
                df_heatmap = df_radar_filtered.set_index('Provinsi')[indikator_cols]
                df_heatmap.columns = [ind_labels[col] for col in df_heatmap.columns]

                fig_heat = px.imshow(
                    df_heatmap,
                    text_auto=".1f",
                    aspect="auto",
                    color_continuous_scale="Blues",
                    labels=dict(x="Indikator", y="Provinsi", color="Skor")
                )
                
                fig_heat.update_layout(
                    height=420, 
                    margin=dict(l=20, r=20, t=30, b=30),
                    coloraxis_showscale=False 
                )
                fig_heat.update_xaxes(side="bottom", tickfont=dict(size=10))
                fig_heat.update_yaxes(tickfont=dict(size=11))
                
                st.plotly_chart(fig_heat, use_container_width=True)
            else:
                st.warning("Data tidak tersedia untuk kombinasi filter ini.")

        # Line Chart
        with col_line:
            st.subheader("Tren Historis Indikator (2021–2025)")
            st.markdown("<small><i>Menampilkan visualisasi terpisah untuk memantau pergerakan nilai aktual.</i></small>", unsafe_allow_html=True)

            df_line_filtered = df[df['Provinsi'].isin(selected_provinsi)].sort_values('Tahun')
            grid_c1, grid_c2 = st.columns(2)

            for idx, col_name in enumerate(indikator_cols):
                with (grid_c1 if idx % 2 == 0 else grid_c2):
                    fig_small = px.line(
                        df_line_filtered, 
                        x='Tahun', 
                        y=col_name, 
                        color='Provinsi',
                        title=f"<b>{ind_labels[col_name]}</b>",
                        markers=True
                    )
                    
                    fig_small.update_layout(
                        height=200, 
                        margin=dict(l=10, r=10, t=40, b=10),
                        showlegend=False
                    )
                    fig_small.update_xaxes(dtick=1, title=None, tickfont=dict(size=9))
                    fig_small.update_yaxes(title=None, tickfont=dict(size=9))
                    st.plotly_chart(fig_small, use_container_width=True)

        st.divider()
        with st.expander("📊 Tabel Data Mentah Aktual & Ekspor Lampiran", expanded=False):
            st.markdown("Berikut adalah data aktual hasil filter wilayah untuk kebutuhan lampiran dokumen anggaran:")
            
            kolom_tabel = ['Provinsi', 'Tahun', 'Target_Semantic'] + indikator_cols
            df_table = df[df['Provinsi'].isin(selected_provinsi)][kolom_tabel].sort_values(['Provinsi', 'Tahun'])
            df_table_renamed = df_table.rename(columns=ind_labels)
            st.dataframe(df_table_renamed, use_container_width=True, hide_index=True)
            csv_data = df_table.to_csv(index=False).encode('utf-8')

            st.download_button(
                label="📥 Ekspor Data ke CSV",
                data=csv_data,
                file_name=f"data_aktual_perbandingan_{len(selected_provinsi)}_provinsi.csv",
                mime="text/csv",
                help="Klik di sini untuk mengunduh berkas tabel mentah dalam format CSV."
            )

elif halaman == "Metodologi & Validitas Model":
    st.title("🛡️ Metodologi & Validitas Model")
    st.markdown(
        "Halaman ini menyajikan dokumentasi teknis, pengujian validitas instrumen, "
        "dan transparansi algoritma yang ditujukan bagi penelaah akademis, peneliti, serta auditor internal."
    )
    st.divider()

    st.subheader("1. Ringkasan Alur Pemrosesan Data & Pemodelan")
    st.markdown(
        "Alur pemrosesan data ujung-ke-ujung (*end-to-end*) dirancang untuk memastikan "
        "kestabilan model dari bias skala dan skewness distribusi variabel ekonomi:"
    )
    
    # Representasi visual alur menggunakan blok HTML yang clean
    st.markdown("""
    <div style="display: flex; flex-wrap: wrap; gap: 8px; align-items: center; justify-content: center; background-color: #f8f9fa; padding: 20px; border-radius: 8px; border: 1px solid #e6e8eb; margin-bottom: 25px;">
        <div style="background-color: #34495e; color: white; padding: 8px 12px; border-radius: 4px; font-size: 12px; font-weight: bold;">Data Mentah Bulanan</div>
        <div style="font-weight: bold; color: #95a5a6;">→</div>
        <div style="background-color: #34495e; color: white; padding: 8px 12px; border-radius: 4px; font-size: 12px; font-weight: bold;">Agregasi Tahunan (Mean)</div>
        <div style="font-weight: bold; color: #95a5a6;">→</div>
        <div style="background-color: #2980b9; color: white; padding: 8px 12px; border-radius: 4px; font-size: 12px; font-weight: bold;">Transformasi log1p</div>
        <div style="font-weight: bold; color: #95a5a6;">→</div>
        <div style="background-color: #2980b9; color: white; padding: 8px 12px; border-radius: 4px; font-size: 12px; font-weight: bold;">RobustScaler</div>
        <div style="font-weight: bold; color: #95a5a6;">→</div>
        <div style="background-color: #27ae60; color: white; padding: 8px 12px; border-radius: 4px; font-size: 12px; font-weight: bold;">Elbow Method (k Optimal)</div>
        <div style="font-weight: bold; color: #95a5a6;">→</div>
        <div style="background-color: #27ae60; color: white; padding: 8px 12px; border-radius: 4px; font-size: 12px; font-weight: bold;">K-Means (k=4)</div>
        <div style="font-weight: bold; color: #95a5a6;">→</div>
        <div style="background-color: #8e44ad; color: white; padding: 8px 12px; border-radius: 4px; font-size: 12px; font-weight: bold;">Linear Sum Assignment</div>
        <div style="font-weight: bold; color: #95a5a6;">→</div>
        <div style="background-color: #d35400; color: white; padding: 8px 12px; border-radius: 4px; font-size: 12px; font-weight: bold;">Label Semantik</div>
    </div>
    """, unsafe_allow_html=True)


    st.subheader("2. Konfigurasi Parameter Hiperparameter Model")
    
    param_data = {
        "Komponen Model / Arsitektur": [
            "Algoritma Klasterisasi",
            "Jumlah Klaster (k Target)",
            "Kriteria Penentuan Nilai k",
            "Penyemaian Acak (Random State)",
            "Jumlah Inisialisasi Paralel (n_init)",
            "Metode Penyekalaan Fitur",
            "Metode Reduksi Dimensi Visual"
        ],
        "Spesifikasi Teknis / Nilai Kontrol": [
            "K-Means (Scikit-Learn Library)",
            "4 Klaster",
            "Elbow Method & KElbowVisualizer Distortion Score",
            "42 (Untuk Konsistensi Hasil Reproduksi)",
            "10 Iterasi Berbeda",
            "RobustScaler (Tahan Terhadap Efek Pencilan/Outliers)",
            "PCA (Principal Component Analysis) - 2 Komponen Utama"
        ]
    }
    st.table(pd.DataFrame(param_data))

    # Matrik Eval
    st.subheader("3. Validitas Internal & Metrik Evaluasi")
    st.markdown(
        "Kinerja struktural pembentukan partisi klaster dievaluasi secara berkala "
        "pada setiap run korpus tahunan untuk menguji stabilitas model matematika:"
    )

    df_metrics_tampil = df_metrics.copy()

    # Menampilkan tabel ringkasan metrik
    st.dataframe(df_metrics_tampil, use_container_width=True, hide_index=True)

    # Grid Grafik Garis Metrik
    kolom_metrik = [c for c in df_metrics_tampil.columns if c != 'Tahun']

    deskripsi_metrik = {
        "WCSS": ("WCSS / Inertia", "Mengukur kepadatan internal.", "Ambang: Lebih Rendah = Lebih Rapat", "#E74C3C"),
        "WCSS (Inersia)": ("WCSS / Inertia", "Mengukur kepadatan internal.", "Ambang: Lebih Rendah = Lebih Rapat", "#E74C3C"),
        "Silhouette": ("Silhouette Score", "Mengukur derajat pemisahan.", "Ambang: Mendekati 1 = Terpisah Baik", "#2ECC71"),
        "Silhouette Score": ("Silhouette Score", "Mengukur derajat pemisahan.", "Ambang: Mendekati 1 = Terpisah Baik", "#2ECC71"),
        "Calinski_Harabasz": ("Calinski-Harabasz", "Rasio dispersi antar-dalam klaster.", "Ambang: Lebih Tinggi = Lebih Baik", "#3498DB"),
        "Calinski-Harabasz Score": ("Calinski-Harabasz", "Rasio dispersi antar-dalam klaster.", "Ambang: Lebih Tinggi = Lebih Baik", "#3498DB"),
        "Davies_Bouldin": ("Davies-Bouldin", "Rasio jarak internal terhadap eksternal.", "Ambang: Mendekati 0 = Partisi Optimal", "#F1C40F"),
        "Davies-Bouldin Score": ("Davies-Bouldin", "Rasio jarak internal terhadap eksternal.", "Ambang: Mendekati 0 = Partisi Optimal", "#F1C40F"),
    }
    warna_fallback = ["#E74C3C", "#2ECC71", "#3498DB", "#F1C40F"]

    def buat_grafik_metrik(df, y_col, judul, penjelasan, ambang, warna):
        fig = px.line(df, x='Tahun', y=y_col, markers=True, color_discrete_map={y_col: warna})
        fig.update_layout(
            height=240, margin=dict(l=20, r=20, t=50, b=20),
            title=dict(text=f"<b>{judul}</b><br><span style='font-size:10px;color:grey;'>{ambang}</span>", font=dict(size=12))
        )
        fig.update_xaxes(dtick=1, title=None)
        fig.update_yaxes(title=None)
        return fig

    kolom_metrik_tampil = kolom_metrik[:4]
    if kolom_metrik_tampil:
        grid_metrik = st.columns(len(kolom_metrik_tampil))
        for i, kolom in enumerate(kolom_metrik_tampil):
            judul, penjelasan, ambang, warna = deskripsi_metrik.get(
                kolom, (kolom, "Metrik evaluasi klaster.", "", warna_fallback[i % len(warna_fallback)])
            )
            with grid_metrik[i]:
                st.plotly_chart(
                    buat_grafik_metrik(df_metrics_tampil, kolom, judul, penjelasan, ambang, warna),
                    use_container_width=True
                )
    else:
        st.warning("Kolom metrik tidak ditemukan pada metrics_results.csv.")

    # PCA 
    st.divider()
    st.subheader("4. Visualisasi Ruang Sebaran Komponen Utama (PCA)")
    
    tahun_metodologi = st.slider("Pilih Tahun untuk Struktur Geometris PCA:", 2021, 2025, 2025, key="slider_pca")
    df_pca = df[df['Tahun'] == tahun_metodologi]
    
    if 'PCA1' in df.columns and 'PCA2' in df.columns:
        kolom_indikator = ['outflow_tunai', 'kartu_atm_debet', 'Server_Based', 'SKNBI_Asal']
        kolom_indikator_tersedia = [k for k in kolom_indikator if k in df_pca.columns]

        hover_data_pca = {'PCA1': ':.4f', 'PCA2': ':.4f', 'Target_Semantic': True}
        if 'Cluster_raw' in df_pca.columns:
            hover_data_pca['Cluster_raw'] = True
        for kolom in kolom_indikator_tersedia:
            hover_data_pca[kolom] = ':.3f'

        fig_scatter_pca = px.scatter(
            df_pca, x='PCA1', y='PCA2',
            color='Target_Semantic',
            hover_name='Provinsi',
            hover_data=hover_data_pca,
            color_discrete_map={klaster: palet_warna.get(klaster, warna_default) for klaster in df_pca['Target_Semantic'].unique()},
            title=f"Proyeksi Partisi Klaster pada Bidang Dua Dimensi PCA ({tahun_metodologi})"
        )
        fig_scatter_pca.update_traces(textposition='top center', marker=dict(size=10, line=dict(width=0.5, color='DarkSlateGrey')))
        fig_scatter_pca.update_layout(
            height=550,
            xaxis_title="Komponen Utama 1 (PCA1) — Menjelaskan variansi mayoritas data",
            yaxis_title="Komponen Utama 2 (PCA2) — Menjelaskan variansi sisa",
            legend=dict(title="Klaster Semantik", orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_scatter_pca, use_container_width=True)
    else:
        st.warning("Data koordinat komponen utama PCA tidak ditemukan di dataset hasil.")

    # Heatmap Centroid
    st.divider()
    st.subheader("5. Analisis Matriks Karakteristik Centroid (Dasar Penamaan)")
    st.markdown(
        "Karakteristik kuantitatif dari rata-rata nilai indikator tertransformasi "
        "yang menjadi penentu klasifikasi dan rujukan pemberian label semantik regional:"
    )
    
    indikator_analisis = ['outflow_tunai', 'kartu_atm_debet', 'Server_Based', 'SKNBI_Asal']
    ind_labels_map = {
        'outflow_tunai': 'Outflow Tunai',
        'kartu_atm_debet': 'Kartu ATM/Debet',
        'Server_Based': 'Server Based',
        'SKNBI_Asal': 'SKNBI Asal'
    }
    
    # Hitung rata-rata tiap indikator untuk basis pembentukan centroid
    df_centroid_map = df.groupby('Target_Semantic')[indikator_analisis].mean().rename(columns=ind_labels_map)
    
    fig_centroid_heatmap = px.imshow(
        df_centroid_map,
        labels=dict(x="Indikator Keuangan/Transaksi", y="Label Klaster Semantik", color="Nilai Skala Log Mean"),
        x=df_centroid_map.columns,
        y=df_centroid_map.index,
        color_continuous_scale="RdBu_r",
        text_auto=".3f"
    )
    fig_centroid_heatmap.update_layout(height=380, margin=dict(t=20, b=20))
    st.plotly_chart(fig_centroid_heatmap, use_container_width=True)

    # Keterbatasan model dan catatan teknis
    st.divider()
    st.subheader("6. Batasan Teknis & Keterbatasan Model (Limitations)")
    
    st.info(
        "Aplikasi kebijakan berbasis data spasial wajib mempertimbangkan beberapa restriksi objektif "
        "berikut guna menghindari kesalahan interpretasi keputusan:"
    )
    
    st.markdown("""
    * **Granularitas Temporal Makro**: Data yang diolah berbasis agregat nilai tahunan (*annual mean*). Pendekatan ini berpotensi mereduksi atau menghilangkan variasi pergerakan musiman (*seasonal monthly variations*) seperti lonjakan transaksi tunai menjelang Idul Fitri atau masa libur akhir tahun.
    * **Anomali Struktural Ibu Kota**: Klaster *'Digital Spesialis Non-Tunai'* mencerminkan profil anomali spasial dan struktur sirkulasi ekonomi unik DKI Jakarta sebagai pusat perputaran uang dan kliring nasional. Karakteristik ini tidak dapat dijadikan bahan acuan generalisasi regulasi langsung ke wilayah kepulauan lain secara pukul rata.
    * **Karakteristik Skala RobustScaler**: Penyekalaan berbasis median dan interkuartil (*RobustScaler*) sangat handal dalam mengisolasi bias pencilan (*outliers*), namun tidak mengeliminasi ketimpangan kesenjangan ekonomi riil. Provinsi dengan basis volume ekonomi masif akan selalu menduduki klaster dominan secara persisten.
    """)

    st.divider()
    st.subheader("7. Pusat Repositori Data & Dokumen Terbuka")
    st.markdown("Unduh berkas lampiran pendukung analisis komparasi untuk arsip akuntabilitas:")

    def buat_pdf_metodologi(df, df_metrics_tampil, palet_warna, warna_default, param_data, tahun_pca):
        """Membangun PDF lengkap berisi seluruh isi halaman Metodologi & Validitas Model
        (struktur sama seperti halaman deploy: bagian 1-6), termasuk tabel dan grafik,
        menggunakan reportlab (dokumen) + matplotlib/seaborn (grafik dirender sebagai gambar)."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            leftMargin=1.8 * cm, rightMargin=1.8 * cm, topMargin=1.6 * cm, bottomMargin=1.6 * cm
        )
        styles = getSampleStyleSheet()
        style_judul = ParagraphStyle('JudulUtama', parent=styles['Title'], fontSize=18, spaceAfter=6)
        style_subjudul = ParagraphStyle('SubJudul', parent=styles['Heading2'], fontSize=13,
                                         spaceBefore=14, spaceAfter=6, textColor=colors.HexColor('#1a1a1a'))
        style_body = ParagraphStyle('BodyTeks', parent=styles['Normal'], fontSize=10, leading=14)
        style_kotak_alur = ParagraphStyle('KotakAlur', parent=styles['Normal'], fontSize=8,
                                           textColor=colors.white, alignment=1)
 
        story = []
 
        # Judul & deskripsi halaman
        story.append(Paragraph("Metodologi & Validitas Model", style_judul))
        story.append(Paragraph(
            "Halaman ini menyajikan dokumentasi teknis, pengujian validitas instrumen, "
            "dan transparansi algoritma yang ditujukan bagi penelaah akademis, peneliti, serta auditor internal.",
            style_body
        ))
        story.append(Spacer(1, 10))
 
        # 1. Ringkasan Alur Pemrosesan Data & Pemodelan
        story.append(Paragraph("1. Ringkasan Alur Pemrosesan Data & Pemodelan", style_subjudul))
        story.append(Paragraph(
            "Alur pemrosesan data ujung-ke-ujung (<i>end-to-end</i>) dirancang untuk memastikan "
            "kestabilan model dari bias skala dan skewness distribusi variabel ekonomi:",
            style_body
        ))
        story.append(Spacer(1, 6))
 
        alur_langkah = [
            ("Data Mentah Bulanan", "#34495e"),
            ("Agregasi Tahunan (Mean)", "#34495e"),
            ("Transformasi log1p", "#2980b9"),
            ("RobustScaler", "#2980b9"),
            ("Elbow Method (k Optimal)", "#27ae60"),
            ("K-Means (k=4)", "#27ae60"),
            ("Linear Sum Assignment", "#8e44ad"),
            ("Label Semantik", "#d35400"),
        ]
        for awal in range(0, len(alur_langkah), 4):
            kelompok = alur_langkah[awal:awal + 4]
            baris_kotak = [[Paragraph(teks, style_kotak_alur) for teks, _ in kelompok]]
            tabel_alur = Table(baris_kotak, colWidths=[4.2 * cm] * len(kelompok))
            gaya_alur = [
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]
            for idx, (_, warna_hex) in enumerate(kelompok):
                gaya_alur.append(('BACKGROUND', (idx, 0), (idx, 0), colors.HexColor(warna_hex)))
            tabel_alur.setStyle(TableStyle(gaya_alur))
            story.append(tabel_alur)
            story.append(Spacer(1, 4))
        story.append(Spacer(1, 8))
 
        # 2. Konfigurasi Parameter Hiperparameter Model
        story.append(Paragraph("2. Konfigurasi Parameter Hiperparameter Model", style_subjudul))
        data_param_tabel = [["Komponen Model / Arsitektur", "Spesifikasi Teknis / Nilai Kontrol"]]
        for komp, spek in zip(param_data["Komponen Model / Arsitektur"], param_data["Spesifikasi Teknis / Nilai Kontrol"]):
            data_param_tabel.append([komp, spek])
        tabel_param = Table(data_param_tabel, colWidths=[7 * cm, 9 * cm])
        tabel_param.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f3f5')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8.5),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#dee2e6')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(tabel_param)
        story.append(Spacer(1, 10))
 
        # 3. Validitas Internal & Metrik Evaluasi
        story.append(Paragraph("3. Validitas Internal & Metrik Evaluasi", style_subjudul))
        story.append(Paragraph(
            "Kinerja struktural pembentukan partisi klaster dievaluasi secara berkala pada setiap run "
            "korpus tahunan untuk menguji stabilitas model matematika:",
            style_body
        ))
        story.append(Spacer(1, 6))
 
        kolom_df = list(df_metrics_tampil.columns)
        data_metrik_tabel = [kolom_df] + df_metrics_tampil.round(4).astype(str).values.tolist()
        lebar_kolom = (16 / len(kolom_df)) * cm
        tabel_metrik = Table(data_metrik_tabel, colWidths=[lebar_kolom] * len(kolom_df))
        tabel_metrik.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f3f5')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#dee2e6')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(tabel_metrik)
        story.append(Spacer(1, 10))
 
        deskripsi_metrik_pdf = {
            "WCSS": ("WCSS / Inertia", "#E74C3C"), "WCSS (Inersia)": ("WCSS / Inertia", "#E74C3C"),
            "Silhouette": ("Silhouette Score", "#2ECC71"), "Silhouette Score": ("Silhouette Score", "#2ECC71"),
            "Calinski_Harabasz": ("Calinski-Harabasz", "#3498DB"), "Calinski-Harabasz Score": ("Calinski-Harabasz", "#3498DB"),
            "Davies_Bouldin": ("Davies-Bouldin", "#F1C40F"), "Davies-Bouldin Score": ("Davies-Bouldin", "#F1C40F"),
        }
        warna_fallback_pdf = ["#E74C3C", "#2ECC71", "#3498DB", "#F1C40F"]
        kolom_metrik_pdf = [c for c in kolom_df if c != 'Tahun'][:4]
 
        gambar_metrik = []
        for i, kolom in enumerate(kolom_metrik_pdf):
            judul_grafik, warna_grafik = deskripsi_metrik_pdf.get(
                kolom, (kolom, warna_fallback_pdf[i % len(warna_fallback_pdf)])
            )
            fig_kecil, ax_kecil = plt.subplots(figsize=(2.6, 1.9))
            ax_kecil.plot(df_metrics_tampil['Tahun'], df_metrics_tampil[kolom],
                          marker='o', color=warna_grafik, linewidth=1.5)
            ax_kecil.set_title(judul_grafik, fontsize=8)
            ax_kecil.tick_params(labelsize=6)
            ax_kecil.grid(True, linestyle='--', alpha=0.4)
            fig_kecil.tight_layout()
            buf_gambar = io.BytesIO()
            fig_kecil.savefig(buf_gambar, format='png', dpi=150)
            plt.close(fig_kecil)
            buf_gambar.seek(0)
            gambar_metrik.append(Image(buf_gambar, width=4 * cm, height=2.9 * cm))
 
        if gambar_metrik:
            tabel_gambar_metrik = Table([gambar_metrik], colWidths=[4 * cm] * len(gambar_metrik))
            tabel_gambar_metrik.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER')]))
            story.append(tabel_gambar_metrik)
        story.append(Spacer(1, 10))
 
        # 4. Visualisasi Ruang Sebaran Komponen Utama (PCA)
        story.append(PageBreak())
        story.append(Paragraph("4. Visualisasi Ruang Sebaran Komponen Utama (PCA)", style_subjudul))
        if 'PCA1' in df.columns and 'PCA2' in df.columns:
            df_pca_pdf = df[df['Tahun'] == tahun_pca]
            fig_pca, ax_pca = plt.subplots(figsize=(6.3, 4.4))
            for klaster in sorted(df_pca_pdf['Target_Semantic'].unique()):
                subset = df_pca_pdf[df_pca_pdf['Target_Semantic'] == klaster]
                ax_pca.scatter(subset['PCA1'], subset['PCA2'], label=klaster,
                                color=palet_warna.get(klaster, warna_default),
                                s=40, edgecolor='black', linewidth=0.3)
            ax_pca.set_xlabel("Komponen Utama 1 (PCA1)", fontsize=8)
            ax_pca.set_ylabel("Komponen Utama 2 (PCA2)", fontsize=8)
            ax_pca.set_title(f"Proyeksi Partisi Klaster pada Bidang Dua Dimensi PCA ({tahun_pca})", fontsize=9)
            ax_pca.legend(fontsize=6, loc='best')
            ax_pca.tick_params(labelsize=7)
            fig_pca.tight_layout()
            buf_pca = io.BytesIO()
            fig_pca.savefig(buf_pca, format='png', dpi=150)
            plt.close(fig_pca)
            buf_pca.seek(0)
            story.append(Image(buf_pca, width=15 * cm, height=10.5 * cm))
        else:
            story.append(Paragraph("Data koordinat komponen utama PCA tidak ditemukan di dataset hasil.", style_body))
        story.append(Spacer(1, 10))
 
        # 5. Analisis Matriks Karakteristik Centroid
        story.append(Paragraph("5. Analisis Matriks Karakteristik Centroid (Dasar Penamaan)", style_subjudul))
        story.append(Paragraph(
            "Karakteristik kuantitatif dari rata-rata nilai indikator tertransformasi yang menjadi penentu "
            "klasifikasi dan rujukan pemberian label semantik regional:",
            style_body
        ))
        story.append(Spacer(1, 6))
 
        indikator_analisis_pdf = ['outflow_tunai', 'kartu_atm_debet', 'Server_Based', 'SKNBI_Asal']
        label_indikator_pdf = {
            'outflow_tunai': 'Outflow Tunai', 'kartu_atm_debet': 'Kartu ATM/Debet',
            'Server_Based': 'Server Based', 'SKNBI_Asal': 'SKNBI Asal'
        }
        df_centroid_pdf = df.groupby('Target_Semantic')[indikator_analisis_pdf].mean().rename(columns=label_indikator_pdf)
 
        fig_heat, ax_heat = plt.subplots(figsize=(6, 3.2))
        sns.heatmap(df_centroid_pdf, annot=True, fmt=".3f", cmap="RdBu_r", ax=ax_heat,
                    cbar_kws={'label': 'Nilai Skala Log Mean'}, annot_kws={"size": 7})
        ax_heat.set_xlabel("Indikator Keuangan/Transaksi", fontsize=8)
        ax_heat.set_ylabel("Label Klaster Semantik", fontsize=8)
        ax_heat.tick_params(labelsize=7)
        fig_heat.tight_layout()
        buf_heat = io.BytesIO()
        fig_heat.savefig(buf_heat, format='png', dpi=150)
        plt.close(fig_heat)
        buf_heat.seek(0)
        story.append(Image(buf_heat, width=14 * cm, height=7.5 * cm))
        story.append(Spacer(1, 10))
 
        # 6. Batasan Teknis & Keterbatasan Model
        story.append(Paragraph("6. Batasan Teknis & Keterbatasan Model (Limitations)", style_subjudul))
        story.append(Paragraph(
            "Aplikasi kebijakan berbasis data spasial wajib mempertimbangkan beberapa restriksi objektif "
            "berikut guna menghindari kesalahan interpretasi keputusan:",
            style_body
        ))
        story.append(Spacer(1, 4))
        poin_batasan = [
            "<b>Granularitas Temporal Makro</b>: Data yang diolah berbasis agregat nilai tahunan "
            "(<i>annual mean</i>). Pendekatan ini berpotensi mereduksi atau menghilangkan variasi pergerakan "
            "musiman (<i>seasonal monthly variations</i>) seperti lonjakan transaksi tunai menjelang Idul Fitri "
            "atau masa libur akhir tahun.",
            "<b>Anomali Struktural Ibu Kota</b>: Klaster 'Digital Spesialis Non-Tunai' mencerminkan profil "
            "anomali spasial dan struktur sirkulasi ekonomi unik DKI Jakarta sebagai pusat perputaran uang dan "
            "kliring nasional. Karakteristik ini tidak dapat dijadikan bahan acuan generalisasi regulasi "
            "langsung ke wilayah kepulauan lain secara pukul rata.",
            "<b>Karakteristik Skala RobustScaler</b>: Penyekalaan berbasis median dan interkuartil "
            "(<i>RobustScaler</i>) sangat handal dalam mengisolasi bias pencilan (<i>outliers</i>), namun tidak "
            "mengeliminasi ketimpangan kesenjangan ekonomi riil. Provinsi dengan basis volume ekonomi masif "
            "akan selalu menduduki klaster dominan secara persisten.",
        ]
        for poin in poin_batasan:
            story.append(Paragraph(f"• {poin}", style_body))
            story.append(Spacer(1, 4))
 
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
 
    dl_col1, dl_col2 = st.columns(2)

    with dl_col1:
        csv_file_bytes = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Unduh Hasil Klasterisasi (CSV)",
            data=csv_file_bytes,
            file_name="hasil_clustering_final.csv",
            mime="text/csv",
            use_container_width=True,
            help="Unduh tabel hasil akhir pelabelan klaster spasial seluruh provinsi."
        )

    with dl_col2:
        pdf_bytes = buat_pdf_metodologi(
            df, df_metrics_tampil, palet_warna, warna_default, param_data, tahun_metodologi   
        )
        st.download_button(
            label="📥 Unduh Dokumen Metodologi (PDF)",
            data=pdf_bytes,
            file_name="Dokumen_Metodologi_Validitas_Klaster.pdf",
            mime="application/pdf",
            use_container_width=True,
            help="Unduh berkas PDF buku putih (*whitepaper*) landasan teori riset."
        )