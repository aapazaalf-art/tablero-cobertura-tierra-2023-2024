import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# Configuración de la página
st.set_page_config(page_title="Cambios Cobertura 2023-2024", layout="wide", page_icon="🌳")

# Título y descripción
st.title("🌳 Tablero Ejecutivo: Cambios en Cobertura del Suelo 2023-2024")
st.markdown("**Análisis de transiciones 2023 → 2024** | Ganancias (+) y Pérdidas (-) en hectáreas")

# ==================== DEFINICIÓN DE COLORES POR TIPO DE COBERTURA ====================
def get_coverage_colors(coverage_names):
    """
    Asigna colores según el tipo de cobertura del suelo
    """
    color_map = {}
    
    for name in coverage_names:
        name_lower = str(name).lower()
        
        # Bosques y vegetación natural
        if any(word in name_lower for word in ['bosque', 'forest', 'selva', 'jungla']):
            color_map[name] = '#2E8B57'  # Verde marino
        elif any(word in name_lower for word in ['arbusto', 'matorral', 'shrub']):
            color_map[name] = '#228B22'  # Verde bosque
        elif any(word in name_lower for word in ['pastizal', 'pasture', 'herbácea']):
            color_map[name] = '#9ACD32'  # Verde amarillento
            
        # Áreas agrícolas
        elif any(word in name_lower for word in ['agrícola', 'agriculture', 'cultivo', 'crop']):
            color_map[name] = '#FFD700'  # Dorado
        elif any(word in name_lower for word in ['pasto', 'ganadero', 'livestock']):
            color_map[name] = '#DAA520'  # Oro viejo
            
        # Áreas urbanas e infraestructura
        elif any(word in name_lower for word in ['urbano', 'urban', 'ciudad', 'city']):
            color_map[name] = '#FF6347'  # Rojo tomate
        elif any(word in name_lower for word in ['infraestructura', 'infrastructure', 'carretera']):
            color_map[name] = '#8B4513'  # Marrón silla
            
        # Cuerpos de agua
        elif any(word in name_lower for word in ['agua', 'water', 'río', 'river', 'lago', 'lake']):
            color_map[name] = '#4169E1'  # Azul real
        elif any(word in name_lower for word in ['humedal', 'wetland']):
            color_map[name] = '#4682B4'  # Azul acero
            
        # Suelos desnudos o erosionados
        elif any(word in name_lower for word in ['suelo', 'soil', 'desnudo', 'bare', 'erosion']):
            color_map[name] = '#D2B48C'  # Marrón claro
        elif any(word in name_lower for word in ['minería', 'mining']):
            color_map[name] = '#A0522D'  # Marrón siesta
            
        # Áreas protegidas
        elif any(word in name_lower for word in ['protegido', 'protected', 'reserva']):
            color_map[name] = '#3CB371'  # Verde medio
            
        # Por defecto
        else:
            color_map[name] = '#808080'  # Gris
    
    return color_map

# ==================== CARGA DE DATOS ====================
st.sidebar.header("📁 Carga de datos")
uploaded_file = st.sidebar.file_uploader("Subir nueva matriz Excel", type=["xlsx"])

try:
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file, sheet_name="Hoja1", index_col=0)
        st.sidebar.success("✅ Archivo cargado correctamente")
    else:
        df = pd.read_excel("data/2023 - 2024.xlsx", sheet_name="Hoja1", index_col=0)
        st.sidebar.info("Usando archivo local en /data")
    
    # Limpiar datos
    df = df.fillna(0)
    
    # Verificar que la matriz no esté vacía
    if df.empty or df.shape[0] == 0 or df.shape[1] == 0:
        st.error("❌ La matriz de datos está vacía o es inválida")
        st.stop()
        
except FileNotFoundError:
    st.error("❌ No se encontró el archivo Excel. Por favor, sube uno usando el botón en la barra lateral.")
    st.info("📌 El archivo debe contener una hoja llamada 'Hoja1' con una matriz de transiciones donde las filas son coberturas en 2023 y las columnas en 2024")
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

# ==================== GRÁFICO DE CAMBIO NETO ====================
st.subheader("📈 Cambio Neto por Cobertura (hectáreas)")

net_df = pd.DataFrame({
    "Cobertura": net_change.index,
    "Cambio Neto (ha)": net_change.values
}).sort_values("Cambio Neto (ha)", ascending=False)

# Obtener colores para las coberturas
coverage_colors = get_coverage_colors(net_df["Cobertura"].tolist())
net_df["Color"] = net_df["Cobertura"].map(coverage_colors)

