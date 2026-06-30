import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Security , Depends , Query
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel, Field
from datetime import date
from sorgular import *

load_dotenv()

app = FastAPI()

API_ANAHTAR_ADI = "X-API-KEY"
SABIT_API_KEY = os.getenv("MY_API_KEY")

api_key_header = APIKeyHeader(name=API_ANAHTAR_ADI, auto_error=True)

def api_key_kontrol(gelen_key: str = Depends(api_key_header)):
    if gelen_key != SABIT_API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Yetkisiz erişim: Yetersiz API anahtarı!"
        )
    return gelen_key


class OdaSema(BaseModel):
    oda_numarasi: int
    tip: str
    fiyat: float

class RezSema(BaseModel):
    oda_id: int
    musteri_adi: str
    giris_tarihi: date
    cikis_tarihi: date

class SezSema(BaseModel):
    sezon_adi: str
    baslangic_tarihi: date
    bitis_tarihi: date
    fiyat_carpani: float

@app.get("/")
def ana_sayfa():
    return {"mesaj": "Antalya Otel Rezervasyon API'sine Hoş Geldiniz!"}

@app.get("/odalar")
def odalar_listele():
    sonuc = tum_odaları_getir()
    return sonuc

@app.get("/rezervasyonlar")
def rezervasyonlar_listele():
    sonuc = tum_rezervasyonlari_getir()
    return sonuc

@app.post("/odalar")
def oda_olustur(oda: OdaSema , api_key: str = Depends(api_key_kontrol)):

    sonuc = yeni_oda_ekle(oda.oda_numarasi, oda.tip, oda.fiyat)
    return sonuc

@app.post("/rezervasyon_yap")
def rezervasyon_olustur(rez: RezSema):
    sonuc = rezervasyon_yap(rez.oda_id, rez.musteri_adi, rez.giris_tarihi, rez.cikis_tarihi )

    if "hata" in sonuc:
        raise HTTPException(status_code=400, detail=sonuc["hata"])
    
    return sonuc

@app.post("/sezon_ekle")
def sezon_olustur(sez: SezSema , api_key: str = Depends(api_key_kontrol)):
    sonuc = sezon_ekle(sez.sezon_adi, sez.baslangic_tarihi, sez.bitis_tarihi, sez.fiyat_carpani)

    if "hata" in sonuc:
        raise HTTPException(status_code=400, detail=sonuc["hata"])
    
    return sonuc

@app.get("/sezonlar")
def sezonlar_listele(api_key: str = Depends(api_key_kontrol)):
    sonuc = tum_sezonları_getir()

    if "hata" in sonuc:
        raise HTTPException(status_code=400, detail=sonuc["hata"])
    
    return sonuc

@app.post("/check_in")
def check_in(rezervasyon_id: int ,api_key: str = Depends(api_key_kontrol)):
    sonuc = check_in_yap(rezervasyon_id)
    if "hata" in sonuc:
        raise HTTPException(status_code=400, detail=sonuc["hata"])

    return sonuc

@app.post("/check_out")
def check_out(rezervasyon_id: int ,api_key: str = Depends(api_key_kontrol)):
    sonuc = check_out_yap(rezervasyon_id)
    if "hata" in sonuc:
        raise HTTPException(status_code=400, detail=sonuc["hata"])

    return sonuc

@app.post("/check_clear")
def check_clear(oda_id: int , api_key: str = Depends(api_key_kontrol)):
    sonuc = check_clear_yap(oda_id)
    if "hata" in sonuc:
        raise HTTPException(status_code=400, detail=sonuc["hata"])

    return sonuc

@app.get("/uygun_odalar")
def  uygun_odalari_getir(
    giris_tarihi: date = Query(..., description="Giriş Tarihi (YYYY-MM-DD)"), 
    cikis_tarihi: date = Query(..., description="Çıkış Tarihi (YYYY-MM-DD)")
    ):

    giris_str = giris_tarihi.strftime("%Y-%m-%d")
    cikis_str = cikis_tarihi.strftime("%Y-%m-%d")

    sonuc = uygun_odalari_listeleme(giris_str , cikis_str)

    if "hata" in sonuc:
        raise HTTPException(status_code=400, detail=sonuc["hata"])
    
    return sonuc