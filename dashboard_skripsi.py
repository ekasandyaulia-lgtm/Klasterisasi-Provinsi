import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 0. KONFIGURASI HALAMAN & DATA
# ==========================================
st.set_page_config(page_title="Dashboard Klasterisasi Keuangan Digital", layout="wide", initial_sidebar_state="expanded")

# Tema Warna Konsisten 
COLOR_MAP = {
    'Digital Rendah': '#e74c3c',              # Merah 
    'Digital Menengah': '#f1c40f',            # Kuning 
    'Digital Maju': '#3498db',                # Biru 
    'Digital Spesialis Non-Tunai': '#2ecc71'  # Hijau 
}

@st.cache_data
def load_data():
    df = pd.read_csv('hasil_clustering_final.csv')
    return df

df = load_data()

# Header Dashboard
st.title("📊 Dinamika Klasterisasi Keuangan Digital Provinsi di Indonesia (2021–2025)")
st.markdown("Dashboard interaktif untuk menganalisis pergerakan, karakteristik, dan profil transaksi digital 34 Provinsi di Indonesia.")
st.markdown("---")

# ==========================================
# 1. LAYOUT TABS (Untuk Navigasi Sidang)
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📍 1. Profil & Peta Klaster", 
    "📈 2. Dinamika Temporal (2021-2025)", 
    "🔍 3. Analisis Spesifik Provinsi",
    "💡 4. Implikasi Kebijakan"
])

# ==========================================
# TAB 1: PETA KLASTER & PROFIL (Menjawab Q1 & Q2)
# ==========================================
with tab1:
    st.header("Peta Persebaran & Karakteristik Klaster")
    
    col_filter, col_desc = st.columns([1, 3])
    with col_filter:
        selected_year = st.selectbox("Pilih Tahun:", sorted(df['Tahun'].unique(), reverse=True))
    
    df_year = df[df['Tahun'] == selected_year]
    
    # Q2: Apakah pengelompokan ini timpang atau berimbang?
    st.subheader(f"Proporsi Klaster Provinsi (Tahun {selected_year})")
    
    cluster_counts = df_year['Target_Semantic'].value_counts().reset_index()
    cluster_counts.columns = ['Klaster', 'Jumlah']
    
    # Metrik di atas
    metrics_cols = st.columns(4)
    for i, row in cluster_counts.iterrows():
        color = COLOR_MAP.get(row['Klaster'], '#000000')
        metrics_cols[i].markdown(
            f"<div style='border: 2px solid {color}; border-radius: 8px; padding: 15px; text-align: center;'>"
            f"<h4 style='margin:0; color: {color};'>{row['Klaster']}</h4>"
            f"<h2 style='margin:0;'>{row['Jumlah']} Provinsi</h2>"
            f"</div>", 
            unsafe_allow_html=True
        )
    
    st.caption("💡 *Insight:* Komposisi klaster menunjukkan tingkat pemerataan adopsi digital. Dominasi di level 'Rendah' atau 'Menengah' mengindikasikan adopsi infrastruktur finansial digital yang masih terpusat.")
    st.write("")
    
    # Q1: Provinsi mana di kategori apa dan kenapa (PCA Scatter)
    st.markdown("### Pemetaan Kemiripan Karakteristik Provinsi (PCA)")
    fig_pca = px.scatter(
        df_year, x='PCA1', y='PCA2', 
        color='Target_Semantic', text='Provinsi',
        color_discrete_map=COLOR_MAP,
        hover_data=['outflow_tunai', 'kartu_atm_debet', 'Server_Based', 'SKNBI_Asal']
    )
    fig_pca.update_traces(textposition='top center', marker=dict(size=12, opacity=0.8))
    fig_pca.update_layout(height=650, showlegend=True, title="Distribusi Provinsi dalam Ruang PCA (Semakin berdekatan, semakin mirip perilakunya)")
    st.plotly_chart(fig_pca, use_container_width=True)

    # Q1: Karakteristik (Bar charts rata-rata)
    st.markdown("### Karakteristik Transaksi Rata-Rata per Klaster")
    st.markdown("Grafik di bawah menjawab *mengapa* algoritma K-Means membedakan mereka.")
    df_mean = df_year.groupby('Target_Semantic')[['outflow_tunai', 'kartu_atm_debet', 'Server_Based', 'SKNBI_Asal']].mean().reset_index()
    
    col_bar1, col_bar2 = st.columns(2)
    with col_bar1:
        fig_outflow = px.bar(df_mean, x='Target_Semantic', y='outflow_tunai', color='Target_Semantic', color_discrete_map=COLOR_MAP, title="Rata-rata Outflow Tunai (Rp Miliar)")
        fig_outflow.update_layout(showlegend=False)
        st.plotly_chart(fig_outflow, use_container_width=True)
        
        fig_atm = px.bar(df_mean, x='Target_Semantic', y='kartu_atm_debet', color='Target_Semantic', color_discrete_map=COLOR_MAP, title="Rata-rata Penggunaan ATM/Debit (Juta Unit)")
        fig_atm.update_layout(showlegend=False)
        st.plotly_chart(fig_atm, use_container_width=True)
        
    with col_bar2:
        fig_server = px.bar(df_mean, x='Target_Semantic', y='Server_Based', color='Target_Semantic', color_discrete_map=COLOR_MAP, title="Rata-rata Uang Elektronik/Server-Based (Juta Unit)")
        fig_server.update_layout(showlegend=False)
        st.plotly_chart(fig_server, use_container_width=True)
        
        fig_sknbi = px.bar(df_mean, x='Target_Semantic', y='SKNBI_Asal', color='Target_Semantic', color_discrete_map=COLOR_MAP, title="Rata-rata Transaksi SKNBI (Rp Miliar)")
        fig_sknbi.update_layout(showlegend=False)
        st.plotly_chart(fig_sknbi, use_container_width=True)

