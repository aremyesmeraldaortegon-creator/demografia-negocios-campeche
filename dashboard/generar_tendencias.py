"""
dashboard/generar_tendencias.py

Genera docs/tendencias.html, la pagina de tendencias 2022-2025 del
dashboard (multiedicion): artefacto censal 2024, indice de dinamismo
temporal, distribucion por tamano, cohortes y mapa por anio.

Uso:
    python dashboard/generar_tendencias.py
"""

import json
import sqlite3
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "denue.db"
GEOJSON_PATH = BASE_DIR / "dashboard" / "campeche_municipios.geojson"
OUT_PATH = BASE_DIR / "docs" / "tendencias.html"

AZUL = "#1f77b4"
NARANJA = "#ff7f0e"
VERDE = "#2ca02c"
ROJO = "#d62728"
GRIS = "#7f7f7f"

EDICIONES = ["2022_11", "2023_11", "2024_11", "2025_05"]
ETIQUETAS = ["nov-2022", "nov-2023", "nov-2024", "may-2025"]
TRANSICIONES = [("2022_11", "2023_11"), ("2023_11", "2024_11"), ("2024_11", "2025_05")]

ORDEN_TAM = [
    "0 a 5 personas", "6 a 10 personas", "11 a 30 personas",
    "31 a 50 personas", "51 a 100 personas", "101 a 250 personas",
    "251 y más personas",
]

MUNICIPIOS = {
    "001": "Calkiní-Dzitbalché", "002": "Campeche", "003": "Carmen", "004": "Champotón",
    "005": "Hecelchakán", "006": "Hopelchén", "007": "Palizada", "008": "Tenabo",
    "009": "Escárcega", "010": "Calakmul", "011": "Candelaria", "012": "Seybaplaya",
}


def cargar():
    con = sqlite3.connect(DB_PATH)
    datos = {ed: pd.read_sql(f"SELECT * FROM denue_{ed}", con) for ed in EDICIONES}
    trans = {}
    for e1, e2 in TRANSICIONES:
        s = pd.read_sql(f"SELECT * FROM t_{e1}__{e2}_sobrevivientes", con)
        n = pd.read_sql(f"SELECT * FROM t_{e1}__{e2}_nacimientos", con)
        m = pd.read_sql(f"SELECT * FROM t_{e1}__{e2}_muertes", con)
        trans[(e1, e2)] = (s, n, m)
    cohortes = pd.read_sql("SELECT * FROM cohortes", con)
    con.close()
    with open(GEOJSON_PATH, encoding="utf-8") as f:
        geojson = json.load(f)
    return datos, trans, cohortes, geojson


def fig_totales(datos):
    totales = [len(datos[ed]) for ed in EDICIONES]
    fig = go.Figure(go.Scatter(x=ETIQUETAS, y=totales, mode="lines+markers+text",
                               text=[f"{t:,}" for t in totales],
                               textposition="top center", line=dict(color=AZUL, width=3)))
    fig.update_layout(height=420, margin=dict(l=10, r=10, t=30, b=40), yaxis_title="Unidades")
    return fig


def fig_supervivencia(datos, trans):
    vals = []
    for e1, e2 in TRANSICIONES:
        s, _, _ = trans[(e1, e2)]
        vals.append(round(len(s) / len(datos[e1]) * 100, 1))
    labels = [f"{e1[:4]}→{e2[:4]}" for e1, e2 in TRANSICIONES]
    colores = [VERDE, ROJO, VERDE]
    fig = go.Figure(go.Bar(x=labels, y=vals, marker_color=colores,
                           text=[f"{v}%" for v in vals], textposition="outside"))
    fig.add_hline(y=90, line_dash="dash", line_color=GRIS)
    fig.update_layout(height=420, margin=dict(l=10, r=10, t=30, b=40),
                      yaxis=dict(range=[0, 115], title="%"),
                      title="Tasa de supervivencia por transición")
    return fig, vals


