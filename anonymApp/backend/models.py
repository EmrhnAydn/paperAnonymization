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