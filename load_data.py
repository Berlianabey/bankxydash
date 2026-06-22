import os
import pickle
import pandas as pd
import numpy as np
import streamlit as st

# Semua file ada di folder yang sama (flat structure)
BASE = os.path.dirname(os.path.abspath(__file__))


def _get_data_path(filename):
    """Cari file di root repo (flat structure)."""
    return os.path.join(BASE, filename)


def _get_raw_path(filename):
    """Cari file dataset mentah (xlsx) di root repo (flat structure)."""
    return os.path.join(BASE, filename)


# ── MAIN DATA ────────────────────────────────────────────────
@st.cache_data
def load_main_data() -> pd.DataFrame:
    # Coba data_final.pkl dulu, fallback ke data_clean.pkl, lalu csv
    for fname in ["data_final.pkl", "data_clean.pkl"]:
        path = _get_data_path(fname)
        if os.path.exists(path):
            with open(path, "rb") as f:
                df = pickle.load(f)
            break
    else:
        path = _get_data_path("data_clean.csv")
        df = pd.read_csv(path)

    # ── Derived columns ───────────────────────────────────────
    if "NPS_category" not in df.columns and "G1A" in df.columns:
        g1a_num = pd.to_numeric(df["G1A"], errors="coerce")
        df["NPS_category"] = pd.cut(
            g1a_num, bins=[-1, 6, 8, 10],
            labels=["Detractor", "Passive", "Promoter"],
        )

    if "loyalty_segment" not in df.columns:
        df = _add_loyalty_segment(df)

    if "loyalty_segment_display" not in df.columns:
        df["loyalty_segment_display"] = df["loyalty_segment"].replace(
            {"Hidden Gem": "At Risk", "Lost Cause": "At Risk"}
        )

    if "service_failure" not in df.columns:
        _t = df.get("failure_teller", pd.Series(False, index=df.index))
        _c = df.get("failure_cs",     pd.Series(False, index=df.index))
        df["service_failure"] = _t | _c

    # rata-rata dimensi
    _rata_map = {
        "rata_teller":   [c for c in df.columns if c.startswith("T_TL3_") and int(c.split("_")[-1]) % 3 == 2],
        "rata_cs":       [c for c in df.columns if c.startswith("T_CS3_") and int(c.split("_")[-1]) % 3 == 2],
        "rata_atm":      [c for c in df.columns if c.startswith("T_AT3_") and int(c.split("_")[-1]) % 3 == 2],
        "rata_fisik":    [c for c in df.columns if c.startswith("T_KC2_") and int(c.split("_")[-1]) % 3 == 2],
        "rata_sekuriti": [c for c in df.columns if c.startswith("T_SC2_") and int(c.split("_")[-1]) % 3 == 2],
        "rata_brand":    [c for c in df.columns if c.startswith("T_C1B_") and int(c.split("_")[-1]) % 3 == 2],
    }
    for col_name, src_cols in _rata_map.items():
        if col_name not in df.columns and src_cols:
            df[col_name] = df[src_cols].mean(axis=1, skipna=True)

    return df


def _add_loyalty_segment(df: pd.DataFrame) -> pd.DataFrame:
    e1a = pd.to_numeric(df["E1A"], errors="coerce") if "E1A" in df.columns else pd.Series(np.nan, index=df.index)
    g1a = pd.to_numeric(df["G1A"], errors="coerce") if "G1A" in df.columns else pd.Series(np.nan, index=df.index)
    high_sat = e1a >= 5
    high_nps = g1a >= 9
    conditions = [high_sat & high_nps, high_sat & ~high_nps,
                  ~high_sat & high_nps, ~high_sat & ~high_nps]
    choices = ["Loyal Aman", "Latent Risk", "Hidden Gem", "Lost Cause"]
    df["loyalty_segment"] = np.select(conditions, choices, default="Latent Risk")
    return df


# ── IPA ──────────────────────────────────────────────────────
@st.cache_data
def load_ipa() -> dict:
    path = _get_data_path("hasil_ipa.pkl")
    if os.path.exists(path):
        with open(path, "rb") as f:
            return pickle.load(f)
    return _compute_ipa()


