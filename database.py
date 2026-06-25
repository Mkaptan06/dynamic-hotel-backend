import mysql.connector
from mysql.connector import Error

# MySQL veri tabanına bağlama

def veri_tabanina_baglan():
    try:
        baglanti = mysql.connector.connect(
            host = "localhost",
            user = "root",
            password = "Mkaptan.kaptan06",
            database = "antalya_otel_db",
        )
        if baglanti.is_connected():
            return baglanti
    except Error as e:
        print("MySQL bağlantı hatası")
        return None