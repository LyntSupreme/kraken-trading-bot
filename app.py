import time
import datetime
import streamlit as st
import plotly.graph_objects as go
from data_engine import obtener_datos
from risk_manager import calcular_tamano_posicion
from execution_engine import ejecutar_orden_real, obtener_conexion_kraken
from scoring_engine import calcular_puntuacion_mercado

st.set_page_config(page_title="Kraken Autonomous Quantitative Bot", page_icon="⚡", layout="wide")

st.title("⚡ Kraken Autonomous Quantitative Bot - Panel de Auditoría en Vivo")
st.markdown("Sistema inteligente con visualización en tiempo real de cada paso del escaneo, análisis de mercado y gestión de órdenes.")

# --- CONTROL DE ESTADO EN SESIÓN ---
if 'modo_autonomo' not in st.session_state:
    st.session_state.modo_autonomo = False
if 'posicion_abierta' not in st.session_state:
    st.session_state.posicion_abierta = False
if 'detalles_posicion' not in st.session_state:
    st.session_state.detalles_posicion = {}
if 'sin_fondos' not in st.session_state:
    st.session_state.sin_fondos = False
if 'log_actividad' not in st.session_state:
    st.session_state.log_actividad = []

def registrar_log(mensaje):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    entrada = f"[{timestamp}] {mensaje}"
    st.session_state.log_actividad.insert(0, entrada)
    # Mantener solo los últimos 15 registros para no saturar la pantalla
    if len(st.session_state.log_actividad) > 15:
        st.session_state.log_actividad.pop()

# Barra lateral: Configuración y Control Maestro
st.sidebar.header("🎛️ Panel de Control Autónomo")
pares_a_escanear = ['ADA/USD', 'BTC/USD', 'ETH/USD', 'SOL/USD', 'LTC/USD']
simbolo_seleccionado = st.sidebar.selectbox("Par de escaneo principal:", pares_a_escanear)

col_btn1, col_btn2 = st.sidebar.columns(2)
with col_btn1:
    if st.button("🟢 INICIAR AUTONOMÍA"):
        st.session_state.modo_autonomo = True
        st.session_state.sin_fondos = False
        registrar_log("🟢 Bot autónomo activado por el usuario.")
        st.rerun()