def _compute_ipa() -> dict:
    df = load_main_data()

    try:
        df_raw = pd.read_excel(_get_raw_path("Deka_project_dataset_BankXYZ.xlsx"), header=0)
        kode_var  = df_raw.iloc[0]
        label_map = {str(v).strip(): str(k).strip()
                     for k, v in kode_var.items() if pd.notna(v)}
    except Exception:
        label_map = {}

    dimensi_cfg = {
        "Fisik":    ("T_KC1_", "T_KC2_"),
        "Brand":    ("T_C1A_", "T_C1B_"),
        "Teller":   ("T_TL2_", "T_TL3_"),
        "CS":       ("T_CS2_", "T_CS3_"),
        "ATM":      ("T_AT2_", "T_AT3_"),
        "Sekuriti": ("T_SC1_", "T_SC2_"),
    }

    hasil = {}
    for nama, (pref_k, pref_p) in dimensi_cfg.items():
        cols_k = sorted([c for c in df.columns if c.startswith(pref_k)],
                        key=lambda x: int(x.split("_")[-1]))
        cols_p = sorted([c for c in df.columns if c.startswith(pref_p)
                         and int(c.split("_")[-1]) % 3 == 2],
                        key=lambda x: int(x.split("_")[-1]))

        df_f = df[df["PANEL"] == "Teller (KUOTA 50%)"] if nama == "Teller" else \
               df[df["PANEL"] == "CS (KUOTA 50%)"]     if nama == "CS"     else df

        rows = []
        for i in range(min(len(cols_k), len(cols_p))):
            mk = df_f[cols_k[i]].mean(skipna=True)
            mp = df_f[cols_p[i]].mean(skipna=True)
            if pd.isna(mk) or pd.isna(mp):
                continue
            rows.append({
                "label": label_map.get(cols_k[i], cols_k[i]),
                "kolom_k": cols_k[i], "kolom_p": cols_p[i],
                "mean_kepentingan": mk, "mean_kepuasan": mp, "gap": mk - mp,
            })

        if not rows:
            continue

        ipa_df = pd.DataFrame(rows)
        mean_k = ipa_df["mean_kepentingan"].mean()
        mean_p = ipa_df["mean_kepuasan"].mean()

        def _q(row):
            if   row["mean_kepentingan"] >= mean_k and row["mean_kepuasan"] <  mean_p: return "Prioritas Utama"
            elif row["mean_kepentingan"] >= mean_k and row["mean_kepuasan"] >= mean_p: return "Pertahankan"
            elif row["mean_kepentingan"] <  mean_k and row["mean_kepuasan"] <  mean_p: return "Prioritas Rendah"
            else:                                                                        return "Berlebihan"

        ipa_df["kuadran"] = ipa_df.apply(_q, axis=1)
        hasil[nama] = ipa_df

    return hasil


# ── EMOTION ──────────────────────────────────────────────────
@st.cache_data
def load_emotion() -> dict:
    path = _get_data_path("emotion_results.pkl")
    if os.path.exists(path):
        with open(path, "rb") as f:
            return pickle.load(f)
    return _compute_emotion()