# ==========================================
# TAB 2: DINAMIKA TEMPORAL (Menjawab Q3)
# ==========================================
with tab2:
    st.header("Dinamika Perubahan Klaster (2021 - 2025)")
    st.markdown("Bagian ini memvisualisasikan **perjalanan waktu (temporal)**. Kita dapat melacak provinsi mana yang secara progresif naik level digital, dan mana yang stagnan.")

    # 1. Area/Bar Chart Komposisi Klaster per Tahun
    df_temporal = df.groupby(['Tahun', 'Target_Semantic']).size().reset_index(name='Jumlah')
    fig_temporal = px.bar(
        df_temporal, x='Tahun', y='Jumlah', color='Target_Semantic', 
        color_discrete_map=COLOR_MAP, title="Evolusi Proporsi Klaster Digital (2021-2025)",
        text='Jumlah'
    )
    fig_temporal.update_layout(barmode='stack', xaxis_type='category')
    st.plotly_chart(fig_temporal, use_container_width=True)

    # 2. Tabel Deteksi Pergerakan Kelas
    st.subheader("Provinsi yang Mengalami Transisi Klaster (2021 vs 2025)")
    
    df_2021 = df[df['Tahun'] == 2021].set_index('Provinsi')['Target_Semantic'].rename('Status_2021')
    df_2025 = df[df['Tahun'] == 2025].set_index('Provinsi')['Target_Semantic'].rename('Status_2025')
    
    perubahan = pd.concat([df_2021, df_2025], axis=1).reset_index()
    perubahan_aktif = perubahan[perubahan['Status_2021'] != perubahan['Status_2025']]
    
    if perubahan_aktif.empty:
        st.info("Tidak ada provinsi yang berpindah klaster antara 2021 dan 2025 (Kondisi Stagnan).")
    else:
        st.dataframe(
            perubahan_aktif.style.apply(lambda x: ['background: lightgreen' if x['Status_2021'] != x['Status_2025'] else '' for i in x], axis=1), 
            use_container_width=True
        )
        st.caption("💡 *Insight:* Provinsi di atas menunjukkan anomali positif/negatif yang patut dibahas lebih lanjut terkait program literasi atau digitalisasi daerah mereka.")

    # 3. Bump Chart / Parallel Categories (Flow)
    st.markdown("### Alur Transisi Klaster Sepanjang Tahun (Sankey / Parallel Categories)")
    # Prepare data for parallel categories
    df_pivot = df.pivot(index='Provinsi', columns='Tahun', values='Target_Semantic').reset_index()
    fig_parcats = px.parallel_categories(
        df_pivot, dimensions=[2021, 2022, 2023, 2024, 2025],
        title="Alur Evolusi Status Klaster per Provinsi",
        color_continuous_scale=px.colors.sequential.Inferno
    )
    # Applying colors is a bit tricky in parcats with categorical data, so we leave it as default or use go.Parcats
    st.plotly_chart(fig_parcats, use_container_width=True)


