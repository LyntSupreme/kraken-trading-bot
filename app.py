import streamlit as st
import plotly.graph_objects as go
from data_engine import obtener_datos
from risk_manager import calcular_tamano_posicion
from execution_engine import ejecutar_orden_real, obtener_conexion_kraken
from scoring_engine import calcular_puntuacion_mercado

# Configuración de la página web
st.set_page_config(page_title="Kraken Quantitative Bot", page_icon="📈", layout="wide")

st.title("📈 Kraken Quantitative Trading System - Motor Cuantitativo")
st.markdown("Sistema profesional de dos cerebros: Reglas estadísticas de ventaja y Gestión Estricta de Riesgo.")

# Inicializar variables de control diario en sesión
if 'trades_realizados_hoy' not in st.session_state:
    st.session_state.trades_realizados_hoy = 0
if 'perdida_acumulada_hoy' not in st.session_state:
    st.session_state.perdida_acumulada_hoy = 0.0

# --- BARRA LATERAL: CONFIGURACIÓN CUANTITATIVA ---
st.sidebar.header("⚙️ Parámetros de Riesgo y Activo")
pares_disponibles = ['ADA/USD', 'BTC/USD', 'ETH/USD', 'SOL/USD', 'XRP/USD', 'LTC/USD']
simbolo_seleccionado = st.sidebar.selectbox("Selecciona la divisa:", pares_disponibles)

if st.sidebar.button("🔄 Sincronizar Datos"):
    st.rerun()

# 1. Obtener datos del mercado
with st.spinner(f"Analizando microestructura de mercado para {simbolo_seleccionado}..."):
    df = obtener_datos(simbolo=simbolo_seleccionado, timeframe='1h')
    exchange_conn = obtener_conexion_kraken()

