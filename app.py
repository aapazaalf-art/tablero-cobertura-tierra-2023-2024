import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import re

# Configuración de la página
st.set_page_config(page_title="Tablero de Cambios de Cobertura", layout="wide", page_icon="🌳")

# ==================== FUNCIÓN PARA EXTRAER AÑOS DEL NOMBRE DEL ARCHIVO ====================
def extract_years_from_filename(filename: str):
    """
    Extrae dos años de 4 dígitos del nombre del archivo.
    Ejemplos: "2023 - 2024.xlsx" -> ("2023", "2024")
              "transiciones_2020_2021.xlsx" -> ("2020", "2021")
              "2022-2023 data.xlsx" -> ("2022", "2023")
    Retorna (None, None) si no encuentra dos años.
    """
    # Busca patrones como 2023-2024, 2023 - 2024, 2023_2024, 2023→2024, etc.
    pattern = r'(\d{4})\s*[-–—_→]\s*(\d{4})'
    match = re.search(pattern, filename)
    if match:
        return match.group(1), match.group(2)
    # Busca dos años consecutivos separados por cualquier no dígito
    numbers = re.findall(r'\d{4}', filename)
    if len(numbers) >= 2:
        return numbers[0], numbers[1]
    return None, None

def get_years_from_file(uploaded_file, default_path="data/2023 - 2024.xlsx"):
    """
    Determina los años a partir del archivo cargado o del archivo por defecto.
    Retorna (year_start, year_end, filename_used).
    """
    if uploaded_file is not None:
        filename = uploaded_file.name
        year1, year2 = extract_years_from_filename(filename)
        if year1 and year2:
            return year1, year2, filename
        else:
            st.sidebar.warning(f"No se pudieron extraer años del nombre '{filename}'. Usando años manuales o por defecto.")
            return None, None, filename
    else:
        # Archivo local por defecto
        default_filename = default_path.split("/")[-1]
        year1, year2 = extract_years_from_filename(default_filename)
        if year1 and year2:
            return year1, year2, default_filename
        else:
            return None, None, default_filename

# ==================== DEFINICIÓN DE COLORES POR TIPO DE COBERTURA (VIBRANTES) ====================
def get_coverage_colors(coverage_names):
    """
    Asigna colores más vibrantes y contrastados según el tipo de cobertura del suelo
    """
    color_map = {}
    
    for name in coverage_names:
        name_lower = str(name).lower()
        
        # Bosques y vegetación natural
        if any(word in name_lower for word in ['bosque', 'forest', 'selva', 'jungla']):
            color_map[name] = '#00A86B'  # Verde jade vibrante
        elif any(word in name_lower for word in ['arbusto', 'matorral', 'shrub']):
            color_map[name] = '#00C853'  # Verde brillante
        elif any(word in name_lower for word in ['pastizal', 'pasture', 'herbácea']):
            color_map[name] = '#C0FF00'  # Lima eléctrico
            
        # Áreas agrícolas
        elif any(word in name_lower for word in ['agrícola', 'agriculture', 'cultivo', 'crop']):
            color_map[name] = '#FFEA00'  # Amarillo intenso
        elif any(word in name_lower for word in ['pasto', 'ganadero', 'livestock']):
            color_map[name] = '#FFC107'  # Ámbar vibrante
            
        # Áreas urbanas e infraestructura
        elif any(word in name_lower for word in ['urbano', 'urban', 'ciudad', 'city']):
            color_map[name] = '#FF3D00'  # Naranja profundo
        elif any(word in name_lower for word in ['infraestructura', 'infrastructure', 'carretera']):
            color_map[name] = '#D84315'  # Naranja terracota
            
        # Cuerpos de agua
        elif any(word in name_lower for word in ['agua', 'water', 'río', 'river', 'lago', 'lake']):
            color_map[name] = '#2979FF'  # Azul eléctrico
        elif any(word in name_lower for word in ['humedal', 'wetland']):
            color_map[name] = '#00B0FF'  # Azul claro brillante
            
        # Suelos desnudos o erosionados
        elif any(word in name_lower for word in ['suelo', 'soil', 'desnudo', 'bare', 'erosion']):
            color_map[name] = '#FFB74D'  # Naranja claro
        elif any(word in name_lower for word in ['minería', 'mining']):
            color_map[name] = '#E64A19'  # Naranja quemado
            
        # Áreas protegidas
        elif any(word in name_lower for word in ['protegido', 'protected', 'reserva']):
            color_map[name] = '#00E676'  # Verde neón
            
        # Por defecto
        else:
            color_map[name] = '#BDBDBD'  # Gris medio
    
    return color_map

