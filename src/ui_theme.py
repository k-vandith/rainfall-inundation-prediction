"""Local, offline visual system for the rainfall workspace."""


def theme_css(
    accent: str = "#2dd4bf",
    danger: str = "#fb7185",
    ok: str = "#34d399",
    warn: str = "#fbbf24",
) -> str:
    return f"""
<style>
:root {{
  --bg:#0b1117;
  --surface:#111b24;
  --surface-raised:#14232d;
  --text:#e7ecf3;
  --muted:#93a4b3;
  --border:#263946;
  --accent:{accent};
  --ok:{ok};
  --warn:{warn};
  --danger:{danger};
}}
html, body, .stApp {{
  background:
    radial-gradient(ellipse at 4% 0%, rgba(45,212,191,.09), transparent 36rem),
    var(--bg);
  color:var(--text);
  font-family:"Segoe UI", ui-sans-serif, system-ui, sans-serif;
}}
[data-testid="stHeader"] {{ background:rgba(11,17,23,.78); }}
[data-testid="stSidebar"] {{
  background:linear-gradient(180deg, #101c25 0%, #0d151d 100%);
  border-right:1px solid var(--border);
}}
[data-testid="stSidebar"] > div {{ padding-top:1.2rem; }}
.block-container {{ padding-top:1.6rem; padding-bottom:2.5rem; max-width:1500px; }}
.kicker {{
  color:var(--accent);
  letter-spacing:.16em;
  text-transform:uppercase;
  font-size:.68rem;
  font-weight:700;
}}
.title {{
  font-size:clamp(1.65rem, 3vw, 2.45rem);
  letter-spacing:-.045em;
  line-height:1.08;
  font-weight:720;
  margin:.35rem 0 .6rem;
}}
.muted {{ color:var(--muted); font-size:.9rem; }}
.top {{
  display:flex; justify-content:space-between; gap:20px;
  align-items:flex-end; margin-bottom:1.4rem;
  padding-bottom:1.25rem; border-bottom:1px solid var(--border);
}}
.pill {{
  border:1px solid rgba(45,212,191,.32);
  background:rgba(45,212,191,.07);
  border-radius:999px; padding:7px 12px;
  color:#a7f3d0; font-size:.68rem; font-weight:700;
  letter-spacing:.08em; white-space:nowrap;
}}
.panel {{
  background:linear-gradient(110deg, rgba(20,35,45,.96), rgba(17,27,36,.94));
  border:1px solid var(--border); border-radius:18px;
  padding:18px 22px; margin-bottom:1rem;
  box-shadow:0 16px 38px rgba(0,0,0,.16);
}}
.risk-panel {{
  display:flex; align-items:center; justify-content:space-between;
  gap:18px; border-left:4px solid var(--accent);
}}
.risk-title {{
  font-size:clamp(2rem, 4vw, 3.1rem); line-height:1;
  letter-spacing:-.04em; font-weight:800; margin:.45rem 0 .4rem;
}}
.risk-mark {{
  display:flex; align-items:center; justify-content:center;
  width:56px; height:56px; flex-shrink:0;
  border:1px solid; border-radius:50%;
  font-size:1.3rem; box-shadow:0 0 30px currentColor;
}}
[data-testid="stMetric"] {{
  background:var(--surface); border:1px solid var(--border);
  border-radius:14px; padding:15px 16px;
}}
[data-testid="stMetricLabel"] {{ color:var(--muted); font-size:.8rem; }}
[data-testid="stMetricValue"] {{ font-weight:750; letter-spacing:-.03em; }}
[data-testid="stMetricDelta"] {{ font-size:.8rem; }}
div[data-testid="stVerticalBlock"] > div:has(> [data-testid="stPlotlyChart"]) {{
  background:rgba(17,27,36,.55);
  border:1px solid var(--border); border-radius:16px;
  padding:8px; margin-bottom:.7rem;
}}
.stButton > button, .stDownloadButton > button {{
  border-radius:10px; border:1px solid var(--border);
  transition:transform .15s ease, border-color .15s ease;
}}
.stButton > button:hover, .stDownloadButton > button:hover {{
  border-color:var(--accent); transform:translateY(-1px);
}}
[data-testid="stFileUploader"] {{
  border:1px dashed #355462; border-radius:12px; padding:8px;
}}
hr {{ border-color:var(--border); }}
small, .stCaption {{ color:var(--muted); }}
@media (max-width: 800px) {{
  .top {{ align-items:flex-start; flex-direction:column; }}
  .pill {{ white-space:normal; }}
  .block-container {{ padding-top:1rem; }}
  .panel {{ padding:15px; }}
}}
</style>
"""


