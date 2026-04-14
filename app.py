import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="Cambios Cobertura 2023-2024", layout="wide", page_icon="🌳")

st.title("🌳 Tablero Ejecutivo: Cambios en Cobertura del Suelo 2023-2024")
st.markdown("**Análisis de transiciones 2023 → 2024** | Ganancias (+) y Pérdidas (-) en hectáreas")

# Cargar datos
st.sidebar.header("📁 Carga de datos")
uploaded_file = st.sidebar.file_uploader("Subir nueva matriz Excel", type=["xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file, sheet_name="Hoja1", index_col=0)
    st.sidebar.success("✅ Archivo cargado correctamente")
else:
    try:
        df = pd.read_excel("data/2023 - 2024.xlsx", sheet_name="Hoja1", index_col=0)
        st.sidebar.info("Usando archivo local en /data")
    except FileNotFoundError:
        st.error("❌ No se encontró el archivo Excel. Sube uno o colócalo en la carpeta data/")
        st.stop()

df = df.fillna(0)

# Crear paleta de colores única por cobertura
n_categorias = len(df.index)
if n_categorias <= 12:
    colores_base = px.colors.qualitative.Pastel
else:
    colores_base = px.colors.qualitative.Set3

color_dict = {categoria: colores_base[i % len(colores_base)] 
              for i, categoria in enumerate(df.index)}

# Cálculos
net_change = df.sum(axis=1).round(2)
total_changed = abs(df.values[df.values < 0].sum()).round(0)

st.sidebar.metric("Área total que cambió", f"{total_changed:,.0f} ha")

# Métricas
col1, col2, col3 = st.columns(3)
col1.metric("Coberturas", len(df))
col2.metric("Ganadoras netas", (net_change > 0).sum())
col3.metric("Perdedoras netas", (net_change < 0).sum())

# Cambio Neto con colores por cobertura y valores visibles
st.subheader("📈 Cambio Neto por Cobertura (hectáreas)")
net_df = pd.DataFrame({
    "Cobertura": net_change.index,
    "Cambio Neto (ha)": net_change.values
}).sort_values("Cambio Neto (ha)", ascending=False)

fig_net = px.bar(
    net_df, x="Cambio Neto (ha)", y="Cobertura", orientation="h",
    color="Cobertura",
    color_discrete_map=color_dict,
    text="Cambio Neto (ha)",  # Mostrar valores en las barras
    height=700
)
fig_net.update_traces(
    marker_line_color='black', 
    marker_line_width=1.5,
    texttemplate='%{text:,.0f} ha',  # Formato de los valores
    textposition='outside'  # Posición del texto fuera de la barra
)
fig_net.update_layout(
    yaxis=dict(categoryorder="total ascending"), 
    showlegend=False,
    plot_bgcolor='white',
    paper_bgcolor='white',
    font=dict(color='black', size=12),
    xaxis_title="Cambio Neto (hectáreas)",
    yaxis_title="Tipo de Cobertura"
)
fig_net.update_xaxes(title_font_color='black', tickfont_color='black')
fig_net.update_yaxes(title_font_color='black', tickfont_color='black')
st.plotly_chart(fig_net, use_container_width=True)

# Top 5
col_a, col_b = st.columns(2)
with col_a:
    st.subheader("🏆 Top 5 Ganadoras")
    top_g = net_df[net_df["Cambio Neto (ha)"] > 0].head(5)
    st.dataframe(top_g.style.format({"Cambio Neto (ha)": "{:,.0f}"}).background_gradient(cmap="Greens"), use_container_width=True)
with col_b:
    st.subheader("📉 Top 5 Perdedoras")
    top_l = net_df[net_df["Cambio Neto (ha)"] < 0].nsmallest(5, "Cambio Neto (ha)")
    st.dataframe(top_l.style.format({"Cambio Neto (ha)": "{:,.0f}"}).background_gradient(cmap="Reds_r"), use_container_width=True)

# Sankey - Diagrama de Flujos con colores coherentes
st.subheader("🔄 Flujos de Transición (Sankey)")
threshold = st.slider("Mostrar solo flujos mayores a (ha)", 0, 50000, 500, step=100)

sources, targets, values = [], [], []
labels = df.index.tolist()

for i in range(len(labels)):
    for j in range(len(labels)):
        if i != j:
            val = df.iloc[i, j]
            if val < -threshold:
                sources.append(i)
                targets.append(j)
                values.append(-val)

# Preparar colores para nodos y enlaces
node_colors = [color_dict[label] for label in labels]

# Para los enlaces: usar el color del nodo origen con opacidad
link_colors = []
for src_idx in sources:
    src_color = node_colors[src_idx]
    # Convertir a rgba con opacidad 0.6
    if src_color.startswith('rgb'):
        link_colors.append(src_color.replace('rgb', 'rgba').replace(')', ', 0.6)'))
    elif src_color.startswith('#'):
        # Convertir hex a rgba
        r = int(src_color[1:3], 16)
        g = int(src_color[3:5], 16)
        b = int(src_color[5:7], 16)
        link_colors.append(f'rgba({r}, {g}, {b}, 0.6)')
    else:
        link_colors.append('rgba(31, 119, 180, 0.6)')

# Preparar etiquetas de nodos con valores totales
total_por_nodo = df.sum(axis=1).abs() + df.sum(axis=0).abs()
node_labels = [f"{label}<br>({total_por_nodo[label]:,.0f} ha)" for label in labels]

# Crear el Sankey con posiciones predefinidas para mejor visualización
# Calcular posiciones basadas en cambio neto
node_x = []
node_y = []
for i, categoria in enumerate(labels):
    if net_change[categoria] > 0:  # Ganadoras a la derecha
        node_x.append(0.8)
    else:  # Perdedoras a la izquierda
        node_x.append(0.2)
    # Distribuir verticalmente
    node_y.append(i / (len(labels) - 1) if len(labels) > 1 else 0.5)

fig_sankey = go.Figure(data=[go.Sankey(
    node=dict(
        pad=20,
        thickness=25,
        line=dict(color="black", width=1.5),
        label=node_labels,
        color=node_colors,
        x=node_x,  # Posiciones X predefinidas
        y=node_y   # Posiciones Y predefinidas
    ),
    link=dict(
        source=sources,
        target=targets,
        value=values,
        color=link_colors,
        hovertemplate='<b>De: %{source.label}</b><br>' +
                      '<b>A: %{target.label}</b><br>' +
                      '<b>Área: %{value:,.0f} ha</b><br>' +
                      '<extra></extra>'
    )
)])

fig_sankey.update_layout(
    height=800,
    font=dict(size=11, color='black', family='Arial'),
    title=dict(
        text="Principales transiciones de cobertura (hectáreas)",
        font=dict(size=16, color='black'),
        x=0.5
    ),
    plot_bgcolor='white',
    paper_bgcolor='white',
    hoverlabel=dict(bgcolor="white", font_size=12, font_family="Arial")
)

st.plotly_chart(fig_sankey, use_container_width=True)

# Heatmap con nombres completos y valores visibles
with st.expander("📋 Matriz Completa - Heatmap"):
    # Mostrar nombres completos en el heatmap con valores
    fig_heat = px.imshow(
        df, 
        color_continuous_scale="RdBu_r", 
        aspect="auto",
        labels=dict(x="Hacia 2024", y="Desde 2023"),
        text_auto='.0f'  # Mostrar valores numéricos en cada celda
    )
    fig_heat.update_layout(
        height=800,
        font=dict(size=10, color='black'),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    fig_heat.update_traces(
        texttemplate='%{text:,.0f}',
        textfont=dict(size=9, color='black')
    )
    fig_heat.update_xaxes(tickangle=45, tickfont=dict(size=9))
    fig_heat.update_yaxes(tickfont=dict(size=9))
    st.plotly_chart(fig_heat, use_container_width=True)

# Gráfico de matriz de transiciones (versión alternativa con valores)
with st.expander("📊 Matriz de Transiciones - Barras Apiladas"):
    st.markdown("**Transiciones desde cada cobertura en 2023 hacia 2024**")
    
    # Crear gráfico de barras apiladas para visualizar transiciones
    df_transitions = df.copy()
    df_transitions = df_transitions.apply(lambda x: -x)  # Convertir a positivos para visualización
    
    fig_stack = px.bar(
        df_transitions,
        x=df_transitions.index,
        y=df_transitions.columns,
        title="Distribución de transiciones por cobertura de origen",
        labels={"value": "Hectáreas transformadas", "variable": "Hacia 2024"},
        text_auto='.0f'
    )
    fig_stack.update_layout(
        height=600,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='black', size=11),
        xaxis_title="Cobertura de origen (2023)",
        yaxis_title="Hectáreas transformadas"
    )
    fig_stack.update_traces(
        texttemplate='%{text:,.0f}',
        textposition='inside',
        textfont=dict(size=9, color='white')
    )
    st.plotly_chart(fig_stack, use_container_width=True)

# Descarga
st.download_button(
    "⬇️ Descargar cambios netos (CSV)",
    net_df.to_csv(index=False).encode("utf-8"),
    "cambios_netos_2023-2024.csv",
    "text/csv"
)

# Descargar matriz completa
csv_matrix = df.copy()
csv_matrix['Tipo'] = csv_matrix.index
csv_matrix = csv_matrix.reset_index(drop=False)
st.download_button(
    "⬇️ Descargar matriz completa (CSV)",
    csv_matrix.to_csv(index=False).encode("utf-8"),
    "matriz_transiciones_2023-2024.csv",
    "text/csv"
)

st.caption("📊 Tablero generado con Streamlit + Plotly • Cada cobertura tiene un color único • Valores numéricos visibles en todos los gráficos")
