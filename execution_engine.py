import datetime
import ccxt
import streamlit as st

def obtener_conexion_kraken():
    """
    Carga las credenciales desde los Secrets de Streamlit Cloud 
    y establece la conexión segura con Kraken.
    """
    try:
        api_key = st.secrets["kraken"]["api_key"]
        secret_key = st.secrets["kraken"]["secret_key"]
        
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
    utilizando los fondos de tu cuenta.
    """
    exchange = obtener_conexion_kraken()
    if not exchange:
        return {"error": "No se pudo conectar con Kraken"}

    try:
        # Cargar los mercados para asegurar la precisión del par (ej. BTC/USD)
        exchange.load_markets()
        
        timestamp_actual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print("\n========================================")
        print("     [TRADING REAL] ENVIANDO ORDEN      ")
        print("========================================")
        print(f"Timestamp:       {timestamp_actual}")
        print(f"Par:             {simbolo}")
        print(f"Operación:       {tipo_operacion}")
        print(f"Volumen:         {tamaño_btc:.5f} BTC")
        print("----------------------------------------")

        # Ejecución de la orden real en el exchange
        if tipo_operacion.upper() in ["BUY", "BUY (LONG)"]:
            # Orden de compra a mercado
            orden = exchange.create_market_buy_order(simbolo, tamaño_btc)
        elif tipo_operacion.upper() in ["SELL", "SELL (SHORT)"]:
            # Orden de venta a mercado
            orden = exchange.create_market_sell_order(simbolo, tamaño_btc)
        else:
            return {"error": "Tipo de operación no reconocido"}

        print("ESTADO: ¡Orden ejecutada con éxito en Kraken!")
        print(f"ID de Orden Real: {orden.get('id')}")
        print(f"Precio de ejecución: ${orden.get('average', orden.get('price', 0)):,.2f}")
        print("========================================\n")

        return {
            "id": orden.get('id'),
            "timestamp": timestamp_actual,
            "simbolo": simbolo,
            "tipo": tipo_operacion,
            "volumen": tamaño_btc,
            "precio": orden.get('average', orden.get('price', 0)),
            "estado": "EJECUTADA_REAL"
        }

    except ccxt.InsufficientFunds as e:
        print(f"Error de ejecución: Fondos insuficientes en la cuenta de Kraken. Detalle: {e}")
        return {"error": "Fondos insuficientes"}
    except Exception as e:
        print(f"Error crítico al enviar la orden a Kraken: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    print("Módulo de Ejecución Real cargado.")
