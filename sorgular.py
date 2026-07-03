import aiomysql
from database import veri_tabani_havuzu_getir
from datetime import datetime, date

# Veri tabanındaki tüm odaları listeleme
async def tum_odaları_getir():
    pool = veri_tabani_havuzu_getir()
    if pool is None:
        return {"hata": "Veri tabanı havuzu başlatılamadı"}

    async with pool.acquire() as baglanti:
        async with baglanti.cursor(aiomysql.DictCursor) as cursor:
            try:
                sql_sorgusu = "SELECT * FROM odalar;"
                await cursor.execute(sql_sorgusu)
                odalar = await cursor.fetchall()
                return odalar
            except Exception as e:
                print(f"Odalar getirilirken hata: {e}")
                return {"hata": f"Veri tabanı hatası: {e}"}

# Veri tabanındaki tüm rezervasyonları listeleme
async def tum_rezervasyonlari_getir():
    pool = veri_tabani_havuzu_getir()
    if pool is None:
        return {"hata": "Veri tabanı havuzu başlatılamadı"}
    
    async with pool.acquire() as baglanti:
        async with baglanti.cursor(aiomysql.DictCursor) as cursor:
            try:
                sql_sorgusu = "SELECT * FROM rezervasyonlar;"
                await cursor.execute(sql_sorgusu)
                rezervasyonlar = await cursor.fetchall()
                return rezervasyonlar
            except Exception as e:
                print(f"Rezervasyonlar getirilirken hata: {e}")
                return {"hata": f"Veri tabanı hatası: {e}"}

# Yeni oda ekleme
async def yeni_oda_ekle(oda_numarasi, tip, fiyat):
    pool = veri_tabani_havuzu_getir()
    if pool is None:
        return {"hata": "Veri tabanı havuzu başlatılamadı"}
    
    async with pool.acquire() as baglanti:
        async with baglanti.cursor() as cursor:
            try:
                sql_sorgusu = "INSERT INTO odalar(oda_numarasi, tip, fiyat) VALUES (%s, %s, %s);"
                degerler = (oda_numarasi, tip, float(fiyat))

                await cursor.execute(sql_sorgusu, degerler)
                yeni_id = cursor.lastrowid
                return {"mesaj": "Oda başarıyla eklendi", "oda_id": yeni_id}
            except Exception as e:
                print(f"Veri ekleme sırasında Hata: {e}")
                return {"hata": f"Veri tabanı hatası: {e}"}

# Rezervasyon yapma
async def rezervasyon_yap(oda_id, musteri_adi, giris_tarihi, cikis_tarihi):
    pool = veri_tabani_havuzu_getir()
    if pool is None:
        return {"hata": "Veri tabanı havuzu başlatılamadı"}

    async with pool.acquire() as baglanti:
        async with baglanti.cursor(aiomysql.DictCursor) as cursor:
            try:
                oda_fiyat_sorgusu = "SELECT fiyat, durum FROM odalar WHERE id = %s"
                await cursor.execute(oda_fiyat_sorgusu, (oda_id,))
                oda_sonuc = await cursor.fetchone()

                if not oda_sonuc:
                    return {"hata": "Oda bulunamadı."}

                if oda_sonuc["durum"] != "Bos":
                    return {"hata": f"Bu oda şu anda rezervasyon için uygun değil. Oda Durumu: {oda_sonuc['durum']}"}
                
                kontrol_sorgusu = """
                SELECT id FROM rezervasyonlar
                WHERE oda_id = %s
                AND durum NOT IN ('CikisYapildi', 'Iptal')
                AND NOT (%s >= cikis_tarihi OR %s <= giris_tarihi);
                """
                await cursor.execute(kontrol_sorgusu, (oda_id, str(giris_tarihi), str(cikis_tarihi)))
                mevcut_rezervasyon = await cursor.fetchone()

                if mevcut_rezervasyon:
                    return {"hata": "Bu oda seçilen tarih aralığında zaten dolu."}
                
                fiyat_sorgusu = """
                WITH RECURSIVE gunler AS (
                    SELECT %s AS gun
                    UNION ALL
                    SELECT DATE_ADD(gun, INTERVAL 1 DAY)
                    FROM gunler
                    WHERE DATE_ADD(gun, INTERVAL 1 DAY) < %s
                )    
                SELECT COALESCE(SUM(COALESCE(s.fiyat_carpani, 1.00)), 0) AS toplam_carpan
                FROM gunler g
                LEFT JOIN sezonlar s ON g.gun BETWEEN s.baslangic_tarihi AND s.bitis_tarihi;
                """
                await cursor.execute(fiyat_sorgusu, (str(giris_tarihi), str(cikis_tarihi)))
                sonuc = await cursor.fetchone()
                toplam_carpan = sonuc["toplam_carpan"] if sonuc else 0

                if toplam_carpan == 0:
                    return {"hata": "Tarih aralığı hesaplanamadı."}
                
                oda_baz_fiyati = oda_sonuc["fiyat"]
                gercek_toplam_tutar = float(toplam_carpan) * float(oda_baz_fiyati)

                ekleme_sorgusu = """
                    INSERT INTO rezervasyonlar (oda_id, musteri_adi, giris_tarihi, cikis_tarihi, total_fiyat, durum)
                    VALUES(%s, %s, %s, %s, %s, 'Onaylandi')
                """
                degerler = (oda_id, musteri_adi, str(giris_tarihi), str(cikis_tarihi), gercek_toplam_tutar)
                await cursor.execute(ekleme_sorgusu, degerler)

                yeni_rezervasyon_id = cursor.lastrowid
                return {"mesaj": "Rezervasyon başarıyla oluşturuldu", "rezervasyon_id": yeni_rezervasyon_id, "hesaplanan_toplam_carpan": gercek_toplam_tutar}
            
            except Exception as e:
                print(f"Rezervasyon sırasında hata: {e}")
                return {"hata": f"Veri tabanı hatası: {e}"}

