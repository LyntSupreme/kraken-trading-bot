import ccxt
import pandas as pd
import pandas_ta as ta

def obtener_datos(simbolo='BTC/USD', timeframe='1h', limite=300):
    """
    Se conecta a Kraken y descarga el historial de precios para cualquier par
    calculando automáticamente la EMA 200.
    """
    try:
        exchange = ccxt.kraken()
        exchange.load_markets()
        
        # Verificar si el símbolo existe en Kraken
        if simbolo not in exchange.symbols:
            print(f"El símbolo {simbolo} no está disponible en Kraken.")
            return None

        # Descargar velas (OHLCV)
        ohlcv = exchange.fetch_ohlcv(simbolo, timeframe=timeframe, limit=limite)
        
        # Convertir a DataFrame de Pandas
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Calcular la EMA 200 usando pandas_ta
        df['EMA_200'] = ta.ema(df['close'], length=200)
        
        # Limpiar valores nulos iniciales de la EMA
        df.dropna(subset=['EMA_200'], inplace=True)
        
        return df

    except Exception as e:
        print(f"Error al obtener datos de Kraken para {simbolo}: {e}")
        return None
