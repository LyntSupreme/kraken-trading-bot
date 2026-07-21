def calcular_tamano_posicion(capital_total, porcentaje_riesgo, precio_entrada, precio_stop_loss):
    """
    Calcula el tamaño de la posición en base al riesgo monetario permitido.
    """
    try:
        if precio_entrada <= precio_stop_loss:
            # Para compras (Long), el Stop Loss debe estar por debajo del precio de entrada
            precio_stop_loss = precio_entrada * 0.98 

        riesgo_por_unidad = abs(precio_entrada - precio_stop_loss)
        if riesgo_por_unidad == 0:
            return None

        dinero_a_arriesgar = capital_total * porcentaje_riesgo
        tamano_posicion = dinero_a_arriesgar / riesgo_por_unidad
        capital_involucrado = tamano_posicion * precio_entrada

        return {
            "riesgo_dinero": dinero_dinero if 'dinero_dinero' in locals() else dinero_a_arriesgar,
            "tamaño_btc": tamano_posicion,
            "capital_involucrado": capital_involucrado
        }
    except Exception as e:
        print(f"Error en risk_manager: {e}")
        return None
