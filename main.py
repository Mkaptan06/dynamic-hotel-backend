from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from datetime import date
from sorgular import *

app = FastAPI()

class OdaSema(BaseModel):
    oda_numarasi: str
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
def oda_olustur(oda: OdaSema):

    sonuc = yeni_oda_ekle(oda.oda_numarasi, oda.tip, oda.fiyat)
    return sonuc

@app.post("/rezervasyon_yap")
def rezervasyon_olustur(rez: RezSema):
    sonuc = rezervasyon_yap(rez.oda_id, rez.musteri_adi, rez.giris_tarihi, rez.cikis_tarihi )

    if "hata" in sonuc:
        raise HTTPException(status_code=400, detail=sonuc["hata"])
    
    return sonuc

@app.post("/sezon_ekle")
def sezon_olustur(sez: SezSema):
    sonuc = sezon_ekle(sez.sezon_adi, sez.baslangic_tarihi, sez.bitis_tarihi, sez.fiyat_carpani)
    if "hata" in sonuc:
        raise HTTPException(status_code=400, detail=sonuc["hata"])
    return sonuc

@app.get("/sezonlar")
def sezonlar_listele():
    sonuc = tum_sezonları_getir()
    return sonuc