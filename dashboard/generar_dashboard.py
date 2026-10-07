"""
dashboard/generar_dashboard.py

Genera docs/index.html, un dashboard autocontenido con Plotly, a partir de
data/denue.db. Incluye KPIs, graficas interactivas con explicacion de cada
una y su hallazgo, mapa coropletico de Campeche, tabla de municipios y
boton de descarga de CSVs.

Uso:
    python dashboard/generar_dashboard.py
"""

import importlib.util
import json
import sqlite3
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

# ============================================================
# Configuracion
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "denue.db"
GEOJSON_PATH = BASE_DIR / "dashboard" / "campeche_municipios.geojson"
OUT_PATH = BASE_DIR / "docs" / "index.html"

AZUL = "#1f77b4"
NARANJA = "#ff7f0e"
VERDE = "#2ca02c"
ROJO = "#d62728"
GRIS = "#7f7f7f"
AZUL_OSCURO = "#14395e"
AMBAR = "#b45309"

MUNICIPIOS = {
    "001": "Calkiní", "002": "Campeche", "003": "Carmen", "004": "Champotón",
    "005": "Hecelchakán", "006": "Hopelchén", "007": "Palizada", "008": "Tenabo",
    "009": "Escárcega", "010": "Calakmul", "011": "Candelaria",
    "012": "Seybaplaya", "013": "Dzitbalché",
}

ORDEN_TAM = [
    "0 a 5 personas", "6 a 10 personas", "11 a 30 personas",
    "31 a 50 personas", "51 a 100 personas", "101 a 250 personas",
    "251 y más personas",
]

NIVELES = ["nucleo", "ampliado", "excluido", "resto"]

NIVELES_ETIQUETAS = {
    "nucleo": "Núcleo", "ampliado": "Ampliado",
    "excluido": "Excluido", "resto": "Resto",
}


# ============================================================
# Datos
# ============================================================
def cargar_etl():
    ruta = BASE_DIR / "etl" / "02_matching_demografia.py"
    spec = importlib.util.spec_from_file_location("etl_matching", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def cargar_datos():
    if not DB_PATH.exists():
        mod = cargar_etl()
        mod.main()
    con = sqlite3.connect(DB_PATH)
    df23 = pd.read_sql("SELECT * FROM denue_2023", con)
    df24 = pd.read_sql("SELECT * FROM denue_2024", con)
    sobre = pd.read_sql("SELECT * FROM sobrevivientes", con)
    nac = pd.read_sql("SELECT * FROM nacimientos", con)
    mue = pd.read_sql("SELECT * FROM muertes", con)
    con.close()
    return df23, df24, sobre, nac, mue


def resumen_municipio(df23, df24, sobre, nac, mue):
    u23 = df23.groupby("cve_mun").size()
    u24 = df24.groupby("cve_mun").size()
    s = sobre.groupby("cve_mun").size()
    n = nac.groupby("cve_mun").size()
    m = mue.groupby("cve_mun").size()
    r = pd.DataFrame({
        "U23": u23, "U24": u24, "Sobrevivientes": s,
        "Nacimientos": n, "Muertes": m,
    }).fillna(0).astype(int)
    r["tasa_supervivencia"] = (r["Sobrevivientes"] / r["U23"] * 100).round(1)
    r["tasa_natalidad"] = (r["Nacimientos"] / r["U24"] * 100).round(1)
    r["tasa_mortalidad"] = (r["Muertes"] / r["U23"] * 100).round(1)
    r["crecimiento_neto"] = ((r["U24"] - r["U23"]) / r["U23"] * 100).round(1)
    r["municipio"] = [MUNICIPIOS.get(c, c) for c in r.index]
    r["cvegeo"] = ["04" + c for c in r.index]
    return r


# ============================================================
# Graficas
# ============================================================
def fig_tasas(res):
    d = res.sort_values("crecimiento_neto")
    fig = go.Figure()
    fig.add_trace(go.Bar(y=d["municipio"], x=d["tasa_natalidad"], name="Natalidad",
                         orientation="h", marker_color=AZUL))
    fig.add_trace(go.Bar(y=d["municipio"], x=d["tasa_mortalidad"], name="Mortalidad",
                         orientation="h", marker_color=NARANJA))
    fig.update_layout(barmode="group", height=620, margin=dict(l=10, r=10, t=30, b=40),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0))
    fig.update_xaxes(title="%")
    return fig