def fig_entrada_salida(datos, trans):
    entrada, salida = [], []
    for e1, e2 in TRANSICIONES:
        s, n, m = trans[(e1, e2)]
        base = len(datos[e1])
        entrada.append(round(len(n) / base * 100, 1))
        salida.append(round(len(m) / base * 100, 1))
    labels = [f"{e1[:4]}→{e2[:4]}" for e1, e2 in TRANSICIONES]
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Entrada (N/U_base)", x=labels, y=entrada, marker_color=AZUL))
    fig.add_trace(go.Bar(name="Salida (M/U_base)", x=labels, y=salida, marker_color=NARANJA))
    fig.update_layout(barmode="group", height=420, margin=dict(l=10, r=10, t=30, b=40),
                      yaxis_title="%", legend=dict(orientation="h"))
    return fig


def calcular_indice(datos, trans):
    filas = []
    for e1, e2 in TRANSICIONES:
        s, n, m = trans[(e1, e2)]
        n_total = len(n)
        m_total = len(m)
        n_nucleo = int((n["sector_servicios"] == "nucleo").sum())
        m_nucleo = int((m["sector_servicios"] == "nucleo").sum())
        idx = round((n_nucleo / n_total) - (m_nucleo / m_total), 4) if n_total and m_total else 0.0
        fila = {"transicion": f"{e1[:4]}→{e2[:4]}", "indice": idx}
        for g in ["A", "B", "C"]:
            ng = int(((n["sector_servicios"] == "nucleo") & (n["grupo_tren"] == g)).sum())
            mg = int(((m["sector_servicios"] == "nucleo") & (m["grupo_tren"] == g)).sum())
            fila[g] = round((ng / n_total) - (mg / m_total), 4)
        filas.append(fila)
    return pd.DataFrame(filas)


def fig_indice_temporal(df_indice):
    fig = go.Figure(go.Scatter(x=df_indice["transicion"], y=df_indice["indice"],
                               mode="lines+markers+text",
                               text=[f"{v:+.4f}" for v in df_indice["indice"]],
                               textposition="top center", line=dict(color=AZUL, width=3)))
    fig.add_hline(y=0, line_dash="dash", line_color=GRIS)
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=30, b=40),
                      yaxis_title="Índice de dinamismo",
                      title="Índice de dinamismo del sector de servicios por transición")
    return fig


def fig_indice_grupos(df_indice):
    fig = go.Figure()
    for g, color in [("A", AZUL), ("B", NARANJA), ("C", GRIS)]:
        fig.add_trace(go.Scatter(x=df_indice["transicion"], y=df_indice[g],
                                 mode="lines+markers", name=f"Grupo {g}",
                                 line=dict(color=color, width=2)))
    fig.add_hline(y=0, line_dash="dash", line_color=GRIS)
    fig.update_layout(height=400, margin=dict(l=10, r=10, t=30, b=40),
                      yaxis_title="Índice de dinamismo",
                      legend=dict(orientation="h"),
                      title="Índice por grupo Tren Maya (A/B/C)")
    return fig


def tabla_tamano(datos):
    filas = []
    for rango in ORDEN_TAM:
        fila = {"rango": rango}
        for ed in EDICIONES:
            fila[ed] = int((datos[ed]["per_ocu"] == rango).sum())
        filas.append(fila)
    return pd.DataFrame(filas)


def tabla_tamano_html(df):
    filas = ""
    for _, r in df.iterrows():
        filas += f'<tr><td>{r["rango"]}</td>'
        for ed in EDICIONES:
            filas += f'<td class="num">{r[ed]:,}</td>'
        filas += "</tr>"
    enc = "".join(f"<th>{ETIQUETAS[i]}</th>" for i in range(len(EDICIONES)))
    return ('<table class="tabla"><thead><tr><th>Rango</th>' + enc +
            '</tr></thead><tbody>' + filas + '</tbody></table>')


def fig_microempresas(datos):
    prop = []
    for ed in EDICIONES:
        n_0_5 = int((datos[ed]["per_ocu"] == "0 a 5 personas").sum())
        prop.append(round(n_0_5 / len(datos[ed]) * 100, 1))
    fig = go.Figure(go.Scatter(x=ETIQUETAS, y=prop, mode="lines+markers+text",
                               text=[f"{p}%" for p in prop], textposition="top center",
                               line=dict(color=ROJO, width=3)))
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=30, b=40),
                      yaxis=dict(range=[70, 100], title="%"),
                      title="Proporción de microempresas (0-5 personas)")
    return fig, prop


