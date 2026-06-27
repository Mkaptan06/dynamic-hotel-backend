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
    
        oda_fiyat_sorgusu = "SELECT fiyat, durum FROM odalar WHERE id = %s"
        cursor.execute(oda_fiyat_sorgusu , (oda_id,))
        oda_sonuc = cursor.fetchone()

        if not oda_sonuc:
            return {"hata": "Oda bulunamadı."}

        if oda_sonuc["durum"] != "Bos":
            return {"hata": f"Bu oda şu anda rezervasyon için uygun değil. Oda Durumu: {oda_sonuc['durum']}"}
        
        kontrol_sorgusu = """
        SELECT id FROM rezervasyonlar
        WHERE oda_id = %s
        AND durum NOT IN ('CikisYapildi' , 'Iptal')
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
        
        oda_baz_fiyati = oda_sonuc["fiyat"]
        gercek_toplam_tutar = float(toplam_carpan) * float(oda_baz_fiyati)

        ekleme_sorgusu = """
            INSERT INTO rezervasyonlar (oda_id, musteri_adi, giris_tarihi, cikis_tarihi ,total_fiyat, durum)
            VALUES(%s, %s, %s, %s, %s, 'Onaylandı')
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

# check_in işlemi
def check_in_yap(rezervasyon_id):
    baglanti = veri_tabanina_baglan()
    if baglanti is None:
        return {"hata": "Veri tabanına bağlanılamadı"}
    
    cursor = baglanti.cursor(dictionary=True)

    try:
        sorgu = """
        SELECT r.oda_id, r.giris_tarihi, r.durum AS rez_durum , o.durum as oda_durum
        FROM rezervasyonlar r
        JOIN odalar o ON r.oda_id = o.id
        WHERE r.id = %s;
        """
        cursor.execute(sorgu,(rezervasyon_id,))
        rezervasyon = cursor.fetchone()

        if not rezervasyon:
            return {"hata": "Rezervasyon bulunamadı"}
        
        if rezervasyon["rez_durum"] == "GirisYapildi":
            return {"hata": "Bu rezervasyon için zaten check-in yapılmış."}
        
        if rezervasyon["giris_tarihi"] != date.today():
            return {"hata": f"Check-in sadece giriş gününde yapılabilir. Giriş tarihi: {rezervasyon['giris_tarihi']}"}
        
        if rezervasyon["oda_durum"] != "Bos":
            return {"hata": f"Oda şu anda check-in için uygun değil. Oda Durumu: {rezervasyon['oda_durum']}"}
        
        oda_id = rezervasyon["oda_id"]

        rez_guncelle = "UPDATE rezervasyonlar SET durum = 'GirisYapildi' WHERE id = %s;"
        cursor.execute(rez_guncelle,(rezervasyon_id,))

        oda_guncelle = "UPDATE odalar SET durum = 'Dolu' WHERE id=%s"
        cursor.execute(oda_guncelle,(oda_id,))

        baglanti.commit()

        return {"mesaj": "Check-in işlemi başarıyla tamamlandı. Müşteri giriş yaptı."}
    
    except mysql.connector.Error as e:
        print(f"Check-in sırasında hata: {e}")
        return {"hata": f"Veri tabanı hatası: {e}"}
    
    finally:
        cursor.close()
        baglanti.close()
    

# check_out işlemi
def check_out_yap(rezervasyon_id):
    
    baglanti = veri_tabanina_baglan()
    if baglanti is None:
        return {"hata": "Veri tabanına bağlanılamadı"}
    
    cursor = baglanti.cursor(dictionary=True)

    try:

        sorgu = """
        SELECT r.oda_id, r.cikis_tarihi, r.durum AS rez_durum, o.durum AS oda_durum
        FROM rezervasyonlar r
        JOIN odalar o ON r.oda_id = o.id
        WHERE r.id = %s ;
        """
        cursor.execute(sorgu, (rezervasyon_id,))
        rezervasyon = cursor.fetchone()

        if not rezervasyon:
            return {"hata": "Rezervasyon bulunamadı."}
        
        if rezervasyon["rez_durum"] == "CikisYapildi":
            return {"hata": "Bu rezervasyon için zaten check-out yapılmış."}
        
        if rezervasyon["cikis_tarihi"] != date.today():
            return {"hata": f"Check-out sadece çıkış gününde yapılabilir. Çıkış tarihi: {rezervasyon['cikis_tarihi']}"}
        
        if rezervasyon["oda_durum"] != "Dolu":
            return {"hata": f"Oda şu anda check-out için uygun değil. Oda Durumu: {rezervasyon['oda_durum']}"}

        oda_id = rezervasyon["oda_id"]

        rez_guncelle = "UPDATE rezervasyonlar SET durum = 'CikisYapildi' WHERE id = %s"
        cursor.execute(rez_guncelle,(rezervasyon_id,))

        oda_guncelle = "UPDATE odalar SET durum = 'Kirli' WHERE id = %s"
        cursor.execute(oda_guncelle,(oda_id,))

        baglanti.commit()

        return {"mesaj": "Check-out işlemi başarıyla tamamlandı. Müşteri çıkış yaptı."}
    
    except mysql.connector.Error as e:
        print(f"Check-out sırasında hata {e}")
        return {"hata": f" Veri tabanı hatası: {e}"}
    
    finally:
        cursor.close()
        baglanti.close()

#  check_clear işlemi
def check_clear_yap(oda_id):
    baglanti = veri_tabanina_baglan()

    if baglanti is None:
        return {"hata": "Veri tabanına bağlanılamadı"}
    
    cursor = baglanti.cursor()

    try:

        sorgu = "SELECT durum FROM odalar WHERE id = %s;"
        cursor.execute(sorgu,(oda_id,))
        oda = cursor.fetchone()

        if not oda:
            return {"hata": "Oda bulunamadı"}
        
        if oda["durum"] != "Kirli":
            return {"hata": f"Sadece kirli odalar temizlendi olarak işaretlenebilir. Oda Durumu: {oda['durum']}"}
        
        oda_guncelle = "UPDATE odalar SET durum = 'Bos' WHERE id = %s;"
        cursor.execute(oda_guncelle,(oda_id))

        baglanti.commit()
        return {"mesaj": "Oda başarıyla temizlendi ve satışa hazır duruma getirildi."}

    
    except mysql.connector.Error as e:
        print(f"Check-clear sırasında hata {e}")
        return {"hata": f" Veri tabanı hatası: {e}"}
    
    finally:
        cursor.close()
        baglanti.close()