def fig_tamano(df23, df24):
    def dist(df):
        cat = pd.Categorical(df["per_ocu"], categories=ORDEN_TAM, ordered=True)
        return pd.Series(cat).value_counts().sort_index()

    d = pd.DataFrame({"2023": dist(df23), "2024": dist(df24)})
    fig = go.Figure()
    fig.add_trace(go.Bar(x=d.index, y=d["2023"], name="2023", marker_color=AZUL))
    fig.add_trace(go.Bar(x=d.index, y=d["2024"], name="2024", marker_color=NARANJA))
    fig.update_layout(barmode="group", height=420, margin=dict(l=10, r=10, t=30, b=40),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0))
    fig.update_xaxes(tickangle=30)
    return fig


def fig_sector(sobre, nac, mue):
    def conteo(df, col="sector_servicios"):
        return df[col].value_counts().reindex(NIVELES).fillna(0).astype(int)

    d = pd.DataFrame({
        "Sobrevivientes": conteo(sobre),
        "Nacimientos": conteo(nac),
        "Muertes": conteo(mue),
    })
    etiquetas = {"nucleo": "Núcleo", "ampliado": "Ampliado", "excluido": "Excluido", "resto": "Resto"}
    x = [etiquetas[n] for n in d.index]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=x, y=d["Sobrevivientes"], name="Sobrevivientes", marker_color=VERDE))
    fig.add_trace(go.Bar(x=x, y=d["Nacimientos"], name="Nacimientos", marker_color=AZUL))
    fig.add_trace(go.Bar(x=x, y=d["Muertes"], name="Muertes", marker_color=ROJO))
    fig.update_layout(barmode="group", height=420, margin=dict(l=10, r=10, t=30, b=40),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0))
    return fig


def fig_indice(nac, mue):
    n_total = len(nac)
    m_total = len(mue)
    indices = {}
    for g in ["A", "B", "C"]:
        ng = int(((nac["sector_servicios"] == "nucleo") & (nac["grupo_tren"] == g)).sum())
        mg = int(((mue["sector_servicios"] == "nucleo") & (mue["grupo_tren"] == g)).sum())
        indices[g] = round((ng / n_total) - (mg / m_total), 4)
    s = pd.Series(indices)
    colores = [VERDE if v >= 0 else ROJO for v in s.values]
    fig = go.Figure(go.Bar(x=s.index, y=s.values, marker_color=colores,
                            text=[f"{v:+.4f}" for v in s.values], textposition="outside"))
    fig.update_layout(height=420, margin=dict(l=10, r=10, t=30, b=40),
                      yaxis_title="(N_núcleo / N_total) - (M_núcleo / M_total)")
    fig.add_hline(y=0, line_dash="dash", line_color=GRIS)
    return fig, s


def fig_top5(res):
    d = res.sort_values("crecimiento_neto", ascending=False).head(5)
    fig = go.Figure(go.Bar(x=d["municipio"], y=d["crecimiento_neto"],
                           marker_color=VERDE,
                           text=[f"{v:+.1f}%" for v in d["crecimiento_neto"]],
                           textposition="outside"))
    fig.update_layout(height=420, margin=dict(l=10, r=10, t=30, b=40), yaxis_title="%")
    return fig


def fig_donut_nucleo(sobre):
    subs = {
        "7211": "Alojamiento",
        "7225": "Alimentos y bebidas",
        "5615": "Agencias de viajes",
    }
    d = sobre[sobre["sector_servicios"] == "nucleo"].copy()
    d["sub"] = d["scian4"].map(subs)
    conteo = d["sub"].value_counts()
    total = int(conteo.sum())
    fig = go.Figure(go.Pie(labels=conteo.index, values=conteo.values, hole=0.55,
                           marker=dict(colors=["#4e79a7", "#f28e2b", "#76b7b2"]),
                           textinfo="percent", textposition="inside",
                           textfont=dict(size=15)))
    fig.add_annotation(x=0.5, y=0.5, showarrow=False,
                       text=f"<b>{total:,}</b><br><span style='font-size:12px;color:#52606d'>sobrevivientes</span>",
                       font=dict(size=20))
    fig.update_layout(height=460, margin=dict(l=10, r=10, t=30, b=10),
                      legend=dict(orientation="h", yanchor="bottom", y=-0.15))
    return fig


