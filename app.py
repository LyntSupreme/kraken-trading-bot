import streamlit as st
import plotly.graph_objects as go
from data_engine import obtener_datos
from risk_manager import calcular_tamano_posicion
from execution_engine import ejecutar_orden_real, obtener_conexion_kraken

# Configuración de la página web
st.set_page_config(page_title="Kraken ADA Manual/Auto Bot", page_icon="🤖", layout="wide")

st.title("🤖 Kraken Trading Bot - Control Manual por Botón")
st.markdown("Ejecución precisa de la estrategia Dual-EMA bajo tu comando directo.")

# --- BARRA LATERAL: CONFIGURACIÓN ---
st.sidebar.header("⚙️ Configuración de Operación")
pares_disponibles = [
    'ADA/USD', 'BTC/USD', 'ETH/USD', 'SOL/USD', 
    'XRP/USD', 'DOT/USD', 'LTC/USD', 'BCH/USD'
]
# Seleccionamos por defecto ADA/USD como pediste
indice_ada = pares_disponibles.index('ADA/USD') if 'ADA/USD' in pares_disponibles else 0
simbolo_seleccionado = st.sidebar.selectbox("Selecciona la divisa a operar:", pares_disponibles, index=indice_ada)

if st.button("🔄 Actualizar Datos y Reportes"):
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
        col3.metric("Estado del Mercado", "TENDENCIA BAJISTA", "PRECAUCIÓN", delta_color="inverse")

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

    # 3. Panel de Gestión de Riesgo y Control por Botón
    st.markdown("---")
    st.subheader("🛡️ Gestión de Capital y Control de Ejecución")
    
    col_a, col_b = st.columns(2)
    with col_a:
        # Seteamos por defecto tu saldo real actual de 19.80 USD
        capital_cuenta = st.number_input("Capital Disponible (USD)", value=19.80, step=1.0)
        porcentaje_riesgo = st.slider("Porcentaje de Capital a Usar en el Trade", min_value=0.10, max_value=1.00, value=0.90, step=0.05, format="%.2f")
    
    with col_b:
        stop_loss_sugerido = precio_actual * 0.98 
        precio_sl_personalizado = st.number_input("Precio de Stop Loss", value=float(stop_loss_sugerido), step=0.001)

    resultado_riesgo = calcular_tamano_posicion(
        capital_total=capital_cuenta,
        porcentaje_riesgo=porcentaje_riesgo,
        precio_entrada=precio_actual,
        precio_stop_loss=precio_sl_personalizado
    )

    if resultado_riesgo:
        r1, r2, r3 = st.columns(3)
        r1.metric("Riesgo Máximo en Dinero", f"${resultado_riesgo['riesgo_dinero']:,.2f}")
        r2.metric("Tamaño de Posición (ADA)", f"{resultado_riesgo['tamaño_btc']:.2f} Unidades")
        r3.metric("Capital Involucrado", f"${resultado_riesgo['capital_involucrado']:,.2f}")

        st.markdown("---")
        st.subheader("⚡ Interruptor de Ejecución Manual")
        
        # Inicializamos el estado del botón en la sesión de Streamlit si no existe
        if 'bot_activado' not in st.session_state:
            st.session_state.bot_activado = False

        # Botón de activación tipo interruptor
        if st.button("🟢 ENCENDER / EJECUTAR ORDEN AHORA" if not st.session_state.bot_activado else "🔴 APAGAR / BOT ACTIVO"):
            st.session_state.bot_activado = not st.session_state.bot_activado
            st.rerun()

        if st.session_state.bot_activado:
            st.warning("⚠️ **¡Interruptor Activado!** Validando y enviando orden real a Kraken...")
            
            # Verificamos si el precio cumple la condición de la estrategia antes de mandar la orden
            if precio_actual > ema_200:
                respuesta_orden = ejecutar_orden_real(
                    simbolo=simbolo_seleccionado,
                    tipo_operacion="BUY",
                    tamaño_btc=resultado_riesgo['tamaño_btc']
                )
                
                if not respuesta_orden or "error" in respuesta_orden:
                    error_msg = respuesta_orden.get('error', 'Error desconocido') if respuesta_orden else 'Respuesta vacía'
                    st.error(f"Kraken rechazó la orden: {error_msg}")
                else:
                    st.success(f"¡Orden de compra ejecutada con éxito en Kraken! ID: {respuesta_orden.get('id', 'N/A')}")
            else:
                st.error("❌ El bot no ejecutó la orden porque el precio actual está por debajo de la EMA 200 (Condición bajista).")
            
            # Apagamos el interruptor tras el intento para evitar bucles de doble ejecución
            st.session_state.bot_activado = False
        else:
            st.info("🔒 **El bot está en reposo.** Presiona el botón verde cuando desees enviar la orden de compra al mercado.")

else:
    st.error(f"No se pudieron cargar los datos de Kraken para {simbolo_seleccionado}.")

# --- REPORTES DESDE KRAKEN ---
st.markdown("---")
st.subheader("📊 Reporte de Cuenta en Kraken")

with st.spinner("Consultando estado actual en Kraken..."):
    exchange_conn = obtener_conexion_kraken()
    if exchange_conn:
        try:
            balance = exchange_conn.fetch_balance()
            st.write("### 💰 Balance Disponible")
            total_free = balance.get('free', {})
            monedas_con_fondos = {k: v for k, v in total_free.items() if v > 0}
            
            if monedas_con_fondos:
                st.json(monedas_con_fondos)
            else:
                st.info("No se encontraron balances positivos disponibles.")

            st.write("### 📋 Órdenes Abiertas")
            ordenes_abiertas = exchange_conn.fetch_open_orders(simbolo_seleccionado)
            if ordenes_abiertas:
                for o in ordenes_abiertas:
                    st.text(f"ID: {o.get('id')} | Lado: {o.get('side')} | Precio: {o.get('price')} | Estado: {o.get('status')}")
            else:
                st.info("No hay órdenes abiertas en este momento para este par.")

            st.write("### 📜 Historial Reciente")
            ordenes_cerradas = exchange_conn.fetch_closed_orders(simbolo_seleccionado, limit=5)
            if ordenes_cerradas:
                for o in ordenes_cerradas:
                    st.text(f"ID: {o.get('id')} | Lado: {o.get('side')} | Precio Ejecutado: {o.get('price')} | Estado: {o.get('status')}")
            else:
                st.info("No hay registros recientes de órdenes cerradas.")

        except Exception as e:
            st.error(f"Error al conectar con Kraken para el reporte: {e}")
    else:
        st.error("Error de autenticación con Kraken. Revisa tus Secrets.")
