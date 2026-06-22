import streamlit as st
import pandas as pd
import numpy as np
from theme import (
    WHITE, GRAY_BORDER, GRAY_TEXT, NAVY_DARK,
    TEAL_MED, TEAL_LIGHT, BLUE_MED,
    SUCCESS, WARNING, DANGER,
)


def _card(label: str, value: str, sub: str, color: str, icon: str = ""):
    st.markdown(f"""
    <div style="background:{WHITE};border-radius:16px;padding:18px 20px 16px 20px;
        border:1px solid {GRAY_BORDER};border-top:none;position:relative;overflow:hidden;
        box-shadow:0 1px 3px rgba(0,39,101,0.06),0 4px 14px rgba(0,39,101,0.05);
        margin-bottom:16px;transition:box-shadow .2s;">
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


# ── SCORECARD ────────────────────────────────────────────────
def render_kpi_scorecard(df: pd.DataFrame):
    n = len(df)
    nps_col = "G1A" if "G1A" in df.columns else None

    if nps_col:
        _s = pd.to_numeric(df[nps_col], errors="coerce")
        p = (_s >= 9).sum()
        d = (_s < 7).sum()
        pct_p = p / n * 100 if n > 0 else 0
        pct_d = d / n * 100 if n > 0 else 0
        nps = pct_p - pct_d
    else:
        pct_p = pct_d = nps = 0

    kep = df["E1A"].mean() if "E1A" in df.columns else 0
    loy = df["F1A"].mean() if "F1A" in df.columns else 0
    sf  = int(df["service_failure"].sum()) if "service_failure" in df.columns else 0
    pct_sf = sf / n * 100 if n > 0 else 0

    ces_cols = [c for c in ["T_J1_1", "T_J1_2", "T_J1_4", "T_J1_5"] if c in df.columns]
    ces = df[ces_cols].mean(skipna=True).mean() if ces_cols else np.nan

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: _card("Total Responden",     f"{n:,}",               "nasabah tersurvei",                         TEAL_MED,  "👥")
    with c2: _card("NPS Score",           f"{nps:.1f}",           f"P {pct_p:.1f}% | D {pct_d:.1f}%",         NAVY_DARK, "📊")
    with c3: _card("Kepuasan Overall",    f"{kep:.2f}",           "rata-rata skala 1–6",                       TEAL_MED,  "⭐")
    with c4: _card("Service Failure",     f"{sf:,}",              f"{pct_sf:.1f}% dari total responden",       DANGER,    "⚠️")
    with c5: _card("Customer Effort Score",
                   f"{ces:.2f}" if not np.isnan(ces) else "N/A",
                   "kemudahan layanan cabang (skala 1–6)",         BLUE_MED,  "🎯")


# ── PRIORITAS LAYANAN (CSI) ───────────────────────────────────
def render_kpi_prioritas(df: pd.DataFrame, hasil_ipa: dict):
    n = len(df)

    total_prioritas = sum(
        len(v[v["kuadran"] == "Prioritas Utama"]) for v in hasil_ipa.values()
    )

    gap_per_dim = {
        d: v[v["kuadran"] == "Prioritas Utama"]["gap"].mean()
        for d, v in hasil_ipa.items()
        if len(v[v["kuadran"] == "Prioritas Utama"]) > 0
    }
    dim_kritis = max(gap_per_dim, key=gap_per_dim.get) if gap_per_dim else "-"

    all_gaps = [
        g for v in hasil_ipa.values()
        for g in v[v["kuadran"] == "Prioritas Utama"]["gap"].tolist()
    ]
    gap_max = max(all_gaps) if all_gaps else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1: _card("Total Responden",         f"{n:,}",             "dalam filter terpilih",                  TEAL_MED,  "👥")
    with c2: _card("Atribut Prioritas Utama", f"{total_prioritas}", "atribut perlu perbaikan segera",         DANGER,    "🎯")
    with c3: _card("Dimensi Terkritis",       dim_kritis,           f"gap {gap_per_dim.get(dim_kritis,0):.3f}", WARNING, "⚡")
    with c4: _card("Gap Terbesar",            f"{gap_max:.3f}",     "selisih kepentingan vs kepuasan",        DANGER,    "📉")


# ── PROFIL CABANG ─────────────────────────────────────────────
def render_kpi_cabang(df: pd.DataFrame):
    n_cabang = df["CABANG"].nunique() if "CABANG" in df.columns else 0

    rata_map = {
        "rata_fisik": "Fisik", "rata_brand": "Brand",
        "rata_teller": "Teller", "rata_cs": "CS",
        "rata_atm": "ATM", "rata_sekuriti": "Sekuriti",
    }
    avail = {v: df[k].mean(skipna=True) for k, v in rata_map.items() if k in df.columns}
    if avail:
        best_dim  = max(avail, key=avail.get)
        worst_dim = min(avail, key=avail.get)
    else:
        best_dim = worst_dim = "-"

    n = len(df)
    sf = int(df["service_failure"].sum()) if "service_failure" in df.columns else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1: _card("Jumlah Cabang",     f"{n_cabang}",   "cabang aktif",                        TEAL_MED,  "🏦")
    with c2: _card("Total Responden",   f"{n:,}",        "dalam filter terpilih",               NAVY_DARK, "👥")
    with c3: _card("Dimensi Terbaik",   best_dim,        f"rata-rata {avail.get(best_dim,0):.2f}", SUCCESS, "🏆")
    with c4: _card("Dimensi Terlemah",  worst_dim,       f"rata-rata {avail.get(worst_dim,0):.2f}", DANGER, "⚠️")


# ── PETA EMOSI ────────────────────────────────────────────────
def render_kpi_emosi(df: pd.DataFrame, emotion_results: dict):
    n = len(df)
    df_emosi = emotion_results.get("df_emosi", pd.DataFrame())

    if len(df_emosi) > 0:
        pos = df_emosi[df_emosi["kategori"] == "positif"]["mean_xyz"].mean()
        neg = df_emosi[df_emosi["kategori"] == "negatif"]["mean_xyz"].mean()
        top_emosi = df_emosi[df_emosi["kategori"] == "positif"].nlargest(1, "mean_xyz")
        top_label = top_emosi["emosi"].iloc[0] if len(top_emosi) > 0 else "-"
        top_val   = top_emosi["mean_xyz"].iloc[0] if len(top_emosi) > 0 else 0
    else:
        pos = neg = top_val = 0
        top_label = "-"

    c1, c2, c3, c4 = st.columns(4)
    with c1: _card("Total Responden",     f"{n:,}",          "nasabah tersurvei",             TEAL_MED,  "👥")
    with c2: _card("Rata Emosi Positif",  f"{pos:.2f}",      "skala 1–6",                     SUCCESS,   "😊")
    with c3: _card("Rata Emosi Negatif",  f"{neg:.2f}",      "skala 1–6 (lebih rendah=baik)", DANGER,    "😟")
    with c4: _card("Emosi Terkuat",       top_label,         f"skor {top_val:.2f}",           TEAL_MED,  "💡")


# ── SEGMENTASI LOYALITAS ──────────────────────────────────────
def render_kpi_segmentasi(df: pd.DataFrame):
    n = len(df)
    seg_col = "loyalty_segment_display" if "loyalty_segment_display" in df.columns else "loyalty_segment"

    loyal    = (df[seg_col] == "Loyal Aman").sum()  if seg_col in df.columns else 0
    latent   = (df[seg_col] == "Latent Risk").sum() if seg_col in df.columns else 0
    at_risk  = (df[seg_col] == "At Risk").sum()     if seg_col in df.columns else 0

    pct_loyal   = loyal   / n * 100 if n > 0 else 0
    pct_at_risk = at_risk / n * 100 if n > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1: _card("Total Responden",  f"{n:,}",          "dalam filter terpilih",       TEAL_MED,  "👥")
    with c2: _card("Loyal Aman",       f"{loyal:,}",      f"{pct_loyal:.1f}% nasabah",  SUCCESS,   "💚")
    with c3: _card("Latent Risk",      f"{latent:,}",     "perlu perhatian",             WARNING,   "⚡")
    with c4: _card("At Risk",          f"{at_risk:,}",    f"{pct_at_risk:.1f}% nasabah", DANGER,   "🔴")


# ── INTELIJEN KOMPETITOR ──────────────────────────────────────
def render_kpi_kompetitor(df: pd.DataFrame, competitive_results: dict):
    n = len(df)
    nps_xyz  = competitive_results.get("nps_xyz",  0)
    nps_komp = competitive_results.get("nps_komp", 0)
    gap_nps  = nps_xyz - nps_komp

    df_bench = competitive_results.get("df_benchmark", pd.DataFrame())
    if len(df_bench) > 0:
        best_gap  = df_bench.loc[df_bench["gap"].idxmax(), "dimensi"]
        worst_gap = df_bench.loc[df_bench["gap"].idxmin(), "dimensi"]
    else:
        best_gap = worst_gap = "-"

    c1, c2, c3, c4 = st.columns(4)
    with c1: _card("Total Responden",   f"{n:,}",              "nasabah tersurvei",           TEAL_MED,  "👥")
    with c2: _card("NPS XYZ vs Komp",  f"{gap_nps:+.1f}",     f"XYZ {nps_xyz:.1f} | Komp {nps_komp:.1f}", TEAL_MED, "📊")
    with c3: _card("Unggul di",         best_gap,              "dimensi terbaik vs kompetitor", SUCCESS,  "🏆")
    with c4: _card("Tertinggal di",     worst_gap,             "dimensi perlu kejar",         DANGER,    "⚠️")