# ==================== CARGA DE DATOS ====================
st.sidebar.header("📁 Carga de datos")
uploaded_file = st.sidebar.file_uploader("Subir nueva matriz Excel", type=["xlsx"])

# Determinar años automáticamente o permitir ingreso manual
auto_year1, auto_year2, filename_used = get_years_from_file(uploaded_file)

if auto_year1 and auto_year2:
    year_start = auto_year1
    year_end = auto_year2
    st.sidebar.success(f"✅ Años detectados: {year_start} → {year_end}")
else:
    # Si no se detectan automáticamente, el usuario puede ingresarlos manualmente
    st.sidebar.warning("No se pudieron detectar los años del nombre del archivo. Ingrésalos manualmente:")
    col_year1, col_year2 = st.sidebar.columns(2)
    year_start = col_year1.text_input("Año inicial", value="2023", max_chars=4)
    year_end = col_year2.text_input("Año final", value="2024", max_chars=4)

# Cargar datos
try:
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file, sheet_name="Hoja1", index_col=0)
        st.sidebar.success("✅ Archivo cargado correctamente")
    else:
        df = pd.read_excel("data/2023 - 2024.xlsx", sheet_name="Hoja1", index_col=0)
        st.sidebar.info(f"Usando archivo local: data/{filename_used}")
    
    # Limpiar datos
    df = df.fillna(0)
    
    # Verificar que la matriz no esté vacía
    if df.empty or df.shape[0] == 0 or df.shape[1] == 0:
        st.error("❌ La matriz de datos está vacía o es inválida")
        st.stop()
        
except FileNotFoundError:
    st.error("❌ No se encontró el archivo Excel. Por favor, sube uno usando el botón en la barra lateral.")
    st.info("📌 El archivo debe contener una hoja llamada 'Hoja1' con una matriz de transiciones donde las filas son coberturas en el año inicial y las columnas en el año final")
    st.stop()
except Exception as e:
    st.error(f"❌ Error al cargar el archivo: {str(e)}")
    st.stop()

# ==================== CÁLCULOS BÁSICOS ====================
net_change = df.sum(axis=1).round(2)
total_changed = abs(df.values[df.values < 0].sum()).round(0)
total_positive_changes = df.values[df.values > 0].sum().round(0)

# Métricas en sidebar
st.sidebar.metric("Área total que cambió", f"{total_changed:,.0f} ha")
st.sidebar.metric("Área total de ganancias", f"{total_positive_changes:,.0f} ha")
st.sidebar.metric("Coberturas analizadas", len(df))

# ==================== MÉTRICAS PRINCIPALES ====================
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total coberturas", len(df), help="Número total de categorías de cobertura")
col2.metric("Ganadoras netas", (net_change > 0).sum(), help="Coberturas que aumentaron su área")
col3.metric("Perdedoras netas", (net_change < 0).sum(), help="Coberturas que disminuyeron su área")
col4.metric("Balance neto", f"{net_change.sum():+,.0f} ha", help="Cambio total neto (ganancias - pérdidas)")

# ==================== TÍTULOS DINÁMICOS ====================
st.title(f"🌳 Tablero Ejecutivo: Cambios en Cobertura del Suelo {year_start}–{year_end}")
st.markdown(f"**Análisis de transiciones {year_start} → {year_end}** | Ganancias (+) y Pérdidas (-) en hectáreas")

# ==================== GRÁFICO DE CAMBIO NETO ====================
st.subheader(f"📈 Cambio Neto por Cobertura (hectáreas) - Período {year_start}–{year_end}")

net_df = pd.DataFrame({
    "Cobertura": net_change.index,
    "Cambio Neto (ha)": net_change.values
}).sort_values("Cambio Neto (ha)", ascending=False)

coverage_colors = get_coverage_colors(net_df["Cobertura"].tolist())
net_df["Color"] = net_df["Cobertura"].map(coverage_colors)

fig_net = px.bar(
    net_df, 
    x="Cambio Neto (ha)", 
    y="Cobertura", 
    orientation="h",
    color="Cobertura",
    color_discrete_map=coverage_colors,
    height=900,
    text="Cambio Neto (ha)"
)

fig_net.update_traces(
    texttemplate='%{text:,.0f} ha',
    textposition='outside',
    textfont=dict(size=20, color='black', weight='bold')
)
fig_net.update_layout(
    yaxis=dict(
        categoryorder="total ascending",
        title="Cobertura del Suelo",
        title_font=dict(size=28, weight='bold'),
        tickfont=dict(size=22, weight='bold')
    ),
    xaxis=dict(
        title="Cambio Neto (hectáreas)",
        title_font=dict(size=28, weight='bold'),
        tickfont=dict(size=22, weight='bold'),
        gridcolor='lightgray'
    ),
    showlegend=False,
    plot_bgcolor='white',
    margin=dict(l=10, r=10, t=40, b=40),
    font=dict(weight='bold')
)

