# models.py
import sqlite3
def get_db_connection():
    conn = sqlite3.connect('anonymDb.db') 
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    """Tabloları oluşturur (gerekli olduğunda manuel çağırabilirsiniz)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    create_tables_script = """
    BEGIN TRANSACTION;
    
    CREATE TABLE IF NOT EXISTS Makale (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        takip_numarasi TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL,
        baslik TEXT,
        pdfFile BLOB NOT NULL,
        anonimPdf BLOB,
        durum TEXT NOT NULL DEFAULT 'Uploaded',
        yukleme_tarihi TEXT DEFAULT (datetime('now'))
    );
    
    CREATE TABLE IF NOT EXISTS Hakem (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ad TEXT NOT NULL,
        uzmanlik TEXT
    );
    
    CREATE TABLE IF NOT EXISTS Degerlendirme (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        makale_id INTEGER NOT NULL,
        hakem_id INTEGER NOT NULL,
        degerlendirme_metin TEXT,
        tarih TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (makale_id) REFERENCES Makale(id),
        FOREIGN KEY (hakem_id) REFERENCES Hakem(id)
    );
    
    CREATE TABLE IF NOT EXISTS Mesajlar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        makale_id INTEGER NOT NULL,
        gonderen TEXT NOT NULL,
        icerik TEXT NOT NULL,
        tarih TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (makale_id) REFERENCES Makale(id)
    );
    
    CREATE TABLE IF NOT EXISTS LogKayitlari (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        makale_id INTEGER NOT NULL,
        mesaj TEXT NOT NULL,
        tarih TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (makale_id) REFERENCES Makale(id)
    );
    
    COMMIT;
    """
    cursor.executescript(create_tables_script)
    
    conn.commit()
    conn.close()




def insert_makale(takip_numarasi, email, baslik, pdf_data):
    """
    Yeni bir makale kaydı ekler.
      - pdf_data = makale PDF dosyasının byte verisi (BLOB)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
    INSERT INTO Makale (takip_numarasi, email, baslik, pdfFile)
    VALUES (?, ?, ?, ?)
    """
    cursor.execute(query, (takip_numarasi, email, baslik, pdf_data))
    
    conn.commit()
    conn.close()


def get_makale_by_takip_no_and_email(takip_numarasi, email):
    """
    Verilen takip_numarasi ve email'e ait makale kaydını getirir.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM Makale WHERE takip_numarasi = ? AND email = ?"
    cursor.execute(query, (takip_numarasi, email))
    row = cursor.fetchone()
    conn.close()
    return row


def get_all_makaleler():
    """
    Tüm makale kayıtlarını döndürür.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM Makale"
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_makale_by_id(makale_id):
    """
    Makale ID'sine göre makale kaydını getirir.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM Makale WHERE id = ?"
    cursor.execute(query, (makale_id,))
    makale = cursor.fetchone()
    conn.close()
    return makale

def get_makale_by_id(makale_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Makale WHERE id = ?", (makale_id,))
    makale = cursor.fetchone()
    conn.close()
    return makale


def get_messages_by_makale_id(makale_id):
    """
    Belirtilen makale_id'ye ait mesajları tarih sırasına göre döndürür.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM Mesajlar WHERE makale_id = ? ORDER BY tarih ASC"
    cursor.execute(query, (makale_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def insert_message(makale_id, gonderen, icerik):
    """
    Mesajlar tablosuna yeni bir mesaj ekler.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "INSERT INTO Mesajlar (makale_id, gonderen, icerik) VALUES (?, ?, ?)"
    cursor.execute(query, (makale_id, gonderen, icerik))
    conn.commit()
    conn.close()


def insert_degerlendirme(makale_id, hakem_id):
    """
    Degerlendirme tablosuna bir satır ekler.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    INSERT INTO Degerlendirme (makale_id, hakem_id, degerlendirme_metin)
    VALUES (?, ?, ?)
    """
    # degerlendirme_metin şimdilik boş veya 'Atandı' gibi sabit bir şey olabilir
    cursor.execute(query, (makale_id, hakem_id, 'Atama yapıldı'))
    conn.commit()
    conn.close()


def check_assignment(makale_id):
    """
    Degerlendirme tablosundan bu makale_id'ye ait herhangi bir hakem ataması var mı?
    Varsa hakem bilgileriyle birlikte döndür (join veya iki sorgu da yapabilirsiniz).
    Yoksa None döndür.
    """
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Burada basitçe hakem_id, Hakem tablosundan ad, uzmanlık bilgisini join ile çekiyoruz
    query = """
    SELECT 
        Degerlendirme.id AS deg_id,
        Degerlendirme.makale_id,
        Degerlendirme.hakem_id,
        Hakem.ad AS hakem_ad,
        Hakem.uzmanlik AS hakem_uzmanlik,
        Degerlendirme.degerlendirme_metin,
        Degerlendirme.tarih
    FROM Degerlendirme
    JOIN Hakem ON Degerlendirme.hakem_id = Hakem.id
    WHERE Degerlendirme.makale_id = ?
    """
    cursor.execute(query, (makale_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "deg_id": row["deg_id"],
            "makale_id": row["makale_id"],
            "hakem_id": row["hakem_id"],
            "hakem_ad": row["hakem_ad"],
            "hakem_uzmanlik": row["hakem_uzmanlik"],
            "degerlendirme_metin": row["degerlendirme_metin"],
            "tarih": row["tarih"]
        }
    else:
        return None

def get_all_reviewers():
    """
    Hakem tablosundaki tüm kayıtları döndürür.
    """
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = "SELECT * FROM Hakem"
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_degerlendirme(makale_id, new_hakem_id):
    """
    Mevcut makaleye ait Degerlendirme kaydını günceller (hakem_id'yi değiştirir).
    Eğer istersek makale_id'ye göre update yapabiliriz (tek atama varsa).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
    UPDATE Degerlendirme
    SET hakem_id = ?
    WHERE makale_id = ?
    """
    cursor.execute(query, (new_hakem_id, makale_id))
    conn.commit()
    conn.close()


def update_anon_pdf(makale_id, anon_pdf_bytes):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = "UPDATE Makale SET anonimPdf = ? WHERE id = ?"
    cursor.execute(sql, (anon_pdf_bytes, makale_id))
    conn.commit()
    conn.close()    