def supervivencia_cohortes(cohortes):
    filas = []
    for ed in EDICIONES:
        c = cohortes[cohortes["cohorte"] == ed]
        n0 = len(c)
        ultima = EDICIONES[-1]
        s = int(c[f"en_{ultima}"].sum()) if n0 else 0
        filas.append({"cohorte": ed, "n": n0,
                      "sobreviven_2025": s,
                      "pct": round(s / n0 * 100, 1) if n0 else 0.0})
    return pd.DataFrame(filas)


def fig_cohortes(df_cohortes):
    d = df_cohortes[df_cohortes["cohorte"] != EDICIONES[-1]]
    fig = go.Figure(go.Bar(x=d["cohorte"], y=d["pct"],
                           text=[f"{v}%" for v in d["pct"]], textposition="outside",
                           marker_color=[AZUL, NARANJA, VERDE]))
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=30, b=40),
                      yaxis=dict(range=[0, 110], title="%"),
                      title="Supervivencia a may-2025 por cohorte")
    return fig


def fig_mapa_anio(datos, ed, geojson, zmin, zmax):
    conteo = datos[ed].groupby("cve_mun").size()
    valores = {("04" + cve): int(v) for cve, v in conteo.items()}
    if "04001" in valores:
        valores.setdefault("04013", valores["04001"])

    locations, z, text = [], [], []
    for f in geojson["features"]:
        cve = f["properties"]["cvegeo"]
        if cve in valores:
            locations.append(cve)
            z.append(valores[cve])
            cve_mun = cve[2:]
            text.append(MUNICIPIOS.get(cve_mun, MUNICIPIOS.get("001", cve)))

    fig = go.Figure(go.Choropleth(
        geojson=geojson, locations=locations, z=z,
        featureidkey="properties.cvegeo", colorscale="Blues",
        zmin=zmin, zmax=zmax, marker_line_width=0.5, marker_line_color="white",
        colorbar=dict(title="Unidades"), text=text,
        hovertemplate="%{text}: %{z:,}<extra></extra>",
    ))
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(height=360, margin=dict(l=0, r=0, t=30, b=0),
                      title=f"Unidades por municipio · {ETIQUETAS[EDICIONES.index(ed)]}")
    return fig


def fig_municipios(datos):
    sel = ["Campeche", "Carmen", "Calkiní-Dzitbalché", "Escárcega", "Calakmul", "Palizada"]
    fig = go.Figure()
    for nombre in sel:
        serie = [int((datos[ed]["municipio"] == nombre).sum()) for ed in EDICIONES]
        fig.add_trace(go.Scatter(x=ETIQUETAS, y=serie, mode="lines+markers", name=nombre))
    fig.update_layout(height=440, margin=dict(l=10, r=10, t=30, b=40), yaxis_title="Unidades")
    return fig


def fig_cohorte_2022(cohortes):
    c22 = cohortes[cohortes["cohorte"] == "2022_11"]
    n0 = len(c22)
    pts = [100] + [int(c22[f"en_{ed}"].sum()) / n0 * 100 for ed in EDICIONES[1:]]
    fig = go.Figure(go.Scatter(x=ETIQUETAS, y=pts, mode="lines+markers+text",
                               text=[f"{p:.1f}%" for p in pts],
                               textposition="top center", line=dict(color=AZUL, width=3)))
    fig.update_layout(height=420, margin=dict(l=10, r=10, t=30, b=40),
                      yaxis=dict(range=[0, 115], title="%"),
                      title=f"Supervivencia de la cohorte 2022 (n={n0:,})")
    return fig, pts