def _compute_emotion() -> dict:
    df = load_main_data()

    emosi_cols_xyz  = sorted([c for c in df.columns if c.startswith("T_H1A_")
                               and int(c.split("_")[-1]) % 3 == 2],
                              key=lambda x: int(x.split("_")[-1]))
    emosi_cols_komp = sorted([c for c in df.columns if c.startswith("T_H1A_")
                               and int(c.split("_")[-1]) % 3 == 0],
                              key=lambda x: int(x.split("_")[-1]))

    emosi_labels = [
        "Senang","Puas","Nyaman","Percaya","Bangga","Kagum",
        "Kecewa","Tidak Puas","Frustrasi","Tidak Percaya","Malu","Marah",
        "Khawatir","Bingung","Lelah",
    ]

    rows_emosi = []
    for i, (c_xyz, c_komp) in enumerate(zip(emosi_cols_xyz[:len(emosi_labels)],
                                             emosi_cols_komp[:len(emosi_labels)])):
        rows_emosi.append({
            "emosi": emosi_labels[i],
            "mean_xyz":  df[c_xyz].mean(skipna=True),
            "mean_komp": df[c_komp].mean(skipna=True),
            "kategori":  "positif" if i < 6 else "negatif",
        })
    df_emosi = pd.DataFrame(rows_emosi)

    rows_korr = []
    for i, c_xyz in enumerate(emosi_cols_xyz[:len(emosi_labels)]):
        if "G1A" in df.columns:
            valid = df[[c_xyz, "G1A"]].dropna()
            if len(valid) > 10:
                rows_korr.append({"emosi": emosi_labels[i],
                                   "korelasi": valid[c_xyz].corr(valid["G1A"])})
    df_korelasi = pd.DataFrame(rows_korr)

    rows_profil = []
    for i, c_xyz in enumerate(emosi_cols_xyz[:len(emosi_labels)]):
        row = {"emosi": emosi_labels[i], "kategori": "positif" if i < 6 else "negatif"}
        if "NPS_category" in df.columns:
            row["promoter"]  = df[df["NPS_category"] == "Promoter"][c_xyz].mean(skipna=True)
            row["passive"]   = df[df["NPS_category"] == "Passive"][c_xyz].mean(skipna=True)
            row["detractor"] = df[df["NPS_category"] == "Detractor"][c_xyz].mean(skipna=True)
        rows_profil.append(row)
    df_profil_segmen = pd.DataFrame(rows_profil)

    return {
        "df_emosi": df_emosi,
        "df_korelasi": df_korelasi,
        "df_profil_segmen": df_profil_segmen,
        "nama_emosi": emosi_labels,
        "emosi_xyz": {r["emosi"]: r["mean_xyz"] for r in rows_emosi},
    }


# ── COMPETITIVE ───────────────────────────────────────────────
@st.cache_data
def load_competitive() -> dict:
    path = _get_data_path("competitive_results.pkl")
    if os.path.exists(path):
        with open(path, "rb") as f:
            return pickle.load(f)
    return _compute_competitive()


def _compute_competitive() -> dict:
    df = load_main_data()

    rata_map = {
        "Fisik":    ("rata_fisik",    [c for c in df.columns if c.startswith("T_KC2_") and int(c.split("_")[-1]) % 3 == 0]),
        "Brand":    ("rata_brand",    [c for c in df.columns if c.startswith("T_C1B_") and int(c.split("_")[-1]) % 3 == 0]),
        "Teller":   ("rata_teller",   [c for c in df.columns if c.startswith("T_TL3_") and int(c.split("_")[-1]) % 3 == 0]),
        "CS":       ("rata_cs",       [c for c in df.columns if c.startswith("T_CS3_") and int(c.split("_")[-1]) % 3 == 0]),
        "ATM":      ("rata_atm",      [c for c in df.columns if c.startswith("T_AT3_") and int(c.split("_")[-1]) % 3 == 0]),
        "Sekuriti": ("rata_sekuriti", [c for c in df.columns if c.startswith("T_SC2_") and int(c.split("_")[-1]) % 3 == 0]),
    }

    rows = []
    dimensi_xyz = {}
    dimensi_komp = {}
    for nama, (col_xyz, cols_komp) in rata_map.items():
        mean_xyz  = df[col_xyz].mean(skipna=True) if col_xyz in df.columns else np.nan
        mean_komp = df[cols_komp].mean(skipna=True).mean() if cols_komp else np.nan
        rows.append({"dimensi": nama, "mean_xyz": mean_xyz,
                     "mean_komp": mean_komp, "gap": mean_xyz - mean_komp})
        dimensi_xyz[nama]  = mean_xyz
        dimensi_komp[nama] = mean_komp

    nps_xyz = nps_komp = 0
    def _nps(s):
        s = pd.to_numeric(s, errors="coerce").dropna()
        if len(s) == 0: return 0
        return float((s >= 9).mean() * 100 - (s < 7).mean() * 100)
    if "G1A" in df.columns:
        nps_xyz  = _nps(df["G1A"])
        nps_komp = _nps(df["G1C"]) if "G1C" in df.columns else 0

    return {
        "df_benchmark": pd.DataFrame(rows),
        "dimensi_xyz":  dimensi_xyz,
        "dimensi_komp": dimensi_komp,
        "nps_xyz":  nps_xyz,
        "nps_komp": nps_komp,
    }


# ── SEGMENTS ─────────────────────────────────────────────────
@st.cache_data
def load_segments() -> dict:
    df = load_main_data()
    seg = df["loyalty_segment_display"].value_counts().to_dict() \
        if "loyalty_segment_display" in df.columns else {}
    return {"counts": seg}