# Crear gráfico de barras con colores personalizados
fig_net = px.bar(
    net_df, 
    x="Cambio Neto (ha)", 
    y="Cobertura", 
    orientation="h",
    color="Cobertura",
    color_discrete_map=coverage_colors,
    height=700,
    text="Cambio Neto (ha)"  # Agregar valores en las barras
)

# Mejorar formato del gráfico
fig_net.update_traces(
    texttemplate='%{text:,.0f} ha',
    textposition='outside',
    textfont=dict(size=10, color='black')
)
fig_net.update_layout(
    yaxis=dict(
        categoryorder="total ascending",
        title="Cobertura del Suelo",
        title_font_size=14,
        tickfont_size=11
    ),
    xaxis=dict(
        title="Cambio Neto (hectáreas)",
        title_font_size=14,
        tickfont_size=11,
        gridcolor='lightgray'
    ),
    showlegend=False,
    plot_bgcolor='white',
    height=700,
    margin=dict(l=10, r=10, t=40, b=40)
)

st.plotly_chart(fig_net, use_container_width=True)

# ==================== TOP 5 GANADORAS Y PERDEDORAS ====================
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("🏆 Top 5 Ganancias Netas")
    top_g = net_df[net_df["Cambio Neto (ha)"] > 0].head(5)
    if not top_g.empty:
        # Formatear para mostrar
        display_df = top_g[["Cobertura", "Cambio Neto (ha)"]].copy()
        display_df["Cambio Neto (ha)"] = display_df["Cambio Neto (ha)"].apply(lambda x: f"{x:,.0f}")
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No hay coberturas con ganancias netas")

with col_b:
    st.subheader("📉 Top 5 Pérdidas Netas")
    top_l = net_df[net_df["Cambio Neto (ha)"] < 0].nsmallest(5, "Cambio Neto (ha)")
    if not top_l.empty:
        display_df = top_l[["Cobertura", "Cambio Neto (ha)"]].copy()
        display_df["Cambio Neto (ha)"] = display_df["Cambio Neto (ha)"].apply(lambda x: f"{x:,.0f}")
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No hay coberturas con pérdidas netas")

# ==================== DIAGRAMA DE SANKEY MEJORADO ====================
st.subheader("🔄 Flujos de Transición (Sankey)")

# Slider para umbral
threshold = st.slider(
    "Mostrar solo flujos mayores a (ha)", 
    min_value=0, 
    max_value=int(df.values.max()) if df.values.max() > 0 else 50000,
    value=500, 
    step=100,
    help="Filtra transiciones pequeñas para mejorar la visualización"
)

# Preparar datos para Sankey
sources, targets, values, link_colors = [], [], [], []
labels = df.index.tolist()

# Obtener colores para nodos
node_colors = [coverage_colors.get(label, '#808080') for label in labels]

for i in range(len(labels)):
    for j in range(len(labels)):
        if i != j:
            val = df.iloc[i, j]
            if val > threshold:  # Transición positiva (pérdida para i, ganancia para j)
                sources.append(i)
                targets.append(j)
                values.append(val)
                # Color del enlace basado en la cobertura de origen
                link_colors.append(coverage_colors.get(labels[i], '#808080'))

# Verificar si hay datos para mostrar
if len(sources) > 0:
    # Crear Sankey con colores personalizados
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
            hovertemplate='<b>%{source.label}</b> → <b>%{target.label}</b><br>'
                         'Área: %{value:,.0f} ha<br>'
                         'Porcentaje del total: %{value:.1f}%<extra></extra>'
        )
    )])
    
    # Mejorar diseño
    fig_sankey.update_layout(
        height=800,
        font=dict(size=12, color='black', family='Arial'),
        title=dict(
            text="Principales transiciones entre coberturas (hectáreas)",
            font=dict(size=16, color='black')
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Arial"
        )
    )
    
    st.plotly_chart(fig_sankey, use_container_width=True)
    
    # Mostrar estadísticas del Sankey
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Transiciones mostradas", len(sources), help="Número de flujos visibles")
    with col2:
        st.metric("Total área en transiciones", f"{sum(values):,.0f} ha", help="Suma de todas las transiciones mostradas")
    with col3:
        if sum(values) > 0:
            avg_flow = sum(values) / len(sources)
            st.metric("Flujo promedio", f"{avg_flow:,.0f} ha", help="Área promedio por transición")