# Sezon ekleme
async def sezon_ekle(sezon_adi, baslangic_tarihi, bitis_tarihi, fiyat_carpani):
    pool = veri_tabani_havuzu_getir()
    if pool is None:
        return {"hata": "Veri tabanı havuzu başlatılamadı"}

    async with pool.acquire() as baglanti:
        async with baglanti.cursor() as cursor:
            try:
                sql_sorgusu = "INSERT INTO sezonlar(sezon_adi, baslangic_tarihi, bitis_tarihi, fiyat_carpani) VALUES (%s, %s, %s, %s);"
                degerler = (sezon_adi, str(baslangic_tarihi), str(bitis_tarihi), float(fiyat_carpani))

                await cursor.execute(sql_sorgusu, degerler)
                yeni_id = cursor.lastrowid
                return {"mesaj": "Sezon başarıyla eklendi", "sezon_id": yeni_id}
            except Exception as e:
                print(f"Sezon ekleme sırasında Hata: {e}")
                return {"hata": f"Veri tabanı hatası: {e}"}
    
# Veri tabanındaki tüm sezonları listeleme
async def tum_sezonları_getir():
    pool = veri_tabani_havuzu_getir()
    if pool is None:
        return {"hata": "Veri tabanı havuzu başlatılamadı"}

    async with pool.acquire() as baglanti:
        async with baglanti.cursor(aiomysql.DictCursor) as cursor:
            try:
                sql_sorgusu = "SELECT * FROM sezonlar;"
                await cursor.execute(sql_sorgusu)
                sezonlar = await cursor.fetchall()
                return sezonlar
            except Exception as e:
                print(f"Sezonlar getirilirken hata: {e}")
                return {"hata": f"Veri tabanı hatası: {e}"}

# check_in işlemi
async def check_in_yap(rezervasyon_id):
    pool = veri_tabani_havuzu_getir()
    if pool is None:
        return {"hata": "Veri tabanı havuzu başlatılamadı"}

    async with pool.acquire() as baglanti:
        async with baglanti.cursor(aiomysql.DictCursor) as cursor:
            try:
                sorgu = """
                SELECT r.oda_id, r.giris_tarihi, r.durum AS rez_durum, o.durum as oda_durum
                FROM rezervasyonlar r
                JOIN odalar o ON r.oda_id = o.id
                WHERE r.id = %s;
                """
                await cursor.execute(sorgu, (rezervasyon_id,))
                rezervasyon = await cursor.fetchone()

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
                await cursor.execute(rez_guncelle, (rezervasyon_id,))

                oda_guncelle = "UPDATE odalar SET durum = 'Dolu' WHERE id=%s"
                await cursor.execute(oda_guncelle, (oda_id,))

                return {"mesaj": "Check-in işlemi başarıyla tamamlandı. Müşteri giriş yaptı."}
            
            except Exception as e:
                print(f"Check-in sırasında hata: {e}")
                return {"hata": f"Veri tabanı hatası: {e}"}
    
