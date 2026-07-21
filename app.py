import time
import streamlit as st
import plotly.graph_objects as go
from data_engine import obtener_datos
from risk_manager import calcular_tamano_posicion
from execution_engine import ejecutar_orden_real, obtener_conexion_kraken

# Configuración de la página web
st.set_page_config(page_title="Kraken Multi-Currency Bot", page_icon="🤖", layout="wide")

st.title("🤖 Kraken Multi-Currency Trading Bot - Panel Autónomo")
st.markdown("Monitoreo, ejecución automática y reportes de la estrategia Dual-EMA.")

# --- BARRA LATERAL: SELECCIÓN DE DIVISAS ---
st.sidebar.header("⚙️ Configuración de Pares")
pares_disponibles = [
    'BTC/USD', 'ETH/USD', 'SOL/USD', 'ADA/USD', 
    'XRP/USD', 'DOT/USD', 'MATIC/USD', 'LINK/USD', 
    'AVAX/USD', 'LTC/USD', 'BCH/USD', 'UNI/USD'
]
simbolo_seleccionado = st.sidebar.selectbox("Selecciona la divisa a operar:", pares_disponibles)

if st.button("🔄 Actualizar Datos del Mercado"):
    st.rerun()

# 1. Obtener datos del motor para el par seleccionado
with st.spinner(f"Conectando con Kraken y descargando datos para {simbolo_seleccionado}..."):
    df = obtener_datos(simbolo=simbolo_seleccionado, timeframe='1h')

