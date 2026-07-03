# 🏨 Otel Rezervasyon API

FastAPI ve MySQL kullanılarak geliştirilmiş, otel rezervasyon süreçlerini yöneten RESTful API projesidir.

## 🚀 Özellikler

- Oda ekleme ve listeleme
- Rezervasyon oluşturma
- Sezon bazlı dinamik fiyatlandırma
- Check-in / Check-out işlemleri
- Oda temizlik yönetimi
- Tarihe göre uygun oda sorgulama
- API Key ile yetkilendirme
- Pydantic ile veri doğrulama

---

## 🛠️ Kullanılan Teknolojiler

- Python
- FastAPI
- MySQL
- aiomysql
- Pydantic
- Uvicorn

---

## 📂 Proje Yapısı

```
├── main.py
├── database.py
├── sorgular.py
├── otel_sql.sql
└── requirements.txt
```

---

## ⚙️ Kurulum

```bash
git clone <repo-link>

cd otel-rezervasyon-api

pip install -r requirements.txt

uvicorn main:app --reload
```

Swagger:

```
http://127.0.0.1:8000/docs
```

---

## 📌 API Endpointleri

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| GET | /odalar | Odaları listele |
| POST | /odalar | Yeni oda ekle |
| GET | /rezervasyonlar | Rezervasyonları listele |
| POST | /rezervasyon_yap | Rezervasyon oluştur |
| POST | /sezon_ekle | Sezon ekle |
| GET | /sezonlar | Sezonları listele |
| POST | /check_in | Check-in |
| POST | /check_out | Check-out |
| POST | /check_clear | Odayı temizle |
| GET | /uygun_odalar | Uygun odaları getir |

---

## 🗄️ Veritabanı

Projede aşağıdaki tablolar kullanılmaktadır:

- odalar
- rezervasyonlar
- sezonlar
- rapor_gecmis_rezervasyonlar

---

## 👨‍💻 Geliştirici

**Mustafa Kaptan**