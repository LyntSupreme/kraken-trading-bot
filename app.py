import time
import streamlit as st
import plotly.graph_objects as go
from data_engine import obtener_datos
from risk_manager import calcular_tamano_posicion
from execution_engine import ejecutar_orden_real, obtener_conexion_kraken
from scoring_engine import calcular_puntuacion_mercado

st.set_page_config(page_title="Kraken Autonomous Quantitative Bot", page_icon="⚡", layout="wide")

st.title("⚡ Kraken Autonomous Quantitative Bot - Operación 100% Automática")
st.markdown("Sistema inteligente: Escanea el mercado, busca entradas óptimas, gestiona ventas en máxima ganancia y se adapta si no hay fondos disponibles.")

# --- CONTROL DE ESTADO EN SESIÓN ---
if 'modo_autonomo' not in st.session_state:
    st.session_state.modo_autonomo = False
if 'posicion_abierta' not in st.session_state:
    st.session_state.posicion_abierta = False
if 'detalles_posicion' not in st.session_state:
    st.session_state.detalles_posicion = {}
if 'sin_fondos' not in st.session_state:
    st.session_state.sin_fondos = False

# Barra lateral: Configuración y Control Maestro
st.sidebar.header("🎛️ Panel de Control Autónomo")
pares_a_escanear = ['ADA/USD', 'BTC/USD', 'ETH/USD', 'SOL/USD', 'LTC/USD']
simbolo_seleccionado = st.sidebar.selectbox("Par de escaneo principal:", pares_a_escanear)

col_btn1, col_btn2 = st.sidebar.columns(2)
with col_btn1:
    if st.button("🟢 INICIAR AUTONOMÍA"):
        st.session_state.modo_autonomo = True
        st.session_state.sin_fondos = False  # Resetear aviso al reiniciar
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
    c3.metric("Estado del Bot", "MONITOREANDO GANANCIA" if st.session_state.posicion_abierta else ("MODO VIGILANCIA (SIN FONDOS)" if st.session_state.sin_fondos else "BUSCANDO ENTRADA"))
    c4.metric("Modo Autónomo", "ENCENDIDO 🟢" if st.session_state.modo_autonomo else "APAGADO 🔴")

    st.markdown("---")

    # Si hay una posición abierta, gestionamos la venta en ganancias máximas y la proyección
    if st.session_state.posicion_abierta:
        pos = st.session_state.detalles_posicion
        precio_entrada = pos['precio_entrada']
        objetivo_ganancia = precio_entrada * 1.02  # Ajustado al +2.0% para buscar la mayor ganancia esperada
        
        st.subheader("🎯 Posición Activa - Monitoreo de Máxima Ganancia")
        
        col_p1, col_p2, col_p3 = st.columns(3)
        col_p1.metric("Precio de Compra (Entrada)", f"${precio_entrada:,.4f}")
        col_p2.metric("Objetivo de Venta (Take Profit +2.0%)", f"${objetivo_ganancia:,.4f}")
        
        ganancia_flotante_pct = ((precio_actual - precio_entrada) / precio_entrada) * 100
        col_p3.metric("Retorno Actual", f"{ganancia_flotante_pct:.2f}%", delta="En curso")

        st.info("⏳ **Proyección estimada:** El sistema está supervisando el movimiento para asegurar la salida en el pico de ganancia proyectado.")

        # VENTA AUTOMÁTICA EN GANANCIAS
        if precio_actual >= objetivo_ganancia:
            st.success("🎉 ¡Objetivo de ganancia máxima alcanzado! Vendiendo automáticamente...")
            res_venta = ejecutar_orden_real(simbolo=pos['simbolo'], tipo_operacion="SELL", tamaño_btc=pos['tamaño'])
            
            if not res_venta or "error" in res_venta:
                st.error(f"Error al vender en Kraken: {res_venta.get('error', 'Desconocido')}")
            else:
                st.success("✅ Venta ejecutada con éxito. Ganancias aseguradas.")
                st.session_state.posicion_abierta = False
                st.session_state.sin_fondos = False  # Permitir reevaluar compras futuras si hay fondos nuevos
                st.rerun()
        
        if st.button("🚨 VENDER MANUALMENTE AHORA (Emergencia)"):
            ejecutar_orden_real(simbolo=pos['simbolo'], tipo_operacion="SELL", tamaño_btc=pos['tamaño'])
            st.session_state.posicion_abierta = False
            st.rerun()

    else:
        # --- LÓGICA DE COMPRA AUTÓNOMA Y GESTIÓN DE FONDOS ---
        st.subheader("🤖 Motor de Decisión Autónoma y Vigilancia")
        UMBRAL_COMPRA = 85
        
        if score_total >= UMBRAL_COMPRA:
            st.success(f"✅ **Ventaja Estadística Alta detectada ({score_total}/120 pts).**")
            
            if st.session_state.sin_fondos:
                st.warning("⚠️ **Aviso del sistema:** El bot detectó anteriormente que no hay fondos disponibles. Omitiendo intento de compra para evitar errores y enfocado en vigilar el mercado.")
            else:
                capital_disponible = 19.80
                resultado_riesgo = calcular_tamano_posicion(capital_disponible, 0.90, precio_actual, precio_actual * 0.98)
                
                if resultado_riesgo and st.session_state.modo_autonomo:
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
                            st.warning("🛡️ **Fondos insuficientes en Kraken detectados.** El bot ha pausado las compras automáticas de manera inteligente y **ahora se encarga exclusivamente de revisar el mercado y esperar oportunidades de venta/ganancia**.")
                            st.rerun()
                        else:
                            st.error(f"Kraken rechazó la orden: {error_msg}")
                    else:
                        st.success(f"🎉 ¡Compra automática completada! ID: {respuesta_orden.get('id', 'N/A')}")
                        st.session_state.posicion_abierta = True
                        st.session_state.detalles_posicion = {
                            "simbolo": simbolo_seleccionado,
                            "precio_entrada": precio_actual,
                            "tamaño": resultado_riesgo['tamaño_btc']
                        }
                        st.rerun()
        else:
            st.warning(f"🛡️ **Sin ventaja suficiente ({score_total}/120 pts).** El bot analiza el mercado pacientemente.")
            if st.session_state.sin_fondos:
                st.info("ℹ️ Estado actual: Sin fondos para operar. El bot opera en **Modo de Vigilancia de Mercado**.")

    # --- BUCLE DE ESPERA AUTÓNOMA ---
    if st.session_state.modo_autonomo and not st.session_state.posicion_abierta:
        st.markdown("---")
        placeholder_ciclo = st.empty()
        TIEMPO_ESPERA = 30
        for segundos in range(TIEMPO_ESPERA, 0, -1):
            msg = f"🔄 Vigilando mercado (Modo sin fondos activo)... Próximo escaneo en {segundos} segundos." if st.session_state.sin_fondos else f"🔄 Bot autónomo escaneando mercado... Próximo análisis en {segundos} segundos."
            placeholder_ciclo.text(msg)
            time.sleep(1)
        st.rerun()

else:
    st.error("No se pudieron cargar los datos de mercado.")