else:
    st.warning(f"No hay transiciones mayores a {threshold:,.0f} hectáreas. Reduce el umbral para ver más flujos.")

# ==================== MATRIZ COMPLETA CON HEATMAP ====================
with st.expander("📋 Matriz Completa de Transiciones - Heatmap Interactivo", expanded=False):
    
    # Preparar datos para heatmap
    heatmap_data = df.copy()
    
    # Crear heatmap mejorado
    fig_heat = px.imshow(
        heatmap_data,
        text_auto=True,  # Mostrar valores en celdas
        color_continuous_scale="RdBu_r",
        aspect="auto",
        labels=dict(x="Cobertura en 2024", y="Cobertura en 2023", color="Hectáreas"),
        title="Matriz de Transiciones 2023 → 2024"
    )
    
    # Mejorar visualización del heatmap
    fig_heat.update_traces(
        texttemplate='%{z:,.0f}',
        textfont=dict(size=10, color='black'),
        hovertemplate='<b>%{y}</b> → <b>%{x}</b><br>Área: %{z:,.0f} ha<extra></extra>'
    )
    
    fig_heat.update_layout(
        height=800,
        font=dict(size=11),
        xaxis=dict(tickangle=45, tickfont=dict(size=10)),
        yaxis=dict(tickfont=dict(size=10))
    )
    
    st.plotly_chart(fig_heat, use_container_width=True)
    
    # Mostrar estadísticas de la matriz
    st.info(f"""
    📊 **Resumen de la matriz:**
    - Total de transiciones positivas: {df[df > 0].count().sum():,}
    - Total de transiciones negativas: {df[df < 0].count().sum():,}
    - Valor máximo de transición: {df.max().max():,.0f} ha
    - Valor mínimo de transición: {df.min().min():,.0f} ha
    """)

# ==================== TABLA DE CAMBIOS NETA CON FORMATO ====================
st.subheader("📊 Tabla Completa de Cambios Netos")

# Crear tabla formateada
summary_table = pd.DataFrame({
    "Cobertura": net_change.index,
    "Cambio Neto (ha)": net_change.values,
    "Porcentaje del total": (net_change.values / net_change.abs().sum() * 100).round(2)
})
summary_table = summary_table.sort_values("Cambio Neto (ha)", ascending=False)

# Formato condicional con colores
def color_negative_red(val):
    """Aplica color rojo a valores negativos y verde a positivos"""
    if isinstance(val, (int, float)):
        if val > 0:
            return 'color: #00CC96'
        elif val < 0:
            return 'color: #EF553B'
    return ''

styled_table = summary_table.style.format({
    "Cambio Neto (ha)": "{:,.0f}",
    "Porcentaje del total": "{:.2f}%"
}).applymap(color_negative_red, subset=["Cambio Neto (ha)"])

st.dataframe(styled_table, use_container_width=True, height=400)

# ==================== DESCARGA DE DATOS ====================
st.subheader("⬇️ Exportar Resultados")

col_download1, col_download2, col_download3 = st.columns(3)

with col_download1:
    # Descargar cambios netos
    csv_net = summary_table.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Cambios Netos (CSV)",
        data=csv_net,
        file_name="cambios_netos_2023-2024.csv",
        mime="text/csv",
        use_container_width=True
    )

with col_download2:
    # Descargar matriz completa
    csv_matrix = df.to_csv().encode('utf-8')
    st.download_button(
        label="📥 Matriz Completa (CSV)",
        data=csv_matrix,
        file_name="matriz_transiciones_2023-2024.csv",
        mime="text/csv",
        use_container_width=True
    )

with col_download3:
    # Descargar resumen estadístico
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
        label="📥 Estadísticas (CSV)",
        data=csv_stats,
        file_name="estadisticas_2023-2024.csv",
        mime="text/csv",
        use_container_width=True
    )

# ==================== PIE DE PÁGINA ====================
st.divider()
st.caption("""
**🌳 Tablero de Análisis de Cobertura del Suelo** | Datos: 2023 → 2024  
🎨 Colores por tipo de cobertura: Verde (bosques/vegetación) | Amarillo (agrícola) | Rojo (urbano) | Azul (agua) | Marrón (suelo/minería)  
📌 Los valores positivos indican ganancias de área, los negativos pérdidas  
🔄 Actualiza el Excel y reinicia la app para nuevos análisis
""")

# Información de dependencias
with st.expander("ℹ️ Información técnica"):
    st.markdown("""
    **Dependencias requeridas:**
    ```bash
    pip install streamlit pandas plotly numpy openpyxl
