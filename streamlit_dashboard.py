"""
Dashboard Klasterisasi Provinsi di Indonesia Berdasarkan Pola Transaksi
Keuangan Digital Menggunakan Algoritma K-Means dengan Analisis Temporal 2021-2025

Skripsi Dashboard — Streamlit + Plotly
Data: hasil_clustering_final.csv (34 provinsi x 5 tahun, hasil clustering final)

Jalankan dengan:
    streamlit run streamlit_dashboard.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ══════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Klasterisasi Transaksi Digital Provinsi Indonesia",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════
# CONSTANTS — warna & urutan cluster konsisten di seluruh dashboard
# ══════════════════════════════════════════════════════════════════════════
CLUSTER_ORDER = [
    "Digital Rendah",
    "Digital Menengah",
    "Digital Maju",
    "Digital Spesialis Non-Tunai",
]

CLUSTER_COLORS = {
    "Digital Rendah": "#ef4444",               # merah
    "Digital Menengah": "#f59e0b",              # amber
    "Digital Maju": "#3b82f6",                  # biru
    "Digital Spesialis Non-Tunai": "#10b981",   # hijau emerald
}

CLUSTER_DESC = {
    "Digital Rendah": "Dependensi tunai tinggi, infrastruktur digital minim.",
    "Digital Menengah": "Transisi menuju digital, mengandalkan ATM/Debit.",
    "Digital Maju": "Adopsi digital tinggi, transaksi server-based bertumbuh.",
    "Digital Spesialis Non-Tunai": "Ekosistem non-tunai matang, pembayaran digital dominan.",
}

CLUSTER_RECOMMENDATION = {
    "Digital Rendah": "Prioritas mendesak: bangun infrastruktur digital dasar. Fokus pada program literasi keuangan dan mengurangi ketergantungan logistik uang tunai fisik.",
    "Digital Menengah": "Dorong transisi dari ATM ke mobile banking. Berikan insentif merchant untuk adopsi QRIS dan edukasi keamanan e-wallet ke konsumen.",
    "Digital Maju": "Optimalkan ekosistem digital yang sudah ada. Perkenalkan produk kredit digital lanjutan dan perkuat kerangka keamanan siber.",
    "Digital Spesialis Non-Tunai": "Jadikan acuan nasional (benchmark). Fokus pada integrasi pembayaran lintas batas dan inisiatif smart city berbasis layanan publik tanpa kertas.",
}

FEATURES = ["outflow_tunai", "kartu_atm_debet", "Server_Based", "SKNBI_Asal"]
FEATURE_LABELS = {
    "outflow_tunai": "Outflow Tunai",
    "kartu_atm_debet": "Kartu ATM/Debet",
    "Server_Based": "Server-Based (E-Wallet)",
    "SKNBI_Asal": "Kliring (SKNBI)",
}

# ══════════════════════════════════════════════════════════════════════════
# CUSTOM CSS
# ══════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .kpi-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 18px 20px;
        display: flex;
        align-items: center;
        gap: 14px;
    }
    .kpi-icon {
        font-size: 22px;
        width: 48px; height: 48px;
        border-radius: 12px;
        display: flex; align-items: center; justify-content: center;
        flex-shrink: 0;
    }
    .kpi-label {
        font-size: 11px; font-weight: 600; letter-spacing: 0.06em;
        text-transform: uppercase; color: #94a3b8;
    }
    .kpi-value { font-size: 22px; font-weight: 700; color: #1e293b; line-height: 1.2; }

    .panel-title {
        font-weight: 700; font-size: 16px; color: #1e293b; margin-bottom: 2px;
    }
    .panel-sub { font-size: 12px; color: #94a3b8; margin-bottom: 14px; }

    .insight-box {
        background: #eff6ff; border-radius: 12px; padding: 12px 16px;
        font-size: 13px; color: #1e40af; margin-top: 10px;
    }

    .policy-card {
        border: 1px solid #e2e8f0; border-radius: 14px; padding: 16px;
        background: #f8fafc; height: 100%;
    }
    .policy-title { font-weight: 700; font-size: 15px; margin-bottom: 6px; }
    .policy-desc { font-size: 12px; color: #64748b; font-style: italic; margin-bottom: 10px; }
    .policy-rec {
        background: white; border: 1px solid #e2e8f0; border-radius: 10px;
        padding: 10px 12px; font-size: 12.5px; color: #334155; line-height: 1.5;
    }
    .policy-n {
        background: white; border: 1px solid #e2e8f0; border-radius: 8px;
        padding: 2px 10px; font-size: 12px; font-weight: 700; color: #1e293b;
    }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# LOAD DATA
# ══════════════════════════════════════════════════════════════════════════
@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv("hasil_clustering_final.csv")
    df["Tahun"] = df["Tahun"].astype(int)
    df["Target_Semantic"] = pd.Categorical(
        df["Target_Semantic"], categories=CLUSTER_ORDER, ordered=True
    )
    return df

df = load_data()
years = sorted(df["Tahun"].unique())
provinces = sorted(df["Provinsi"].unique())

# ══════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 🗺️ Filter Dashboard")
    st.markdown("---")
    selected_year = st.select_slider("Tahun Observasi", options=years, value=years[-1])
    st.markdown("---")
    selected_prov = st.selectbox(
        "Provinsi (Drill-down)",
        options=provinces,
        index=provinces.index("Jawa Barat") if "Jawa Barat" in provinces else 0,
    )
    st.markdown("---")
    st.markdown(f"""
    <div style='font-size:11px; color:#94a3b8; line-height:1.7'>
    <b style='color:#475569'>Tentang Dashboard</b><br>
    Klasterisasi K-Means pada {len(provinces)} provinsi Indonesia berdasarkan
    pola transaksi keuangan digital periode {years[0]}–{years[-1]}.<br><br>
    <b style='color:#475569'>Variabel:</b><br>
    {"<br>".join("• " + v for v in FEATURE_LABELS.values())}
    </div>
    """, unsafe_allow_html=True)

df_year = df[df["Tahun"] == selected_year].copy()

# ══════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div style='background:white; border:1px solid #e2e8f0; border-radius:18px;
            padding:24px 28px; margin-bottom:20px;'>
    <div style='font-size:11px; font-weight:700; letter-spacing:0.08em;
                text-transform:uppercase; color:#3b82f6; margin-bottom:6px;'>
        SKRIPSI · ANALISIS KLASTERISASI TEMPORAL
    </div>
    <h1 style='font-size:25px; font-weight:800; color:#1e293b; margin:0; line-height:1.3;'>
        Klasterisasi Provinsi di Indonesia Berdasarkan Pola Transaksi Keuangan Digital
    </h1>
    <p style='font-size:14px; color:#64748b; margin-top:8px;'>
        Algoritma K-Means dengan Analisis Temporal {years[0]}–{years[-1]} ·
        Menampilkan data tahun <b style='color:#1e293b'>{selected_year}</b>
    </p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# KPI CARDS
# ══════════════════════════════════════════════════════════════════════════
counts_year = df_year["Target_Semantic"].value_counts()
dominant_cluster = counts_year.idxmax()

kpi_specs = [
    ("🗺️", "Total Provinsi", f"{len(provinces)}", "#3b82f6", "#eff6ff"),
    ("⏱️", "Tahun Dianalisis", f"{len(years)} ({years[0]}–{years[-1]})", "#6366f1", "#eef2ff"),
    ("📊", "Jumlah Cluster", "4", "#10b981", "#ecfdf5"),
    ("👥", "Cluster Dominan", dominant_cluster, CLUSTER_COLORS[dominant_cluster], "#fff7ed"),
]
kpi_cols = st.columns(4)
for col, (icon, label, value, color, bg) in zip(kpi_cols, kpi_specs):
    with col:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon" style="background:{bg}; color:{color};">{icon}</div>
            <div>
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{value}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# ROW 1 — Distribusi (donut) + Karakteristik (radar) + Evolusi Temporal (area)
# ══════════════════════════════════════════════════════════════════════════
col1, col2, col3 = st.columns([1, 1.2, 1.1])

# --- Donut chart: distribusi cluster tahun terpilih ---
with col1:
    st.markdown('<div class="panel-title">📍 Distribusi Cluster</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="panel-sub">Temuan: ketimpangan adopsi digital di {selected_year}</div>', unsafe_allow_html=True)

    dist_df = counts_year.reindex(CLUSTER_ORDER).fillna(0).reset_index()
    dist_df.columns = ["Cluster", "Jumlah"]

    fig_donut = go.Figure(data=[go.Pie(
        labels=dist_df["Cluster"], values=dist_df["Jumlah"], hole=0.65,
        marker=dict(colors=[CLUSTER_COLORS[c] for c in dist_df["Cluster"]]),
        textinfo="none", sort=False
    )])
    fig_donut.update_layout(
        showlegend=False,
        annotations=[dict(text=f"{len(df_year)}<br><span style='font-size:11px;color:#94a3b8'>Provinsi</span>",
                           x=0.5, y=0.5, showarrow=False, font=dict(size=26, color="#1e293b"))],
        margin=dict(l=10, r=10, t=10, b=10), height=260,
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_donut, use_container_width=True)

    for _, row in dist_df.iterrows():
        st.markdown(f"""
        <div style='display:flex;align-items:center;font-size:12px;margin-bottom:4px;'>
            <div style='width:10px;height:10px;border-radius:50%;background:{CLUSTER_COLORS[row["Cluster"]]};margin-right:8px;'></div>
            <span style='color:#475569'>{row["Cluster"]}: <b>{int(row["Jumlah"])}</b></span>
        </div>
        """, unsafe_allow_html=True)

# --- Radar chart: karakteristik rata-rata per cluster ---
with col2:
    st.markdown('<div class="panel-title">📡 Karakteristik Perilaku Transaksi</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="panel-sub">Rata-rata nilai indikator per cluster · {selected_year}</div>', unsafe_allow_html=True)

    fig_radar = go.Figure()
    for cluster in CLUSTER_ORDER:
        sub = df_year[df_year["Target_Semantic"] == cluster]
        if sub.empty:
            continue
        vals = sub[FEATURES].mean().tolist()
        # normalisasi 0-1 berdasarkan rentang tahun terpilih agar bentuk radar terbaca
        vals_norm = []
        for i, f in enumerate(FEATURES):
            lo, hi = df_year[f].min(), df_year[f].max()
            vals_norm.append((vals[i] - lo) / (hi - lo + 1e-9))
        vals_norm.append(vals_norm[0])
        labels = [FEATURE_LABELS[f] for f in FEATURES] + [FEATURE_LABELS[FEATURES[0]]]

        fig_radar.add_trace(go.Scatterpolar(
            r=vals_norm, theta=labels, fill="toself", name=cluster,
            line_color=CLUSTER_COLORS[cluster], fillcolor=CLUSTER_COLORS[cluster], opacity=0.35
        ))

    fig_radar.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 1], showticklabels=False, gridcolor="#e2e8f0"),
            angularaxis=dict(gridcolor="#e2e8f0", color="#64748b", tickfont=dict(size=10)),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, font=dict(size=10)),
        margin=dict(l=30, r=30, t=10, b=10), height=300,
    )
    st.plotly_chart(fig_radar, use_container_width=True)

# --- Stacked area: evolusi temporal seluruh tahun ---
with col3:
    st.markdown('<div class="panel-title">📈 Evolusi Temporal</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="panel-sub">Pergeseran cluster {years[0]}–{years[-1]}</div>', unsafe_allow_html=True)

    evo = (
        df.groupby(["Tahun", "Target_Semantic"]).size()
        .reset_index(name="Jumlah")
        .pivot(index="Tahun", columns="Target_Semantic", values="Jumlah")
        .reindex(columns=CLUSTER_ORDER)
        .fillna(0)
        .reset_index()
    )

    fig_area = go.Figure()
    for cluster in CLUSTER_ORDER:
        fig_area.add_trace(go.Scatter(
            x=evo["Tahun"], y=evo[cluster], mode="lines", name=cluster,
            stackgroup="one", line=dict(width=0.5, color=CLUSTER_COLORS[cluster]),
            fillcolor=CLUSTER_COLORS[cluster],
        ))
    fig_area.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#64748b", size=11),
        xaxis=dict(title="", gridcolor="#f1f5f9", tickmode="array", tickvals=years),
        yaxis=dict(title="Jumlah Provinsi", gridcolor="#f1f5f9"),
        showlegend=False, margin=dict(l=0, r=0, t=10, b=0), height=210,
    )
    st.plotly_chart(fig_area, use_container_width=True)

    st.markdown(f"""
    <div class="insight-box">
        💡 <b>Insight:</b> Perhatikan perluasan area biru/hijau pada grafik —
        menandakan mobilitas digital yang membaik di sejumlah provinsi
        sepanjang periode {years[0]}–{years[-1]}.
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# ROW 2 — PCA Scatter + Province Drill-down
# ══════════════════════════════════════════════════════════════════════════
col4, col5 = st.columns([1.3, 1])

