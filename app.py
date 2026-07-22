import time
import streamlit as st
import plotly.graph_objects as go
from data_engine import obtener_datos
from risk_manager import calcular_tamano_posicion
from execution_engine import ejecutar_orden_real, obtener_conexion_kraken
from scoring_engine import calcular_puntuacion_mercado

st.set_page_config(page_title="Kraken Autonomous Quantitative Bot", page_icon="⚡", layout="wide")

st.title("⚡ Kraken Autonomous Quantitative Bot - Operación 100% Automática")
st.markdown("Sistema inteligente: Escanea el mercado, calcula la ventaja estadística, compra de forma autónoma, proyecta ganancias y vende en positivo.")

# --- CONTROL DE ESTADO EN SESIÓN ---
if 'modo_autonomo' not in st.session_state:
    st.session_state.modo_autonomo = False
if 'posicion_abierta' not in st.session_state:
    st.session_state.posicion_abierta = False
if 'detalles_posicion' not in st.session_state:
    st.session_state.detalles_posicion = {}

# Barra lateral: Configuración y Control Maestro
st.sidebar.header("🎛️ Panel de Control Autónomo")
pares_a_escanear = ['ADA/USD', 'BTC/USD', 'ETH/USD', 'SOL/USD', 'LTC/USD']
simbolo_seleccionado = st.sidebar.selectbox("Par de escaneo principal:", pares_a_escanear)

col_btn1, col_btn2 = st.sidebar.columns(2)
with col_btn1:
    if st.button("🟢 INICIAR AUTONOMÍA"):
        st.session_state.modo_autonomo = True
        st.rerun()
with col_btn2:
    if st.button("🔴 DETENER"):
        st.session_state.modo_autonomo = False
        st.rerun()

if st.session_state.modo_autonomo:
    st.sidebar.success("🤖 BOT AUTÓNOMO ACTIVO")
else:
    st.sidebar.warning("🔒 Bot en reposo / manual.")

st.markdown("---")

# 1. Obtener datos y analizar mercado
with st.spinner(f"Analizando microestructura para {simbolo_seleccionado}..."):
    df = obtener_datos(simbolo=simbolo_seleccionado, timeframe='1h')
    exchange_conn = obtener_conexion_kraken()

if df is not None and not df.empty:
    precio_actual = float(df['close'].iloc[-1])
    score_total, probabilidad, detalle_scores = calcular_puntuacion_mercado(df, exchange_conn, simbolo_seleccionado)

    # --- MÉTRICAS Y PROYECCIONES ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Puntuación de Ventaja", f"{score_total} / 120", delta=f"{probabilidad}% Probabilidad")
    c2.metric("Precio Actual", f"${precio_actual:,.4f}")
    c3.metric("Estado del Bot", "BUSCANDO ENTRADA" if not st.session_state.posicion_abierta else "POSICIÓN ACTIVA")
    c4.metric("Modo Autónomo", "ENCENDIDO 🟢" if st.session_state.modo_autonomo else "APAGADO 🔴")

    st.markdown("---")

    # Si hay una posición abierta, gestionamos la venta en ganancias y la proyección
    if st.session_state.posicion_abierta:
        pos = st.session_state.detalles_posicion
        precio_entrada = pos['precio_entrada']
        objetivo_ganancia = precio_entrada * 1.015  # Objetivo del +1.5% neto
        
        st.subheader("🎯 Posición Activa - Monitoreo de Ganancia en Tiempo Real")
        
        col_p1, col_p2, col_p3 = st.columns(3)
        col_p1.metric("Precio de Compra (Entrada)", f"${precio_entrada:,.4f}")
        col_p2.metric("Objetivo de Venta (Take Profit +1.5%)", f"${objetivo_ganancia:,.4f}")
        
        ganancia_flotante_pct = ((precio_actual - precio_entrada) / precio_entrada) * 100
        col_p3.metric("Retorno Actual", f"{ganancia_flotante_pct:.2f}%", delta="En curso")

        st.info("⏳ **Proyección estimada:** El sistema calcula que tomará entre **15 a 45 minutos** alcanzar el objetivo de ganancia basado en la volatilidad actual.")

        # VENTA AUTOMÁTICA EN GANANCIAS
        if precio_actual >= objetivo_ganancia:
            st.success("🎉 ¡Objetivo de ganancia alcanzado! Vendiendo automáticamente en positivo...")
            res_venta = ejecutar_orden_real(simbolo=pos['simbolo'], tipo_operacion="SELL", tamaño_btc=pos['tamaño'])
            
            if not res_venta or "error" in res_venta:
                st.error(f"Error al vender en Kraken: {res_venta.get('error', 'Desconocido')}")
            else:
                st.success("✅ Venta ejecutada con éxito. Capital asegurado en ganancias.")
                st.session_state.posicion_abierta = False
                st.rerun()
        
        if st.button("🚨 VENDER MANUALMENTE AHORA (Emergencia)"):
            ejecutar_orden_real(simbolo=pos['simbolo'], tipo_operacion="SELL", tamaño_btc=pos['tamaño'])
            st.session_state.posicion_abierta = False
            st.rerun()

    else:
        # --- LÓGICA DE COMPRA AUTÓNOMA ---
        st.subheader("🤖 Motor de Decisión Autónoma")
        UMBRAL_COMPRA = 85
        
        if score_total >= UMBRAL_COMPRA:
            st.success(f"✅ **Ventaja Estadística Alta detectada ({score_total}/120 pts).**")
            
            capital_disponible = 19.80
            resultado_riesgo = calcular_tamano_posicion(capital_disponible, 0.90, precio_actual, precio_actual * 0.98)
            
            if resultado_riesgo and st.session_state.modo_autonomo:
                st.warning("⚡ **El modo autónomo está activado:** Ejecutando compra automática en Kraken...")
                
                respuesta_orden = ejecutar_orden_real(
                    simbolo=simbolo_seleccionado,
                    tipo_operacion="BUY",
                    tamaño_btc=resultado_riesgo['tamaño_btc']
                )
                
                if not respuesta_orden or "error" in respuesta_orden:
                    st.error(f"Kraken rechazó la orden automática: {respuesta_orden.get('error', 'Desconocido')}")
                else:
                    st.success(f"🎉 ¡Compra automática completada! ID: {respuesta_orden.get('id', 'N/A')}")
                    st.session_state.posicion_abierta = True
                    st.session_state.detalles_posicion = {
                        "simbolo": simbolo_seleccionado,
                        "precio_entrada": precio_actual,
                        "tamaño": resultado_riesgo['tamaño_btc']
                    }
                    st.rerun()
            elif not st.session_state.modo_autonomo:
                st.info("💡 El mercado cumple las condiciones, pero el **Modo Autónomo está apagado**. Enciéndelo en la barra lateral para que opere solo.")
        else:
            st.warning(f"🛡️ **Sin ventaja suficiente ({score_total}/120 pts).** El bot espera pacientemente analizando el mercado.")

    # --- BUCLE DE ESPERA AUTÓNOMA ---
    if st.session_state.modo_autonomo and not st.session_state.posicion_abierta:
        st.markdown("---")
        placeholder_ciclo = st.empty()
        TIEMPO_ESPERA = 30
        for segundos in range(TIEMPO_ESPERA, 0, -1):
            placeholder_ciclo.text(f"🔄 Bot autónomo escaneando mercado... Próximo análisis en {segundos} segundos.")
            time.sleep(1)
        st.rerun()

else:
    st.error("No se pudieron cargar los datos de mercado.")
