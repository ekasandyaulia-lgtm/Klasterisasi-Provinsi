import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from streamlit_option_menu import option_menu
import json
import plotly.graph_objects as go

# Unduh PDF
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet

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
            contoh_pdf = b"Data placeholder PDF. Integrasikan library seperti fpdf/reportlab untuk men-generate grafik dan teks dashboard ke PDF."
            st.download_button(
                label="Unduh PDF", 
                data=contoh_pdf, 
                file_name=f"Laporan_Overview_{tahun}.pdf", 
                mime="application/pdf", 
                use_container_width=True,
                help="Klik untuk mengunduh rekap laporan tahun ini dalam format PDF"
            )
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

            df_valid = df_merged[df_merged['Server_Based_prev'] > 1.0]
            if not df_valid.empty:
                row = df_valid.nlargest(1, 'growth').iloc[0]
            else:
                row = df_merged.nlargest(1, 'growth').iloc[0]
            provinsi_tertinggi = row['Provinsi']
            pertumbuhan_tertinggi = row['growth']

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
        
        # --- BAGIAN HEATMAP (PENGGANTI RADAR CHART) ---
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

        # --- BAGIAN LINE CHART TREN ---
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

    # ==============================================================
    # 3. PANEL METRIK EVALUASI (Tabel + Grafik Garis)
    # ==============================================================
    st.subheader("3. Validitas Internal & Metrik Evaluasi")
    st.markdown(
        "Kinerja struktural pembentukan partisi klaster dievaluasi secara berkala "
        "pada setiap run korpus tahunan untuk menguji stabilitas model matematika:"
    )

    # Menggunakan data metrik ASLI dari metrics_results.csv (df_metrics hasil load_data()),
    # bukan angka hardcoded, agar konsisten dengan angka yang ditampilkan
    # di halaman "Dinamika Temporal" > Evaluasi Stabilitas Klaster.
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

    # ==============================================================
    # 4. VISUALISASI SEBARAN PCA (Scatter Plot)
    # ==============================================================
    st.divider()
    st.subheader("4. Visualisasi Ruang Sebaran Komponen Utama (PCA)")
    
    tahun_metodologi = st.slider("Pilih Tahun untuk Struktur Geometris PCA:", 2021, 2025, 2025, key="slider_pca")
    df_pca = df[df['Tahun'] == tahun_metodologi]
    
    if 'PCA1' in df.columns and 'PCA2' in df.columns:
        fig_scatter_pca = px.scatter(
            df_pca, x='PCA1', y='PCA2',
            color='Target_Semantic',
            hover_name='Provinsi',
            text='Provinsi',
            color_discrete_map={klaster: palet_warna.get(klaster, warna_default) for klaster in df_pca['Target_Semantic'].unique()},
            title=f"Proyeksi Partisi Klaster pada Bidang Dua Dimensi PCA ({tahun_metodologi})"
        )
        fig_scatter_pca.update_traces(textposition='top center', marker=dict(size=10, line=dict(width=0.5, color='DarkSlateGrey')))
        fig_scatter_pca.update_layout(
            height=500,
            xaxis_title="Komponen Utama 1 (PCA1) — Menjelaskan variansi mayoritas data",
            yaxis_title="Komponen Utama 2 (PCA2) — Menjelaskan variansi sisa",
            legend=dict(title="Klaster Semantik", orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_scatter_pca, use_container_width=True)
    else:
        st.warning("Data koordinat komponen utama PCA tidak ditemukan di dataset hasil.")

    # ==============================================================
    # 5. HEATMAP KARAKTERISTIK CENTROID
    # ==============================================================
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

    # ==============================================================
    # 6. BAGIAN KETERBATASAN MODEL (Limitations)
    # ==============================================================
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

    # ==============================================================
    # 7. TAUTAN UNDUH (DATASET, NOTEBOOK, DOKUMEN)
    # ==============================================================
    st.divider()
    st.subheader("7. Pusat Repositori Data & Dokumen Terbuka")
    st.markdown("Unduh berkas lampiran pendukung analisis komparasi untuk arsip akuntabilitas:")
    
    dl_col1, dl_col2, dl_col3 = st.columns(3)
    
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
        st.download_button(
            label="📥 Unduh Notebook Pemodelan (.ipynb)",
            data=b"# Berkas Jupyter Notebook Analisis Klaster",
            file_name="Kmeans_Clustering_skripsi.ipynb",
            mime="application/octet-stream",
            use_container_width=True,
            help="Unduh catatan langkah eksperimen kode Python lengkap."
        )
        
    with dl_col3:
        st.download_button(
            label="📥 Unduh Dokumen Metodologi (PDF)",
            data=b"Laporan Kajian Metodologi Struktur Spasial Klaster Digital",
            file_name="Dokumen_Metodologi_Validitas_Klaster.pdf",
            mime="application/pdf",
            use_container_width=True,
            help="Unduh berkas PDF buku putih (*whitepaper*) landasan teori riset."
        )