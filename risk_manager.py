def calcular_tamano_posicion(capital_total, porcentaje_riesgo, precio_entrada, precio_stop_loss):
    """
    Calcula el tamaño de la posición y valida los límites de riesgo 
    según las reglas estrictas del sistema (máximo 1% por operación).
    """
    # 1. Validar que el riesgo no supere el límite permitido
    if porcentaje_riesgo > 0.01:
        print("ALERTA: El riesgo excede el límite máximo permitido del 1%. Ajustando al 1%.")
        porcentaje_riesgo = 0.01

    # 2. Capital máximo dispuesto a arriesgar en dinero real/simulado
    riesgo_en_dinero = capital_total * porcentaje_riesgo

    # 3. Distancia del riesgo por cada unidad (ej. por cada dólar que baje el BTC)
    riesgo_por_unidad = abs(precio_entrada - precio_stop_loss)

    if riesgo_por_unidad == 0:
        print("Error: El precio de entrada y el Stop Loss no pueden ser iguales.")
        return None

    # 4. Cantidad de activos (BTC) que podemos comprar
    tamaño_posicion_btc = riesgo_en_dinero / riesgo_por_unidad
    
    # 5. Capital total necesario para abrir esa posición
    capital_involucrado = tamaño_posicion_btc * precio_entrada

    return {
        "riesgo_dinero": riesgo_en_dinero,
        "tamaño_btc": tamaño_posicion_btc,
        "capital_involucrado": capital_involucrado
    }

if __name__ == "__main__":
    # Prueba rápida del módulo con un capital simulado de $10,000 USD
    print("Probando Motor de Gestión de Riesgo...")
    capital_ejemplo = 10000.0
    precio_actual_ejemplo = 65917.80
    # Simulamos un Stop Loss a una distancia conservadora (ej. 2% abajo)
    stop_loss_ejemplo = precio_actual_ejemplo * 0.98 
    
    resultado = calcular_tamano_posicion(
        capital_total=capital_ejemplo, 
        porcentaje_riesgo=0.01, 
        precio_entrada=precio_actual_ejemplo, 
        precio_stop_loss=stop_loss_ejemplo
    )
    
    if resultado:
        print(f"Capital Total Simulado: ${capital_ejemplo:,.2f}")
        print(f"Riesgo Máximo (1%): ${resultado['riesgo_dinero']:,.2f}")
        print(f"Tamaño de Posición sugerido: {resultado['tamaño_btc']:.5f} BTC")
        print(f"Capital necesario en la orden: ${resultado['capital_involucrado']:,.2f}")