with col4:
    st.markdown('<div class="panel-title">🔵 Pemetaan PCA Semantik</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="panel-sub">Hubungan spasial antar provinsi berdasarkan perilaku transaksi · {selected_year}</div>', unsafe_allow_html=True)

    fig_scatter = px.scatter(
        df_year, x="PCA1", y="PCA2",
        color="Target_Semantic",
        color_discrete_map=CLUSTER_COLORS,
        category_orders={"Target_Semantic": CLUSTER_ORDER},
        hover_name="Provinsi",
        hover_data={"Target_Semantic": True, "PCA1": ":.2f", "PCA2": ":.2f"},
    )
    fig_scatter.update_traces(marker=dict(size=11, opacity=0.85, line=dict(width=1, color="white")))
    fig_scatter.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#64748b", size=11),
        legend=dict(title="", orientation="h", yanchor="bottom", y=1.02, font=dict(size=10)),
        xaxis=dict(title="PC1 — Kematangan Digital →", gridcolor="#f1f5f9", zeroline=False),
        yaxis=dict(title="PC2", gridcolor="#f1f5f9", zeroline=False),
        margin=dict(l=0, r=0, t=40, b=0), height=340,
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

with col5:
    st.markdown(f'<div class="panel-title">🔍 Drill-down Provinsi: {selected_prov}</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-sub">Perjalanan 5 tahun & detail indikator</div>', unsafe_allow_html=True)

    prov_data = df[df["Provinsi"] == selected_prov].sort_values("Tahun")

    # Timeline horizontal dengan titik warna cluster per tahun
    timeline_cols = st.columns(len(prov_data))
    prev_level = None
    for i, (col_t, (_, row)) in enumerate(zip(timeline_cols, prov_data.iterrows())):
        cluster = row["Target_Semantic"]
        level = CLUSTER_ORDER.index(cluster)
        arrow = ""
        if prev_level is not None:
            if level > prev_level:
                arrow = "⬆️"
            elif level < prev_level:
                arrow = "⬇️"
        prev_level = level
        with col_t:
            st.markdown(f"""
            <div style='text-align:center'>
                <div style='font-size:10px;color:#94a3b8;font-weight:600;'>{int(row['Tahun'])}</div>
                <div style='width:16px;height:16px;border-radius:50%;background:{CLUSTER_COLORS[cluster]};
                            margin:4px auto;border:2px solid white;box-shadow:0 0 0 2px #e2e8f0;'></div>
                <div style='font-size:10px;'>{arrow}</div>
            </div>
            """, unsafe_allow_html=True)

    # Line chart 3 indikator utama sepanjang waktu
    fig_line = go.Figure()
    line_colors = {"Server_Based": "#10b981", "kartu_atm_debet": "#3b82f6", "outflow_tunai": "#ef4444"}
    dash_map = {"Server_Based": "solid", "kartu_atm_debet": "solid", "outflow_tunai": "dash"}
    for feat in ["Server_Based", "kartu_atm_debet", "outflow_tunai"]:
        fig_line.add_trace(go.Scatter(
            x=prov_data["Tahun"], y=prov_data[feat], mode="lines+markers",
            name=FEATURE_LABELS[feat], line=dict(color=line_colors[feat], dash=dash_map[feat], width=2.5),
            marker=dict(size=6),
        ))
    fig_line.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#64748b", size=10),
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, font=dict(size=9)),
        xaxis=dict(title="", gridcolor="#f1f5f9", tickmode="array", tickvals=years),
        yaxis=dict(title="", gridcolor="#f1f5f9"),
        margin=dict(l=0, r=0, t=10, b=0), height=190,
    )
    st.plotly_chart(fig_line, use_container_width=True)

    current_cluster = prov_data.iloc[-1]["Target_Semantic"]
    st.markdown(f"""
    <div style='background:{CLUSTER_COLORS[current_cluster]}1A; border-radius:10px; padding:10px 14px; font-size:12px; color:#334155;'>
        Status {prov_data.iloc[-1]['Tahun']}: <b style='color:{CLUSTER_COLORS[current_cluster]}'>{current_cluster}</b><br>
        <span style='color:#64748b'>{CLUSTER_DESC[current_cluster]}</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# ROW 3 — Tabel perubahan cluster antar tahun
# ══════════════════════════════════════════════════════════════════════════
st.markdown('<div class="panel-title">🔄 Perubahan Cluster Antar Tahun</div>', unsafe_allow_html=True)
st.markdown('<div class="panel-sub">Provinsi yang mengalami pergerakan naik / turun kategori selama periode penelitian</div>', unsafe_allow_html=True)

pivot = df.pivot_table(index="Provinsi", columns="Tahun", values="Target_Semantic", aggfunc="first")
change_records = []
for i in range(len(years) - 1):
    y1, y2 = years[i], years[i + 1]
    changed = pivot[pivot[y1] != pivot[y2]]
    for prov, row in changed.iterrows():
        lvl1, lvl2 = CLUSTER_ORDER.index(row[y1]), CLUSTER_ORDER.index(row[y2])
        change_records.append({
            "Provinsi": prov,
            "Periode": f"{y1} → {y2}",
            "Cluster Awal": row[y1],
            "Cluster Akhir": row[y2],
            "Arah": "⬆️ Naik" if lvl2 > lvl1 else "⬇️ Turun",
        })

if change_records:
    st.dataframe(pd.DataFrame(change_records), use_container_width=True, hide_index=True, height=180)
else:
    st.info("Tidak ada perubahan cluster pada periode ini.")

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# ROW 4 — Policy Implication Cards
# ══════════════════════════════════════════════════════════════════════════
st.markdown(f'<div class="panel-title">💡 Implikasi & Rekomendasi Kebijakan · {selected_year}</div>', unsafe_allow_html=True)
st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

policy_cols = st.columns(4)
for col_p, cluster in zip(policy_cols, CLUSTER_ORDER):
    n = int(counts_year.get(cluster, 0))
    with col_p:
        st.markdown(f"""
        <div class="policy-card" style="border-top:3px solid {CLUSTER_COLORS[cluster]};">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                <span class="policy-title" style="color:{CLUSTER_COLORS[cluster]}">{cluster}</span>
                <span class="policy-n">n = {n}</span>
            </div>
            <div class="policy-desc">"{CLUSTER_DESC[cluster]}"</div>
            <div class="policy-rec">{CLUSTER_RECOMMENDATION[cluster]}</div>
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div style='text-align:center; color:#94a3b8; font-size:11px; margin-top:36px; padding-top:18px; border-top:1px solid #e2e8f0;'>
    Klasterisasi Provinsi Indonesia · K-Means · Analisis Temporal {years[0]}–{years[-1]} · Skripsi
</div>
""", unsafe_allow_html=True)
