import datetime

def simular_orden_mercado(simbolo, tipo_operacion, tamaño_btc, precio_entrada):
    """
    Simula la ejecución de una orden de compra o venta en el exchange
    y registra los datos básicos de la operación en modo Paper Trading.
    """
    timestamp_actual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Simulamos un ID de orden único basado en el tiempo
    id_orden_simulada = f"SIM-{int(datetime.datetime.now().timestamp())}"
    
    print("\n========================================")
    print("      [PAPER TRADING] EJECUCIÓN        ")
    print("========================================")
    print(f"Timestamp:       {timestamp_actual}")
    print(f"ID de Orden:     {id_orden_simulada}")
    print(f"Par:             {simbolo}")
    print(f"Operación:       {tipo_operacion}")
    print(f"Volumen:         {tamaño_btc:.5f} BTC")
    print(f"Precio Ejecución: ${precio_entrada:,.2f}")
    print("----------------------------------------")
    print("ESTADO: Orden simulada abierta con éxito.")
    print("========================================\n")
    
    # Devolvemos un diccionario con el registro de la orden simulada
    return {
        "id": id_orden_simulada,
        "timestamp": timestamp_actual,
        "simbolo": simbolo,
        "tipo": tipo_operacion,
        "volumen": tamaño_btc,
        "precio": precio_entrada
    }

if __name__ == "__main__":
    # Prueba rápida del módulo de ejecución simulada
    print("Probando Motor de Ejecución en Papel...")
    simular_orden_mercado(
        simbolo="BTC/USD",
        tipo_operacion="BUY (LONG)",
        tamaño_btc=0.07579,
        precio_entrada=65972.10
    )
