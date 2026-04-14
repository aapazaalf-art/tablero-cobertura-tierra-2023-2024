import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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

# Cálculos
net_change = df.sum(axis=1).round(2)
total_changed = abs(df.values[df.values < 0].sum()).round(0)

st.sidebar.metric("Área total que cambió", f"{total_changed:,.0f} ha")

# Métricas
col1, col2, col3 = st.columns(3)
col1.metric("Coberturas", len(df))
col2.metric("Ganadoras netas", (net_change > 0).sum())
col3.metric("Perdedoras netas", (net_change < 0).sum())

# Cambio Neto
st.subheader("📈 Cambio Neto por Cobertura (hectáreas)")
net_df = pd.DataFrame({
    "Cobertura": net_change.index,
    "Cambio Neto (ha)": net_change.values
}).sort_values("Cambio Neto (ha)", ascending=False)

fig_net = px.bar(
    net_df, x="Cambio Neto (ha)", y="Cobertura", orientation="h",
    color=net_df["Cambio Neto (ha)"] > 0,
    color_discrete_map={True: "#00CC96", False: "#EF553B"},
    height=700
)
fig_net.update_layout(yaxis=dict(categoryorder="total ascending"), showlegend=False)
st.plotly_chart(fig_net, use_container_width=True)

# Top 5
col_a, col_b = st.columns(2)
with col_a:
    st.subheader("🏆 Top 5 Ganadoras")
    top_g = net_df[net_df["Cambio Neto (ha)"] > 0].head(5)
# Reemplaza la línea 61 con:
def color_texto(valor):
    """Cambia color del texto según el valor"""
    if isinstance(valor, (int, float)):
        if valor > 0:
            return 'color: green'
        elif valor < 0:
            return 'color: red'
    return ''

styled_df = top_g.style.format({"Cambio Neto (ha)": "{:,.0f}"}).applymap(color_texto, subset=["Cambio Neto (ha)"])
st.dataframe(styled_df, use_container_width=True)
with col_b:
    st.subheader("📉 Top 5 Perdedoras")
    top_l = net_df[net_df["Cambio Neto (ha)"] < 0].nsmallest(5, "Cambio Neto (ha)")
    st.dataframe(top_l.style.format({"Cambio Neto (ha)": "{:,.0f}"}).background_gradient(cmap="Reds_r"), use_container_width=True)

# Sankey - Diagrama de Flujos
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

fig_sankey = go.Figure(data=[go.Sankey(
    node=dict(pad=15, thickness=20, line=dict(color="black", width=0.5),
              label=labels, color="#1f77b4"),
    link=dict(source=sources, target=targets, value=values, color="rgba(31, 119, 180, 0.5)")
)])
fig_sankey.update_layout(height=780, font_size=11,
                         title="Principales transiciones de cobertura (ha)")
st.plotly_chart(fig_sankey, use_container_width=True)

# Heatmap
with st.expander("📋 Matriz Completa - Heatmap"):
    fig_heat = px.imshow(df, color_continuous_scale="RdBu_r", aspect="auto",
                         labels=dict(x="Hacia 2024", y="Desde 2023"))
    fig_heat.update_layout(height=800)
    st.plotly_chart(fig_heat, use_container_width=True)

# Descarga
st.download_button(
    "⬇️ Descargar cambios netos (CSV)",
    net_df.to_csv(index=False).encode("utf-8"),
    "cambios_netos_2023-2024.csv",
    "text/csv"
)

st.caption("Tablero generado con Streamlit + Plotly • Actualiza el Excel y reinicia la app")