def construir_html(figs, vals_supervivencia, pts_cohorte, df_indice, df_tam, prop_micro, df_cohortes):
    # hallazgos del indice temporal
    ult = df_indice.iloc[-1]
    gA_recupera = "sí se recupera" if ult["A"] > df_indice.iloc[1]["A"] else "no se recupera del todo"

    css = """
    :root { color-scheme: light; }
    * { box-sizing: border-box; }
    body { margin:0; font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
           background:#eef1f5; color:#1f2933; line-height:1.6; }
    .wrap { max-width: 1120px; margin: 0 auto; padding: 32px 22px 80px; }
    header.hero { background: linear-gradient(135deg, #1f77b4 0%, #14395e 100%);
                  color:#fff; padding: 56px 40px; border-radius: 16px; margin-bottom: 28px; }
    header.hero h1 { margin:0 0 12px; font-size:2rem; line-height:1.3; }
    header.hero .sub { font-size:1.1rem; opacity:.92; }
    nav { margin: 0 0 24px; }
    nav a { color:#1f77b4; text-decoration:none; font-weight:600; }
    section { background:#fff; border-radius:14px; padding:30px 34px; margin:28px 0;
              box-shadow: 0 1px 5px rgba(0,0,0,.08); }
    section h2 { margin:0 0 6px; font-size:1.35rem; color:#14395e; }
    .que-es { color:#3e4c59; margin:4px 0 12px; }
    .hallazgo { background:#fdf0ef; border-left:4px solid #d62728; color:#7a2020;
                padding:12px 16px; border-radius:8px; margin:14px 0; }
    .hallazgo.ok { background:#eef7f0; border-left-color:#2ca02c; color:#1f5130; }
    .tabla { width:100%; border-collapse:collapse; font-size:.88rem; margin-top:12px; }
    .tabla th, .tabla td { padding:8px 10px; border-bottom:1px solid #e4e7eb; text-align:left; }
    .tabla th { background:#eef2f7; color:#14395e; }
    .tabla .num { text-align:right; font-variant-numeric: tabular-nums; }
    .tabla tbody tr:nth-child(even) { background:#f8fafc; }
    .fig-grid { display:flex; flex-wrap:wrap; gap:12px; }
    .fig-grid > div { flex:1 1 400px; min-width:320px; }
    footer { text-align:center; color:#7b8794; font-size:.82rem; margin-top:40px; }
    """
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tendencias 2022–2025 · Demografía de negocios en Campeche</title>
<style>{css}</style>
</head>
<body>
<div class="wrap">

<nav><a href="index.html">← Volver al snapshot 2023–2024</a></nav>

<header class="hero">
  <h1>Tendencias 2022–2025</h1>
  <div class="sub">Cuatro ediciones del DENUE · la serie temporal y el artefacto censal de 2024</div>
</header>

<section>
  <h2>1. Total de unidades económicas</h2>
  <div class="que-es">De 41,638 (nov-2022) a 47,408 (may-2025). Nota: la última edición es de mayo,
  así que el último tramo cubre solo 6 meses.</div>
  {figs["totales"]}
</section>

<section>
  <h2>2. El artefacto censal de 2024</h2>
  <div class="que-es">La edición nov-2024 es exhaustiva (Censos Económicos). La tasa de supervivencia
  cae de <b>{vals_supervivencia[0]}%</b> (2022→2023) a <b>{vals_supervivencia[1]}%</b> (2023→2024) y se
  recupera a <b>{vals_supervivencia[2]}%</b> (2024→2025).</div>
  <div class="hallazgo"><b>Hallazgo clave:</b> la caída a {vals_supervivencia[1]}% no es un colapso real
  de negocios, sino la re-codificación masiva de CLEEs que introduce el censo económico.</div>
  {figs["supervivencia"]}
  {figs["entrada_salida"]}
</section>

<section>
  <h2>3. Índice de dinamismo del sector de servicios (Tren Maya)</h2>
  <div class="que-es">El índice <code>(N_núcleo/N_total) − (M_núcleo/M_total)</code> por transición:
  si es positivo, el núcleo de servicios gana peso; si es negativo, lo pierde.</div>
  {figs["indice_temporal"]}
  <div class="que-es">Desglose por grupo de exposición al Tren Maya. En la transición 2024→2025 el
  grupo A es {ult["A"]:+.4f} ({gA_recupera}), el grupo B {ult["B"]:+.4f} y el grupo C {ult["C"]:+.4f}.</div>
  {figs["indice_grupos"]}
</section>

<section>
  <h2>4. Distribución por tamaño (¿se diversifica el tejido?)</h2>
  <div class="que-es">Proporción de microempresas (0-5 personas) en cada edición. Si baja, el tejido
  se está diversificando; si se mantiene, sigue dominado por lo micro.</div>
  {figs["microempresas"]}
  {tabla_tamano_html(df_tam)}
</section>

<section>
  <h2>5. Tendencia por municipio</h2>
  {figs["municipios"]}
</section>