with col_btn2:
    if st.button("🔴 DETENER"):
        st.session_state.modo_autonomo = False
        registrar_log("🔴 Bot detenido por el usuario.")
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
    c3.metric("Estado del Bot", "MONITOREANDO GANANCIA" if st.session_state.posicion_abierta else ("MODO VIGILANCIA (SIN FONDOS)" if st.session_state.sin_fondos else "BUSCANDO ENTRADA"))
    c4.metric("Modo Autónomo", "ENCENDIDO 🟢" if st.session_state.modo_autonomo else "APAGADO 🔴")

    st.markdown("---")

    # --- DESglose visual en tiempo real de la puntuación (Criterios del bot) ---
    with st.expander("📊 Ver desglose en vivo del análisis de mercado (Criterios de Puntuación)", expanded=True):
        col_s1, col_s2, col_s3, col_s4, col_s5, col_s6 = st.columns(6)
        col_s1.metric("Trend (Máx 20)", f"{detalle_scores.get('Trend', 0)} pts")
        col_s2.metric("Volume (Máx 20)", f"{detalle_scores.get('Volume', 0)} pts")
        col_s3.metric("Liquidity (Máx 20)", f"{detalle_scores.get('Liquidity', 0)} pts")
        col_s4.metric("Momentum (Máx 20)", f"{detalle_scores.get('Momentum', 0)} pts")
        col_s5.metric("OrderBook (Máx 20)", f"{detalle_scores.get('OrderBook', 0)} pts")
        col_s6.metric("News Base", f"{detalle_scores.get('News', 15)} pts")

    # Si hay una posición abierta, gestionamos la venta
    if st.session_state.posicion_abierta:
        pos = st.session_state.detalles_posicion
        precio_entrada = pos['precio_entrada']
        objetivo_ganancia = precio_entrada * 1.02  # +2.0% objetivo
        
        st.subheader("🎯 Posición Activa - Monitoreo de Máxima Ganancia")
        
        col_p1, col_p2, col_p3 = st.columns(3)
        col_p1.metric("Precio de Compra (Entrada)", f"${precio_entrada:,.4f}")
        col_p2.metric("Objetivo de Venta (Take Profit +2.0%)", f"${objetivo_ganancia:,.4f}")
        
        ganancia_flotante_pct = ((precio_actual - precio_entrada) / precio_entrada) * 100
        col_p3.metric("Retorno Actual", f"{ganancia_flotante_pct:.2f}%", delta="En curso")

        st.info("⏳ **Proyección estimada:** Supervisando el movimiento en tiempo real para asegurar la salida en el pico de ganancia.")

        if precio_actual >= objetivo_ganancia:
            registrar_log(f"🎉 ¡Objetivo alcanzado en {simbolo_seleccionado}! Precio: ${precio_actual} >= Objetivo: ${objetivo_ganancia}")
            res_venta = ejecutar_orden_real(simbolo=pos['simbolo'], tipo_operacion="SELL", tamaño_btc=pos['tamaño'])
            
            if not res_venta or "error" in res_venta:
                registrar_log(f"❌ Error al vender: {res_venta.get('error', 'Desconocido')}")
                st.error(f"Error al vender en Kraken: {res_venta.get('error', 'Desconocido')}")
            else:
                registrar_log("✅ Venta ejecutada con éxito. Ganancias aseguradas.")
                st.success("✅ Venta ejecutada con éxito. Ganancias aseguradas.")
                st.session_state.posicion_abierta = False
                st.session_state.sin_fondos = False
                st.rerun()
        
        if st.button("🚨 VENDER MANUALMENTE AHORA (Emergencia)"):
            registrar_log("🚨 Venta manual forzada por el usuario.")
            ejecutar_orden_real(simbolo=pos['simbolo'], tipo_operacion="SELL", tamaño_btc=pos['tamaño'])
            st.session_state.posicion_abierta = False
            st.rerun()

    else:
        # --- LÓGICA DE COMPRA AUTÓNOMA Y VIGILANCIA ---
        st.subheader("🤖 Motor de Decisión Autónoma y Seguimiento")
        UMBRAL_COMPRA = 85
        
        if score_total >= UMBRAL_COMPRA:
            registrar_log(f"✅ ¡Ventaja alta detectada en {simbolo_seleccionado} con {score_total}/120 pts!")
            st.success(f"✅ **Ventaja Estadística Alta detectada ({score_total}/120 pts).**")
            
            if st.session_state.sin_fondos:
                registrar_log("⚠️ Modo sin fondos activo: Omitiendo intento de orden en Kraken. Vigilando mercado.")
                st.warning("⚠️ **Aviso del sistema:** El bot detectó anteriormente que no hay fondos disponibles. Omitiendo intento de compra y enfocado en vigilar el mercado.")
            else:
                capital_disponible = 19.80
                resultado_riesgo = calcular_tamano_posicion(capital_disponible, 0.90, precio_actual, precio_actual * 0.98)
                
                if resultado_riesgo and st.session_state.modo_autonomo:
                    registrar_log(f"⚡ Intentando enviar orden de compra de {resultado_riesgo['tamaño_btc']} a Kraken...")
                    st.warning("⚡ **Intentando ejecutar compra automática en Kraken...**")
                    
                    respuesta_orden = ejecutar_orden_real(
                        simbolo=simbolo_seleccionado,
                        tipo_operacion="BUY",
                        tamaño_btc=resultado_riesgo['tamaño_btc']
                    )
                    
                    if respuesta_orden and "error" in respuesta_orden:
                        error_msg = respuesta_orden["error"]
                        if "Fondos insuficientes" in error_msg or "Insufficient funds" in error_msg:
                            st.session_state.sin_fondos = True
                            registrar_log("🛡️ Fondos insuficientes en Kraken. Activando Modo de Vigilancia de Mercado.")
                            st.warning("🛡️ **Fondos insuficientes en Kraken detectados.** El bot ha pausado las compras automáticas y **ahora se encarga exclusivamente de vigilar el mercado**.")
                            st.rerun()
                        else:
                            registrar_log(f"❌ Error de Kraken: {error_msg}")
                            st.error(f"Kraken rechazó la orden: {error_msg}")
                    else:
                        id_orden = respuesta_orden.get('id', 'N/A')
                        registrar_log(f"🎉 ¡Compra automática completada con éxito! ID: {id_orden}")
                        st.success(f"🎉 ¡Compra automática completada! ID: {id_orden}")
                        st.session_state.posicion_abierta = True
                        st.session_state.detalles_posicion = {
                            "simbolo": simbolo_seleccionado,
                            "precio_entrada": precio_actual,
                            "tamaño": resultado_riesgo['tamaño_btc']
                        }
                        st.rerun()
        else:
            registrar_log(f"🛡️ Puntuación baja ({score_total}/120 pts) para {simbolo_seleccionado}. El bot espera sin arriesgar capital.")
            st.warning(f"🛡️ **Sin ventaja suficiente ({score_total}/120 pts).** El bot analiza el mercado pacientemente.")
            if st.session_state.sin_fondos:
                st.info("ℹ️ Estado actual: Sin fondos. El bot opera en **Modo de Vigilancia de Mercado** revisando fluctuaciones.")

    # --- SECCIÓN VISUAL DE AUDITORÍA EN TIEMPO REAL (TERMINAL DE LOGS) ---
    st.markdown("### 🖥️ Terminal de Actividad y Auditoría en Vivo")
    st.markdown("Aquí puedes ver el registro paso a paso de lo que el bot está haciendo en este momento:")
    
    # Contenedor visual tipo terminal oscura o limpia
    with st.container():
        log_text = "\n".join(st.session_state.log_actividad) if st.session_state.log_actividad else "[Iniciando registro de auditoría del bot...]"
        st.text_area("Registro de Eventos en Tiempo Real", value=log_text, height=200, disabled=True)

    # --- BUCLE DE ESPERA AUTÓNOMA ---
    if st.session_state.modo_autonomo and not st.session_state.posicion_abierta:
        st.markdown("---")
        placeholder_ciclo = st.empty()
        TIEMPO_ESPERA = 30
        for segundos in range(TIEMPO_ESPERA, 0, -1):
            msg = f"🔄 Vigilando mercado (Modo sin fondos activo)... Próximo escaneo en {segundos}s." if st.session_state.sin_fondos else f"🔄 Bot autónomo escaneando mercado... Próximo análisis en {segundos}s."
            placeholder_ciclo.text(msg)
            time.sleep(1)
        st.rerun()

else:
    st.error("No se pudieron cargar los datos de mercado.")
