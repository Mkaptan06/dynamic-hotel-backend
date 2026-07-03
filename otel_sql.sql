USE antalya_otel_db;

CREATE TABLE IF NOT EXISTS odalar (
    id INT AUTO_INCREMENT PRIMARY KEY,
    oda_numarasi VARCHAR(10) NOT NULL,
    tip VARCHAR(50),
    fiyat DECIMAL(10, 2),
    durum VARCHAR(20) DEFAULT 'Bos'
);

CREATE TABLE IF NOT EXISTS rezervasyonlar (
    id INT AUTO_INCREMENT PRIMARY KEY,
    oda_id INT,
    musteri_adi VARCHAR(100) NOT NULL,
    giris_tarihi DATE,
    cikis_tarihi DATE,
    total_fiyat DECIMAL(10, 2) NOT NULL,
    durum VARCHAR(20) DEFAULT 'Onaylandi',
    FOREIGN KEY (oda_id) REFERENCES odalar(id)
);

CREATE TABLE IF NOT EXISTS sezonlar (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sezon_adi VARCHAR(50) NOT NULL,
    baslangic_tarihi DATE NOT NULL,
    bitis_tarihi DATE NOT NULL,
    fiyat_carpani DECIMAL(5, 2) NOT NULL
);

CREATE INDEX idx_sezon_tarihi ON sezonlar (baslangic_tarihi, bitis_tarihi);

CREATE TABLE rapor_gecmis_rezervasyonlar (
	id INT AUTO_INCREMENT PRIMARY KEY,
    rezervasyon_id INT,
    oda_numarasi VARCHAR(10),
    oda_tipi VARCHAR(50),
    giris_tarihi DATE,
    cikis_tarihi DATE,
    total_fiyat DECIMAL(10, 2)
);

INSERT INTO sezonlar (sezon_adi, baslangic_tarihi, bitis_tarihi, fiyat_carpani) VALUES
('Düşük Sezon (Kış)', '2026-01-01', '2026-05-31', 0.80),  
('Yüksek Sezon (Yaz)', '2026-06-01', '2026-08-31', 1.50), 
('Orta Sezon (Sonbahar)', '2026-09-01', '2026-12-31', 1.00);


DELIMITER //
CREATE TRIGGER rezervasyon_raporla
AFTER INSERT ON rezervasyonlar
FOR EACH ROW
BEGIN
	DECLARE v_oda_numarasi VARCHAR(10);
    DECLARE v_oda_tipi VARCHAR(50);
    
    SELECT oda_numarasi , tip INTO v_oda_numarasi , v_oda_tipi
    FROM odalar
    WHERE id = NEW.oda_id;
    
    INSERT INTO rapor_gecmis_rezervasyonlar 
    (rezervasyon_id, oda_numarasi, oda_tipi, giris_tarihi, cikis_tarihi, total_fiyat)
    VALUES 
    (NEW.id, v_oda_numarasi, v_oda_tipi, NEW.giris_tarihi, NEW.cikis_tarihi, NEW.total_fiyat);
    
END //
DELIMITER ;
