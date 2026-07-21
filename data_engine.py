import ccxt
import pandas as pd

def obtener_datos(simbolo='BTC/USD', timeframe='1h', limite=300):
    """
    Se conecta a Kraken y descarga el historial de precios para cualquier par
    calculando automáticamente la EMA 200 de forma nativa.
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
        
        # Calcular la EMA 200 de forma nativa (sin librerías externas)
        df['EMA_200'] = df['close'].ewm(span=200, adjust=False).mean()
        
        # Limpiar valores nulos iniciales de la EMA
        df.dropna(subset=['EMA_200'], inplace=True)
        
        return df

    except Exception as e:
        print(f"Error al obtener datos de Kraken para {simbolo}: {e}")
        return None
