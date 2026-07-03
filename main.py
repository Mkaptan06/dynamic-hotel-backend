import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Security , Depends , Query
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel, Field , field_validator ,model_validator
from datetime import date
from database import asenkron_havuz_baslat, asenkron_havuz_kapat
from sorgular import *


@asynccontextmanager
async def lifespan(app: FastAPI):
    
    await asenkron_havuz_baslat()
    yield
    await asenkron_havuz_kapat()

app = FastAPI(lifespan=lifespan)


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

    @field_validator('fiyat')
    def fiyat_kontrolu(cls , v):
        if v <= 0:
            raise ValueError('Oda fiyatı 0 veya negatif olamaz.')
        return v

class RezSema(BaseModel):
    oda_id: int
    musteri_adi: str
    giris_tarihi: date
    cikis_tarihi: date

    @model_validator(mode='after')
    def tarih_kontrolu(self):
        if self.giris_tarihi >= self.cikis_tarihi:
            raise ValueError('Giriş tarihi, çıkış tarihinden önce olmalıdır.')
        if self.giris_tarihi < date.today():
            raise ValueError('Geçmiş bir tarihe rezervasyon yapılamaz.')
        return self

class SezSema(BaseModel):
    sezon_adi: str
    baslangic_tarihi: date
    bitis_tarihi: date
    fiyat_carpani: float

@app.get("/")
async def ana_sayfa():
    return {"mesaj": "Antalya Otel Rezervasyon API'sine Hoş Geldiniz!"}

@app.get("/odalar")
async def odalar_listele():
    sonuc = await tum_odaları_getir()
    return sonuc

@app.get("/rezervasyonlar")
async def rezervasyonlar_listele():
    sonuc =await tum_rezervasyonlari_getir()
    return sonuc

@app.post("/odalar")
async def oda_olustur(oda: OdaSema , api_key: str = Depends(api_key_kontrol)):

    sonuc =await yeni_oda_ekle(oda.oda_numarasi, oda.tip, oda.fiyat)
    return sonuc

@app.post("/rezervasyon_yap")
async def rezervasyon_olustur(rez: RezSema , api_key: str = Depends(api_key_kontrol)):
    sonuc = await rezervasyon_yap(rez.oda_id, rez.musteri_adi, rez.giris_tarihi, rez.cikis_tarihi )

    if "hata" in sonuc:
        raise HTTPException(status_code=400, detail=sonuc["hata"])
    
    return sonuc

@app.post("/sezon_ekle")
async def sezon_olustur(sez: SezSema , api_key: str = Depends(api_key_kontrol)):
    sonuc = await sezon_ekle(sez.sezon_adi, sez.baslangic_tarihi, sez.bitis_tarihi, sez.fiyat_carpani)

    if "hata" in sonuc:
        raise HTTPException(status_code=400, detail=sonuc["hata"])
    
    return sonuc

@app.get("/sezonlar")
async def sezonlar_listele(api_key: str = Depends(api_key_kontrol)):
    sonuc =await tum_sezonları_getir()

    if "hata" in sonuc:
        raise HTTPException(status_code=400, detail=sonuc["hata"])
    
    return sonuc

@app.post("/check_in")
async def check_in(rezervasyon_id: int ,api_key: str = Depends(api_key_kontrol)):
    sonuc =await check_in_yap(rezervasyon_id)
    if "hata" in sonuc:
        raise HTTPException(status_code=400, detail=sonuc["hata"])

    return sonuc

@app.post("/check_out")
async def check_out(rezervasyon_id: int ,api_key: str = Depends(api_key_kontrol)):
    sonuc =await check_out_yap(rezervasyon_id)
    if "hata" in sonuc:
        raise HTTPException(status_code=400, detail=sonuc["hata"])

    return sonuc

@app.post("/check_clear")
async def check_clear(oda_id: int , api_key: str = Depends(api_key_kontrol)):
    sonuc =await check_clear_yap(oda_id)
    if "hata" in sonuc:
        raise HTTPException(status_code=400, detail=sonuc["hata"])

    return sonuc

@app.get("/uygun_odalar")
async def  uygun_odalari_getir(
    giris_tarihi: date = Query(..., description="Giriş Tarihi (YYYY-MM-DD)"), 
    cikis_tarihi: date = Query(..., description="Çıkış Tarihi (YYYY-MM-DD)")
    ):

    giris_str = giris_tarihi.strftime("%Y-%m-%d")
    cikis_str = cikis_tarihi.strftime("%Y-%m-%d")

    sonuc = await uygun_odalari_listeleme(giris_tarihi, cikis_tarihi)
    if "hata" in sonuc:
        raise HTTPException(status_code=400, detail=sonuc["hata"])
    
    return sonuc