def fig_donut_supervivencia(s_total, m_total):
    fig = go.Figure(go.Pie(labels=["Sobrevivieron", "Murieron"],
                           values=[s_total, m_total], hole=0.5,
                           marker=dict(colors=[VERDE, ROJO]),
                           textinfo="label+percent", textfont=dict(size=14)))
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=40, b=10),
                      legend=dict(orientation="h"),
                      title="Destino de los negocios de 2023")
    return fig


def fig_mapa(res, geojson):
    fig = go.Figure(go.Choropleth(
        geojson=geojson,
        locations=res["cvegeo"],
        z=res["crecimiento_neto"],
        featureidkey="properties.cvegeo",
        colorscale="RdYlGn",
        zmid=0,
        marker_line_width=0.7,
        marker_line_color="white",
        colorbar=dict(title="Crec. neto (%)"),
        text=res["municipio"],
        hovertemplate="%{text}: %{z:.1f}%<extra></extra>",
    ))
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(height=560, margin=dict(l=0, r=0, t=30, b=0))
    return fig


# ============================================================
# HTML
# ============================================================
def kpi(titulo, valor, color, sub=""):
    return (
        f'<div class="kpi" style="border-top:4px solid {color};">'
        f'<div class="kpi-titulo">{titulo}</div>'
        f'<div class="kpi-valor" style="color:{color};">{valor}</div>'
        f'<div class="kpi-sub">{sub}</div></div>'
    )


def seccion(numero, titulo, que_es, hallazgo, fig_html):
    return f"""
<section class="tarjeta">
  <div class="sec-cab">
    <span class="sec-num">{numero}</span>
    <h2>{titulo}</h2>
  </div>
  <div class="que-es"><strong>Qué muestra:</strong> {que_es}</div>
  <div class="hallazgo"><strong>Hallazgo:</strong> {hallazgo}</div>
  <div class="figura">{fig_html}</div>
</section>"""


def tabla_niveles(df23, df24, sobre, nac, mue):
    u23 = df23.groupby("sector_servicios").size()
    u24 = df24.groupby("sector_servicios").size()
    s = sobre.groupby("sector_servicios").size()
    n = nac.groupby("sector_servicios").size()
    m = mue.groupby("sector_servicios").size()
    r = pd.DataFrame({"U23": u23, "U24": u24, "Sobrevivientes": s,
                      "Nacimientos": n, "Muertes": m}).reindex(NIVELES).fillna(0).astype(int)
    r["crecimiento"] = ((r["U24"] - r["U23"]) / r["U23"] * 100).round(1)
    filas = ""
    for nivel in NIVELES:
        row = r.loc[nivel]
        color = VERDE if row["crecimiento"] >= 0 else ROJO
        filas += (
            f'<tr><td><b>{NIVELES_ETIQUETAS[nivel]}</b></td>'
            f'<td class="num">{row["U23"]:,}</td><td class="num">{row["U24"]:,}</td>'
            f'<td class="num">{row["Sobrevivientes"]:,}</td><td class="num">{row["Nacimientos"]:,}</td>'
            f'<td class="num">{row["Muertes"]:,}</td>'
            f'<td class="num" style="color:{color};font-weight:600;">{row["crecimiento"]:+.1f}%</td></tr>'
        )
    return (
        '<table class="tabla"><thead><tr>'
        '<th>Nivel</th><th>Unidades 2023</th><th>Unidades 2024</th><th>Sobrevivientes</th><th>Nacimientos</th>'
        '<th>Muertes</th><th>Crec. neto</th>'
        '</tr></thead><tbody>' + filas + '</tbody></table>'
    )


def tabla_html(res):
    filas = ""
    for _, r in res.sort_values("crecimiento_neto", ascending=False).iterrows():
        color = VERDE if r["crecimiento_neto"] >= 0 else ROJO
        filas += (
            f'<tr><td>{r["municipio"]}</td>'
            f'<td class="num">{r["U23"]:,}</td><td class="num">{r["U24"]:,}</td>'
            f'<td class="num">{r["Nacimientos"]:,}</td><td class="num">{r["Muertes"]:,}</td>'
            f'<td class="num">{r["tasa_supervivencia"]:.1f}%</td>'
            f'<td class="num">{r["tasa_natalidad"]:.1f}%</td>'
            f'<td class="num">{r["tasa_mortalidad"]:.1f}%</td>'
            f'<td class="num" style="color:{color};font-weight:600;">{r["crecimiento_neto"]:+.1f}%</td></tr>'
        )
    return (
        '<table class="tabla"><thead><tr>'
        '<th>Municipio</th><th>Unidades 2023</th><th>Unidades 2024</th><th>Nacim.</th><th>Muertes</th>'
        '<th>Superv.</th><th>Natal.</th><th>Mortal.</th><th>Crec. neto</th>'
        '</tr></thead><tbody>' + filas + '</tbody></table>'
    )