# check_out işlemi
async def check_out_yap(rezervasyon_id):
    pool = veri_tabani_havuzu_getir()
    if pool is None:
        return {"hata": "Veri tabanı havuzu başlatılamadı"}
    
    async with pool.acquire() as baglanti:
        async with baglanti.cursor(aiomysql.DictCursor) as cursor:
            try:
                sorgu = """
                SELECT r.oda_id, r.cikis_tarihi, r.durum AS rez_durum, o.durum AS oda_durum
                FROM rezervasyonlar r
                JOIN odalar o ON r.oda_id = o.id
                WHERE r.id = %s;
                """
                await cursor.execute(sorgu, (rezervasyon_id,))
                rezervasyon = await cursor.fetchone()

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
                await cursor.execute(rez_guncelle, (rezervasyon_id,))

                oda_guncelle = "UPDATE odalar SET durum = 'Kirli' WHERE id = %s"
                await cursor.execute(oda_guncelle, (oda_id,))

                return {"mesaj": "Check-out işlemi başarıyla tamamlandı. Müşteri çıkış yaptı."}
            
            except Exception as e:
                print(f"Check-out sırasında hata: {e}")
                return {"hata": f"Veri tabanı hatası: {e}"}

# check_clear işlemi
async def check_clear_yap(oda_id):
    pool = veri_tabani_havuzu_getir()
    if pool is None:
        return {"hata": "Veri tabanı havuzu başlatılamadı"}

    async with pool.acquire() as baglanti:
        async with baglanti.cursor(aiomysql.DictCursor) as cursor:
            try:
                sorgu = "SELECT durum FROM odalar WHERE id = %s;"
                await cursor.execute(sorgu, (oda_id,))
                oda = await cursor.fetchone()

                if not oda:
                    return {"hata": "Oda bulunamadı"}
                
                if oda["durum"] != "Kirli":
                    return {"hata": f"Sadece kirli odalar temizlendi olarak işaretlenebilir. Oda Durumu: {oda['durum']}"}
                
                oda_guncelle = "UPDATE odalar SET durum = 'Bos' WHERE id = %s;"
                await cursor.execute(oda_guncelle, (oda_id,))

                return {"mesaj": "Oda başarıyla temizlendi ve satışa hazır duruma getirildi."}
            except Exception as e:
                print(f"Check-clear sırasında hata: {e}")
                return {"hata": f"Veri tabanı hatası: {e}"}

# Tarihe uygun odaları listeleme 
async def uygun_odalari_listeleme(giris_tarihi, cikis_tarihi):
    pool = veri_tabani_havuzu_getir()
    if pool is None:
        return {"hata": "Veri tabanı havuzu başlatılamadı"}

    if giris_tarihi >= cikis_tarihi:
        return {"hata": "Giriş tarihi, çıkış tarihinden önce olmalıdır."}

    async with pool.acquire() as baglanti:
        async with baglanti.cursor(aiomysql.DictCursor) as cursor:
            try:
                sorgu = """ 
                WITH RECURSIVE gunler AS (
                SELECT %s AS GUN
                UNION ALL
                SELECT DATE_ADD(gun, INTERVAL 1 DAY)
                FROM gunler
                WHERE DATE_ADD(GUN, INTERVAL 1 DAY) < %s
                ),
                toplam_carpim_tablosu AS (
                SELECT COALESCE(SUM(COALESCE(s.fiyat_carpani, 1.00)), 0) AS toplam_carpan
                FROM gunler g 
                LEFT JOIN sezonlar s ON g.gun BETWEEN s.baslangic_tarihi AND s.bitis_tarihi
                )
                SELECT o.id, o.oda_numarasi, o.tip, (SELECT tct.toplam_carpan FROM toplam_carpim_tablosu tct) * o.fiyat AS Fiyat
                FROM odalar o 
                LEFT JOIN (
                    SELECT DISTINCT oda_id
                    FROM rezervasyonlar
                    WHERE durum NOT IN ('CikisYapildi', 'Iptal')
                        AND NOT (%s >= cikis_tarihi OR %s <= giris_tarihi)
                ) AS dolu_odalar ON o.id  = dolu_odalar.oda_id
                WHERE o.durum = 'Bos' AND dolu_odalar.oda_id IS NULL;
                """ 

                parametreler = (str(giris_tarihi), str(cikis_tarihi), str(giris_tarihi), str(cikis_tarihi))
                await cursor.execute(sorgu, parametreler)
                uygun_odalar = await cursor.fetchall()

                return {"uygun_odalar": uygun_odalar}
            except Exception as e:
                print(f"Uygun odalar listelenirken hata: {e}")
                return {"hata": f"Veri tabanı hatası: {e}"}