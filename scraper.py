import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import pytz

# 1. Definir la hora actual en Mallorca
zona_horaria = pytz.timezone('Europe/Madrid')
ahora = datetime.now(zona_horaria).strftime('%Y-%m-%d %H:00')

# 2. Visitar la web de la estación
url = 'https://www.estacionsclimatiquesiibb.cat/weatherstationdataview/117202'
respuesta = requests.get(url)
soup = BeautifulSoup(respuesta.text, 'html.parser')

# --- AQUÍ FALTA LA MAGIA ---
# Necesitamos decirle al script en qué parte exacta del código de la web
# están escondidos los números "35,6" y "27,1".
temperatura = "25.0" # Valor de ejemplo (hay que extraer el real)
humedad = "60"       # Valor de ejemplo (hay que extraer el real)

# 3. Guardar el dato en nuestro archivo CSV
nueva_fila = [ahora, temperatura, humedad]

with open('historico_clima.csv', 'a', newline='') as archivo:
    escritor = csv.writer(archivo)
    escritor.writerow(nueva_fila)

print(f"Datos guardados: {ahora} | Temp: {temperatura}°C | Hum: {humedad}%")
