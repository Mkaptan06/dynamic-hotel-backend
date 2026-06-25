import mysql.connector
from database import veri_tabanina_baglan
from datetime import datetime, date


# Veri tabanındaki tüm odalar listeleme
def tum_odaları_getir():
    baglanti = veri_tabanina_baglan()
    if baglanti is None:
        return {"hata": "Veri tabanına bağlanılamadı"}

    cursor = baglanti.cursor(dictionary=True)
    sql_sorgusu = "SELECT * FROM odalar;"
    cursor.execute(sql_sorgusu)

    odalar = cursor.fetchall()

    cursor.close()
    baglanti.close()
    return odalar

# Veri tabanındaki tüm rezervasyonları listeleme
def tum_rezervasyonlari_getir():
    baglanti = veri_tabanina_baglan()
    if baglanti is None:
        return {"hata": "Veri tabanına bağlanılamadı"}
    
    cursor = baglanti.cursor(dictionary=True)
    sql_sorgusu = "SELECT * FROM rezervasyonlar;"
    cursor.execute(sql_sorgusu)

    rezervasyonlar = cursor.fetchall()

    cursor.close()
    baglanti.close()
    return rezervasyonlar

# Yeni oda ekleme
def yeni_oda_ekle(oda_numarasi , tip , fiyat):
    baglanti = veri_tabanina_baglan()
    if baglanti is None:
        return {"hata": "Veri tabanına bağlanılamadı"}
    
    cursor =baglanti.cursor()
    try:
        sql_sorgusu = "INSERT INTO odalar(oda_numarası, tip ,fiyat) VALUES (%s ,%s ,%s);"
        degerler = (oda_numarasi, tip, fiyat)

        cursor.execute(sql_sorgusu, degerler)
        baglanti.commit()

        yeni_id = cursor.lastrowid
        return {"mesaj": "Oda başarıyla eklendi", "oda_id": yeni_id}
    except mysql.connector.Error as e:
        print(f"Veri ekleme sırasında MySQL Hatası: {e}")
        return {"hata": f"Veri tabanı hatası: {e}"}
    
    finally:
        cursor.close()
        baglanti.close()


# Rezervasyon yapma
def rezervasyon_yap(oda_id, musteri_adi, giris_tarihi, cikis_tarihi):
    baglanti = veri_tabanina_baglan()
    if baglanti is None:
        return {"hata": "Veri tabanına bağlanılamadı"}
    
    cursor = baglanti.cursor(dictionary=True)

    try:

        if giris_tarihi >= cikis_tarihi:
            return {"hata": "Giriş tarihi, çıkış tarihinden önce olmalıdır."}
    
        kontrol_sorgusu = """
        SELECT id FROM rezervasyonlar
        WHERE oda_id = %s
        AND NOT (%s >= cikis_tarihi OR %s <= giris_tarihi);
        """

        cursor.execute(kontrol_sorgusu , (oda_id , giris_tarihi , cikis_tarihi))
        mevcut_rezervasyon = cursor.fetchone()

        if mevcut_rezervasyon:
            return {"hata": "Bu oda seçilen tarih aralığında zaten dolu."}
        
        fiyat_sorgusu = """
        WITH RECURSIVE gunler AS (
            SELECT %s AS gun
            UNION ALL
            SELECT DATE_ADD(gun , INTERVAL 1 DAY)
            FROM gunler
            WHERE DATE_ADD(gun, INTERVAL 1 DAY) < %s
        )    
        SELECT COALESCE (SUM(COALESCE(s.fiyat_carpani, 1.00)), 0 ) AS toplam_carpan
        FROM gunler g
        LEFT JOIN sezonlar s ON g.gun BETWEEN s.baslangic_tarihi AND s.bitis_tarihi;
        """

        cursor.execute(fiyat_sorgusu, (giris_tarihi,cikis_tarihi))
        sonuc = cursor.fetchone()
        toplam_carpan = sonuc["toplam_carpan"] if sonuc else 0

        if toplam_carpan == 0:
            return {"hata": "Tarih aralığı hesaplanamadı."}
        
        oda_fiyat_sorgusu = "SELECT fiyat FROM odalar WHERE id = %s"
        cursor.execute(oda_fiyat_sorgusu , (oda_id,))
        oda_sonuc = cursor.fetchone()

        if not oda_sonuc:
            return {"hata": "Oda bulunamadı."}
        
        oda_baz_fiyati = oda_sonuc["fiyat"]
        gercek_toplam_tutar = float(toplam_carpan) * float(oda_baz_fiyati)

        ekleme_sorgusu = """
            INSERT INTO rezervasyonlar (oda_id, musteri_adi, giris_tarihi, cikis_tarihi ,total_fiyat)
            VALUES(%s, %s, %s, %s, %s)
        """

        degerler = (oda_id , musteri_adi , giris_tarihi, cikis_tarihi , gercek_toplam_tutar)
        cursor.execute(ekleme_sorgusu , tuple(str(x) if isinstance(x,(date, datetime)) else x for x in degerler))

        baglanti.commit()
        yeni_rezervasyon_id = cursor.lastrowid
        return {"mesaj": "Rezervasyon başarıyla oluşturuldu", "rezervasyon_id": yeni_rezervasyon_id , "hesaplanan_toplam_carpan": gercek_toplam_tutar}
    
    except mysql.connector.Error as e:
        print(f"Rezervasyon sırasında MySQL hatası: {e}")
        return {"hata": f"Veri tabanı hatası {e}"}
    
    finally:
        cursor.close()
        baglanti.close()

# Sezon ekleme
def sezon_ekle(sezon_adi,  baslangic_tarihi, bitis_tarihi, fiyat_carpani):
    baglanti = veri_tabanina_baglan()
    if baglanti is None:
        return {"hata" : "Veri tabanına bağlanılamadı"}
    
    cursor = baglanti.cursor()

    try:
        sql_sorgusu = "INSERT INTO sezonlar(sezon_adi, baslangic_tarihi, bitis_tarihi, fiyat_carpani) VALUES (%s,%s,%s,%s);"
        degerler = (sezon_adi, baslangic_tarihi, bitis_tarihi, fiyat_carpani)

        cursor.execute(sql_sorgusu,degerler)
        baglanti.commit()

        yeni_id = cursor.lastrowid
        return {"mesaj": "Sezon başarıyla eklendi", "sezon_id": yeni_id}
    except mysql.connector.Error as e:
        print(f"Veri ekleme sırasında MySQL Hatası: {e}")
        return {"hata": f"Veri tabanı hatası: {e}"}
    finally:
        cursor.close()
        baglanti.close()
    
# Veri tabanındaki tüm sezonları listeleme
def tum_sezonları_getir():
    baglanti = veri_tabanina_baglan()
    if baglanti is None:
        return {"hata": "Veri tabanına bağlanılamadı"}

    cursor = baglanti.cursor(dictionary=True)
    sql_sorgusu = "SELECT * FROM sezonlar;"
    cursor.execute(sql_sorgusu)

    sezonlar = cursor.fetchall()

    cursor.close()
    baglanti.close()
    return sezonlar