def construir_html(figs_html, res, df23, df24, sobre, nac, mue, idx_global, idx_grupo):
    total_23 = int(res["U23"].sum())
    total_24 = int(res["U24"].sum())
    n_total = len(nac)
    m_total = len(mue)
    s_total = len(sobre)
    crecimiento = round((total_24 - total_23) / total_23 * 100, 1)
    sup = round(s_total / total_23 * 100, 1)
    mor = round(m_total / total_23 * 100, 1)

    # hallazgos calculados
    palizada = res.loc[res["municipio"] == "Palizada", "crecimiento_neto"].iloc[0]
    nucleo_sobre = int((sobre["sector_servicios"] == "nucleo").sum())
    resto_sobre = int((sobre["sector_servicios"] == "resto").sum())

    csv_mun = res[["municipio", "U23", "U24", "Nacimientos", "Muertes",
                   "tasa_supervivencia", "tasa_natalidad", "tasa_mortalidad",
                   "crecimiento_neto"]].rename(columns={"U23": "Unidades_2023", "U24": "Unidades_2024"}).to_csv(index=False)
    csv_sec = pd.DataFrame({
        "nivel": NIVELES,
        "sobrevivientes": [int((sobre["sector_servicios"] == n).sum()) for n in NIVELES],
        "nacimientos": [int((nac["sector_servicios"] == n).sum()) for n in NIVELES],
        "muertes": [int((mue["sector_servicios"] == n).sum()) for n in NIVELES],
    }).to_csv(index=False)
    csv_grupo = pd.DataFrame({
        "grupo": ["A", "B", "C"],
        "indice_dinamismo": [idx_grupo[g] for g in ["A", "B", "C"]],
    }).to_csv(index=False)

    datos_js = json.dumps({
        "municipios": csv_mun, "sector": csv_sec, "grupo": csv_grupo,
    })

    css = """
    :root { color-scheme: light; }
    * { box-sizing: border-box; }
    body { margin:0; font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
           background:#eef1f5; color:#1f2933; line-height:1.6; }
    .wrap { max-width: 1120px; margin: 0 auto; padding: 32px 22px 80px; }
    header.hero { background: linear-gradient(135deg, #1f77b4 0%, #14395e 100%);
                  color:#fff; padding: 56px 40px; border-radius: 16px; margin-bottom: 34px; }
    header.hero h1 { margin:0 0 14px; font-size: 2.1rem; line-height:1.3; }
    header.hero .sub { font-size:1.15rem; opacity:.92; }
    .kpis { display:grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap:16px; margin: 0 0 34px; }
    .kpi { background:#fff; border-radius:12px; padding:20px; box-shadow: 0 1px 5px rgba(0,0,0,.08); }
    .kpi-titulo { font-size:.78rem; text-transform:uppercase; letter-spacing:.05em; color:#52606d; }
    .kpi-valor { font-size:2rem; font-weight:700; margin:6px 0 2px; }
    .kpi-sub { font-size:.78rem; color:#7b8794; }
    .tarjeta { background:#fff; border-radius:14px; padding:34px 36px; margin:32px 0;
               box-shadow: 0 1px 5px rgba(0,0,0,.08); }
    .sec-cab { display:flex; align-items:center; gap:12px; margin-bottom:10px; }
    .sec-num { background:#1f77b4; color:#fff; font-weight:700; border-radius:8px;
               padding:4px 12px; font-size:.95rem; }
    .sec-cab h2 { margin:0; font-size:1.45rem; color:#14395e; }
    .que-es { color:#3e4c59; margin:8px 0 14px; font-size:1.02rem; }
    .hallazgo { background:#eef7f0; border-left:4px solid #2ca02c; color:#1f5130;
                padding:12px 16px; border-radius:8px; margin-bottom:16px; font-size:.97rem; }
    .hallazgo.neg { background:#fdf0ef; border-left-color:#d62728; color:#7a2020; }
    .subsec { margin:24px 0 8px; font-size:1.1rem; color:#14395e;
              border-bottom:2px solid #e4e7eb; padding-bottom:6px; }
    .scorp { margin-top:18px; background:#f8fafc; border:1px solid #e4e7eb;
             border-radius:8px; padding:12px 16px; }
    .scorp summary { cursor:pointer; font-weight:600; color:#14395e; }
    .scorp p { margin:10px 0 0; font-size:.95rem; }
    .conclusion { background:#fff7e6; border:1px solid #ffd58a; }
    .figura { margin-top:14px; }
    .fig-dos { display:flex; flex-wrap:wrap; gap:16px; }
    .fig-dos > div { flex:1 1 400px; min-width:340px; }
    .tabla { width:100%; border-collapse:collapse; font-size:.9rem; margin-top:12px; }
    .tabla th, .tabla td { padding:9px 12px; border-bottom:1px solid #e4e7eb; text-align:left; }
    .tabla th { background:#eef2f7; color:#14395e; }
    .tabla .num { text-align:right; font-variant-numeric: tabular-nums; }
    .tabla tbody tr:nth-child(even) { background:#f8fafc; }
    .botones { display:flex; gap:10px; flex-wrap:wrap; margin-top:16px; }
    button.btn { background:#1f77b4; color:#fff; border:none; padding:11px 18px;
                 border-radius:8px; cursor:pointer; font-size:.9rem; }
    button.btn:hover { background:#14395e; }
    button.btn.sec { background:#eef2f7; color:#14395e; }
    .nota { font-size:.85rem; color:#7b8794; margin-top:14px; }
    footer { text-align:center; color:#7b8794; font-size:.82rem; margin-top:40px; }
    """

    mapa = seccion(
        "1", "Mapa: crecimiento neto por municipio",
        "Cada municipio se colorea según su <b>crecimiento neto</b>, es decir, cuánto varió "
        "el número de unidades económicas entre nov-2023 y nov-2024 (en %). El verde indica "
        "que el municipio ganó negocios; el rojo, que los perdió. Pasa el cursor sobre cada "
        "municipio para ver su valor exacto.",
        f"Solo <b>Palizada</b> se contrajo ({palizada:+.1f}%). Todos los demás municipios "
        f"crecieron.",
        figs_html["mapa"],
    )

    tasas = seccion(
        "2", "Nacimientos y muertes por municipio",
        "Compara la <b>tasa de natalidad</b> (negocios nuevos sobre el total 2024, en azul) "
        "contra la <b>tasa de mortalidad</b> (negocios que cerraron sobre el total 2023, en "
        "naranja) de cada municipio. Una barra azul más larga significa que el municipio está "
        "creando más negocios de los que pierde.",
        "En <b>12 de los 13 municipios</b> la natalidad supera a la mortalidad; el crecimiento "
        "es un fenómeno extendido, no de unos pocos polos.",
        figs_html["tasas"],
    )

    tamano = seccion(
        "3", "Distribución por tamaño de negocio",
        "Muestra cuántas unidades económicas hay en cada rango de <b>personal ocupado</b>, en "
        "2023 (azul) y 2024 (naranja). Permite ver si la economía local está compuesta por "
        "negocios grandes o pequeños.",
        "El <b>85.7%</b> de las unidades tiene entre 0 y 5 personas: la economía campechana es "
        "abrumadoramente microempresarial, lo que explica la paradoja del PIB (renta petrolera "
        "sin derrame en el tejido de base).",
        figs_html["tamano"],
    )

    sector = f"""
<section class="tarjeta">
  <div class="sec-cab"><span class="sec-num">4</span><h2>Sector de servicios</h2></div>
  <div class="que-es">El sector de servicios se divide en <b>niveles</b> según su código SCIAN.
  El <b>núcleo</b> agrupa alojamiento, alimentos y bebidas, y agencias de viajes; es ahí donde
  se esperaría ver el efecto del Tren Maya.</div>
  <div class="hallazgo"><strong>Hallazgo:</strong> el núcleo es minoritario
  ({nucleo_sobre:,} sobrevivientes frente a {resto_sobre:,} del resto), así que su peso en la
  economía total es pequeño.</div>

  <h3 class="subsec">A) Composición del núcleo de servicios</h3>
  <div class="figura">{figs_html["sector_donut"]}</div>

  <h3 class="subsec">B) Comparación entre niveles</h3>
  <div class="figura">{tabla_niveles(df23, df24, sobre, nac, mue)}</div>
  <p class="nota">Unidades = unidades económicas (negocios). Fuente: DENUE/INEGI.</p>

  <details class="scorp">
    <summary>¿Qué significan los códigos SCIAN y los niveles?</summary>
    <p>Los códigos como <b>7211</b> pertenecen al <b>SCIAN</b> (Sistema de Clasificación
    Industrial de América del Norte, del INEGI); sus primeros cuatro dígitos identifican el
    giro del negocio.<br>
    · <b>Núcleo</b> — alojamiento (7211), alimentos y bebidas (7225), agencias de viajes (5615).<br>
    · <b>Ampliado</b> — bares y centros nocturnos (7224), parques recreativos (7132), museos (7121).<br>
    · <b>Excluido</b> — transporte turístico terrestre (4871), excluido por circularidad.<br>
    · <b>Resto</b> — todos los demás giros de la economía.</p>
  </details>
</section>"""

    indice = seccion(
        "5", "Índice de dinamismo del sector de servicios",
        "Mide si el núcleo de servicios gana o pierde peso en la economía, comparando su "
        "participación en los <b>nacimientos</b> frente a las <b>muertes</b>: "
        "<code>(N_núcleo / N_total) − (M_núcleo / M_total)</code>.<br><br>"
        "<b>N_núcleo</b> = nacimientos del núcleo · <b>N_total</b> = nacimientos totales · "
        "<b>M_núcleo</b> = muertes del núcleo · <b>M_total</b> = muertes totales.<br><br>"
        "Se calcula por <b>grupo de exposición al Tren Maya</b>:<br>"
        "· <b>Grupo A</b> — conectados y expuestos (estaciones operativas desde dic-2023): "
        "Calkiní, Campeche, Champotón, Hecelchakán, Tenabo, Escárcega.<br>"
        "· <b>Grupo B</b> — conectados con exposición marginal (estaciones del Tramo 7, "
        "abiertas hasta dic-2024): Carmen, Calakmul, Candelaria.<br>"
        "· <b>Grupo C</b> — no conectados: Hopelchén, Palizada, Seybaplaya, Dzitbalché.",
        f"El índice global es <b>{idx_global:+.4f}</b>, pero el dinamismo positivo se concentra "
        f"en el <b>grupo B</b> ({idx_grupo['B']:+.4f}); los grupos A ({idx_grupo['A']:+.4f}) y "
        f"C ({idx_grupo['C']:+.4f}) son cercanos a cero o negativos.",
        figs_html["indice"],
    )

    top5 = seccion(
        "6", "Top 5 municipios por crecimiento neto",
        "Los cinco municipios con mayor crecimiento neto, con su valor exacto sobre cada barra.",
        "<b>Calakmul (+29.1%)</b>, <b>Dzitbalché (+28.3%)</b> y <b>Hopelchén (+25.7%)</b> "
        "lideran. Son municipios pequeños, donde cada nueva unidad tiene un impacto porcentual "
        "grande.",
        figs_html["top5"],
    )

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Demografía de negocios en Campeche</title>
<style>{css}</style>
</head>
<body>
<div class="wrap">