st.plotly_chart(fig_net, use_container_width=True)

# ==================== TOP 5 GANADORAS Y PERDEDORAS ====================
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("🏆 Top 5 Ganancias Netas")
    top_g = net_df[net_df["Cambio Neto (ha)"] > 0].head(5)
    if not top_g.empty:
        display_df = top_g[["Cobertura", "Cambio Neto (ha)"]].copy()
        display_df["Cambio Neto (ha)"] = display_df["Cambio Neto (ha)"].apply(lambda x: f"{x:,.0f}")
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("No hay coberturas con ganancias netas")

with col_b:
    st.subheader("📉 Top 5 Pérdidas Netas")
    top_l = net_df[net_df["Cambio Neto (ha)"] < 0].nsmallest(5, "Cambio Neto (ha)")
    if not top_l.empty:
        display_df = top_l[["Cobertura", "Cambio Neto (ha)"]].copy()
        display_df["Cambio Neto (ha)"] = display_df["Cambio Neto (ha)"].apply(lambda x: f"{x:,.0f}")
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("No hay coberturas con pérdidas netas")

# ==================== DIAGRAMA DE SANKEY ====================
st.subheader(f"🔄 Flujos de Transición (Sankey) - {year_start} → {year_end}")

max_val = int(df.values.max()) if df.values.max() > 0 else 50000
threshold = st.slider(
    "Mostrar solo flujos mayores a (ha)", 
    min_value=0, 
    max_value=max_val,
    value=min(500, max_val), 
    step=100,
    help="Filtra transiciones pequeñas para mejorar la visualización"
)

sources, targets, values, link_colors = [], [], [], []
labels = df.index.tolist()
node_colors = [coverage_colors.get(label, '#BDBDBD') for label in labels]

for i in range(len(labels)):
    for j in range(len(labels)):
        if i != j:
            val = df.iloc[i, j]
            if val > threshold:
                sources.append(i)
                targets.append(j)
                values.append(val)
                link_colors.append(coverage_colors.get(labels[i], '#BDBDBD'))

