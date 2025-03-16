# expert_selector.py (specialization detection with NLP)
# expert_selector.py

import sqlite3
from io import BytesIO

# Eğer PyPDF2 kütüphanesi yoksa "pip install PyPDF2" komutu ile kurabilirsiniz.
import PyPDF2

# Basit bir anahtar kelime tabanlı eşleştirme yapmak için örnek kelime setleri
SUBJECT_KEYWORDS = {
    "Machine Learning": ["machine learning", "ml", "supervised", "unsupervised", "regression", "classification"],
    "Artificial Intelligence": ["artificial intelligence", "ai", "knowledge representation", "reasoning"],
    "Image Processing": ["image processing", "computer vision", "segmentation", "feature extraction"],
    "Cryptology": ["cryptology", "cryptography", "encryption", "decryption", "secure communication"],
    "Neural Network": ["neural network", "deep learning", "layer", "backpropagation"],
    "Reinforcement Learning": ["reinforcement learning", "agent", "reward", "q-learning", "policy gradient"],
    "Computer Network": ["computer network", "networking", "tcp/ip", "routing", "switching"],
    "Data Mining": ["data mining", "knowledge discovery", "cluster analysis"],
    "Cloud Computing": ["cloud computing", "virtualization", "distributed system"],
    "Cyber Security": ["cyber security", "cybersecurity", "intrusion detection", "malware"],
    "Big Data Analytics": ["big data", "spark", "hadoop", "analytics"],
    "Natural Language Processing": ["nlp", "natural language", "text processing", "language model"],
    "Bioinformatics": ["bioinformatics", "genomics", "proteomics", "sequence analysis"],
    "Robotics": ["robot", "robotics", "autonomous", "manipulator"],
    "Database Systems": ["database", "sql", "query", "transaction", "index"]
}

DB_NAME = "anonymDb.db"  # Sizin projenizdeki SQLite dosyası (ör: anonymDb.db vb.)

def guess_subject_area_from_pdf(pdf_path: str) -> str:
    """
    Bir PDF dosyasını okuyup (temel anahtar kelime analizi ile) en muhtemel uzmanlık alanını döndürür.
    pdf_path: PDF dosya yolu (örn: "makale.pdf")
    return: Tahmin edilen uzmanlık alanı (örn: "Machine Learning")
    """
    try:
        # 1) PDF dosyasını açalım
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text_content = ""
            
            # 2) Tüm sayfaları birleştirerek metin elde edelim
            for page in reader.pages:
                text_content += page.extract_text() or ""

    except Exception as e:
        print("PDF dosyası okunurken hata oluştu:", e)
        return "Unknown"  # Hata durumunda bilinmeyen olarak dön

    text_content = text_content.lower()  # Karşılaştırmaları kolaylaştırmak için küçük harfe dönüştür

    # 3) Basit anahtar kelime eşleştirmesi: Hangi konuya ait kelimeler daha çok geçiyorsa onu tahmin et
    best_subject = "Unknown"
    best_count = 0

    for subject_area, keywords in SUBJECT_KEYWORDS.items():
        count = 0
        for kw in keywords:
            if kw in text_content:
                count += text_content.count(kw)
        
        if count > best_count:
            best_count = count
            best_subject = subject_area

    return best_subject

def find_best_reviewer(subject_area: str) -> dict:
    """
    Verilen uzmanlık alanına en uygun hakemi (veya hakemlerden birini) veritabanından döndürür.
    subject_area: str - Örn: "Machine Learning"
    return: {"id": int, "ad": str, "uzmanlik": str} formatında bir sözlük veya None
    """
    # Veritabanına bağlan
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1) Tüm hakemleri çekelim
    query = "SELECT * FROM Hakem"
    cursor.execute(query)
    hakemler = cursor.fetchall()

    # 2) En uygun hakemi seçmek için basit bir benzerlik ölçüsü yapalım:
    #    Uzmanlık alanı ile subject_area'yı string olarak kıyaslayabiliriz 
    #    (örn. partial match, tam eşleşme, basit benzerlik gibi).
    best_hakem = None
    best_score = -1

    # Çok basit bir benzerlik: subject_area string'i hakemin uzmanlığında ne kadar geçiyor?
    # (Daha iyi bir yaklaşım: fuzzywuzzy, spaCy vb. ile semantic similarity)
    for hakem in hakemler:
        uzmanlik = hakem["uzmanlik"].lower()
        subject_lower = subject_area.lower()

        # Örnek puanlama: subject_area, hakemin uzmanlık metninde geçiyorsa +10 puan
        score = 0
        if subject_lower in uzmanlik:
            score += 10
        
        # Bazı ek heuristics eklemek isterseniz, burayı genişletebilirsiniz

        if score > best_score:
            best_score = score
            best_hakem = hakem

    conn.close()

    if best_hakem:
        # dict biçiminde döndürelim
        return {
            "id": best_hakem["id"],
            "ad": best_hakem["ad"],
            "uzmanlik": best_hakem["uzmanlik"]
        }
    else:
        return None