<header class="hero">
  <h1>¿Cómo cambió el tejido empresarial de Campeche tras la apertura del Tren Maya?</h1>
  <div class="sub">Comparación nov-2023 vs nov-2024 en los 13 municipios · DENUE / INEGI</div>
</header>

<div class="kpis">
  {kpi("Unidades 2023", f"{total_23:,}", AZUL)}
  {kpi("Unidades 2024", f"{total_24:,}", NARANJA)}
  {kpi("Sobrevivientes", f"{s_total:,}", VERDE)}
  {kpi("Nacimientos", f"{n_total:,}", AZUL)}
  {kpi("Muertes", f"{m_total:,}", ROJO)}
  {kpi("Crecimiento neto", f"{crecimiento:+.1f}%", VERDE if crecimiento >= 0 else ROJO)}
  {kpi("Tasa de supervivencia", f"{sup}%", AMBAR, "solo 7 de cada 10 negocios sobrevivieron")}
  {kpi("Tasa de mortalidad", f"{mor}%", ROJO, "3 de cada 10 negocios murieron")}
</div>

<section class="tarjeta">
  <div class="sec-cab"><span class="sec-num">•</span><h2>La paradoja del PIB campechano</h2></div>
  <div class="que-es">Campeche tiene uno de los PIB per cápita más altos de México gracias a la
  extracción petrolera, pero esa riqueza no se traduce en una economía local dinámica. Este
  dashboard mira <b>debajo del PIB</b>: cuántos negocios nacen, cuántos mueren y cuántos
  sobreviven en cada municipio.</div>
