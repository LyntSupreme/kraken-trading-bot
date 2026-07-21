def calcular_tamano_posicion(capital_total, porcentaje_riesgo, precio_entrada, precio_stop_loss):
    """
    Calcula el tamaño de la posición asegurando que cumpla con los mínimos 
    y decimales exactos permitidos para cuentas pequeñas.
    """
    try:
        if precio_entrada <= 0:
            return None

        # Si el capital es pequeño (< $25), usamos casi el 95% para superar el lote mínimo de Kraken
        capital_a_usar = capital_total * porcentaje_riesgo
        if capital_a_usar < 10.0 and capital_total >= 10.0:
            capital_a_usar = capital_total * 0.95  # Forzar uso del saldo para superar mínimos del exchange

        # Tamaño de posición basado en capital dedicado a la orden
        tamano_posicion = capital_a_usar / precio_entrada

        # Redondear estrictamente a 2 decimales (estándar seguro para ADA y altcoins en Kraken)
        tamano_posicion = round(tamano_posicion, 2)

        # Si tras redondear queda en 0 por ser muy bajo, asignamos al menos 1 unidad mínima segura
        if tamano_posicion <= 0:
            tamano_posicion = 1.0

        capital_involucrado = tamano_posicion * precio_entrada

        return {
            "riesgo_dinero": capital_a_usar,
            "tamaño_btc": tamano_posicion,
            "capital_involucrado": capital_involucrado
        }
    except Exception as e:
        print(f"Error en risk_manager: {e}")
        return None
