import streamlit as st
import pandas as pd
from theme import WHITE, GRAY_BORDER, NAVY_DARK

# Mapping label tampilan → nilai asli di data
PANEL_LABEL_MAP = {
    "CS":     "CS (KUOTA 50%)",
    "Teller": "Teller (KUOTA 50%)",
}
PANEL_DISPLAY = {v: k for k, v in PANEL_LABEL_MAP.items()}  # reverse


def render_filters(df: pd.DataFrame) -> pd.DataFrame:
    with st.sidebar:
        st.markdown(f"""
        <div style="padding: 16px 0 8px 0;display:flex;align-items:center;gap:10px;">
            <div style="width:34px;height:34px;min-width:34px;border-radius:10px;
                background:rgba(255,255,255,0.16);display:flex;align-items:center;
                justify-content:center;font-size:1.1rem;">🏦</div>
            <div>
                <div style="font-size:1rem;font-weight:700;color:{WHITE};
                    font-family:Poppins,sans-serif;margin-bottom:2px;line-height:1.1;">
                    Bank XYZ
                </div>
                <div style="font-size:0.72rem;color:rgba(255,255,255,0.65);line-height:1.1;">
                    Customer Experience Dashboard
                </div>
            </div>
        </div>
        <hr style="border:none;border-top:1px solid rgba(255,255,255,0.2);margin:8px 0 16px 0;">
        """, unsafe_allow_html=True)

        st.markdown('<p style="color:rgba(255,255,255,0.8);font-size:0.8rem;font-weight:600;margin-bottom:8px;">🔍 FILTER DATA</p>',
                    unsafe_allow_html=True)

        # ── Provinsi ─────────────────────────────────────────
        prov_options = ["Semua"] + sorted(df["PROV"].dropna().unique().tolist())
        prov_sel = st.selectbox("Provinsi", prov_options, key="filter_prov")

        # ── Cabang ───────────────────────────────────────────
        df_prov = df if prov_sel == "Semua" else df[df["PROV"] == prov_sel]
        cab_options = ["Semua"] + sorted(df_prov["CABANG"].dropna().unique().tolist())
        cab_sel = st.selectbox("Cabang", cab_options, key="filter_cab")

        # ── Touchpoint — tampilkan label bersih ──────────────
        if "PANEL" in df.columns:
            raw_panels = df["PANEL"].dropna().unique().tolist()
            # Buat label bersih (hapus " (KUOTA 50%)" dll)
            clean_labels = []
            raw_to_clean = {}
            clean_to_raw = {}
            for raw in sorted(raw_panels):
                clean = raw.replace(" (KUOTA 50%)", "").strip()
                clean_labels.append(clean)
                raw_to_clean[raw]   = clean
                clean_to_raw[clean] = raw

            panel_display_options = ["Semua"] + clean_labels
            panel_clean_sel = st.selectbox("Touchpoint", panel_display_options, key="filter_panel")
            panel_raw_sel   = clean_to_raw.get(panel_clean_sel, None)
        else:
            panel_clean_sel = "Semua"
            panel_raw_sel   = None

        # ── Lama Nasabah ─────────────────────────────────────
        lama_order = [
            "1 bulan s/d 3 bulan", "3 bulan s/d 11 bulan",
            "1 tahun s/d 2 tahun 11 bulan",
            "3 tahun s/d 4 tahun 11 bulan", "5 tahun atau lebih",
        ]
        if "S4" in df.columns:
            lama_options = ["Semua"] + [l for l in lama_order if l in df["S4"].values]
        else:
            lama_options = ["Semua"]
        lama_sel = st.selectbox("Lama Nasabah", lama_options, key="filter_lama")

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        st.markdown('<p style="color:rgba(255,255,255,0.5);font-size:0.7rem;text-align:center;">v2.0 · Revised 2026</p>',
                    unsafe_allow_html=True)

    # ── Apply filters ────────────────────────────────────────
    df_out = df.copy()
    if prov_sel != "Semua":
        df_out = df_out[df_out["PROV"] == prov_sel]
    if cab_sel != "Semua":
        df_out = df_out[df_out["CABANG"] == cab_sel]
    if panel_clean_sel != "Semua" and panel_raw_sel and "PANEL" in df_out.columns:
        df_out = df_out[df_out["PANEL"] == panel_raw_sel]
    if lama_sel != "Semua" and "S4" in df_out.columns:
        df_out = df_out[df_out["S4"] == lama_sel]

    return df_out