if len(sources) > 0:
    fig_sankey = go.Figure(data=[go.Sankey(
        node=dict(
            pad=20,
            thickness=25,
            line=dict(color="black", width=0.8),
            label=labels,
            color=node_colors,
            hovertemplate='<b>%{label}</b><br>Total: %{value:,.0f} ha<extra></extra>'
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color=link_colors,
            hovertemplate=f'<b>%{{source.label}}</b> → <b>%{{target.label}}</b><br>'
                         f'Área: %{{value:,.0f}} ha<br>'
                         f'Porcentaje: %{{value:.1f}}%<extra></extra>'
        )
    )])
    
    fig_sankey.update_layout(
        height=1000,
        font=dict(size=24, weight='bold', color='black', family='Arial'),
        title=dict(
            text=f"Principales transiciones entre coberturas (hectáreas) - {year_start} → {year_end}",
            font=dict(size=32, weight='bold', color='black')
        ),
        hoverlabel=dict(bgcolor="white", font_size=24, font_family="Arial", font_weight='bold')
    )
    
    st.plotly_chart(fig_sankey, use_container_width=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Transiciones mostradas", len(sources))
    with col2:
        st.metric("Total área en transiciones", f"{sum(values):,.0f} ha")
    with col3:
        if sum(values) > 0:
            st.metric("Flujo promedio", f"{sum(values) / len(sources):,.0f} ha")
else:
    st.warning(f"No hay transiciones mayores a {threshold:,.0f} hectáreas. Reduce el umbral para ver más flujos.")

# ==================== MATRIZ COMPLETA CON HEATMAP ====================
with st.expander("📋 Matriz Completa de Transiciones - Heatmap Interactivo", expanded=False):
    
    fig_heat = px.imshow(
        df,
        text_auto=True,
        color_continuous_scale="RdBu_r",
        aspect="auto",
        labels=dict(x=f"Cobertura en {year_end}", y=f"Cobertura en {year_start}", color="Hectáreas"),
        title=f"Matriz de Transiciones {year_start} → {year_end}"
    )
    
    fig_heat.update_traces(
        texttemplate='%{z:,.0f}',
        textfont=dict(size=20, color='black', weight='bold'),
        hovertemplate=f'<b>%{{y}}</b> → <b>%{{x}}</b><br>Área: %{{z:,.0f}} ha<extra></extra>'
    )
    
    fig_heat.update_layout(
        height=1000,
        font=dict(size=22, weight='bold'),
        xaxis=dict(tickangle=45, tickfont=dict(size=20, weight='bold')),
        yaxis=dict(tickfont=dict(size=20, weight='bold')),
        title_font=dict(size=28, weight='bold')
    )
    
    st.plotly_chart(fig_heat, use_container_width=True)
    
    st.info(f"""
    **Resumen de la matriz:**
    - Total de transiciones positivas: {df[df > 0].count().sum():,}
    - Total de transiciones negativas: {df[df < 0].count().sum():,}
    - Valor máximo de transición: {df.max().max():,.0f} ha
    - Valor mínimo de transición: {df.min().min():,.0f} ha
    """)

# ==================== TABLA DE CAMBIOS NETOS ====================
st.subheader("📊 Tabla Completa de Cambios Netos")

summary_table = pd.DataFrame({
    "Cobertura": net_change.index,
    "Cambio Neto (ha)": net_change.values,
    "Porcentaje del total": (net_change.values / net_change.abs().sum() * 100).round(2)
})
summary_table = summary_table.sort_values("Cambio Neto (ha)", ascending=False)

def color_negative_red(val):
    if isinstance(val, (int, float)):
        if val > 0:
            return 'color: #00CC96'
        elif val < 0:
            return 'color: #EF553B'
    return ''

styled_table = summary_table.style.format({
    "Cambio Neto (ha)": "{:,.0f}",
    "Porcentaje del total": "{:.2f}%"
}).map(color_negative_red, subset=["Cambio Neto (ha)"])

st.dataframe(styled_table, use_container_width=True, height=400)

# ==================== DESCARGA DE DATOS ====================
st.subheader("⬇️ Exportar Resultados")

col_download1, col_download2, col_download3 = st.columns(3)

with col_download1:
    csv_net = summary_table.to_csv(index=False).encode('utf-8')
    st.download_button(
        label=f"📥 Cambios Netos ({year_start}-{year_end}).csv",
        data=csv_net,
        file_name=f"cambios_netos_{year_start}_{year_end}.csv",
        mime="text/csv",
        use_container_width=True
    )

with col_download2:
    csv_matrix = df.to_csv().encode('utf-8')
    st.download_button(
        label=f"📥 Matriz Completa ({year_start}-{year_end}).csv",
        data=csv_matrix,
        file_name=f"matriz_transiciones_{year_start}_{year_end}.csv",
        mime="text/csv",
        use_container_width=True
    )

with col_download3:
    stats_df = pd.DataFrame({
        "Métrica": [
            "Total coberturas",
            "Total área que cambió (ha)",
            "Total ganancias (ha)",
            "Total pérdidas (ha)",
            "Balance neto (ha)",
            "Coberturas ganadoras",
            "Coberturas perdedoras",
            "Mayor ganancia (ha)",
            "Mayor pérdida (ha)"
        ],
        "Valor": [
            len(df),
            f"{total_changed:,.0f}",
            f"{total_positive_changes:,.0f}",
            f"{total_changed:,.0f}",
            f"{net_change.sum():+,.0f}",
            (net_change > 0).sum(),
            (net_change < 0).sum(),
            f"{net_change.max():+,.0f}",
            f"{net_change.min():+,.0f}"
        ]
    })
    csv_stats = stats_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label=f"📥 Estadísticas ({year_start}-{year_end}).csv",
        data=csv_stats,
        file_name=f"estadisticas_{year_start}_{year_end}.csv",
        mime="text/csv",
        use_container_width=True
    )

# ==================== PIE DE PÁGINA ====================
st.divider()
st.caption(f"""
**🌳 Tablero de Análisis de Cobertura del Suelo** | Datos: {year_start} → {year_end}  
🎨 Colores mejorados y más vibrantes por tipo de cobertura | Textos en negrita y tamaño aumentado para mejor visibilidad  
📌 Los valores positivos indican ganancias de área, los negativos pérdidas  
🔄 Actualiza el Excel y reinicia la app para nuevos análisis
""")

# Información técnica
with st.expander("ℹ️ Información técnica"):
    st.markdown("**Dependencias requeridas:**")
    st.code("pip install streamlit pandas plotly numpy openpyxl", language="bash")
    st.markdown("**Estructura del archivo Excel:**")
    st.markdown("- Hoja llamada: `Hoja1`")
    st.markdown("- Formato: Matriz cuadrada donde filas = coberturas en el año inicial, columnas = coberturas en el año final")
    st.markdown("- Valores: Hectáreas de transición")
    st.markdown("**Detección de años:**")
    st.markdown("Los años se extraen automáticamente del nombre del archivo (ej. `2023-2024.xlsx`, `2020_2021_datos.xlsx`). Si no se detectan, puedes ingresarlos manualmente en la barra lateral.")
    st.markdown("**Ejecutar la app:**")
    st.code("streamlit run app.py", language="bash")
