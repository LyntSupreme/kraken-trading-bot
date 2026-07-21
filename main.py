from data_engine import obtener_datos
from risk_manager import calcular_tamano_posicion
from execution_engine import simular_orden_mercado

def ejecutar_sistema_bot():
    print("========================================")
    print("  INICIANDO EVALUACIÓN DEL KRAKEN BOT   ")
    print("========================================")
    
    # 1. Obtenemos datos del mercado actual
    df = obtener_datos(simbolo='BTC/USD', timeframe='1h')
    
    if df is None:
        print("Error crítico: No se pudieron obtener los datos del mercado.")
        return

    # 2. Extraemos variables clave
    precio_actual = df['close'].iloc[-1]
    ema_200 = df['EMA_200'].iloc[-1]
    
    print(f"Par: BTC/USD | Temporalidad: 1h")
    print(f"Precio Actual: ${precio_actual:,.2f}")
    print(f"EMA 200 (Tendencia): ${ema_200:,.2f}")
    print("----------------------------------------")
    
    # 3. Evaluamos la estrategia de tendencia
    if precio_actual > ema_200:
        print("ESTADO: TENDENCIA ALCISTA (Precio > EMA 200)")
        print("Señal: OPORTUNIDAD DE COMPRA (LONG) DETECTADA")
        print("----------------------------------------")
        
        # Parámetros de simulación de cuenta ($10,000 USD)
        capital_cuenta = 10000.0
        riesgo_permitido = 0.01  # 1% estricto
        stop_loss_sugerido = precio_actual * 0.98  # 2% de distancia
        
        # 4. Aplicamos el Motor de Gestión de Riesgo
        calculo_riesgo = calcular_tamano_posicion(
            capital_total=capital_cuenta,
            porcentaje_riesgo=riesgo_permitido,
            precio_entrada=precio_actual,
            precio_stop_loss=stop_loss_sugerido
        )
        
        if calculo_riesgo:
            print("--- PLAN DE ORDEN SEGURIZADA ---")
            print(f"Capital de la Cuenta: ${capital_cuenta:,.2f}")
            print(f"Riesgo Máximo Asumido: ${calculo_riesgo['riesgo_dinero']:,.2f} (1%)")
            print(f"Precio de Stop Loss:   ${stop_loss_sugerido:,.2f}")
            print(f"Tamaño de Posición:    {calculo_riesgo['tamaño_btc']:.5f} BTC")
            print(f"Inversión Requerida:   ${calculo_riesgo['capital_involucrado']:,.2f}")
            print("----------------------------------------")
            
            # 5. Enviamos la orden al Motor de Ejecución Simulada (Paper Trading)
            simular_orden_mercado(
                simbolo="BTC/USD",
                tipo_operacion="BUY (LONG)",
                tamaño_btc=calculo_riesgo['tamaño_btc'],
                precio_entrada=precio_actual
            )
    else:
         print("ESTADO: TENDENCIA BAJISTA O LATERAL (Precio < EMA 200)")
         print("Señal: FUERA DEL MERCADO. Preservando capital.")
         print("----------------------------------------")

if __name__ == "__main__":
    ejecutar_sistema_bot()