</section>

{mapa}
{tasas}
{tamano}
{sector}
{indice}
{top5}

<section class="tarjeta conclusion">
  <div class="sec-cab"><span class="sec-num">★</span><h2>Conclusión: más reemplazo que desarrollo</h2></div>
  <div class="que-es">El <b>+12.3% de crecimiento NO equivale a desarrollo</b>: solo 7 de cada
  10 negocios de 2023 sobrevivieron. El crecimiento se explica por nacimientos que reemplazan
  a los que murieron, no por el fortalecimiento del tejido existente. El 85.7% son
  microempresas, y el Tren Maya (grupo A) muestra un índice de dinamismo negativo. La economía
  campechana se <b>reemplaza más de lo que se desarrolla</b>, lo que da sentido a la paradoja
  del PIB: la renta petrolera no se traduce en un tejido empresarial robusto y acumulativo.</div>
  <div class="figura">{figs_html["donut_supervivencia"]}</div>
</section>

<section class="tarjeta">
  <div class="sec-cab"><span class="sec-num">7</span><h2>Tabla completa de municipios</h2></div>
  <div class="que-es">Todas las métricas por municipio: unidades 2023 y 2024, nacimientos,
  muertes, tasas y crecimiento neto. La última columna se colorea en verde (crecimiento) o
  rojo (contracción).</div>
  {tabla_html(res)}
  <div class="botones">
    <button class="btn" onclick="descargar('resumen_municipio.csv', DATOS.municipios)">Descargar CSVs</button>
    <button class="btn sec" onclick="descargar('resumen_sector.csv', DATOS.sector)">Sector (.csv)</button>
    <button class="btn sec" onclick="descargar('resumen_grupo.csv', DATOS.grupo)">Grupo (.csv)</button>
  </div>
  <p class="nota">Nota: la edición nov-2024 está ligada a los Censos Económicos 2024
  (actualización exhaustiva), por lo que parte del crecimiento puede deberse a una mejor
  cobertura censal.</p>