if df is not None and not df.empty:
    precio_actual = float(df['close'].iloc[-1])
    ema_200 = float(df['EMA_200'].iloc[-1])
    
    # Métricas visuales
    col1, col2, col3 = st.columns(3)
    col1.metric(f"Precio Actual ({simbolo_seleccionado})", f"${precio_actual:,.4f}")
    col2.metric("EMA 200 (Tendencia)", f"${ema_200:,.4f}")
    
    if precio_actual > ema_200:
        col3.metric("Estado del Mercado", "TENDENCIA ALCISTA", "LONG HABILITADO", delta_color="normal")
    else:
        col3.metric("Estado del Mercado", "TENDENCIA BAJISTA", "FUERA DE MERCADO", delta_color="inverse")

    st.markdown("---")

    # 2. Gráfico interactivo
    st.subheader(f"Gráfico de Precios y Tendencia ({simbolo_seleccionado})")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['close'], mode='lines', name=f'Precio {simbolo_seleccionado}', line=dict(color='orange', width=2)))
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['EMA_200'], mode='lines', name='EMA 200', line=dict(color='blue', width=2, dash='dash')))
    
    fig.update_layout(
        xaxis_title="Fecha y Hora",
        yaxis_title="Precio en USD",
        template="plotly_dark",
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

    # 3. Panel de Gestión de Riesgo y Piloto Automático
    st.markdown("---")
    st.subheader("🛡️ Gestión de Riesgo y Piloto Automático")
    
    col_a, col_b = st.columns(2)
    with col_a:
        capital_cuenta = st.number_input("Capital de la Cuenta (USD)", value=20.0, step=5.0)
        porcentaje_riesgo = st.slider("Porcentaje de Riesgo por Trade", min_value=0.01, max_value=1.0, value=0.50, step=0.05, format="%.2f")
    
    with col_b:
        stop_loss_sugerido = precio_actual * 0.98 
        precio_sl_personalizado = st.number_input("Precio de Stop Loss", value=float(stop_loss_sugerido), step=0.01)

    resultado_riesgo = calcular_tamano_posicion(
        capital_total=capital_cuenta,
        porcentaje_riesgo=porcentaje_riesgo,
        precio_entrada=precio_actual,
        precio_stop_loss=precio_sl_personalizado
    )

    if resultado_riesgo:
        r1, r2, r3 = st.columns(3)
        r1.metric("Riesgo Máximo en Dinero", f"${resultado_riesgo['riesgo_dinero']:,.2f}")
        r2.metric("Tamaño de Posición", f"{resultado_riesgo['tamaño_btc']:.5f} Unidades")
        r3.metric("Capital Involucrado", f"${resultado_riesgo['capital_involucrado']:,.2f}")

        st.markdown("---")
        st.subheader("⚡ Estado del Piloto Automático y Ejecución")

        if precio_actual > ema_200:
            st.success(f"🤖 **Piloto Automático Activo:** {simbolo_seleccionado} en Tendencia Alcista. Enviando orden a Kraken...")
            
            respuesta_orden = ejecutar_orden_real(
                simbolo=simbolo_seleccionado,
                tipo_operacion="BUY",
                tamaño_btc=resultado_riesgo['tamaño_btc']
            )
            
            if not respuesta_orden or "error" in respuesta_orden:
                error_msg = respuesta_orden.get('error', 'Error desconocido') if respuesta_orden else 'Respuesta vacía'
                st.error(f"Aviso de ejecución: {error_msg}")
            else:
                st.info(f"¡Orden procesada en Kraken! ID: {respuesta_orden.get('id', 'N/A')}")
        else:
            st.warning(f"🛡️ **Piloto Automático en Espera:** {simbolo_seleccionado} está en tendencia bajista.")

else:
    st.error(f"No se pudieron cargar los datos de Kraken para {simbolo_seleccionado}.")

# --- REPORTES Y BALANCE DIRECTO DE KRAKEN ---
st.markdown("---")
st.subheader("📊 Reportes y Estado de Operaciones en Kraken")

if st.button("📥 Consultar Balance y Órdenes Abiertas en Kraken"):
    with st.spinner("Conectando con los servidores de Kraken para extraer el reporte..."):
        exchange_conn = obtener_conexion_kraken()
        if exchange_conn:
            try:
                # Consultar balance real de la cuenta
                balance = exchange_conn.fetch_balance()
                st.write("### 💰 Balance de la Cuenta")
                
                total_free = balance.get('free', {})
                monedas_con_fondos = {k: v for k, v in total_free.items() if v > 0}
                
                if monedas_con_fondos:
                    st.json(monedas_con_fondos)
                else:
                    st.info("No se encontraron balances positivos disponibles.")

                # Consultar órdenes abiertas actuales
                st.write("### 📋 Órdenes Abiertas Actualmente")
                ordenes_abiertas = exchange_conn.fetch_open_orders(simbolo_seleccionado)
                if ordenes_abiertas:
                    for o in ordenes_abiertas:
                        st.text(f"ID: {o.get('id')} | Lado: {o.get('side')} | Precio: {o.get('price')} | Estado: {o.get('status')}")
                else:
                    st.info("No hay órdenes abiertas en este momento para este par.")

                # Consultar historial de órdenes cerradas
                st.write("### 📜 Historial de Órdenes Cerradas")
                ordenes_cerradas = exchange_conn.fetch_closed_orders(simbolo_seleccionado, limit=5)
                if ordenes_cerradas:
                    for o in ordenes_cerradas:
                        st.text(f"ID: {o.get('id')} | Lado: {o.get('side')} | Precio Ejecutado: {o.get('price')} | Estado: {o.get('status')}")
                else:
                    st.info("No hay registros recientes de órdenes cerradas para este par.")

            except Exception as e:
                st.error(f"No se pudo obtener el reporte de Kraken: {e}")
        else:
            st.error("Error de autenticación con Kraken. Revisa tus Secrets.")

# 4. Bucle de actualización automática
st.markdown("---")
st.write(f"🔄 Bot operando de forma autónoma sobre {simbolo_seleccionado}...")

TIEMPO_ESPERA = 60  
placeholder = st.empty()

for segundos_restantes in range(TIEMPO_ESPERA, 0, -1):
    placeholder.text(f"Próxima revisión de mercado en {segundos_restantes} segundos...")
    time.sleep(1)

st.rerun()
