import streamlit as st
import sys, os
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import pickle
import json
import folium
from streamlit_folium import st_folium

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from load_data import load_main_data, load_ipa, load_emotion, load_competitive, load_segments, _fix_mojibake
from filters import render_filters
from theme import (get_full_css, TEAL_MED, TEAL_DARK, NAVY_DARK,
                          BLUE_MED, TEAL_LIGHT, WHITE, GRAY_LIGHT,
                          GRAY_BORDER, GRAY_TEXT, SUCCESS, WARNING, DANGER, CHART_COLORS)
from kpi_bar import (render_kpi_scorecard, render_kpi_prioritas,
                            render_kpi_cabang, render_kpi_emosi,
                            render_kpi_segmentasi, render_kpi_kompetitor)

# ── CONFIG ───────────────────────────────────────────────────
st.set_page_config(
    page_title="Bank XYZ | Customer Experience Intelligence",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(get_full_css(), unsafe_allow_html=True)

st.markdown(f"""
    <style>
    .stApp {{
        background-color: {GRAY_LIGHT} !important;
    }}
    .main .block-container {{
        background-color: {GRAY_LIGHT};
        padding-top: 2rem;
    }}

    .stTabs [data-baseweb="tab-list"] {{
        gap: 4px;
        background: {WHITE};
        padding: 5px 8px;
        border-radius: 14px;
        border: 1px solid {GRAY_BORDER};
        margin-bottom: 24px;
        justify-content: center;
        display: flex;
        width: fit-content;
        margin-left: auto;
        margin-right: auto;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }}
    .stTabs [data-baseweb="tab"] {{
        background: transparent;
        border-radius: 10px;
        padding: 8px 22px;
        font-size: 0.875rem;
        font-weight: 600;
        color: {NAVY_DARK};
        border: none;
        font-family: Poppins, sans-serif;
        transition: all 0.2s;
        white-space: nowrap;
    }}
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(90deg, #002765, #2CB5D4) !important;
        color: {WHITE} !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 8px rgba(0,39,101,0.25) !important;
        border-bottom: none !important;
    }}
    .stTabs [data-baseweb="tab-highlight"] {{ display: none !important; }}
    .stTabs [data-baseweb="tab-border"] {{ display: none !important; }}
    .stTabs [data-baseweb="tab"] p {{
        font-size: 0.875rem !important;
        font-weight: inherit !important;
    }}

    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #002765, #2CB5D4) !important;
    }}
    [data-testid="stSidebar"] .stSelectbox label {{
        font-size: 0.78rem !important;
        font-weight: 500 !important;
        color: rgba(255,255,255,0.7) !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    [data-testid="stSidebarNav"] {{ display: none !important; }}

    .section-title {{
        font-size: 1rem;
        font-weight: 700;
        color: {NAVY_DARK};
        margin: 0 0 12px 0;
        padding: 0 0 0 11px;
        font-family: Poppins, sans-serif;
        border-left: 4px solid {TEAL_MED};
        line-height: 1.3;
    }}

    .chart-card {{
        background: {WHITE};
        border-radius: 16px;
        padding: 24px;
        border: 1px solid {GRAY_BORDER};
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        margin-bottom: 16px;
    }}
    </style>
""", unsafe_allow_html=True)

# ── LOAD DATA ────────────────────────────────────────────────
df = load_main_data()
df_filtered = render_filters(df)

rata_cols = {
    'Fisik Bank': 'rata_fisik',
    'Brand Image': 'rata_brand',
    'Teller': 'rata_teller',
    'CS': 'rata_cs',
    'ATM': 'rata_atm',
    'Sekuriti': 'rata_sekuriti',
}

# ── HEADER ───────────────────────────────────────────────────
_n_cabang_total = df['CABANG'].nunique() if 'CABANG' in df.columns else 128
st.markdown(f"""
<div style="margin-bottom: 8px;display:flex;align-items:center;gap:14px;">
    <div style="width:46px;height:46px;min-width:46px;border-radius:13px;
        background:linear-gradient(135deg,#002765,#2CB5D4);
        display:flex;align-items:center;justify-content:center;
        box-shadow:0 4px 12px rgba(0,39,101,0.25);">
        <span style="font-size:1.5rem;">🏦</span>
    </div>
    <div>
        <div style="
            font-size: 1.75rem;
            font-weight: 600;
            background: linear-gradient(135deg, #002765, #2CB5D4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-family: CalSans, Poppins, sans-serif;
            margin-bottom: 4px;
            line-height: 1.2;
        ">Bank XYZ Customer Experience Intelligence</div>
        <div style="font-size:0.85rem;color:#9CA3AF;">
            Dashboard analisis kepuasan nasabah &nbsp;·&nbsp;
            {len(df_filtered):,} responden terpilih &nbsp;·&nbsp;
            {_n_cabang_total} kantor cabang
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ── TABS ─────────────────────────────────────────────────────
# NEW ORDER:
# 1. Scorecard
# 2. Customer Service Index (Prioritas Layanan)
# 3. Loyalitas Index
# 4. Profil Cabang
# 5. Peta Emosi & Profil Nasabah (gabung)
# 6. Intelijen Kompetitor
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Scorecard",
    "Customer Service Index",
    "Loyalitas Index",
    "Profil Cabang",
    "Peta Emosi & Profil Nasabah",
    "Intelijen Kompetitor",
])


@st.cache_data
def load_geojson_provinsi():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        'indonesia.geojson')
    with open(path, 'r') as f:
        return json.load(f)

# Mapping nama provinsi di dataset survei -> nama provinsi di geojson (field 'Propinsi', huruf besar)
PROV_MAP = {
    'DKI Jakarta':        'DKI JAKARTA',
    'Jawa Barat':         'JAWA BARAT',
    'Jawa Tengah':        'JAWA TENGAH',
    'Jawa Timur':         'JAWA TIMUR',
    'Banten':             'PROBANTEN',          # nama provinsi di sumber geojson lama
    'Bali':               'BALI',
    'Lampung':            'LAMPUNG',
    'Sumatera Selatan':   'SUMATERA SELATAN',
    'Sumatera Utara':     'SUMATERA UTARA',
    'Riau':                'RIAU',
    'Kepulauan Riau':      'RIAU',               # geojson lama belum memisahkan Kepri dari Riau
    'Kalimantan Selatan':  'KALIMANTAN SELATAN',
    'Kalimantan Timur':    'KALIMANTAN TIMUR',
    'Sulawesi Selatan':    'SULAWESI SELATAN',
}

def render_peta(df_input):
    geojson = load_geojson_provinsi()
    df_prov = df_input.groupby('PROV').size().reset_index(name='Jumlah Responden')
    df_prov['state'] = df_prov['PROV'].map(PROV_MAP)
    df_prov_geo = df_prov.dropna(subset=['state'])

    # Provinsi yang punya responden tapi tidak ada di batas peta (mis. Kepulauan Riau bila tergabung Riau)
    unmatched = df_prov[df_prov['state'].isna()]

    m = folium.Map(location=[-2.5, 118], zoom_start=5, tiles='CartoDB positron')

    folium.Choropleth(
        geo_data=geojson,
        name='choropleth',
        data=df_prov_geo,
        columns=['state', 'Jumlah Responden'],
        key_on='feature.properties.Propinsi',
        fill_color='Blues',
        fill_opacity=0.85,
        line_opacity=0.4,
        line_color=NAVY_DARK,
        legend_name='Jumlah Responden',
        nan_fill_color='#E5E7EB',
        nan_fill_opacity=0.5,
    ).add_to(m)

    # Gabungkan jumlah responden per state (mengatasi Riau + Kepulauan Riau jadi satu wilayah)
    state_totals = df_prov_geo.groupby('state')['Jumlah Responden'].sum()

    for feat in geojson['features']:
        nama_state = feat['properties']['Propinsi']
        if nama_state not in state_totals.index:
            continue
        jumlah = int(state_totals[nama_state])
        geom = feat['geometry']
        if geom['type'] == 'Polygon':
            pts = geom['coordinates'][0]
        else:
            pts = max(geom['coordinates'], key=len)[0]
        lat = sum(p[1] for p in pts) / len(pts)
        lon = sum(p[0] for p in pts) / len(pts)
        folium.Marker(
            [lat, lon],
            icon=folium.DivIcon(
                html=f'''<div style="font-size:11px;font-weight:700;color:{NAVY_DARK};
                    background:{WHITE};padding:3px 7px;border-radius:6px;
                    border:1.5px solid {TEAL_MED};box-shadow:0 1px 4px rgba(0,0,0,0.15);
                    white-space:nowrap;">👥 {jumlah:,}</div>'''
            )
        ).add_to(m)

    st_folium(m, width=None, height=400, returned_objects=[])

    if len(unmatched) > 0:
        nama_unmatched = ", ".join(unmatched['PROV'].tolist())
        st.caption(f"ℹ️ {nama_unmatched} ditampilkan tergabung dengan provinsi induk pada peta "
                   f"karena batas wilayah administratif yang digunakan belum memisahkan provinsi "
                   f"baru hasil pemekaran.")


def compute_ces(df_input):
    """Customer Effort Score dari kolom T_J1 (kemudahan layanan cabang)."""
    ces_cols = ['T_J1_1', 'T_J1_2', 'T_J1_4', 'T_J1_5']
    available = [c for c in ces_cols if c in df_input.columns]
    if not available:
        return np.nan
    return df_input[available].mean(skipna=True).mean()


def deteksi_straightlining(df_input):
    """
    Deteksi pola straight-lining pada 15 item emosi (T_H1A_*, kolom XYZ).
    Straight-liner = responden yang memberi nilai identik pada SEMUA 15 item,
    termasuk item yang bermakna berlawanan (mis. 'Senang' dan 'Marah' sekaligus).
    Pola ini menandakan responden mengisi survei tanpa membaca pertanyaan,
    sehingga skor emosi pada baris tersebut tidak merepresentasikan persepsi asli.
    """
    emosi_cols_xyz = sorted(
        [c for c in df_input.columns if c.startswith("T_H1A_") and int(c.split("_")[-1]) % 3 == 2],
        key=lambda x: int(x.split("_")[-1])
    )
    if len(emosi_cols_xyz) < 15:
        return None

    sub = df_input[emosi_cols_xyz]
    row_std = sub.std(axis=1, skipna=True)
    is_flat = row_std == 0

    n_total = len(df_input)
    n_flat = int(is_flat.sum())
    pct_flat = (n_flat / n_total * 100) if n_total > 0 else 0

    df_flagged = df_input.loc[is_flat]
    by_prov = (df_flagged.groupby('PROV').size().sort_values(ascending=False)
               if 'PROV' in df_flagged.columns and len(df_flagged) > 0 else pd.Series(dtype=int))

    # Provinsi dengan SELURUH responden-nya straight-line (kasus paling parah)
    prov_full_flat = []
    if 'PROV' in df_input.columns:
        total_per_prov = df_input.groupby('PROV').size()
        flat_per_prov  = df_flagged.groupby('PROV').size() if len(df_flagged) > 0 else pd.Series(dtype=int)
        for prov, total in total_per_prov.items():
            flat_n = flat_per_prov.get(prov, 0)
            if flat_n == total and total > 0:
                prov_full_flat.append((prov, int(total)))

    # ── Cek pengelompokan skor (polarity collapse) ───────────
    # Bandingkan rata-rata emosi POSITIF vs NEGATIF, dengan & tanpa straight-liner.
    # Jika gap-nya kecil bahkan setelah straight-liner dibuang, ini indikasi
    # masalah pada arah skala kuesioner / acquiescence bias, bukan cuma straight-lining.
    emosi_neg_idx = [6, 7, 8, 9, 10, 11, 12, 13, 14]  # index emosi negatif (Kecewa..Lelah)
    emosi_pos_idx = [0, 1, 2, 3, 4, 5]                # index emosi positif (Senang..Kagum)
    cols_pos = [emosi_cols_xyz[i] for i in emosi_pos_idx if i < len(emosi_cols_xyz)]
    cols_neg = [emosi_cols_xyz[i] for i in emosi_neg_idx if i < len(emosi_cols_xyz)]

    mean_pos_all = df_input[cols_pos].mean(skipna=True).mean()
    mean_neg_all = df_input[cols_neg].mean(skipna=True).mean()

    df_bersih = df_input.loc[~is_flat]
    mean_pos_bersih = df_bersih[cols_pos].mean(skipna=True).mean() if len(df_bersih) > 0 else np.nan
    mean_neg_bersih = df_bersih[cols_neg].mean(skipna=True).mean() if len(df_bersih) > 0 else np.nan

    polarity_collapse = (
        pd.notna(mean_pos_bersih) and pd.notna(mean_neg_bersih)
        and abs(mean_pos_bersih - mean_neg_bersih) < 0.5
    )

    return {
        'n_total': n_total,
        'n_flat': n_flat,
        'pct_flat': pct_flat,
        'by_prov': by_prov,
        'prov_full_flat': prov_full_flat,
        'mask_flat': is_flat,
        'mean_pos_all': mean_pos_all,
        'mean_neg_all': mean_neg_all,
        'mean_pos_bersih': mean_pos_bersih,
        'mean_neg_bersih': mean_neg_bersih,
        'n_bersih': len(df_bersih),
        'polarity_collapse': polarity_collapse,
    }


# ════════════════════════════════════════════════════════════
# TAB 1 — SCORECARD
# (urutan: KPI cards → peta → dimensi+NPS → distribusi → prioritas)
# ════════════════════════════════════════════════════════════
with tab1:
    if len(df_filtered) == 0:
        st.warning("Tidak ada data untuk filter yang dipilih.")
        st.stop()

    # ── KPI Cards baris 1: Total Responden, NPS, Kepuasan Overall, Service Failure ──
    n_total   = len(df_filtered)
    nps_col   = 'G1A' if 'G1A' in df_filtered.columns else None

    if nps_col:
        _nps_series = pd.to_numeric(df_filtered[nps_col], errors="coerce")
        promoters   = (_nps_series >= 9).sum()
        passives    = ((_nps_series >= 7) & (_nps_series <= 8)).sum()
        detractors  = (_nps_series < 7).sum()
        pct_p = promoters  / n_total * 100 if n_total > 0 else 0
        pct_d = detractors / n_total * 100 if n_total > 0 else 0
        nps_score = pct_p - pct_d
    else:
        nps_score = 0

    kep_overall = df_filtered['E1A'].mean() if 'E1A' in df_filtered.columns else 0
    loy_overall = df_filtered['F1A'].mean() if 'F1A' in df_filtered.columns else 0

    n_failure = df_filtered['service_failure'].sum() if 'service_failure' in df_filtered.columns else 0
    pct_failure = n_failure / n_total * 100 if n_total > 0 else 0

    ces_score = compute_ces(df_filtered)

    # KPI row — 5 cards
    k1, k2, k3, k4, k5 = st.columns(5)

    def kpi_card(col, label, value, sub, color, icon=""):
        with col:
            st.markdown(f"""
            <div style="background:{WHITE};border-radius:16px;padding:18px 20px 16px 20px;
                border:1px solid {GRAY_BORDER};border-top:none;position:relative;overflow:hidden;
                box-shadow:0 1px 3px rgba(0,39,101,0.06),0 4px 14px rgba(0,39,101,0.05);
                margin-bottom:16px;">
                <div style="position:absolute;top:0;left:0;right:0;height:4px;
                    background:linear-gradient(90deg,{color},{color}99);"></div>
                <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:10px;">
                    <p style="font-size:0.76rem;font-weight:600;color:{GRAY_TEXT};
                        margin:0;text-transform:uppercase;letter-spacing:0.3px;">{label}</p>
                    <span style="font-size:1.05rem;line-height:1;width:30px;height:30px;
                        min-width:30px;border-radius:9px;background:{color}14;
                        display:flex;align-items:center;justify-content:center;">{icon}</span>
                </div>
                <p style="font-size:1.5rem;font-weight:700;color:{NAVY_DARK};
                    margin:0 0 4px 0;line-height:1.15;font-family:Poppins,sans-serif;">{value}</p>
                <p style="font-size:0.74rem;color:{color};margin:0;font-weight:500;">{sub}</p>
            </div>""", unsafe_allow_html=True)

    kpi_card(k1, "Total Responden", f"{n_total:,}", "nasabah tersurvei", TEAL_MED, "👥")
    kpi_card(k2, "NPS Score", f"{nps_score:.1f}", f"Promoter {pct_p:.1f}% | Detractor {pct_d:.1f}%", NAVY_DARK, "📊")
    kpi_card(k3, "Kepuasan Overall", f"{kep_overall:.2f}", "skala 1–6", TEAL_MED, "⭐")
    kpi_card(k4, "Service Failure", f"{n_failure:,}", f"{pct_failure:.1f}% dari total responden", DANGER, "⚠️")
    kpi_card(k5, "Customer Effort Score", f"{ces_score:.2f}" if not np.isnan(ces_score) else "N/A",
             "kemudahan layanan cabang (skala 1–6)", BLUE_MED, "🎯")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── PETA ─────────────────────────────────────────────────
    st.markdown(f'<p class="section-title">Sebaran Responden per Provinsi</p>', unsafe_allow_html=True)
    render_peta(df_filtered)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── Dimensi Layanan + NPS Distribusi ─────────────────────
    col_dim, col_nps = st.columns([3, 2])

    with col_dim:
        st.markdown(f'<p class="section-title">Kepuasan per Dimensi Layanan</p>', unsafe_allow_html=True)
        # Urutan: Fisik Bank - Brand Image - Teller - CS - ATM - Sekuriti
        items = list(rata_cols.items())
        for baris in range(2):
            cols_3 = st.columns(3)
            for j in range(3):
                idx = baris * 3 + j
                if idx >= len(items): break
                nama, col = items[idx]
                mean_val = df_filtered[col].mean(skipna=True)
                if pd.isna(mean_val): continue
                pct = (mean_val / 6) * 100
                if pct >= 90: warna, status = SUCCESS, "Sangat Baik"
                elif pct >= 80: warna, status = TEAL_MED, "Baik"
                elif pct >= 70: warna, status = WARNING, "Cukup"
                else: warna, status = DANGER, "Perlu Perhatian"
                with cols_3[j]:
                    st.markdown(f"""
                    <div style="background:{WHITE};border-radius:10px;padding:16px;
                        border:1px solid {GRAY_BORDER};border-left:4px solid {warna};
                        margin-bottom:10px;box-shadow:0 1px 4px rgba(0,0,0,0.04);">
                        <div style="font-size:0.8rem;color:#6B7280;font-weight:500;
                            margin-bottom:4px;">{nama}</div>
                        <div style="font-size:1.5rem;font-weight:700;color:{warna};
                            margin-bottom:2px;">{mean_val:.2f}</div>
                        <div style="font-size:0.72rem;color:{warna};margin-bottom:8px;">
                            {status}</div>
                        <div style="background:{GRAY_BORDER};border-radius:4px;height:4px;">
                            <div style="background:{warna};width:{pct:.1f}%;
                                height:4px;border-radius:4px;"></div>
                        </div>
                    </div>""", unsafe_allow_html=True)

    with col_nps:
        st.markdown(f'<p class="section-title">Distribusi NPS Nasabah</p>', unsafe_allow_html=True)

        if nps_col:
            pct_passive = int(passives) / n_total * 100 if n_total > 0 else 0
        else:
            pct_p = pct_passive = pct_d = nps_score = 0

        fig_donut = go.Figure(go.Pie(
            labels=['Promoter', 'Passive', 'Detractor'],
            values=[pct_p, pct_passive, pct_d],
            hole=0.50,
            marker=dict(colors=[SUCCESS, WARNING, DANGER],
                       line=dict(color=WHITE, width=3)),
            textinfo='label+percent',
            textfont=dict(size=12, family='Poppins'),
            hovertemplate='<b>%{label}</b><br>%{percent}<extra></extra>',
            pull=[0.04, 0, 0],
        ))
        fig_donut.add_annotation(
            text=f"<b>{nps_score:.1f}</b><br><span style='font-size:10px'>NPS Score</span>",
            x=0.5, y=0.5,
            font=dict(size=26, color=NAVY_DARK, family='Poppins'),
            showarrow=False, align='center'
        )
        fig_donut.update_layout(
            height=380, margin=dict(t=10,b=10,l=10,r=10),
            paper_bgcolor='white', showlegend=True,
            legend=dict(orientation='h', yanchor='bottom', y=-0.12,
                       xanchor='center', x=0.5,
                       font=dict(family='Poppins', size=11))
        )
        with st.container(border=True):
            st.plotly_chart(fig_donut, use_container_width=True,
               config={'displayModeBar': False})

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Distribusi Kepuasan & Loyalitas ──────────────────────
    col_kep, col_loy = st.columns(2)

    def buat_bar_dist(dist_data, warna_scale):
        x_vals = [int(x) for x in dist_data.index]
        fig = go.Figure(go.Bar(
            x=x_vals, y=dist_data.values,
            marker=dict(color=dist_data.values, colorscale=warna_scale,
                       line=dict(color=WHITE, width=1.5)),
            text=[f"{v:,}" for v in dist_data.values],
            textposition='outside',
            textfont=dict(family='Poppins', size=11, color=NAVY_DARK),
            hovertemplate='Skor %{x}<br>%{y:,} nasabah<extra></extra>',
        ))
        fig.update_layout(
            height=240, margin=dict(t=10,b=20,l=10,r=10),
            paper_bgcolor='white', plot_bgcolor='white',
            xaxis=dict(tickmode='array', tickvals=x_vals,
                      ticktext=[str(x) for x in x_vals],
                      tickfont=dict(family='Poppins', size=12), showgrid=False),
            yaxis=dict(tickfont=dict(family='Poppins'), showgrid=True,
                      gridcolor=GRAY_BORDER, gridwidth=1),
            showlegend=False, bargap=0.35,
        )
        fig.update_xaxes(fixedrange=True)
        fig.update_yaxes(fixedrange=True)
        return fig

    with col_kep:
        st.markdown(f'<p class="section-title">Distribusi Kepuasan Overall</p>', unsafe_allow_html=True)
        kep_dist = df_filtered['E1A'].value_counts().sort_index()
        fig_kep = buat_bar_dist(kep_dist, [[0,NAVY_DARK],[0.5,TEAL_MED],[1,TEAL_LIGHT]])
        with st.container(border=True):
            st.plotly_chart(fig_kep, use_container_width=True,
                       config={'displayModeBar': False})

    with col_loy:
        st.markdown(f'<p class="section-title">Distribusi Loyalitas</p>', unsafe_allow_html=True)
        loy_dist = df_filtered['F1A'].value_counts().sort_index()
        fig_loy = buat_bar_dist(loy_dist, [[0,NAVY_DARK],[0.5,BLUE_MED],[1,TEAL_LIGHT]])
        with st.container(border=True):
            st.plotly_chart(fig_loy, use_container_width=True,
                       config={'displayModeBar': False})

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Prioritas Perhatian ───────────────────────────────────
    st.markdown(f'<p class="section-title">Prioritas Perhatian</p>', unsafe_allow_html=True)

    alert_items = []
    dimensi_kepentingan = {
        'Teller':   [c for c in df.columns if c.startswith('T_TL2_')],
        'CS':       [c for c in df.columns if c.startswith('T_CS2_')],
        'ATM':      [c for c in df.columns if c.startswith('T_AT2_')],
        'Fisik':    [c for c in df.columns if c.startswith('T_KC1_')],
        'Sekuriti': [c for c in df.columns if c.startswith('T_SC1_')],
        'Brand':    [c for c in df.columns if c.startswith('T_C1A_')],
    }
    dimensi_kepuasan = {
        'Teller':   [c for c in df.columns if c.startswith('T_TL3_') and int(c.split('_')[-1])%3==2],
        'CS':       [c for c in df.columns if c.startswith('T_CS3_') and int(c.split('_')[-1])%3==2],
        'ATM':      [c for c in df.columns if c.startswith('T_AT3_') and int(c.split('_')[-1])%3==2],
        'Fisik':    [c for c in df.columns if c.startswith('T_KC2_') and int(c.split('_')[-1])%3==2],
        'Sekuriti': [c for c in df.columns if c.startswith('T_SC2_') and int(c.split('_')[-1])%3==2],
        'Brand':    [c for c in df.columns if c.startswith('T_C1B_') and int(c.split('_')[-1])%3==2],
    }

    BASE = os.path.dirname(os.path.abspath(__file__))

    try:
        df_raw = pd.read_excel(os.path.join(BASE,
                               'Deka_project_dataset_BankXYZ.xlsx'), header=0)
        kode_var  = df_raw.iloc[0]
        label_map = {str(v).strip(): _fix_mojibake(str(k).strip())
                     for k,v in kode_var.items() if pd.notna(v)}
    except Exception:
        label_map = {}

    for nama in dimensi_kepentingan:
        cols_k = dimensi_kepentingan[nama]
        cols_p = sorted(dimensi_kepuasan[nama], key=lambda x: int(x.split('_')[-1]))
        df_f = df_filtered[df_filtered['PANEL']=='Teller (KUOTA 50%)'] if nama=='Teller' else \
               df_filtered[df_filtered['PANEL']=='CS (KUOTA 50%)']     if nama=='CS'     else df_filtered
        n = min(len(cols_k), len(cols_p))
        for i in range(n):
            mk = df_f[cols_k[i]].mean(skipna=True)
            mp = df_f[cols_p[i]].mean(skipna=True)
            if pd.notna(mk) and pd.notna(mp) and mk > mp:
                alert_items.append({'dimensi': nama, 'kolom_k': cols_k[i],
                                   'gap': mk-mp, 'kepentingan': mk, 'kepuasan': mp})

    alert_items = sorted(alert_items, key=lambda x: -x['gap'])[:5]
    warna_alert = [DANGER, '#F97316', WARNING, TEAL_MED, BLUE_MED]

    for idx, item in enumerate(alert_items):
        label = label_map.get(item['kolom_k'], item['kolom_k'])
        warna = warna_alert[idx]
        st.markdown(f"""
        <div style="background:{WHITE};border-radius:12px;padding:14px 18px;
            border:1px solid {GRAY_BORDER};border-left:5px solid {warna};
            margin-bottom:8px;box-shadow:0 1px 4px rgba(0,0,0,0.04);
            display:flex;justify-content:space-between;align-items:center;
            flex-wrap:wrap;gap:10px;">
            <div style="display:flex;align-items:center;gap:10px;flex:1;min-width:240px;">
                <span style="background:{warna};color:white;border-radius:6px;
                    padding:3px 10px;font-size:0.72rem;font-weight:700;
                    white-space:nowrap;">#{idx+1} {item['dimensi']}</span>
                <span style="font-size:0.9rem;font-weight:500;
                    color:{NAVY_DARK};line-height:1.4;">{label}</span>
            </div>
            <div style="text-align:right;min-width:180px;white-space:nowrap;">
                <span style="font-size:0.78rem;color:{GRAY_TEXT};">
                    K:{item['kepentingan']:.2f} &nbsp;|&nbsp; P:{item['kepuasan']:.2f} &nbsp;|&nbsp;
                </span>
                <span style="font-size:0.88rem;font-weight:700;color:{warna};">
                    Gap {item['gap']:.3f}</span>
            </div>
        </div>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# TAB 2 — CUSTOMER SERVICE INDEX (Prioritas Layanan)
# KPI: Total Responden, Atribut Prioritas, Dimensi Terkritis, Gap Terbesar
# → IPA dengan filter dimensi (Fisik-Brand-Teller-CS-ATM-Sekuriti)
# → KPI samping: Prioritas Utama, Pertahankan, Prioritas Rendah, Berlebihan
# → Visual IPA
# → Atribut Prioritas Utama
# ════════════════════════════════════════════════════════════
with tab2:
    if len(df_filtered) == 0:
        st.warning("Tidak ada data untuk filter yang dipilih.")
        st.stop()

    hasil_ipa = load_ipa()

    # ── KPI Cards ────────────────────────────────────────────
    n_tot_2 = len(df_filtered)

    # Hitung total atribut prioritas di semua dimensi
    total_prioritas = sum(
        len(hasil_ipa[d][hasil_ipa[d]['kuadran']=='Prioritas Utama'])
        for d in hasil_ipa
    )
    # Dimensi terkritis: yang punya gap rata-rata terbesar
    gap_per_dim = {}
    for d_name, ipa_df in hasil_ipa.items():
        pr = ipa_df[ipa_df['kuadran']=='Prioritas Utama']
        if len(pr) > 0:
            gap_per_dim[d_name] = pr['gap'].mean()
    dim_kritis = max(gap_per_dim, key=gap_per_dim.get) if gap_per_dim else '-'
    # Gap terbesar global
    all_gaps = []
    for d_name, ipa_df in hasil_ipa.items():
        pr = ipa_df[ipa_df['kuadran']=='Prioritas Utama']
        if len(pr) > 0:
            all_gaps.extend(pr['gap'].tolist())
    gap_terbesar = max(all_gaps) if all_gaps else 0

    k1, k2, k3, k4 = st.columns(4)
    kpi_card(k1, "Total Responden", f"{n_tot_2:,}", "dalam filter terpilih", TEAL_MED, "👥")
    kpi_card(k2, "Atribut Prioritas Utama", f"{total_prioritas}", "atribut perlu perbaikan segera", DANGER, "🎯")
    kpi_card(k3, "Dimensi Terkritis", dim_kritis, f"gap rata-rata {gap_per_dim.get(dim_kritis,0):.3f}", WARNING, "⚡")
    kpi_card(k4, "Gap Terbesar", f"{gap_terbesar:.3f}", "selisih kepentingan vs kepuasan", DANGER, "📉")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── IPA Filter + KPI Kuadran ─────────────────────────────
    st.markdown(f'<p class="section-title">Importance Performance Analysis</p>', unsafe_allow_html=True)

    # Urutan dimensi: Fisik Bank - Brand Image - Teller - CS - ATM - Sekuriti
    DIMENSI_ORDER = ['Fisik', 'Brand', 'Teller', 'CS', 'ATM', 'Sekuriti']
    dimensi_options = [d for d in DIMENSI_ORDER if d in hasil_ipa]
    # Add any remaining
    for d in hasil_ipa:
        if d not in dimensi_options:
            dimensi_options.append(d)

    col_sel, col_info = st.columns([2, 3])

    with col_sel:
        dimensi_dipilih = st.selectbox(
            "Pilih Dimensi Layanan",
            dimensi_options,
            key="ipa_dimensi"
        )

    ipa = hasil_ipa[dimensi_dipilih]
    n_prioritas   = len(ipa[ipa['kuadran'] == 'Prioritas Utama'])
    n_pertahankan = len(ipa[ipa['kuadran'] == 'Pertahankan'])
    n_rendah      = len(ipa[ipa['kuadran'] == 'Prioritas Rendah'])
    n_berlebihan  = len(ipa[ipa['kuadran'] == 'Berlebihan'])

    with col_info:
        st.markdown(f"""
        <div style="display:flex;gap:10px;margin-top:20px;">
            <div style="flex:1;text-align:center;background:{WHITE};
                border-radius:10px;padding:12px 8px;
                border:1px solid {GRAY_BORDER};border-top:3px solid {DANGER};">
                <div style="font-size:1.5rem;font-weight:700;color:{DANGER};">{n_prioritas}</div>
                <div style="font-size:0.7rem;color:#6B7280;">Prioritas Utama</div>
            </div>
            <div style="flex:1;text-align:center;background:{WHITE};
                border-radius:10px;padding:12px 8px;
                border:1px solid {GRAY_BORDER};border-top:3px solid {SUCCESS};">
                <div style="font-size:1.5rem;font-weight:700;color:{SUCCESS};">{n_pertahankan}</div>
                <div style="font-size:0.7rem;color:#6B7280;">Pertahankan</div>
            </div>
            <div style="flex:1;text-align:center;background:{WHITE};
                border-radius:10px;padding:12px 8px;
                border:1px solid {GRAY_BORDER};border-top:3px solid {BLUE_MED};">
                <div style="font-size:1.5rem;font-weight:700;color:{BLUE_MED};">{n_rendah}</div>
                <div style="font-size:0.7rem;color:#6B7280;">Prioritas Rendah</div>
            </div>
            <div style="flex:1;text-align:center;background:{WHITE};
                border-radius:10px;padding:12px 8px;
                border:1px solid {GRAY_BORDER};border-top:3px solid {WARNING};">
                <div style="font-size:1.5rem;font-weight:700;color:{WARNING};">{n_berlebihan}</div>
                <div style="font-size:0.7rem;color:#6B7280;">Berlebihan</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── IPA Chart ────────────────────────────────────────────
    kuadran_warna = {
        'Prioritas Utama':  DANGER,
        'Pertahankan':      SUCCESS,
        'Prioritas Rendah': BLUE_MED,
        'Berlebihan':       WARNING,
    }

    fig_ipa = go.Figure()
    for kuadran, warna in kuadran_warna.items():
        df_k = ipa[ipa['kuadran'] == kuadran]
        if len(df_k) == 0: continue
        fig_ipa.add_trace(go.Scatter(
            x=df_k['mean_kepuasan'],
            y=df_k['mean_kepentingan'],
            mode='markers+text',
            name=kuadran,
            marker=dict(color=warna, size=12,
                       line=dict(color=WHITE, width=2)),
            text=df_k['label'].str[:25],
            textposition='top center',
            textfont=dict(size=8, family='Poppins', color='#374151'),
            hovertemplate=(
                '<b>%{text}</b><br>'
                'Kepuasan: %{x:.3f}<br>'
                'Kepentingan: %{y:.3f}<extra></extra>'
            ),
        ))

    mean_k = ipa['mean_kepentingan'].mean()
    mean_p = ipa['mean_kepuasan'].mean()
    x_range = [ipa['mean_kepuasan'].min()-0.05, ipa['mean_kepuasan'].max()+0.05]
    y_range = [ipa['mean_kepentingan'].min()-0.05, ipa['mean_kepentingan'].max()+0.05]

    fig_ipa.add_hline(y=mean_k, line_dash='dash',
                      line_color=GRAY_TEXT, line_width=1.5, opacity=0.5)
    fig_ipa.add_vline(x=mean_p, line_dash='dash',
                      line_color=GRAY_TEXT, line_width=1.5, opacity=0.5)

    for label_q, x_q, y_q in [
        ("Prioritas Utama",  x_range[0]+0.005, y_range[1]-0.005),
        ("Pertahankan",      x_range[1]-0.005, y_range[1]-0.005),
        ("Prioritas Rendah", x_range[0]+0.005, y_range[0]+0.005),
        ("Berlebihan",       x_range[1]-0.005, y_range[0]+0.005),
    ]:
        fig_ipa.add_annotation(
            x=x_q, y=y_q, text=label_q,
            font=dict(size=9, color='#9CA3AF', family='Poppins'),
            showarrow=False, opacity=0.8
        )

    fig_ipa.update_layout(
        height=480,
        margin=dict(t=20,b=60,l=60,r=20),
        paper_bgcolor='white',
        plot_bgcolor='white',
        xaxis=dict(title='Rata-rata Kepuasan',
                  tickfont=dict(family='Poppins', size=11),
                  gridcolor=GRAY_BORDER, gridwidth=1),
        yaxis=dict(title='Rata-rata Kepentingan',
                  tickfont=dict(family='Poppins', size=11),
                  gridcolor=GRAY_BORDER, gridwidth=1),
        legend=dict(orientation='h', yanchor='bottom', y=-0.18,
                   xanchor='center', x=0.5,
                   font=dict(family='Poppins', size=11)),
        hoverlabel=dict(font=dict(family='Poppins')),
    )
    with st.container(border=True):
        st.plotly_chart(fig_ipa, use_container_width=True,
                       config={'displayModeBar': False})

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Atribut Prioritas Utama ───────────────────────────────
    st.markdown(f'<p class="section-title">Atribut Prioritas Utama — {dimensi_dipilih}</p>',
                unsafe_allow_html=True)

    prioritas = ipa[ipa['kuadran'] == 'Prioritas Utama'].sort_values('gap', ascending=False)

    if len(prioritas) == 0:
        with st.container(border=True):
            st.success(f"Tidak ada atribut Prioritas Utama di dimensi {dimensi_dipilih}.")
    else:
        warna_prior = [DANGER, '#F97316', WARNING, TEAL_MED, BLUE_MED]
        for idx_p, (_, row) in enumerate(prioritas.iterrows()):
            gap_pct = (row['gap'] / row['mean_kepentingan']) * 100
            warna = warna_prior[min(idx_p, len(warna_prior)-1)]
            st.markdown(f"""
            <div style="background:{WHITE};border-radius:12px;padding:14px 18px;
                border:1px solid {GRAY_BORDER};border-left:5px solid {warna};
                margin-bottom:8px;box-shadow:0 1px 4px rgba(0,0,0,0.04);
                display:flex;justify-content:space-between;align-items:center;
                flex-wrap:wrap;gap:10px;">
                <div style="display:flex;align-items:flex-start;gap:10px;flex:1;min-width:260px;">
                    <span style="background:{warna};color:white;border-radius:6px;
                        padding:3px 10px;font-size:0.72rem;font-weight:700;
                        white-space:nowrap;margin-top:1px;">#{idx_p+1}</span>
                    <div>
                        <div style="font-size:0.9rem;font-weight:500;line-height:1.4;
                            color:{NAVY_DARK};">{row['label']}</div>
                        <div style="font-size:0.75rem;color:{GRAY_TEXT};margin-top:4px;">
                            Kepentingan: <b style="color:{NAVY_DARK};">{row['mean_kepentingan']:.3f}</b>
                            &nbsp;|&nbsp;
                            Kepuasan: <b style="color:{TEAL_MED};">{row['mean_kepuasan']:.3f}</b>
                        </div>
                    </div>
                </div>
                <div style="text-align:right;min-width:100px;white-space:nowrap;">
                    <div style="font-size:1.1rem;font-weight:700;color:{warna};">
                        -{gap_pct:.1f}%</div>
                    <div style="font-size:0.68rem;color:{GRAY_TEXT};">Gap: {row['gap']:.3f}</div>
                </div>
            </div>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# TAB 3 — LOYALITAS INDEX (Segmentasi Loyalitas)
# ════════════════════════════════════════════════════════════
with tab3:
    if len(df_filtered) == 0:
        st.warning("Tidak ada data untuk filter yang dipilih.")
        st.stop()

    render_kpi_segmentasi(df_filtered)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    if 'loyalty_segment_display' not in df_filtered.columns:
        df_filtered = df_filtered.copy()
        df_filtered['loyalty_segment_display'] = df_filtered['loyalty_segment'].replace({
            'Hidden Gem': 'At Risk', 'Lost Cause': 'At Risk'
        })

    SEGMENT_COLORS = {'Loyal Aman': SUCCESS, 'Latent Risk': WARNING, 'At Risk': DANGER}

    st.markdown(f'<p class="section-title">Loyalty Risk Matrix</p>',
                unsafe_allow_html=True)

    fig_matrix = go.Figure()
    for seg, warna_s in SEGMENT_COLORS.items():
        df_seg = df_filtered[df_filtered['loyalty_segment_display'] == seg]
        if len(df_seg) == 0: continue
        fig_matrix.add_trace(go.Scatter(
            x=df_seg['E1A'] + np.random.uniform(-0.08, 0.08, len(df_seg)),
            y=df_seg['G1A'] + np.random.uniform(-0.15, 0.15, len(df_seg)),
            mode='markers',
            name=f"{seg} ({len(df_seg)})",
            marker=dict(color=warna_s, size=7, opacity=0.6,
                       line=dict(color=WHITE, width=1)),
            hovertemplate=f'<b>{seg}</b><br>Kepuasan: %{{x:.1f}}<br>NPS: %{{y:.0f}}<extra></extra>',
        ))

    fig_matrix.add_hline(y=8, line_dash='dash', line_color=GRAY_TEXT,
                         line_width=1.5, opacity=0.5)
    fig_matrix.add_vline(x=5, line_dash='dash', line_color=GRAY_TEXT,
                         line_width=1.5, opacity=0.5)

    for label_m, x_m, y_m in [
        ("Loyal Aman", 5.5, 9.5), ("Latent Risk", 5.5, 6.5),
        ("Hidden Gem", 4.5, 9.5), ("Lost Cause", 4.5, 6.5),
    ]:
        fig_matrix.add_annotation(x=x_m, y=y_m, text=label_m,
            font=dict(size=9, color='#9CA3AF', family='Poppins'),
            showarrow=False, opacity=0.7)

    fig_matrix.update_layout(
        height=420,
        margin=dict(t=10, b=60, l=60, r=20),
        paper_bgcolor='white', plot_bgcolor='white',
        xaxis=dict(title='Kepuasan Overall (E1A)',
                  tickfont=dict(family='Poppins', size=11),
                  gridcolor=GRAY_BORDER, range=[3.5, 6.5]),
        yaxis=dict(title='NPS Score (G1A)',
                  tickfont=dict(family='Poppins', size=11),
                  gridcolor=GRAY_BORDER, range=[3, 11]),
        legend=dict(font=dict(family='Poppins', size=11),
                   orientation='h', y=-0.15),
    )
    with st.container(border=True):
        st.plotly_chart(fig_matrix, use_container_width=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    col_s1, col_s2 = st.columns(2)

    with col_s1:
        st.markdown(f'<p class="section-title">Kepuasan per Dimensi per Segmen</p>',
                    unsafe_allow_html=True)
        rata_cols_seg = {
            'Fisik': 'rata_fisik', 'Brand': 'rata_brand',
            'Teller': 'rata_teller', 'CS': 'rata_cs',
            'ATM': 'rata_atm', 'Sekuriti': 'rata_sekuriti',
        }
        fig_seg_dim = go.Figure()
        for seg, warna_s in SEGMENT_COLORS.items():
            df_s = df_filtered[df_filtered['loyalty_segment_display'] == seg]
            if len(df_s) == 0: continue
            vals = [df_s[col].mean(skipna=True) for col in rata_cols_seg.values()]
            fig_seg_dim.add_trace(go.Bar(
                x=list(rata_cols_seg.keys()), y=vals,
                name=f"{seg} (n={len(df_s)})",
                marker_color=warna_s, opacity=0.85,
                hovertemplate='%{x}: %{y:.3f}<extra>' + seg + '</extra>',
            ))
        fig_seg_dim.update_layout(
            barmode='group', height=320,
            margin=dict(t=10, b=40, l=20, r=20),
            paper_bgcolor='white', plot_bgcolor='white',
            xaxis=dict(tickfont=dict(family='Poppins', size=11), showgrid=False),
            yaxis=dict(tickfont=dict(family='Poppins', size=11),
                      gridcolor=GRAY_BORDER, range=[4.0, 6.2]),
            legend=dict(font=dict(family='Poppins', size=10),
                       orientation='h', y=-0.2),
        )
        with st.container(border=True):
            st.plotly_chart(fig_seg_dim, use_container_width=True)

    with col_s2:
        st.markdown(f'<p class="section-title">Tren Loyalitas per Lama Nasabah</p>',
                    unsafe_allow_html=True)

        urutan_lama = [
            '1 bulan s/d 3 bulan', '3 bulan s/d 11 bulan',
            '1 tahun s/d 2 tahun 11 bulan',
            '3 tahun s/d 4 tahun 11 bulan', '5 tahun atau lebih'
        ]
        label_lama = ['< 3 bln', '3-11 bln', '1-3 thn', '3-5 thn', '5+ thn']
        tren_data = []
        for lama, label in zip(urutan_lama, label_lama):
            df_l = df_filtered[df_filtered['S4'] == lama]
            if len(df_l) == 0: continue
            tren_data.append({
                'label': label,
                'mean_nps': df_l['G1A'].mean(skipna=True),
                'pct_promoter': (df_l['NPS_category'] == 'Promoter').mean() * 100,
                'n': len(df_l)
            })

        if tren_data:
            df_tren = pd.DataFrame(tren_data)
            fig_tren = go.Figure()
            fig_tren.add_trace(go.Scatter(
                x=df_tren['label'], y=df_tren['mean_nps'],
                mode='lines+markers', name='Rata-rata NPS',
                line=dict(color=TEAL_MED, width=2.5),
                marker=dict(size=10, color=TEAL_MED,
                           line=dict(color=WHITE, width=2)),
                hovertemplate='%{x}<br>NPS: %{y:.2f}<extra></extra>',
                yaxis='y1',
            ))
            fig_tren.add_trace(go.Bar(
                x=df_tren['label'], y=df_tren['pct_promoter'],
                name='% Promoter',
                marker_color=SUCCESS, opacity=0.3,
                hovertemplate='%{x}<br>% Promoter: %{y:.1f}%<extra></extra>',
                yaxis='y2',
            ))
            fig_tren.update_layout(
                height=320,
                margin=dict(t=10, b=40, l=50, r=50),
                paper_bgcolor='white', plot_bgcolor='white',
                xaxis=dict(tickfont=dict(family='Poppins', size=11), showgrid=False),
                yaxis=dict(title='Rata-rata NPS', range=[8, 11],
                          tickfont=dict(family='Poppins', size=10),
                          gridcolor=GRAY_BORDER),
                yaxis2=dict(title='% Promoter', overlaying='y', side='right',
                           range=[0, 120],
                           tickfont=dict(family='Poppins', size=10)),
                legend=dict(font=dict(family='Poppins', size=10),
                           orientation='h', y=-0.2),
            )
            with st.container(border=True):
                st.plotly_chart(fig_tren, use_container_width=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    st.markdown(f'<p class="section-title">Distribusi Nasabah per Segmen Loyalitas</p>',
                unsafe_allow_html=True)

    SEGMENT_COLORS_MAP = {
        'Loyal Aman': SUCCESS, 'Latent Risk': WARNING, 'At Risk': DANGER
    }
    seg_counts = df_filtered['loyalty_segment_display'].value_counts().reset_index()
    seg_counts.columns = ['segmen', 'jumlah']
    seg_counts['pct'] = (seg_counts['jumlah'] / seg_counts['jumlah'].sum() * 100).round(1)
    seg_counts['warna'] = seg_counts['segmen'].map(SEGMENT_COLORS_MAP)

    col_r1, col_r2 = st.columns([1, 2])

    with col_r1:
        with st.container(border=True):
            fig_seg_pie = go.Figure(go.Pie(
                labels=seg_counts['segmen'].tolist(),
                values=seg_counts['jumlah'].tolist(),
                hole=0.6,
                marker=dict(
                    colors=seg_counts['warna'].tolist(),
                    line=dict(color=WHITE, width=3)
                ),
                textinfo='label+percent',
                textfont=dict(size=12, family='Poppins'),
                hovertemplate='<b>%{label}</b><br>%{value:,} nasabah<br>%{percent}<extra></extra>',
                pull=[0.04 if s == 'At Risk' else 0
                      for s in seg_counts['segmen']],
            ))
            fig_seg_pie.add_annotation(
                text=f"<b>{seg_counts['jumlah'].sum():,}</b><br><span style='font-size:10px'>Total</span>",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=20, color=NAVY_DARK, family='Poppins'),
                align='center'
            )
            fig_seg_pie.update_layout(
                height=320, margin=dict(t=10,b=10,l=10,r=10),
                paper_bgcolor='white', showlegend=True,
                legend=dict(orientation='h', y=-0.12, x=0.5,
                           xanchor='center', font=dict(family='Poppins', size=11))
            )
            st.plotly_chart(fig_seg_pie, use_container_width=True,
                           config={'displayModeBar': False})

    with col_r2:
        for _, row in seg_counts.iterrows():
            rekomendasi_teks = {
                'Loyal Aman':  'Jadikan brand ambassador. Tawarkan program referral atau upgrade produk premium.',
                'Latent Risk': 'Investigasi faktor di luar cabang. Lakukan outreach personal dan survei lanjutan.',
                'At Risk':     'Intervensi segera. Prioritaskan peningkatan ATM dan CS di cabang bermasalah.',
            }
            teks = rekomendasi_teks.get(row['segmen'], '')
            st.markdown(f"""
            <div style="background:{WHITE};border-radius:14px;padding:16px 20px;
                border:1px solid {GRAY_BORDER};border-left:5px solid {row['warna']};
                margin-bottom:10px;display:flex;align-items:center;gap:20px;">
                <div style="min-width:80px;text-align:center;">
                    <div style="font-size:1.8rem;font-weight:700;
                        color:{row['warna']};">{row['jumlah']:,}</div>
                    <div style="font-size:0.72rem;color:{GRAY_TEXT};">
                        {row['pct']}% nasabah</div>
                </div>
                <div>
                    <div style="font-size:0.95rem;font-weight:700;
                        color:{NAVY_DARK};margin-bottom:4px;">{row['segmen']}</div>
                    <div style="font-size:0.82rem;color:#374151;
                        line-height:1.5;">{teks}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# TAB 4 — PROFIL CABANG (sama dengan sebelumnya)
# ════════════════════════════════════════════════════════════
with tab4:
    if len(df_filtered) == 0:
        st.warning("Tidak ada data untuk filter yang dipilih.")
        st.stop()

    render_kpi_cabang(df_filtered)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    cabang_data = df_filtered.groupby('CABANG')[list(rata_cols.values())].mean().round(2)
    cabang_data.columns = list(rata_cols.keys())
    cabang_data['Rata-rata'] = cabang_data.mean(axis=1).round(2)
    cabang_data = cabang_data.sort_values('Rata-rata', ascending=False)

    top5    = cabang_data.head(5)
    bottom5 = cabang_data.tail(5).sort_values('Rata-rata', ascending=True)

    col_top, col_bot = st.columns(2)

    with col_top:
        st.markdown(f'<p class="section-title">🏆 Top 5 Cabang Terbaik</p>',
                    unsafe_allow_html=True)
        for i, (cabang, row) in enumerate(top5.iterrows()):
            rank_colors = [SUCCESS, TEAL_MED, TEAL_LIGHT, '#a8d8b9', '#c8ecd5']
            warna_rank  = rank_colors[i]
            st.markdown(f"""
            <div style="background:{WHITE};border-radius:12px;padding:14px 18px;
                border:1px solid {GRAY_BORDER};border-left:5px solid {warna_rank};
                margin-bottom:8px;box-shadow:0 1px 4px rgba(0,0,0,0.04);
                display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <span style="font-size:0.75rem;font-weight:700;color:{GRAY_TEXT};
                        margin-right:8px;">#{i+1}</span>
                    <span style="font-size:0.9rem;font-weight:600;
                        color:{NAVY_DARK};">{cabang}</span>
                </div>
                <div style="text-align:right;">
                    <span style="font-size:1.15rem;font-weight:700;
                        color:{warna_rank};">{row['Rata-rata']:.2f}</span>
                    <span style="font-size:0.72rem;color:{GRAY_TEXT};
                        margin-left:4px;">/ 6.00</span>
                </div>
            </div>""", unsafe_allow_html=True)

    with col_bot:
        st.markdown(f'<p class="section-title">⚠️ Bottom 5 Cabang Perlu Perhatian</p>',
                    unsafe_allow_html=True)
        for i, (cabang, row) in enumerate(bottom5.iterrows()):
            rank_colors = [DANGER, '#F97316', WARNING, '#fcd97a', '#fde9a0']
            warna_rank  = rank_colors[i]
            st.markdown(f"""
            <div style="background:{WHITE};border-radius:12px;padding:14px 18px;
                border:1px solid {GRAY_BORDER};border-left:5px solid {warna_rank};
                margin-bottom:8px;box-shadow:0 1px 4px rgba(0,0,0,0.04);
                display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <span style="font-size:0.75rem;font-weight:700;color:{GRAY_TEXT};
                        margin-right:8px;">#{i+1}</span>
                    <span style="font-size:0.9rem;font-weight:600;
                        color:{NAVY_DARK};">{cabang}</span>
                </div>
                <div style="text-align:right;">
                    <span style="font-size:1.15rem;font-weight:700;
                        color:{warna_rank};">{row['Rata-rata']:.2f}</span>
                    <span style="font-size:0.72rem;color:{GRAY_TEXT};
                        margin-left:4px;">/ 6.00</span>
                </div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    col_radar, col_waktu = st.columns([1, 1])

    with col_radar:
        st.markdown(f'<p class="section-title">Branch DNA — Radar Profil Cabang</p>',
                    unsafe_allow_html=True)

        cabang_list = sorted(df_filtered['CABANG'].dropna().unique().tolist())
        cabang_pilih = st.multiselect(
            "Pilih 1-3 Cabang",
            cabang_list,
            default=cabang_list[:2] if len(cabang_list) >= 2 else cabang_list[:1],
            max_selections=3,
            key="radar_cabang"
        )

        if cabang_pilih:
            fig_radar = go.Figure()
            kategori = list(rata_cols.keys())
            warna_radar = ['#00C9C9', "#FCE561", '#A855F7']

            for idx_c, cabang in enumerate(cabang_pilih):
                df_c = df_filtered[df_filtered['CABANG'] == cabang]
                nilai = [df_c[col].mean(skipna=True) for col in rata_cols.values()]
                nilai_closed = nilai + [nilai[0]]
                kategori_closed = kategori + [kategori[0]]

                fig_radar.add_trace(go.Scatterpolar(
                    r=nilai_closed,
                    theta=kategori_closed,
                    fill='toself',
                    name=cabang,
                    line=dict(color=warna_radar[idx_c % 3], width=2),
                    fillcolor=warna_radar[idx_c % 3],
                    opacity=0.35,
                ))

            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[4.5, 6.0],
                                   tickfont=dict(family='Poppins', size=9)),
                    angularaxis=dict(tickfont=dict(family='Poppins', size=10)),
                ),
                height=380,
                margin=dict(t=20, b=20, l=20, r=20),
                paper_bgcolor='white',
                legend=dict(font=dict(family='Poppins', size=10),
                           orientation='h', y=-0.1),
                showlegend=True,
            )
            with st.container(border=True):
                st.plotly_chart(fig_radar, use_container_width=True)
        else:
            st.info("Pilih minimal 1 cabang.")

    with col_waktu:
        st.markdown(f'<p class="section-title">Waktu Tunggu — Top 5 Cabang Terburuk</p>',
                    unsafe_allow_html=True)

        waktu_data = df_filtered.groupby('CABANG').agg(
            teller_aktual=('TL5', 'mean'),
            teller_toleransi=('TL6', 'mean'),
            cs_aktual=('CS5', 'mean'),
            cs_toleransi=('CS6', 'mean'),
        ).round(1).dropna(how='all').reset_index()

        panel_waktu = st.radio("Panel", ["Teller", "CS"],
                               horizontal=True, key="panel_waktu")

        if panel_waktu == "Teller":
            wd = waktu_data.dropna(subset=['teller_aktual']).copy()
            aktual_col, tol_col = 'teller_aktual', 'teller_toleransi'
        else:
            wd = waktu_data.dropna(subset=['cs_aktual']).copy()
            aktual_col, tol_col = 'cs_aktual', 'cs_toleransi'

        with st.container(border=True):
            if len(wd) > 0:
                wd['selisih'] = wd[aktual_col] - wd[tol_col].fillna(wd[aktual_col])
                wd = wd.sort_values('selisih', ascending=False).head(5)

                for _, row_w in wd.iterrows():
                    aktual   = row_w[aktual_col]
                    tol      = row_w[tol_col] if pd.notna(row_w[tol_col]) else aktual
                    melebihi = aktual > tol
                    warna_status = DANGER if melebihi else SUCCESS
                    label_status = f"⚠️ +{aktual-tol:.0f} mnt" if melebihi else "✅ Dalam batas"
                    pct_bar = min(aktual / max(wd[aktual_col].max(), 1) * 100, 100)

                    st.markdown(f"""
                    <div style="margin-bottom:10px;">
                        <div style="display:flex;justify-content:space-between;
                            align-items:center;margin-bottom:4px;">
                            <span style="font-size:0.82rem;font-weight:600;
                                color:{NAVY_DARK};">{row_w['CABANG']}</span>
                            <div style="text-align:right;">
                                <span style="font-size:0.82rem;font-weight:700;
                                    color:{warna_status};">{aktual:.0f} mnt</span>
                                <span style="font-size:0.72rem;color:{GRAY_TEXT};
                                    margin-left:6px;">tol: {tol:.0f} mnt</span>
                                <span style="font-size:0.72rem;font-weight:600;
                                    color:{warna_status};margin-left:6px;">
                                    {label_status}</span>
                            </div>
                        </div>
                        <div style="background:{GRAY_BORDER};border-radius:4px;height:6px;">
                            <div style="background:{warna_status};width:{pct_bar:.1f}%;
                                height:6px;border-radius:4px;"></div>
                        </div>
                    </div>""", unsafe_allow_html=True)
            else:
                st.info("Tidak ada data waktu tunggu untuk filter ini.")


# ════════════════════════════════════════════════════════════
# TAB 5 — PETA EMOSI & PROFIL NASABAH (gabung)
# Urutan: Peta Emosi dulu, kemudian Profil Nasabah
# ════════════════════════════════════════════════════════════
with tab5:
    if len(df_filtered) == 0:
        st.warning("Tidak ada data untuk filter yang dipilih.")
        st.stop()

    # ════ BAGIAN A: PETA EMOSI ════════════════════════════════
    emotion_results = load_emotion()
    render_kpi_emosi(df_filtered, emotion_results)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Data Quality Flag: deteksi straight-lining ───────────
    sl = deteksi_straightlining(df_filtered)
    if sl and sl['n_flat'] > 0:
        warna_dq = DANGER if sl['pct_flat'] >= 30 else WARNING
        with st.expander(
            f"⚠️ Peringatan Kualitas Data — {sl['n_flat']:,} dari {sl['n_total']:,} responden "
            f"({sl['pct_flat']:.1f}%) menjawab seluruh 15 item emosi dengan nilai identik",
            expanded=(sl['pct_flat'] >= 30)
        ):
            st.markdown(f"""
            <div style="background:{WHITE};border-radius:12px;padding:16px 20px;
                border-left:5px solid {warna_dq};margin-bottom:12px;">
                <p style="font-size:0.85rem;color:#374151;line-height:1.6;margin:0;">
                Sebanyak <b style="color:{warna_dq};">{sl['n_flat']:,} responden ({sl['pct_flat']:.1f}%)</b>
                memberi skor yang <b>sama persis pada seluruh 15 pertanyaan emosi</b> — termasuk pasangan
                emosi yang seharusnya berlawanan makna (misalnya "Senang" dan "Marah" sekaligus bernilai 6).
                Pola ini disebut <b>straight-lining</b>, indikasi kuat responden mengisi survei tanpa
                membaca pertanyaan secara saksama. Skor emosi dari responden ini sebaiknya
                <b>tidak dijadikan dasar pengambilan keputusan</b> tanpa pembersihan data lebih lanjut.
                </p>
            </div>
            """, unsafe_allow_html=True)

            if sl['prov_full_flat']:
                daftar = ", ".join([f"{p} ({n} dari {n} responden)" for p, n in sl['prov_full_flat']])
                st.markdown(f"""
                <div style="background:#FEF2F2;border-radius:10px;padding:12px 16px;
                    border:1px solid #FECACA;margin-bottom:12px;">
                    <span style="font-size:0.8rem;color:{DANGER};font-weight:600;">
                        🔴 Provinsi dengan SELURUH respondennya straight-line:</span>
                    <span style="font-size:0.8rem;color:#374151;"> {daftar}.</span>
                    <br><span style="font-size:0.76rem;color:{GRAY_TEXT};">
                        Rata-rata emosi di provinsi ini bukan estimasi yang valid dan tidak
                        boleh dibandingkan langsung dengan provinsi lain pada chart di bawah.</span>
                </div>
                """, unsafe_allow_html=True)

            if len(sl['by_prov']) > 0:
                st.markdown(f'<p style="font-size:0.82rem;font-weight:600;color:{NAVY_DARK};margin-bottom:6px;">Distribusi Straight-liner per Provinsi</p>', unsafe_allow_html=True)
                fig_sl = go.Figure(go.Bar(
                    y=sl['by_prov'].index.tolist(),
                    x=sl['by_prov'].values.tolist(),
                    orientation='h',
                    marker_color=DANGER, opacity=0.75,
                    text=[f"{v:,}" for v in sl['by_prov'].values],
                    textposition='outside',
                    textfont=dict(family='Poppins', size=10),
                    hovertemplate='%{y}<br>%{x:,} responden straight-line<extra></extra>',
                ))
                fig_sl.update_layout(
                    height=max(220, 28 * len(sl['by_prov'])),
                    margin=dict(t=10, b=10, l=10, r=60),
                    paper_bgcolor='white', plot_bgcolor='white',
                    xaxis=dict(tickfont=dict(family='Poppins', size=10), gridcolor=GRAY_BORDER),
                    yaxis=dict(tickfont=dict(family='Poppins', size=10), autorange='reversed'),
                )
                st.plotly_chart(fig_sl, use_container_width=True, config={'displayModeBar': False})

            st.caption("Rekomendasi: pertimbangkan mengeluarkan responden straight-liner dari "
                       "analisis emosi pada putaran survei berikutnya, atau tambahkan pertanyaan "
                       "kontrol (attention check) untuk menyaring jawaban tidak valid sejak awal.")

            # ── Polarity collapse: emosi positif & negatif tetap mengelompok tinggi ──
            if sl.get('polarity_collapse'):
                st.markdown(f"""
                <div style="background:#FFF7ED;border-radius:10px;padding:12px 16px;
                    border:1px solid #FED7AA;margin-top:12px;">
                    <span style="font-size:0.8rem;color:#C2410C;font-weight:600;">
                        🟠 Temuan tambahan — skor emosi positif dan negatif tetap mengelompok tinggi
                        meski straight-liner sudah dikeluarkan:</span>
                    <br><span style="font-size:0.8rem;color:#374151;">
                        Pada {sl['n_bersih']:,} responden non-straight-liner, rata-rata emosi
                        <b>positif</b> ({sl['mean_pos_bersih']:.2f}) dan rata-rata emosi
                        <b>negatif</b> ({sl['mean_neg_bersih']:.2f}) hanya berselisih
                        {abs(sl['mean_pos_bersih']-sl['mean_neg_bersih']):.2f} poin pada skala 1–6 —
                        nasabah cenderung memberi skor tinggi pada emosi "Kecewa", "Frustrasi", dan
                        "Tidak Percaya" sama seperti pada emosi "Senang" dan "Puas".</span>
                    <br><span style="font-size:0.76rem;color:{GRAY_TEXT};">
                        Ini bisa disebabkan oleh arah skala pada item emosi negatif yang membingungkan
                        responden (mis. kalimat negatif dengan skala "sangat setuju"), atau oleh
                        acquiescence bias (kecenderungan menjawab tinggi pada semua pernyataan).
                        Sebaiknya item-item ini ditinjau ulang sebelum dijadikan dasar insight emosi
                        pada chart "Spektrum Emosi" di bawah.</span>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    df_emosi    = emotion_results['df_emosi']
    df_korelasi = emotion_results['df_korelasi']

    st.markdown(f'<p class="section-title">Spektrum Emosi Nasabah — XYZ vs Kompetitor</p>',
                unsafe_allow_html=True)

    emosi_pos = df_emosi[df_emosi['kategori'] == 'positif'].sort_values('mean_xyz', ascending=True)
    emosi_neg = df_emosi[df_emosi['kategori'] == 'negatif'].sort_values('mean_xyz', ascending=False)

    col_ep, col_en = st.columns(2)

    def buat_lollipop(df_e, warna_xyz, judul, x_range):
        fig = go.Figure()
        for _, r in df_e.iterrows():
            fig.add_shape(type='line',
                x0=r['mean_komp'], x1=r['mean_xyz'],
                y0=r['emosi'], y1=r['emosi'],
                line=dict(color=GRAY_BORDER, width=2))
        fig.add_trace(go.Scatter(
            x=df_e['mean_komp'], y=df_e['emosi'],
            mode='markers', name='Kompetitor',
            marker=dict(color=GRAY_TEXT, size=9, symbol='circle'),
            hovertemplate='%{y} — Kompetitor: %{x:.3f}<extra></extra>',
        ))
        fig.add_trace(go.Scatter(
            x=df_e['mean_xyz'], y=df_e['emosi'],
            mode='markers', name='Bank XYZ',
            marker=dict(color=warna_xyz, size=12, symbol='circle',
                       line=dict(color=WHITE, width=2)),
            hovertemplate='%{y} — XYZ: %{x:.3f}<extra></extra>',
        ))
        fig.update_layout(
            title=judul, height=320,
            margin=dict(t=30, b=20, l=110, r=20),
            paper_bgcolor='white', plot_bgcolor='white',
            xaxis=dict(range=x_range, tickfont=dict(family='Poppins', size=10),
                      gridcolor=GRAY_BORDER),
            yaxis=dict(tickfont=dict(family='Poppins', size=10), showgrid=False),
            legend=dict(font=dict(family='Poppins', size=10),
                       orientation='h', y=-0.18),
            title_font=dict(family='Poppins', size=12, color=NAVY_DARK),
        )
        return fig

    with col_ep:
        fig_pos = buat_lollipop(emosi_pos, SUCCESS, 'Emosi Positif', [4.3, 6.2])
        with st.container(border=True):
            st.plotly_chart(fig_pos, use_container_width=True)

    with col_en:
        fig_neg = buat_lollipop(emosi_neg, DANGER, 'Emosi Negatif', [0.8, 2.5])
        with st.container(border=True):
            st.plotly_chart(fig_neg, use_container_width=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    st.markdown(f'<p class="section-title">Korelasi Emosi terhadap NPS</p>',
                unsafe_allow_html=True)

    df_korr = df_korelasi.sort_values('korelasi', ascending=True)
    warna_korr = [SUCCESS if k > 0 else DANGER for k in df_korr['korelasi']]

    fig_korr = go.Figure(go.Bar(
        y=df_korr['emosi'], x=df_korr['korelasi'],
        orientation='h',
        marker_color=warna_korr, opacity=0.85,
        text=[f"{k:+.3f}" for k in df_korr['korelasi']],
        textposition='outside',
        textfont=dict(family='Poppins', size=10),
        hovertemplate='%{y}<br>Korelasi: %{x:.4f}<extra></extra>',
    ))
    fig_korr.add_vline(x=0, line_color=GRAY_TEXT, line_width=1.5, opacity=0.5)
    fig_korr.update_layout(
        height=420,
        margin=dict(t=10, b=20, l=120, r=80),
        paper_bgcolor='white', plot_bgcolor='white',
        xaxis=dict(title='Korelasi Pearson dengan NPS',
                  tickfont=dict(family='Poppins', size=11),
                  gridcolor=GRAY_BORDER, zeroline=False),
        yaxis=dict(tickfont=dict(family='Poppins', size=11)),
    )
    with st.container(border=True):
        st.plotly_chart(fig_korr, use_container_width=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    st.markdown(f'<p class="section-title">Profil Emosi: Promoter vs Detractor</p>',
                unsafe_allow_html=True)

    profil_seg = emotion_results['df_profil_segmen']

    col_e1, col_e2 = st.columns(2)

    with col_e1:
        with st.container(border=True):
            st.markdown(f'<p style="font-size:0.9rem;font-weight:600;color:{NAVY_DARK};margin-bottom:8px;">Skor Rata-rata Emosi per Segmen</p>', unsafe_allow_html=True)
            segmen_cols = ['promoter', 'passive', 'detractor']
            available   = [c for c in segmen_cols if c in profil_seg.columns]
            if available:
                emosi_labels = profil_seg['emosi'].tolist()
                fig_heat_emosi = go.Figure(go.Heatmap(
                    z=[[profil_seg[c].iloc[i] for c in available]
                       for i in range(len(profil_seg))],
                    x=[s.capitalize() for s in available],
                    y=emosi_labels,
                    colorscale=[[0, DANGER], [0.5, WARNING], [1, SUCCESS]],
                    text=[[f"{profil_seg[c].iloc[i]:.2f}" for c in available]
                          for i in range(len(profil_seg))],
                    texttemplate='%{text}',
                    textfont=dict(size=10, family='Poppins'),
                    hovertemplate='%{y} — %{x}: %{z:.3f}<extra></extra>',
                    colorbar=dict(title='Skor', tickfont=dict(family='Poppins', size=9)),
                ))
                fig_heat_emosi.update_layout(
                    height=480, margin=dict(t=10, b=20, l=100, r=20),
                    paper_bgcolor='white', plot_bgcolor='white',
                    xaxis=dict(tickfont=dict(family='Poppins', size=11)),
                    yaxis=dict(tickfont=dict(family='Poppins', size=10), autorange='reversed'),
                )
                st.plotly_chart(fig_heat_emosi, use_container_width=True,
                               config={'displayModeBar': False})

    with col_e2:
        with st.container(border=True):
            st.markdown(f'<p style="font-size:0.9rem;font-weight:600;color:{NAVY_DARK};margin-bottom:8px;">Gap Emosi: Promoter vs Detractor</p>', unsafe_allow_html=True)
            if 'promoter' in profil_seg.columns and 'detractor' in profil_seg.columns:
                profil_sorted = profil_seg.copy()
                profil_sorted['gap_pd'] = profil_sorted['promoter'] - profil_sorted['detractor']
                profil_sorted = profil_sorted.sort_values('gap_pd', ascending=True)
                warna_gap = [SUCCESS if g > 0 else DANGER for g in profil_sorted['gap_pd']]
                fig_gap_emosi = go.Figure(go.Bar(
                    y=profil_sorted['emosi'], x=profil_sorted['gap_pd'],
                    orientation='h', marker_color=warna_gap, opacity=0.85,
                    text=[f"{g:+.2f}" for g in profil_sorted['gap_pd']],
                    textposition='outside',
                    textfont=dict(family='Poppins', size=10),
                    hovertemplate='%{y}<br>Gap P-D: %{x:+.3f}<extra></extra>',
                ))
                fig_gap_emosi.add_vline(x=0, line_color=GRAY_TEXT, line_width=1.5, opacity=0.5)
                fig_gap_emosi.update_layout(
                    height=480, margin=dict(t=10, b=20, l=110, r=60),
                    paper_bgcolor='white', plot_bgcolor='white',
                    xaxis=dict(title='Selisih Skor (Promoter − Detractor)',
                               tickfont=dict(family='Poppins', size=10),
                               gridcolor=GRAY_BORDER, zeroline=False),
                    yaxis=dict(tickfont=dict(family='Poppins', size=10), showgrid=False),
                )
                st.plotly_chart(fig_gap_emosi, use_container_width=True,
                               config={'displayModeBar': False})

                top_gap = profil_sorted.tail(3)['emosi'].tolist()
                bot_gap = profil_sorted.head(3)['emosi'].tolist()
                st.markdown(f"""
                <div style="background:{GRAY_LIGHT};border-radius:10px;
                    padding:12px 16px;margin-top:8px;">
                    <div style="font-size:0.8rem;color:{NAVY_DARK};font-weight:600;
                        margin-bottom:6px;">Insight Otomatis</div>
                    <div style="font-size:0.78rem;color:#374151;line-height:1.6;">
                        Promoter merasakan <b style="color:{SUCCESS};">
                        {', '.join(top_gap)}</b> jauh lebih kuat dari Detractor.<br>
                        Emosi <b style="color:{DANGER};">
                        {', '.join(bot_gap[:2])}</b> paling kecil perbedaannya
                        — perlu dieksplorasi lebih lanjut.
                    </div>
                </div>""", unsafe_allow_html=True)

    # ════ BAGIAN B: PROFIL NASABAH ════════════════════════════
    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="border-top:2px solid {GRAY_BORDER};padding-top:20px;margin-bottom:16px;">
        <p style="font-size:1.1rem;font-weight:700;color:{NAVY_DARK};
            font-family:Poppins,sans-serif;margin:0;">👤 Profil Nasabah</p>
    </div>""", unsafe_allow_html=True)

    P5_ORDER = [
        'C2 : Rp. 1.000.001 - Rp. 1.500.000','C1 : Rp. 1.500.001 - Rp. 2.000.000',
        'B : Rp. 2.000.001 - Rp. 3.000.000','A2 : Rp. 3.000.001 - Rp. 4.500.000',
        'A1 : Rp. 4.500.000 - Rp 6.000.000','A1.1 : Rp 6.000.001 - Rp 7.500.000',
        'A1.2 : Rp 7.500.001- Rp 9.000.000','A1.3 : Rp 9.000.001- Rp 10.500.000',
        'A1.4 : Rp 10.500.0001 - Rp 15.000.000','A1.5 : Rp 15.000.001- Rp 20.000.000',
        'A1.6 : Rp 20.000.001 - Rp 25.000.000',
    ]
    P5_LABEL = {
        'C2 : Rp. 1.000.001 - Rp. 1.500.000':'1-1.5 Jt',
        'C1 : Rp. 1.500.001 - Rp. 2.000.000':'1.5-2 Jt',
        'B : Rp. 2.000.001 - Rp. 3.000.000':'2-3 Jt',
        'A2 : Rp. 3.000.001 - Rp. 4.500.000':'3-4.5 Jt',
        'A1 : Rp. 4.500.000 - Rp 6.000.000':'4.5-6 Jt',
        'A1.1 : Rp 6.000.001 - Rp 7.500.000':'6-7.5 Jt',
        'A1.2 : Rp 7.500.001- Rp 9.000.000':'7.5-9 Jt',
        'A1.3 : Rp 9.000.001- Rp 10.500.000':'9-10.5 Jt',
        'A1.4 : Rp 10.500.0001 - Rp 15.000.000':'10.5-15 Jt',
        'A1.5 : Rp 15.000.001- Rp 20.000.000':'15-20 Jt',
        'A1.6 : Rp 20.000.001 - Rp 25.000.000':'20-25 Jt',
    }
    P6_ORDER = [
        'Rp. 1.000.001 - Rp. 1.500.000','Rp. 1.500.001 - Rp. 2.000.000',
        'Rp. 2.000.001 - Rp. 3.000.000','Rp. 3.000.001 - Rp. 4.500.000',
        'Rp. 4.500.000 - Rp 6.000.000','Rp 6.000.001 - Rp 7.500.000',
        'Rp 7.500.001- Rp 9.000.000','Rp 9.000.001- Rp 10.500.000',
        'Rp 10.500.0001 - Rp 15.000.000','Rp 15.000.001- Rp 20.000.000',
        'Rp 20.000.001 - Rp 25.000.000','Di atas Rp 25.000.000',
    ]
    P6_LABEL = {
        'Rp. 1.000.001 - Rp. 1.500.000':'1-1.5 Jt',
        'Rp. 1.500.001 - Rp. 2.000.000':'1.5-2 Jt',
        'Rp. 2.000.001 - Rp. 3.000.000':'2-3 Jt',
        'Rp. 3.000.001 - Rp. 4.500.000':'3-4.5 Jt',
        'Rp. 4.500.000 - Rp 6.000.000':'4.5-6 Jt',
        'Rp 6.000.001 - Rp 7.500.000':'6-7.5 Jt',
        'Rp 7.500.001- Rp 9.000.000':'7.5-9 Jt',
        'Rp 9.000.001- Rp 10.500.000':'9-10.5 Jt',
        'Rp 10.500.0001 - Rp 15.000.000':'10.5-15 Jt',
        'Rp 15.000.001- Rp 20.000.000':'15-20 Jt',
        'Rp 20.000.001 - Rp 25.000.000':'20-25 Jt',
        'Di atas Rp 25.000.000':'>25 Jt',
    }
    S7_ORDER = ['1 bulan sekali','2 minggu sekali','1 minggu sekali','1 minggu 2 kali atau lebih']
    S7_LABEL = {
        '1 bulan sekali':'1x/bulan','2 minggu sekali':'2x/bulan',
        '1 minggu sekali':'1x/minggu','1 minggu 2 kali atau lebih':'≥2x/minggu',
    }
    P3_ORDER = ['SD','SLTP','SLTA','Akademi/D3','Sarjana (S1)','Paska Sarjana (S2)','Doktor (S3)']
    P4_MAIN  = [
        'Pegawai/Karyawan Swasta','Wiraswasta/Pengusaha/Pedagang',
        'Pegawai Negeri Sipil (Bukan Guru)','Pegawai Negeri Sipil (Guru)',
        'Ibu Rumah Tangga','Tenaga Honorer','Mahasiswa/i'
    ]

    df7 = df_filtered.copy()
    n_tot7   = len(df7)
    n_menikah = (df7['P1'] == 'Menikah').sum()
    n_digital = (df7['D4'] == 'Ya').sum()
    freq_top  = df7['S7'].value_counts().idxmax() if n_tot7 > 0 else '-'
    pend_top  = df7['P3'].value_counts().idxmax() if n_tot7 > 0 else '-'

    kc1, kc2, kc3, kc4 = st.columns(4)
    for col_k, label_k, val_k, sub_k, warna_k in [
        (kc1,'Status Menikah', f"{n_menikah:,}",
         f"{n_menikah/n_tot7*100:.1f}% dari total" if n_tot7 else '-', TEAL_MED),
        (kc2,'Sadar Digital (D4)', f"{n_digital:,}",
         f"{n_digital/n_tot7*100:.1f}% mengenal layanan digital" if n_tot7 else '-', NAVY_DARK),
        (kc3,'Frekuensi Dominan', freq_top, 'kunjungan ke cabang', TEAL_MED),
        (kc4,'Pendidikan Dominan', pend_top, 'tingkat pendidikan terbanyak', NAVY_DARK),
    ]:
        with col_k:
            st.markdown(f"""
            <div style="background:{WHITE};border-radius:14px;padding:18px 20px;
                border:1.5px solid {GRAY_BORDER};border-top:4px solid {warna_k};
                box-shadow:0 2px 10px rgba(0,39,101,0.06);margin-bottom:16px;">
                <p style="font-size:0.78rem;font-weight:500;color:{GRAY_TEXT};
                    margin:0 0 6px 0;">{label_k}</p>
                <p style="font-size:1.4rem;font-weight:700;color:#1a1a2e;
                    margin:0 0 4px 0;line-height:1.2;">{val_k}</p>
                <p style="font-size:0.75rem;color:{warna_k};margin:0;">{sub_k}</p>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    col_freq, col_dig = st.columns(2)

    with col_freq:
        st.markdown(f'<p class="section-title">Frekuensi Kunjungan vs Kepuasan & Loyalitas</p>',
                    unsafe_allow_html=True)
        rows_freq = []
        for s7 in S7_ORDER:
            d = df7[df7['S7'] == s7]
            if len(d) == 0: continue
            rows_freq.append({
                'label': S7_LABEL.get(s7, s7),
                'n': len(d),
                'mean_kep': d['E1A'].mean(),
                'mean_nps': d['G1A'].mean(),
            })
        df_freq = pd.DataFrame(rows_freq)
        fig_freq = go.Figure()
        fig_freq.add_trace(go.Bar(
            x=df_freq['label'], y=df_freq['mean_kep'],
            name='Rata-rata Kepuasan', marker_color=TEAL_MED, opacity=0.85, yaxis='y1',
            hovertemplate='%{x}<br>Kepuasan: %{y:.3f}<extra></extra>',
        ))
        fig_freq.add_trace(go.Scatter(
            x=df_freq['label'], y=df_freq['mean_nps'],
            name='Rata-rata NPS', mode='lines+markers',
            line=dict(color=NAVY_DARK, width=2.5),
            marker=dict(size=9, color=NAVY_DARK, line=dict(color=WHITE, width=2)),
            yaxis='y2', hovertemplate='%{x}<br>NPS: %{y:.2f}<extra></extra>',
        ))
        fig_freq.update_layout(
            height=300, margin=dict(t=10,b=10,l=10,r=50),
            paper_bgcolor=WHITE, plot_bgcolor=WHITE,
            xaxis=dict(tickfont=dict(family='Poppins', size=11), showgrid=False),
            yaxis=dict(title='Kepuasan', range=[5.7,6.1],
                      tickfont=dict(family='Poppins', size=10), gridcolor=GRAY_BORDER),
            yaxis2=dict(title='NPS', overlaying='y', side='right', range=[8.8,9.9],
                       tickfont=dict(family='Poppins', size=10), showgrid=False),
            legend=dict(font=dict(family='Poppins', size=10), orientation='h', y=-0.2),
        )
        with st.container(border=True):
            st.plotly_chart(fig_freq, use_container_width=True, config={'displayModeBar': False})

    with col_dig:
        st.markdown(f'<p class="section-title">Kesadaran Digital vs Kepuasan</p>',
                    unsafe_allow_html=True)
        df_d4 = df7[df7['D4'].isin(['Ya','Tidak Tahu'])].copy()
        grp_dig = df_d4.groupby('D4').agg(
            n=('SERIAL','count'), mean_kep=('E1A','mean'), mean_nps=('G1A','mean'),
        ).reset_index()
        grp_dig['label'] = grp_dig['D4'].map({'Ya':'Sadar Digital','Tidak Tahu':'Belum Sadar'})
        fig_dig = go.Figure()
        warna_dig = [TEAL_MED, GRAY_TEXT]
        for i, (_, r) in enumerate(grp_dig.iterrows()):
            fig_dig.add_trace(go.Bar(
                x=[r['label']], y=[r['mean_kep']], name=r['label'],
                marker_color=warna_dig[i], opacity=0.85,
                text=[f"{r['mean_kep']:.3f}"], textposition='outside',
                textfont=dict(family='Poppins', size=12, color=NAVY_DARK),
                hovertemplate=f"{r['label']}<br>n={int(r['n'])}<br>Kepuasan: {r['mean_kep']:.3f}<extra></extra>",
            ))
        fig_dig.update_layout(
            height=300, showlegend=False, margin=dict(t=10,b=10,l=10,r=10),
            paper_bgcolor=WHITE, plot_bgcolor=WHITE,
            xaxis=dict(tickfont=dict(family='Poppins', size=13), showgrid=False),
            yaxis=dict(range=[5.75,6.0], tickfont=dict(family='Poppins', size=10), gridcolor=GRAY_BORDER),
            bargap=0.5,
        )
        with st.container(border=True):
            st.plotly_chart(fig_dig, use_container_width=True, config={'displayModeBar': False})

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    st.markdown(f'<p class="section-title">Segmen Ekonomi vs Kepuasan & NPS</p>',
                unsafe_allow_html=True)
    col_p5, col_p6 = st.columns(2)

    def buat_ekonomi_chart(df_src, kolom, order, label_map_e, judul, warna_bar):
        rows = []
        for val in order:
            d = df_src[df_src[kolom] == val]
            if len(d) < 5: continue
            rows.append({'label': label_map_e.get(val, val), 'n': len(d),
                         'mean_kep': d['E1A'].mean(), 'mean_nps': d['G1A'].mean()})
        if not rows:
            return None, None
        dff = pd.DataFrame(rows)
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=dff['label'], y=dff['mean_kep'], name='Kepuasan',
            marker_color=warna_bar, opacity=0.8, yaxis='y1',
            hovertemplate='%{x}<br>Kepuasan: %{y:.3f}<extra></extra>',
        ))
        fig.add_trace(go.Scatter(
            x=dff['label'], y=dff['mean_nps'], name='NPS', mode='lines+markers',
            line=dict(color=NAVY_DARK, width=2),
            marker=dict(size=7, color=NAVY_DARK, line=dict(color=WHITE, width=2)),
            yaxis='y2', hovertemplate='%{x}<br>NPS: %{y:.2f}<extra></extra>',
        ))
        fig.update_layout(
            title=judul, height=300, margin=dict(t=30,b=10,l=10,r=50),
            paper_bgcolor=WHITE, plot_bgcolor=WHITE,
            xaxis=dict(tickfont=dict(family='Poppins', size=9), tickangle=-30, showgrid=False),
            yaxis=dict(range=[5.7,6.05], tickfont=dict(family='Poppins', size=9), gridcolor=GRAY_BORDER),
            yaxis2=dict(overlaying='y', side='right', range=[8.8,9.9],
                       tickfont=dict(family='Poppins', size=9), showgrid=False),
            legend=dict(font=dict(family='Poppins', size=9), orientation='h', y=-0.25),
            title_font=dict(family='Poppins', size=11, color=NAVY_DARK),
        )
        return fig, dff

    with col_p5:
        fig_p5, dff_p5 = buat_ekonomi_chart(df7,'P5',P5_ORDER,P5_LABEL,'Pengeluaran Rutin per Bulan',TEAL_MED)
        if fig_p5:
            with st.container(border=True):
                st.plotly_chart(fig_p5, use_container_width=True, config={'displayModeBar': False})

    with col_p6:
        fig_p6, _ = buat_ekonomi_chart(df7,'P6',P6_ORDER,P6_LABEL,'Penghasilan Rumah Tangga per Bulan',BLUE_MED)
        if fig_p6:
            with st.container(border=True):
                st.plotly_chart(fig_p6, use_container_width=True, config={'displayModeBar': False})

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    st.markdown(f'<p class="section-title">Kepuasan & NPS per Segmen Pekerjaan</p>',
                unsafe_allow_html=True)
    rows_p4 = []
    for p4 in P4_MAIN:
        d = df7[df7['P4'] == p4]
        if len(d) < 10: continue
        rows_p4.append({
            'label': p4.replace('Pegawai Negeri Sipil','PNS')
                       .replace('Pegawai/Karyawan Swasta','Karyawan Swasta')
                       .replace('Wiraswasta/Pengusaha/Pedagang','Wiraswasta')
                       .replace('Ibu Rumah Tangga','IRT'),
            'n': len(d), 'mean_kep': d['E1A'].mean(), 'mean_nps': d['G1A'].mean(),
        })
    df_p4 = pd.DataFrame(rows_p4).sort_values('mean_kep', ascending=True)
    fig_p4 = go.Figure()
    grand_mean = df7['E1A'].mean()
    for _, r in df_p4.iterrows():
        fig_p4.add_shape(type='line', x0=grand_mean, x1=r['mean_kep'],
                         y0=r['label'], y1=r['label'],
                         line=dict(color=GRAY_BORDER, width=2))
    fig_p4.add_vline(x=grand_mean, line_dash='dash', line_color=GRAY_TEXT, line_width=1.5, opacity=0.6)
    fig_p4.add_annotation(x=grand_mean, y=len(df_p4)-0.3,
        text=f'Rata-rata: {grand_mean:.3f}',
        font=dict(size=9, color=GRAY_TEXT, family='Poppins'),
        showarrow=False, xanchor='left', xshift=5)
    fig_p4.add_trace(go.Scatter(
        x=df_p4['mean_kep'], y=df_p4['label'],
        mode='markers+text',
        marker=dict(color=[SUCCESS if v >= grand_mean else DANGER for v in df_p4['mean_kep']],
                   size=14, line=dict(color=WHITE, width=2)),
        text=[f"{v:.3f}" for v in df_p4['mean_kep']],
        textposition='middle right',
        textfont=dict(family='Poppins', size=10, color=NAVY_DARK),
        customdata=df_p4[['n','mean_nps']].values,
        hovertemplate='<b>%{y}</b><br>n=%{customdata[0]}<br>Kepuasan: %{x:.3f}<br>NPS: %{customdata[1]:.2f}<extra></extra>',
        showlegend=False,
    ))
    fig_p4.update_layout(
        height=320, margin=dict(t=10,b=10,l=160,r=80),
        paper_bgcolor=WHITE, plot_bgcolor=WHITE,
        xaxis=dict(range=[5.75,5.97], tickfont=dict(family='Poppins', size=10),
                  gridcolor=GRAY_BORDER, title='Rata-rata Kepuasan'),
        yaxis=dict(tickfont=dict(family='Poppins', size=11), showgrid=False),
    )
    with st.container(border=True):
        st.plotly_chart(fig_p4, use_container_width=True, config={'displayModeBar': False})

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    col_p1, col_p3 = st.columns(2)
    with col_p1:
        st.markdown(f'<p class="section-title">Komposisi Status Pernikahan</p>', unsafe_allow_html=True)
        grp_p1 = df7['P1'].value_counts().reset_index()
        grp_p1.columns = ['status','n']
        grp_p1 = grp_p1[grp_p1['status'].isin(['Menikah','Belum menikah','Duda / Janda'])]
        kep_p1 = df7.groupby('P1')['E1A'].mean().reset_index()
        kep_p1.columns = ['status','mean_kep']
        grp_p1 = grp_p1.merge(kep_p1, on='status', how='left')
        for _, r in grp_p1.iterrows():
            pct = r['n'] / grp_p1['n'].sum() * 100
            warna_p1 = TEAL_MED if r['status']=='Menikah' else (
                BLUE_MED if r['status']=='Belum menikah' else GRAY_TEXT)
            st.markdown(f"""
            <div style="background:{WHITE};border-radius:12px;padding:14px 18px;
                border:1px solid {GRAY_BORDER};border-left:5px solid {warna_p1};
                margin-bottom:8px;display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <div style="font-size:0.9rem;font-weight:600;color:{NAVY_DARK};">{r['status']}</div>
                    <div style="font-size:0.75rem;color:{GRAY_TEXT};margin-top:2px;">n = {r['n']:,} &nbsp;·&nbsp; {pct:.1f}% responden</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:1.1rem;font-weight:700;color:{warna_p1};">{r['mean_kep']:.3f}</div>
                    <div style="font-size:0.7rem;color:{GRAY_TEXT};">rata-rata kepuasan</div>
                </div>
            </div>""", unsafe_allow_html=True)

    with col_p3:
        st.markdown(f'<p class="section-title">Kepuasan per Tingkat Pendidikan</p>', unsafe_allow_html=True)
        rows_p3 = []
        for p3 in P3_ORDER:
            d = df7[df7['P3'] == p3]
            if len(d) < 5: continue
            rows_p3.append({'label': p3, 'n': len(d), 'mean_kep': d['E1A'].mean()})
        df_p3 = pd.DataFrame(rows_p3)
        fig_p3 = go.Figure(go.Bar(
            x=df_p3['label'], y=df_p3['mean_kep'],
            marker_color=[TEAL_MED if v >= df7['E1A'].mean() else GRAY_TEXT for v in df_p3['mean_kep']],
            opacity=0.85,
            text=[f"{v:.3f}" for v in df_p3['mean_kep']], textposition='outside',
            textfont=dict(family='Poppins', size=10, color=NAVY_DARK),
            customdata=df_p3['n'].values,
            hovertemplate='<b>%{x}</b><br>n=%{customdata}<br>Kepuasan: %{y:.3f}<extra></extra>',
        ))
        fig_p3.add_hline(y=df7['E1A'].mean(), line_dash='dash',
                         line_color=GRAY_TEXT, line_width=1.5, opacity=0.6)
        fig_p3.update_layout(
            height=280, margin=dict(t=10,b=10,l=10,r=10),
            paper_bgcolor=WHITE, plot_bgcolor=WHITE,
            xaxis=dict(tickfont=dict(family='Poppins', size=10), tickangle=-20, showgrid=False),
            yaxis=dict(range=[5.75,6.05], tickfont=dict(family='Poppins', size=10), gridcolor=GRAY_BORDER),
            showlegend=False,
        )
        with st.container(border=True):
            st.plotly_chart(fig_p3, use_container_width=True, config={'displayModeBar': False})


# ════════════════════════════════════════════════════════════
# TAB 6 — INTELIJEN KOMPETITOR (sama dengan sebelumnya)
# ════════════════════════════════════════════════════════════
with tab6:
    if len(df_filtered) == 0:
        st.warning("Tidak ada data untuk filter yang dipilih.")
        st.stop()

    competitive_results = load_competitive()
    render_kpi_kompetitor(df_filtered, competitive_results)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    df_bench    = competitive_results['df_benchmark']
    dimensi_xyz = competitive_results['dimensi_xyz']

    st.markdown(f'<p class="section-title">XYZ vs Kompetitor — 6 Dimensi</p>',
                unsafe_allow_html=True)

    col_radar_c, col_gap = st.columns([1, 1])

    with col_radar_c:
        fig_radar_c = go.Figure()
        dimensi_nama = df_bench['dimensi'].tolist()
        xyz_vals  = df_bench['mean_xyz'].tolist()
        komp_vals = df_bench['mean_komp'].tolist()

        for vals, nama, warna_r, fill_op in [
            (xyz_vals,  'Bank XYZ',   '#00C9C9', 0.3),
            (komp_vals, 'Kompetitor', '#FF6B35', 0.2),
        ]:
            vals_c = vals + [vals[0]]
            nama_c = dimensi_nama + [dimensi_nama[0]]
            fig_radar_c.add_trace(go.Scatterpolar(
                r=vals_c, theta=nama_c, fill='toself', name=nama,
                line=dict(color=warna_r, width=2.5),
                fillcolor=warna_r, opacity=fill_op,
            ))

        fig_radar_c.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[4.5,6.2],
                               tickfont=dict(family='Poppins', size=9)),
                angularaxis=dict(tickfont=dict(family='Poppins', size=10)),
            ),
            height=380, margin=dict(t=20,b=20,l=20,r=20),
            paper_bgcolor='white',
            legend=dict(font=dict(family='Poppins', size=11), orientation='h', y=-0.1),
            showlegend=True,
        )
        with st.container(border=True):
            st.plotly_chart(fig_radar_c, use_container_width=True, config={'displayModeBar': False})

    with col_gap:
        fig_gap = go.Figure(go.Bar(
            x=df_bench['gap'], y=df_bench['dimensi'],
            orientation='h',
            marker_color=[SUCCESS if g > 0 else DANGER for g in df_bench['gap']],
            opacity=0.85,
            text=[f"+{g:.3f}" if g > 0 else f"{g:.3f}" for g in df_bench['gap']],
            textposition='outside',
            textfont=dict(family='Poppins', size=11),
            hovertemplate='%{y}<br>Gap: %{x:.3f}<extra></extra>',
        ))
        fig_gap.add_vline(x=0, line_color=GRAY_TEXT, line_width=1.5, opacity=0.5)
        fig_gap.update_layout(
            height=380, title='Gap Kepuasan (XYZ - Kompetitor)',
            margin=dict(t=40,b=20,l=20,r=60),
            paper_bgcolor='white', plot_bgcolor='white',
            xaxis=dict(tickfont=dict(family='Poppins', size=11), gridcolor=GRAY_BORDER),
            yaxis=dict(tickfont=dict(family='Poppins', size=11)),
            title_font=dict(family='Poppins', size=12, color=NAVY_DARK),
        )
        with st.container(border=True):
            st.plotly_chart(fig_gap, use_container_width=True, config={'displayModeBar': False})

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    st.markdown(f'<p class="section-title">Distribusi Bank yang Digunakan Nasabah</p>',
                unsafe_allow_html=True)

    col_pie1, col_pie2, col_pie3 = st.columns(3)
    BANK_COLORS = [TEAL_MED, NAVY_DARK, BLUE_MED, WARNING, DANGER, TEAL_LIGHT]

    def buat_bar_bank(bank_series, multi_sep=None, title='', n_top=6):
        if multi_sep:
            bank_list = []
            for b in bank_series:
                for item in str(b).split(multi_sep):
                    item = item.strip()
                    if item: bank_list.append(item)
            counts = pd.Series(bank_list).value_counts().head(n_top)
        else:
            counts = bank_series.value_counts().head(n_top)
        total = counts.sum()
        pct   = (counts / total * 100).round(1)
        short = (counts.index
                 .str.replace('Bank Rakyat Indonesia','BRI',regex=False)
                 .str.replace('Bank Negara Indonesia','BNI',regex=False)
                 .str.replace('Bank Central Asia','BCA',regex=False)
                 .str.replace('Bank Tabungan Negara','BTN',regex=False)
                 .str.replace(r'\s*\(.*?\)','',regex=True).str.strip())
        fig = go.Figure(go.Bar(
            y=short[::-1], x=counts.values[::-1], orientation='h',
            marker=dict(color=BANK_COLORS[:len(counts)][::-1], line=dict(color='white',width=1)),
            text=[f"{p}%" for p in pct.values[::-1]], textposition='outside',
            textfont=dict(family='Poppins', size=10, color=NAVY_DARK),
            hovertemplate='<b>%{y}</b><br>%{x} nasabah<extra></extra>',
        ))
        fig.update_layout(
            title=dict(text=title, font=dict(family='Poppins',size=12,color=NAVY_DARK), x=0),
            height=280, margin=dict(t=30,b=10,l=10,r=60),
            paper_bgcolor='white', plot_bgcolor='white',
            xaxis=dict(showgrid=True, gridcolor='#E2E6EE', tickfont=dict(family='Poppins',size=9)),
            yaxis=dict(tickfont=dict(family='Poppins',size=10), showgrid=False),
            showlegend=False,
        )
        return fig

    with col_pie1:
        bank_aktif = df_filtered['A1AX'].dropna()
        bank_aktif = bank_aktif[bank_aktif.str.strip() != '']
        with st.container(border=True):
            st.plotly_chart(buat_bar_bank(bank_aktif, multi_sep=';',
                title='Bank Lain yang Aktif Digunakan'), use_container_width=True,
                config={'displayModeBar': False})

    with col_pie2:
        bank_simpan = df_filtered['A1B'].dropna()
        bank_simpan = bank_simpan[bank_simpan.str.strip() != '']
        with st.container(border=True):
            st.plotly_chart(buat_bar_bank(bank_simpan, title='Bank Utama Menyimpan Dana'),
                use_container_width=True, config={'displayModeBar': False})

    with col_pie3:
        bank_trans = df_filtered['A1C'].dropna()
        bank_trans = bank_trans[bank_trans.str.strip() != '']
        with st.container(border=True):
            st.plotly_chart(buat_bar_bank(bank_trans, title='Bank Utama Bertransaksi'),
                use_container_width=True, config={'displayModeBar': False})

    st.markdown(f'<p class="section-title">NPS XYZ vs Kompetitor</p>', unsafe_allow_html=True)

    nps_xyz  = competitive_results.get('nps_xyz', 0)
    nps_komp = competitive_results.get('nps_komp', 0)

    col_nps1, col_nps2, col_nps3 = st.columns(3)
    for col_n, label_n, val_n, warna_n in [
        (col_nps1,'NPS Bank XYZ',   nps_xyz,  SUCCESS),
        (col_nps2,'NPS Kompetitor', nps_komp, GRAY_TEXT),
        (col_nps3,'Gap XYZ - Komp', nps_xyz - nps_komp if nps_komp else 0, TEAL_MED),
    ]:
        with col_n:
            val_str = f"+{val_n:.1f}" if val_n > 0 else f"{val_n:.1f}"
            st.markdown(f"""
            <div style="text-align:center;background:{GRAY_LIGHT};border-radius:12px;padding:20px;
                border-top:4px solid {warna_n};">
                <div style="font-size:0.82rem;color:#6B7280;margin-bottom:8px;">{label_n}</div>
                <div style="font-size:2rem;font-weight:700;color:{warna_n};">{val_str}</div>
            </div>""", unsafe_allow_html=True)