</section>

<footer>Fuente: DENUE / INEGI · Generado con Plotly · Demografía de negocios en Campeche</footer>

</div>

<script>
const DATOS = {datos_js};
function descargar(nombre, contenido) {{
  const blob = new Blob([contenido], {{type: 'text/csv;charset=utf-8'}});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = nombre;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}}
</script>
</body>
</html>"""


def main():
    df23, df24, sobre, nac, mue = cargar_datos()
    res = resumen_municipio(df23, df24, sobre, nac, mue)

    with open(GEOJSON_PATH, encoding="utf-8") as f:
        geojson = json.load(f)

    fig_ind, idx_grupo = fig_indice(nac, mue)
    n_total = len(nac)
    m_total = len(mue)
    n_nucleo = int((nac["sector_servicios"] == "nucleo").sum())
    m_nucleo = int((mue["sector_servicios"] == "nucleo").sum())
    idx_global = round((n_nucleo / n_total) - (m_nucleo / m_total), 4)

    figs = {
        "mapa": fig_mapa(res, geojson),
        "tasas": fig_tasas(res),
        "tamano": fig_tamano(df23, df24),
        "sector_donut": fig_donut_nucleo(sobre),
        "indice": fig_ind,
        "top5": fig_top5(res),
        "donut_supervivencia": fig_donut_supervivencia(len(sobre), len(mue)),
    }

    figs_html = {}
    primero = True
    for nombre, fig in figs.items():
        include_js = "inline" if primero else False
        figs_html[nombre] = fig.to_html(
            full_html=False, include_plotlyjs=include_js,
            config={"displayModeBar": False, "displaylogo": False, "responsive": True},
        )
        primero = False

    html = construir_html(figs_html, res, df23, df24, sobre, nac, mue, idx_global, idx_grupo)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(html, encoding="utf-8")
    print(f"Dashboard generado en: {OUT_PATH.relative_to(BASE_DIR)}")
    print(f"Tamaño: {OUT_PATH.stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
