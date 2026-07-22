import datetime
import ccxt
import streamlit as st

def obtener_conexion_kraken():
    """
    Carga las credenciales desde los Secrets de Streamlit Cloud 
    y establece la conexión segura con Kraken.
    """
    try:
        api_key = st.secrets["kraken"]["api_key"].strip()
        secret_key = st.secrets["kraken"]["secret_key"].strip()
        
        exchange = ccxt.kraken({
            'apiKey': api_key,
            'secret': secret_key,
            'enableRateLimit': True,
        })
        return exchange
    except Exception as e:
        print(f"Error al conectar con Kraken: {e}")
        return None

def ejecutar_orden_real(simbolo, tipo_operacion, tamaño_btc):
    """
    Ejecuta una orden real de mercado (Compra o Venta) en Kraken 
    protegida contra valores nulos.
    """
    # Blindaje contra valores None
    if tamaño_btc is None:
        return {"error": "El tamaño de la orden es nulo (None)."}

    try:
        tamaño_btc = float(tamaño_btc)
    except (ValueError, TypeError):
        return {"error": f"El tamaño de la orden no es un número válido: {tamaño_btc}"}

    exchange = obtener_conexion_kraken()
    if not exchange:
        return {"error": "No se pudo conectar con Kraken"}

    try:
        exchange.load_markets()
        
        timestamp_actual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print("\n========================================")
        print("       [TRADING REAL] ENVIANDO ORDEN      ")
        print("========================================")
        print(f"Timestamp:       {timestamp_actual}")
        print(f"Par:             {simbolo}")
        print(f"Operación:       {tipo_operacion}")
        print(f"Volumen:         {tamaño_btc:.5f}")
        print("----------------------------------------")

        if tipo_operacion.upper() in ["BUY", "BUY (LONG)"]:
            orden = exchange.create_market_buy_order(simbolo, tamaño_btc)
        elif tipo_operacion.upper() in ["SELL", "SELL (SHORT)"]:
            orden = exchange.create_market_sell_order(simbolo, tamaño_btc)
        else:
            return {"error": "Tipo de operación no reconocido"}

        print("ESTADO: ¡Orden ejecutada con éxito en Kraken!")
        print(f"ID de Orden Real: {orden.get('id')}")
        print("========================================\n")

        return {
            "id": orden.get('id', 'Desconocido'),
            "timestamp": timestamp_actual,
            "simbolo": simbolo,
            "tipo": tipo_operacion,
            "volumen": tamaño_btc,
            "precio": orden.get('average', orden.get('price', 0.0)) or 0.0,
            "estado": "EJECUTADA_REAL"
        }

    except ccxt.InsufficientFunds as e:
        return {"error": f"Fondos insuficientes en la cuenta de Kraken: {e}"}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    print("Módulo de Ejecución Real cargado.")
