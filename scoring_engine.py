import pandas as pd

def calcular_puntuacion_mercado(df, exchange_conn, simbolo):
    """
    Calcula un puntaje sobre 120 puntos evaluando múltiples variables técnicas y de libro de órdenes.
    """
    puntuacion_detalle = {
        "Trend": 0,      # Máx 20
        "Volume": 0,     # Máx 20
        "Liquidity": 0,  # Máx 20
        "Momentum": 0,   # Máx 20
        "OrderBook": 0,  # Máx 20
        "News": 15       # Valor base por defecto (15/20)
    }
    
    try:
        # 1. Trend (Tendencia vs EMA 200 y EMA 50)
        precio_actual = float(df['close'].iloc[-1])
        ema_200 = float(df['EMA_200'].iloc[-1])
        
        # Calculamos una EMA 50 rápida si no existe
        if 'EMA_50' not in df.columns:
            df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
        ema_50 = float(df['EMA_50'].iloc[-1])
        
        if precio_actual > ema_200 and ema_50 > ema_200:
            puntuacion_detalle["Trend"] = 20
        elif precio_actual > ema_200:
            puntuacion_detalle["Trend"] = 15
        else:
            puntuacion_detalle["Trend"] = 5

        # 2. Volume (Volumen actual vs Promedio)
        volumen_actual = float(df['volume'].iloc[-1])
        volumen_promedio = float(df['volume'][-20:].mean())
        if volumen_actual > (volumen_promedio * 1.5):
            puntuacion_detalle["Volume"] = 20
        elif volumen_actual > volumen_promedio:
            puntuacion_detalle["Volume"] = 15
        else:
            puntuacion_detalle["Volume"] = 8

        # 3. Liquidity (Basado en el volumen monetario aproximado)
        liquidez_valor = volumen_actual * precio_actual
        if liquidez_valor > 10000:
            puntuacion_detalle["Liquidity"] = 20
        else:
            puntuacion_detalle["Liquidity"] = 12

        # 4. Momentum (RSI Simplificado de 14 periodos)
        delta = df['close'].diff()
        ganancia = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        perdida = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = ganancia / perdida
        rsi = 100 - (100 / (1 + rs))
        rsi_actual = float(rsi.iloc[-1])
        
        if 45 <= rsi_actual <= 65:
            puntuacion_detalle["Momentum"] = 20
        elif 35 <= rsi_actual < 45 or 65 < rsi_actual <= 75:
            puntuacion_detalle["Momentum"] = 14
        else:
            puntuacion_detalle["Momentum"] = 8

        # 5. Order Book (Libro de Órdenes real de Kraken)
        if exchange_conn:
            order_book = exchange_conn.fetch_order_book(simbolo, limit=10)
            bids_vol = sum([b[1] for b in order_book.get('bids', [])])
            asks_vol = sum([a[1] for a in order_book.get('asks', [])])
            
            if bids_vol > asks_vol * 1.2:
                puntuacion_detalle["OrderBook"] = 20
            elif bids_vol >= asks_vol:
                puntuacion_detalle["OrderBook"] = 15
            else:
                puntuacion_detalle["OrderBook"] = 8
        else:
            puntuacion_detalle["OrderBook"] = 10

    except Exception as e:
        print(f"Error calculando puntuación: {e}")

    total_score = sum(puntuacion_detalle.values())
    probabilidad = round((total_score / 120.0) * 100, 1)

    return total_score, probabilidad, puntuacion_detalle
