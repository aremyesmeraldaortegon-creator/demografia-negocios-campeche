# Demografía de negocios en Campeche

Análisis de nacimientos, muertes y sobrevivencia de negocios en los 13 municipios de Campeche, comparando el DENUE (nov-2023 vs. nov-2024), con foco en el sector turístico y el Tren Maya.

---

## 0. Nota metodológica: por qué se hace así

Antes de presentar cualquier cifra, conviene explicar las tres decisiones metodológicas que estructuran todo el análisis. No son arbitrarias: cada una responde a una limitación concreta de la fuente de datos.

### 0.1 ¿Por qué comparar nov-2023 vs. nov-2024?

El Tren Maya se inauguró en diciembre de 2023. Nov-2023 es el último corte previo a la apertura, mientras que nov-2024 es el primer corte anual completo posterior y corresponde a los Censos Económicos 2024 (una actualización exhaustiva, no incremental). Comparar un año exacto entre ambas fotos aísla el efecto del Tren Maya de variaciones estacionales: cualquier diferencia entre las dos ediciones no puede atribuirse a la estacionalidad del turismo, sino al cambio estructural en el tejido empresarial.

### 0.2 ¿Por qué un esquema híbrido para definir nacimiento/muerte?

El DENUE no es un panel longitudinal: no sigue al mismo negocio con un identificador perfectamente estable entre ediciones. Depender de un solo criterio produciría sesgos severos:

- Si solo se usa la CLEE, cualquier cambio administrativo del INEGI se leería como "muerte + nacimiento" aunque el negocio siga operando.
- Si solo se usa la llave compuesta (nombre + dirección + giro), cualquier cambio de nombre o mudanza mínima se leería como muerte.

Por eso se adopta el esquema híbrido, siguiendo la lógica del Estudio de Demografía de los Negocios (EDN) del INEGI:

1. Coincidencia por CLEE → sobreviviente.
2. Si no hay match: regla de 3 variables clave (nombre, SCIAN, ubicación). Si cambia ≤1 → sobreviviente; ≥2 → muerte + nacimiento.
3. Validación auxiliar con FECHA_ALTA.

Detalle operativo en `docs/metodologia.md`.

### 0.3 ¿Por qué estratificar el sector turístico en 3 niveles?

Los giros que suelen etiquetarse como "turismo" no responden igual al fenómeno. Meterlos todos en una sola bolsa introduce dos problemas:

1. **Circularidad causal.** El código SCIAN 4871 (transporte turístico terrestre) podría incluir al propio Tren Maya. Medir el efecto del Tren Maya incluyendo al Tren Maya en la muestra invalida el análisis.

2. **Heterogeneidad no controlada.** Museos (7121) y parques recreativos (7132) tienen dinámicas muy distintas a las de un hotel: muchos son públicos y su supervivencia no depende del mercado turístico, sino del presupuesto gubernamental.

Por eso se trabaja con tres niveles:

| Nivel | SCIAN | Rol en el análisis |
|---|---|---|
| Núcleo | 7211, 7225, 5615 | Análisis principal |
| Ampliado | + 7224, 7132, 7121 | Análisis de robustez |
| Excluido | 4871 | Excluido por circularidad causal |

---

## 1. Contexto y objetivo

*[Borrador — por completar]*

La paradoja del PIB campechano: Campeche tiene uno de los PIB per cápita más altos del país por la actividad petrolera, pero eso no se refleja necesariamente en el dinamismo de su economía local. Mi objetivo es explorar esta paradoja a través de la demografía de los negocios, usando como "experimento natural" la apertura del Tren Maya en diciembre de 2023.

- **Pregunta central:** ¿cómo cambió el tejido empresarial de los municipios de Campeche tras la apertura del Tren Maya?
- **Objetivos específicos:**
  - Medir nacimientos, muertes y sobrevivencia de unidades económicas entre dos ediciones del DENUE.
  - Comparar el sector turístico frente al resto de la economía.

---

## 2. Fuente de datos

*[Borrador — por completar]*

El Directorio Estadístico Nacional de Unidades Económicas (DENUE) del INEGI es la fuente principal. Uso dos "fotos" en el tiempo:

| Foto | Período | Fuente / vía de acceso |
|------|---------|------------------------|
| Antes (histórica) | nov-2023 | Descarga masiva de una edición histórica del DENUE |
| Después (actual) | nov-2024 | Edición de los Censos Económicos 2024 |

- **API del DENUE:** https://www.inegi.org.mx/app/api/denue/v1/consulta/ (requiere token gratuito). Se usa para consultas puntuales de cualquier edición.
- **Descarga masiva:** para la foto histórica (nov-2023) se usa la descarga masiva de la edición histórica del DENUE, en lugar del API.
- **Edición histórica:** *[describir cómo se obtiene la descarga masiva]*.

---

## 3. Extracción y almacenamiento (ETL)

*[Borrador — por completar]*

El proceso de extracción, transformación y carga (ETL) se organiza en la carpeta `etl/`. El detalle metodológico vive en `docs/metodologia.md`.

- **Extracción:** consultas al API del DENUE para la foto actual; descarga masiva para la foto histórica.
- **Almacenamiento:** base de datos SQLite (`data/`).
- **Transformación:** limpieza, normalización de giros (SCIAN) y clasificación del sector turístico.

---

## 4. Demografía de negocios: panorama general

*[Borrador — por completar]*

Notebook: `notebooks/01_panorama_general.ipynb`

Análisis agregado para todos los municipios y todos los giros: nacimientos, muertes y sobrevivencia por municipio, tasas de entrada y salida, y distribución por sector y tamaño de establecimiento.

---

## 5. Demografía de negocios: sector turístico

*[Borrador — por completar]*

Notebook: `notebooks/02_sector_turistico.ipynb`

Comparación del sector turístico contra el resto de los sectores, usando los niveles núcleo y ampliado, y desglose por subsector (hoteles, restaurantes, agencias de viajes). Se analiza el dinamismo diferencial en los municipios conectados por el Tren Maya.

---

## 6. Hallazgos y conclusión

*[Borrador — por completar]*

Resumen de los resultados principales y su relación con la paradoja del PIB campechano. Pendiente de redactar una vez terminado el análisis.

---

## Estructura del repositorio

```
demografia-negocios-campeche/
├── data/              # Datos crudos y base SQLite (ignorados por git)
├── docs/
│   └── metodologia.md # Metodología detallada
├── etl/               # Scripts de extracción, transformación y carga
├── notebooks/
│   ├── 01_panorama_general.ipynb
│   └── 02_sector_turistico.ipynb
├── README.md
├── .env.example       # Variables de entorno de ejemplo
├── .gitignore
└── requirements.txt   # Dependencias del proyecto
```

> **Nota:** el archivo `.env` (sin `.example`) contiene el token del INEGI y está ignorado por git vía `.gitignore`.

## Instalación

```bash
git clone <url-del-repo>   # reemplazar por la URL real una vez publicado
cd demografia-negocios-campeche
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
cp .env.example .env         # y llena tu INEGI_TOKEN
```

*Pasos de instalación pendientes de validar.*