<section>
  <h2>6. Supervivencia por cohorte</h2>
  <div class="que-es">Qué porcentaje de cada generación de negocios sigue activa en may-2025.
  (La cohorte 2024 tiene ventana de solo 6 meses, por eso su tasa es alta.)</div>
  {figs["cohortes"]}
  <div class="hallazgo ok"><b>Hallazgo:</b> la cohorte 2022 sobrevive {pts_cohorte[-1]:.1f}% a 2025
  (≈2.5 años); la cohorte 2023, {df_cohortes.loc[df_cohortes['cohorte']=='2023_11','pct'].iloc[0]}%;
  y la cohorte 2024, {df_cohortes.loc[df_cohortes['cohorte']=='2024_11','pct'].iloc[0]}% (6 meses).</div>
</section>

<section>
  <h2>7. Mapa por año</h2>
  <div class="que-es">Unidades económicas por municipio en cada una de las cuatro ediciones.</div>
  <div class="fig-grid">
    {figs["mapa_2022"]}{figs["mapa_2023"]}{figs["mapa_2024"]}{figs["mapa_2025"]}
  </div>
</section>

<section>
  <h2>Glosario de claves y abreviaturas</h2>
  <details open>
    <summary>¿Qué significan estos términos?</summary>
    <div class="que-es">
      · <b>CLEE</b> — Clave Única de Identificación de Establecimientos: identificador único del INEGI para cada negocio.<br>
      · <b>SCIAN</b> — Sistema de Clasificación Industrial de América del Norte: código que identifica el giro del negocio.<br>
      · <b>Edición</b> — una "foto" del DENUE en un momento dado (p. ej. nov-2022, may-2025).<br>
      · <b>Transición</b> — comparación entre dos ediciones consecutivas.<br>
      · <b>U_base</b> — unidades económicas en la edición de partida de una transición.<br>
      · <b>S / N / M</b> — sobrevivientes, nacimientos y muertes entre dos ediciones.<br>
      · <b>Cohorte</b> — conjunto de negocios que aparecen por primera vez en una misma edición.<br>
      · <b>Artefacto censal</b> — distorsión que introduce la edición exhaustiva de 2024 (re-codifica masivamente las CLEEs).<br>
      · <b>Ventana temporal</b> — meses reales entre dos ediciones (12m, 12m o 6m).
    </div>
  </details>
</section>

<footer>Fuente: DENUE / INEGI · Generado con Plotly · Demografía de negocios en Campeche</footer>

</div>
</body>
</html>"""


def main():
    datos, trans, cohortes, geojson = cargar()

    fig_sup, vals_supervivencia = fig_supervivencia(datos, trans)
    fig_cohorte, pts_cohorte = fig_cohorte_2022(cohortes)
    df_indice = calcular_indice(datos, trans)
    df_tam = tabla_tamano(datos)
    _, prop_micro = fig_microempresas(datos)
    df_cohortes = supervivencia_cohortes(cohortes)

    # rango de color comun para los mapas
    todos_valores = []
    for ed in EDICIONES:
        todos_valores.extend(datos[ed].groupby("cve_mun").size().values.tolist())
    zmin = min(todos_valores)
    zmax = max(todos_valores)

    figs = {
        "totales": fig_totales(datos),
        "supervivencia": fig_sup,
        "entrada_salida": fig_entrada_salida(datos, trans),
        "indice_temporal": fig_indice_temporal(df_indice),
        "indice_grupos": fig_indice_grupos(df_indice),
        "microempresas": fig_microempresas(datos)[0],
        "municipios": fig_municipios(datos),
        "cohortes": fig_cohortes(df_cohortes),
        "mapa_2022": fig_mapa_anio(datos, "2022_11", geojson, zmin, zmax),
        "mapa_2023": fig_mapa_anio(datos, "2023_11", geojson, zmin, zmax),
        "mapa_2024": fig_mapa_anio(datos, "2024_11", geojson, zmin, zmax),
        "mapa_2025": fig_mapa_anio(datos, "2025_05", geojson, zmin, zmax),
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

    html = construir_html(figs_html, vals_supervivencia, pts_cohorte,
                          df_indice, df_tam, prop_micro, df_cohortes)
    OUT_PATH.write_text(html, encoding="utf-8")
    print(f"Dashboard de tendencias generado en: {OUT_PATH.relative_to(BASE_DIR)}")
    print(f"Tamaño: {OUT_PATH.stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