# ==========================================
# TAB 3: DRILL-DOWN PROVINSI (Menjawab Q4)
# ==========================================
with tab3:
    st.header("Analisis Spesifik Per Provinsi")
    st.markdown("Membongkar pola transaksi historis dan tren untuk satu provinsi secara mendetail.")
    
    selected_prov = st.selectbox("Pilih Provinsi:", sorted(df['Provinsi'].unique()))
    
    df_prov = df[df['Provinsi'] == selected_prov].sort_values('Tahun')
    
    # Timeline Status Klaster
    st.subheader(f"Perjalanan Historis Klaster: {selected_prov} (2021 - 2025)")
    cols = st.columns(len(df_prov))
    for i, (idx, row) in enumerate(df_prov.iterrows()):
        color = COLOR_MAP.get(row['Target_Semantic'], '#bdc3c7')
        cols[i].markdown(
            f"<div style='background-color:{color}; padding:15px; border-radius:10px; text-align:center; color:white; font-weight:bold;'>"
            f"{row['Tahun']}<br><span style='font-size:0.9em; font-weight:normal;'>{row['Target_Semantic']}</span></div>", 
            unsafe_allow_html=True
        )
    
    st.write("---")
    
    # Line chart tren metrik transaksi
    st.subheader(f"Tren Indikator Keuangan {selected_prov}")
    
    # Bikin 2 kolom untuk Line charts biar rapi
    lc1, lc2 = st.columns(2)
    
    with lc1:
        fig_trend1 = go.Figure()
        fig_trend1.add_trace(go.Scatter(x=df_prov['Tahun'], y=df_prov['outflow_tunai'], mode='lines+markers', name='Outflow Tunai', line=dict(color='#e67e22', width=3)))
        fig_trend1.add_trace(go.Scatter(x=df_prov['Tahun'], y=df_prov['SKNBI_Asal'], mode='lines+markers', name='SKNBI', line=dict(color='#8e44ad', width=3)))
        fig_trend1.update_layout(title="Tren Nilai Tunai & Kliring (Rp Miliar)", xaxis_type='category', hovermode='x unified')
        st.plotly_chart(fig_trend1, use_container_width=True)

    with lc2:
        fig_trend2 = go.Figure()
        fig_trend2.add_trace(go.Scatter(x=df_prov['Tahun'], y=df_prov['kartu_atm_debet'], mode='lines+markers', name='Kartu ATM/Debet', line=dict(color='#2980b9', width=3)))
        fig_trend2.add_trace(go.Scatter(x=df_prov['Tahun'], y=df_prov['Server_Based'], mode='lines+markers', name='Server-Based (E-Wallet)', line=dict(color='#16a085', width=3)))
        fig_trend2.update_layout(title="Tren Volume Instrumen Non-Tunai (Juta Unit)", xaxis_type='category', hovermode='x unified')
        st.plotly_chart(fig_trend2, use_container_width=True)

