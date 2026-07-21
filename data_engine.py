import ccxt
import pandas as pd

def obtener_datos(simbolo='BTC/USD', timeframe='1h'):
    """
    Conecta con Kraken y descarga datos históricos recientes 
    para calcular la EMA de forma nativa.
    """
    try:
        # Inicializamos el exchange Kraken (modo público)
        exchange = ccxt.kraken()
        
        # Descargamos los últimos 250 periodos (necesarios para la EMA 200)
        bars = exchange.fetch_ohlcv(simbolo, timeframe=timeframe, limit=250)
        
        # Convertimos la lista a un DataFrame de Pandas (tabla estructurada)
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Convertimos el timestamp a formato de fecha legible
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Calculamos la EMA 200 de forma nativa con Pandas
        df['EMA_200'] = df['close'].ewm(span=200, adjust=False).mean()
        
        return df

    except Exception as e:
        print(f"Error al conectar con Kraken: {e}")
        return None

if __name__ == "__main__":
    print("Probando descarga de datos de Kraken...")
    df_prueba = obtener_datos()
    if df_prueba is not None:
        print("¡Datos descargados con éxito!")
        print(df_prueba.tail(3))
