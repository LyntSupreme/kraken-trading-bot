import time
import streamlit as st
import plotly.graph_objects as go
from data_engine import obtener_datos
from risk_manager import calcular_tamano_posicion
from execution_engine import ejecutar_orden_real

# Configuración de la página web
st.set_page_config(page_title="Kraken Multi-Currency Bot", page_icon="🤖", layout="wide")

st.title("🤖 Kraken Multi-Currency Trading Bot - Panel Autónomo")
st.markdown("Monitoreo y ejecución automática de estrategia Dual-EMA en múltiples pares.")

# --- BARRA LATERAL: SELECCIÓN DE DIVISAS ---
st.sidebar.header("⚙️ Configuración de Pares")
pares_disponibles = [
    'BTC/USD', 'ETH/USD', 'SOL/USD', 'ADA/USD', 
    'XRP/USD', 'DOT/USD', 'MATIC/USD', 'LINK/USD', 
    'AVAX/USD', 'LTC/USD', 'BCH/USD', 'UNI/USD'
]
simbolo_seleccionado = st.sidebar.selectbox("Selecciona la divisa a operar:", pares_disponibles)

# Botón para actualizar datos manualmente
if st.button("🔄 Actualizar Datos del Mercado"):
    st.rerun()

# 1. Obtener datos del motor para el par seleccionado
with st.spinner(f"Conectando con Kraken y descargando datos para {simbolo_seleccionado}..."):
    df = obtener_datos(simbolo=simbolo_seleccionado, timeframe='1h')

if df is not None:
    precio_actual = df['close'].iloc[-1]
    ema_200 = df['EMA_200'].iloc[-1]
    
    # Métricas visuales arriba
    col1, col2, col3 = st.columns(3)
    col1.metric(f"Precio Actual ({simbolo_seleccionado})", f"${precio_actual:,.4f}")
    col2.metric("EMA 200 (Tendencia)", f"${ema_200:,.4f}")
    
    if precio_actual > ema_200:
        col3.metric("Estado del Mercado", "TENDENCIA ALCISTA", "LONG HABILITADO", delta_color="normal")
    else:
        col3.metric("Estado del Mercado", "TENDENCIA BAJISTA", "FUERA DE MERCADO", delta_color="inverse")

    st.markdown("---")

    # 2. Gráfico interactivo de Velas y EMA usando Plotly
    st.subheader(f"Gráfico de Precios y Tendencia ({simbolo_seleccionado})")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['close'], mode='lines', name=f'Precio {simbolo_seleccionado}', line=dict(color='orange', width=2)))
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['EMA_200'], mode='lines', name='EMA 200', line=dict(color='blue', width=2, dash='dash')))
    
    fig.update_layout(
        xaxis_title="Fecha y Hora",
        yaxis_title="Precio en USD",
        template="plotly_dark",
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)

    # 3. Panel de Gestión de Riesgo y Piloto Automático
    st.markdown("---")
    st.subheader("🛡️ Gestión de Riesgo y Piloto Automático")
    
    col_a, col_b = st.columns(2)
    with col_a:
        capital_cuenta = st.number_input("Capital de la Cuenta (USD)", value=10000.0, step=500.0)
        porcentaje_riesgo = st.slider("Porcentaje de Riesgo por Trade", min_value=0.001, max_value=0.01, value=0.01, step=0.001, format="%.3f")
    
    with col_b:
        stop_loss_sugerido = precio_actual * 0.98  # 2% por defecto
        precio_sl_personalizado = st.number_input("Precio de Stop Loss", value=float(stop_loss_sugerido), step=0.01)

    # Calcular riesgo con los valores de la interfaz
    resultado_riesgo = calcular_tamano_posicion(
        capital_total=capital_cuenta,
        porcentaje_riesgo=porcentaje_riesgo,
        precio_entrada=precio_actual,
        precio_stop_loss=precio_sl_personalizado
    )

    if resultado_riesgo:
        st.success("Plan de orden calculado de forma segura bajo los límites establecidos.")
        r1, r2, r3 = st.columns(3)
        r1.metric("Riesgo Máximo en Dinero", f"${resultado_riesgo['riesgo_dinero']:,.2f}")
        r2.metric("Tamaño de Posición", f"{resultado_riesgo['tamaño_btc']:.5f} Unidades")
        r3.metric("Capital Involucrado en Orden", f"${resultado_riesgo['capital_involucrado']:,.2f}")

        st.markdown("---")
        st.subheader("⚡ Estado del Piloto Automático Multi-Divisa")

        # LÓGICA DE EJECUCIÓN AUTÓNOMA
        if precio_actual > ema_200:
            st.success(f"🤖 **Piloto Automático Activo:** {simbolo_seleccionado} en Tendencia Alcista. Enviando orden real a Kraken...")
            
            respuesta_orden = ejecutar_orden_real(
                simbolo=simbolo_seleccionado,
                tipo_operacion="BUY",
                tamaño_btc=resultado_riesgo['tamaño_btc']
            )
            
            if "error" in respuesta_orden:
                st.error(f"Error al ejecutar la orden autónoma: {respuesta_orden['error']}")
            else:
                st.info(f"¡Orden autónoma ejecutada con éxito para {simbolo_seleccionado}! ID: {respuesta_orden['id']}")
        else:
            st.warning(f"🛡️ **Piloto Automático en Espera:** {simbolo_seleccionado} está en tendencia bajista. El bot no abrirá operaciones.")

else:
    st.error(f"No se pudieron cargar los datos de Kraken para {simbolo_seleccionado}. Verifica tu conexión.")

# 4. Bucle de actualización automática en segundo plano (cada 60 segundos)
st.markdown("---")
st.write(f"🔄 Bot operando de forma autónoma sobre {simbolo_seleccionado}...")

TIEMPO_ESPERA = 60  
placeholder = st.empty()

for segundos_restantes in range(TIEMPO_ESPERA, 0, -1):
    placeholder.text(f"Próxima revisión de mercado en {segundos_restantes} segundos...")
    time.sleep(1)

st.rerun()
