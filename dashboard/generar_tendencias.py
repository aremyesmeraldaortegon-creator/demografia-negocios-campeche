"""
dashboard/generar_tendencias.py

Genera docs/tendencias.html, la pagina de tendencias 2022-2025 del
dashboard (multiedicion, con el analisis del artefacto censal 2024 y
las curvas de cohorte).

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
OUT_PATH = BASE_DIR / "docs" / "tendencias.html"

AZUL = "#1f77b4"
NARANJA = "#ff7f0e"
VERDE = "#2ca02c"
ROJO = "#d62728"
GRIS = "#7f7f7f"

EDICIONES = ["2022_11", "2023_11", "2024_11", "2025_05"]
ETIQUETAS = ["nov-2022", "nov-2023", "nov-2024", "may-2025"]
TRANSICIONES = [("2022_11", "2023_11"), ("2023_11", "2024_11"), ("2024_11", "2025_05")]


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
    return datos, trans, cohortes


def fig_totales(datos):
    totales = [len(datos[ed]) for ed in EDICIONES]
    fig = go.Figure(go.Scatter(x=ETIQUETAS, y=totales, mode="lines+markers+text",
                               text=[f"{t:,}" for t in totales],
                               textposition="top center", line=dict(color=AZUL, width=3)))
    fig.update_layout(height=420, margin=dict(l=10, r=10, t=30, b=40),
                      yaxis_title="Unidades")
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
    entrada = []
    salida = []
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


def fig_municipios(datos):
    sel = ["Campeche", "Carmen", "Calkiní-Dzitbalché", "Escárcega", "Calakmul", "Palizada"]
    fig = go.Figure()
    for nombre in sel:
        serie = [int((datos[ed]["municipio"] == nombre).sum()) for ed in EDICIONES]
        fig.add_trace(go.Scatter(x=ETIQUETAS, y=serie, mode="lines+markers", name=nombre))
    fig.update_layout(height=440, margin=dict(l=10, r=10, t=30, b=40),
                      yaxis_title="Unidades")
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


def construir_html(figs, vals_supervivencia, pts_cohorte):
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
  de negocios, sino la re-codificación masiva de CLEEs que introduce el censo económico. El 42.9% de
  "nacimientos" y 30.6% de "muertes" de esa transición son, en su mayoría, artefacto de cobertura.</div>
  {figs["supervivencia"]}
  {figs["entrada_salida"]}
</section>

<section>
  <h2>3. Tendencia por municipio</h2>
  <div class="que-es">Unidades económicas de una selección de municipios a lo largo de las cuatro
  ediciones.</div>
  {figs["municipios"]}
</section>

<section>
  <h2>4. Supervivencia de la cohorte 2022</h2>
  <div class="que-es">De los negocios presentes en nov-2022, qué porcentaje sigue presente en cada
  edición posterior. Al final (may-2025), sobrevive el <b>{pts_cohorte[-1]:.1f}%</b>.</div>
  <div class="hallazgo ok"><b>Hallazgo:</b> de 41,638 negocios de 2022, solo el {pts_cohorte[-1]:.1f}%
  seguía activo en 2025 (≈2.5 años después). El resto cerró o fue re-codificado.</div>
  {figs["cohorte"]}
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
    datos, trans, cohortes = cargar()

    fig_sup, vals_supervivencia = fig_supervivencia(datos, trans)
    fig_cohorte, pts_cohorte = fig_cohorte_2022(cohortes)

    figs = {
        "totales": fig_totales(datos),
        "supervivencia": fig_sup,
        "entrada_salida": fig_entrada_salida(datos, trans),
        "municipios": fig_municipios(datos),
        "cohorte": fig_cohorte,
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

    html = construir_html(figs_html, vals_supervivencia, pts_cohorte)
    OUT_PATH.write_text(html, encoding="utf-8")
    print(f"Dashboard de tendencias generado en: {OUT_PATH.relative_to(BASE_DIR)}")
    print(f"Tamaño: {OUT_PATH.stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