# ==========================================
# TAB 4: IMPLIKASI KEBIJAKAN (Menjawab Q5)
# ==========================================
with tab4:
    st.header("Implikasi Kebijakan Berdasarkan Hasil Klasterisasi")
    st.markdown("Rekomendasi strategis berdasarkan pengelompokan tingkat kematangan finansial digital.")
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.markdown(
            f"<div style='border-left: 6px solid {COLOR_MAP['Digital Rendah']}; padding: 15px; background-color: #f9f9f9; border-radius: 5px; height: 100%;'>"
            f"<h3 style='color: {COLOR_MAP['Digital Rendah']}; margin-top:0;'>🔴 Digital Rendah</h3>"
            "<b>Karakteristik:</b> Ketergantungan tinggi pada uang tunai, adopsi E-Wallet & instrumen digital sangat rendah.<br><br>"
            "<b>Rekomendasi Kebijakan:</b><br>"
            "<ul>"
            "<li>Fokus pada pembangunan infrastruktur dasar (sinyal telekomunikasi) dan edukasi literasi keuangan digital tahap awal.</li>"
            "<li>Pemerintah daerah perlu memfasilitasi program QRIS untuk UMKM dan pasar tradisional sebagai titik masuk (entry-point).</li>"
            "</ul>"
            "</div>", unsafe_allow_html=True
        )
        st.write("")
        st.markdown(
            f"<div style='border-left: 6px solid {COLOR_MAP['Digital Menengah']}; padding: 15px; background-color: #f9f9f9; border-radius: 5px; height: 100%;'>"
            f"<h3 style='color: {COLOR_MAP['Digital Menengah']}; margin-top:0;'>🟡 Digital Menengah</h3>"
            "<b>Karakteristik:</b> Transaksi ATM/Debet mulai mapan, namun platform Server-Based (Dompet Digital) masih belum mengimbangi.<br><br>"
            "<b>Rekomendasi Kebijakan:</b><br>"
            "<ul>"
            "<li>Dorong insentif penggunaan platform non-tunai (misalnya diskon retribusi parkir/pasar jika menggunakan e-wallet).</li>"
            "<li>Peningkatan akuisisi merchant digital di sektor ekonomi sekunder.</li>"
            "</ul>"
            "</div>", unsafe_allow_html=True
        )
                 
    with col_p2:
        st.markdown(
            f"<div style='border-left: 6px solid {COLOR_MAP['Digital Maju']}; padding: 15px; background-color: #f9f9f9; border-radius: 5px; height: 100%;'>"
            f"<h3 style='color: {COLOR_MAP['Digital Maju']}; margin-top:0;'>🔵 Digital Maju</h3>"
            "<b>Karakteristik:</b> Keseimbangan penggunaan ATM/Debet dan E-Wallet tinggi, pertumbuhan out-flow tunai terkendali.<br><br>"
            "<b>Rekomendasi Kebijakan:</b><br>"
            "<ul>"
            "<li>Peningkatan kerangka perlindungan konsumen dan <i>Cyber Security</i>.</li>"
            "<li>Fokus pada pengembangan ekosistem yang terintegrasi (Smart City) untuk retribusi pajak dan layanan publik.</li>"
            "</ul>"
            "</div>", unsafe_allow_html=True
        )
        st.write("")
        st.markdown(
            f"<div style='border-left: 6px solid {COLOR_MAP['Digital Spesialis Non-Tunai']}; padding: 15px; background-color: #f9f9f9; border-radius: 5px; height: 100%;'>"
            f"<h3 style='color: {COLOR_MAP['Digital Spesialis Non-Tunai']}; margin-top:0;'>🟢 Digital Spesialis Non-Tunai</h3>"
            "<b>Karakteristik:</b> Anomali positif. Nilai SKNBI dan transaksi Server-Based meledak, menjadi pusat perputaran perbankan digital.<br><br>"
            "<b>Rekomendasi Kebijakan:</b><br>"
            "<ul>"
            "<li>Provinsi menjadi pusat *Role Model* / *Sandbox* untuk inovasi teknologi finansial nasional.</li>"
            "<li>Mendorong ekspansi Open Banking dan skema pembayaran lintas negara (Cross-Border Payments).</li>"
            "</ul>"
            "</div>", unsafe_allow_html=True
        )
