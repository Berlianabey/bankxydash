TEAL_MED   = "#2CB5D4"
TEAL_DARK  = "#1A8FA8"
TEAL_LIGHT = "#A8E6F0"
NAVY_DARK  = "#002765"
BLUE_MED   = "#3B82F6"
WHITE      = "#FFFFFF"
GRAY_LIGHT = "#F3F4F6"
GRAY_BORDER= "#E5E7EB"
GRAY_TEXT  = "#6B7280"
SUCCESS    = "#10B981"
WARNING    = "#F59E0B"
DANGER     = "#EF4444"

CHART_COLORS = [TEAL_MED, NAVY_DARK, BLUE_MED, WARNING, DANGER, TEAL_LIGHT, "#A855F7", "#F97316"]


def get_full_css():
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {{
    font-family: 'Poppins', sans-serif;
}}

.kpi-card {{
    background: {WHITE};
    border-radius: 14px;
    padding: 18px 20px;
    border: 1.5px solid {GRAY_BORDER};
    box-shadow: 0 2px 10px rgba(0,39,101,0.06);
    margin-bottom: 16px;
}}

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

div[data-testid="stMetricValue"] {{
    font-size: 1.5rem !important;
    font-weight: 700 !important;
    color: {NAVY_DARK} !important;
}}
</style>
"""