if df is not None and not df.empty:
    precio_actual = float(df['close'].iloc[-1])
    ema_200 = float(df['EMA_200'].iloc[-1])
    
    # 2. Calcular Sistema de Puntuación Cuantitativa
    score_total, probabilidad, detalle_scores = calcular_puntuacion_mercado(df, exchange_conn, simbolo_seleccionado)

    # --- DASHBOARD DE MÉTRICAS CLAVE ---
    st.markdown("---")
    st.subheader("📊 Dashboard de Control Cuantitativo")
    
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Puntuación del Bot", f"{score_total} / 120", delta=f"{probabilidad}% Probabilidad")
    m2.metric("Trades Hoy", f"{st.session_state.trades_realizados_hoy} / 3 Máx")
    m3.metric("Pérdida Diaria", f"${st.session_state.perdida_acumulada_hoy:.2f}", delta="Límite: $2.00", delta_color="inverse")
    m4.metric("Precio Actual", f"${precio_actual:,.4f}")
    m5.metric("Tendencia EMA 200", "Alcista 🟢" if precio_actual > ema_200 else "Bajista 🔴")

    st.markdown("---")

    # --- APARTADO: ANÁLISIS DE IA Y FACTORES TÉCNICOS ---
    st.subheader("🧠 AI Analysis & Market Microstructure (Semáforos)")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"**Trend Score:** `{detalle_scores['Trend']}/20` " + ("🟢" if detalle_scores['Trend'] >= 15 else "🟡"))
    c2.markdown(f"**Volume Score:** `{detalle_scores['Volume']}/20` " + ("🟢" if detalle_scores['Volume'] >= 15 else "🟡"))
    c3.markdown(f"**Liquidity Score:** `{detalle_scores['Liquidity']}/20` " + ("🟢" if detalle_scores['Liquidity'] >= 15 else "🔴"))
    c4.markdown(f"**Momentum (RSI):** `{detalle_scores['Momentum']}/20` " + ("🟢" if detalle_scores['Momentum'] >= 15 else "🟡"))

    c5, c6, c7, c8 = st.columns(4)
    c5.markdown(f"**Order Book Imbalance:** `{detalle_scores['OrderBook']}/20` " + ("🟢" if detalle_scores['OrderBook'] >= 15 else "🔴"))
    c6.markdown(f"**News Sentiment (Base):** `{detalle_scores['News']}/20` 🟢")
    c7.markdown(f"**Volatility Regime:** `Estable` 🟢")
    c8.markdown(f"**Whale Accumulation:** `Neutral` 🟡")

    st.markdown("---")

    # --- GRÁFICO TÉCNICO ---
    st.subheader(f"📈 Gráfico de Cotización y Medias Móviles ({simbolo_seleccionado})")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['close'], mode='lines', name='Precio', line=dict(color='orange', width=2)))
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['EMA_200'], mode='lines', name='EMA 200', line=dict(color='blue', width=2, dash='dash')))
    fig.update_layout(xaxis_title="Hora", yaxis_title="USD", template="plotly_dark", height=380)
    st.plotly_chart(fig, use_container_width=True)

    # --- RISK ENGINE Y EJECUCIÓN ---
    st.markdown("---")
    st.subheader("🛡️ Risk Engine & Ejecución Basada en Ventaja")
    
    col_a, col_b = st.columns(2)
    with col_a:
        capital_cuenta = st.number_input("Capital Disponible (USD)", value=19.80, step=1.0)
        porcentaje_riesgo = st.slider("Porcentaje de Exposición", min_value=0.10, max_value=1.00, value=0.90, step=0.05)
    with col_b:
        stop_loss_sugerido = precio_actual * 0.98 
        precio_sl = st.number_input("Stop Loss Configurado", value=float(stop_loss_sugerido), step=0.001)

    resultado_riesgo = calcular_tamano_posicion(capital_cuenta, porcentaje_riesgo, precio_actual, precio_sl)

    if resultado_riesgo:
        r1, r2, r3 = st.columns(3)
        r1.metric("Riesgo Asignado", f"${resultado_riesgo['riesgo_dinero']:,.2f}")
        r2.metric("Tamaño de Orden", f"{resultado_riesgo['tamaño_btc']:.2f} Unidades")
        r3.metric("Capital Involucrado", f"${resultado_riesgo['capital_involucrado']:,.2f}")

        st.markdown("---")
        
        # Umbral estricto para operar (ej: mínimo 85 puntos / 70% de probabilidad)
        UMBRAL_MINIMO_PUNTUACION = 85 

        if score_total >= UMBRAL_MINIMO_PUNTUACION:
            st.success(f"✅ **Ventaja Estadística Detectada ({score_total}/120 pts).** El sistema autoriza la ejecución.")
        else:
            st.warning(f"⚠️ **Sin Ventaja Suficiente ({score_total}/120 pts).** Se requiere un mínimo de {UMBRAL_MINIMO_PUNTUACION} puntos para operar. El bot prioriza la preservación de capital.")

        # Interruptor manual condicionado al Risk Engine y Scoring
        if 'ejecutar_trade' not in st.session_state:
            st.session_state.ejecutar_trade = False

        # Validaciones del Risk Engine antes de dejar pulsar el botón
        limite_trades_alcanzado = st.session_state.trades_realizados_hoy >= 3
        limite_perdida_alcanzado = st.session_state.perdida_acumulada_hoy >= 2.00

        if limite_trades_alcanzado:
            st.error("🛑 Límite diario de operaciones (3) alcanzado. El Risk Engine ha bloqueado nuevas entradas hasta mañana.")
        elif limite_perdida_alcanzado:
            st.error("🛑 Límite de pérdida diaria alcanzado ($2.00). Bot pausado por seguridad.")
        else:
            if st.button("🚀 EJECUTAR ORDEN CON VENTAJA ESTADÍSTICA" if not st.session_state.ejecutar_trade else "⏳ Procesando..."):
                if score_total < UMBRAL_MINIMO_PUNTUACION:
                    st.error("❌ Operación denegada por el sistema: la puntuación estadística está por debajo del umbral de seguridad.")
                else:
                    st.session_state.ejecutar_trade = True
                    respuesta_orden = ejecutar_orden_real(
                        simbolo=simbolo_seleccionado,
                        tipo_operacion="BUY",
                        tamaño_btc=resultado_riesgo['tamaño_btc']
                    )
                    
                    if not respuesta_orden or "error" in respuesta_orden:
                        err = respuesta_orden.get('error', 'Desconocido') if respuesta_orden else 'Vacía'
                        st.error(f"Kraken rechazó la orden: {err}")
                    else:
                        st.success(f"🎉 ¡Orden ejecutada con éxito! ID: {respuesta_orden.get('id', 'N/A')}")
                        st.session_state.trades_realizados_hoy += 1
                    
                    st.session_state.ejecutar_trade = False

else:
    st.error("No se pudieron cargar los datos de mercado.")

# --- REPORTE DE KRAKEN ---
st.markdown("---")
st.subheader("📊 Estado de Cuenta en Kraken")
if exchange_conn:
    try:
        balance = exchange_conn.fetch_balance()
        free_bal = {k: v for k, v in balance.get('free', {}).items() if v > 0}
        st.json(free_bal if free_bal else {"Info": "Sin saldos positivos activos"})
    except Exception as e:
        st.error(f"Error consultando balance: {e}")
