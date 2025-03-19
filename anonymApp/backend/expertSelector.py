# expertSelector.py

import sqlite3
import re
from io import BytesIO
import PyPDF2

DB_NAME = "anonymDb.db"  # SQLite dosyanızın adı

# Mevcut SUBJECT_KEYWORDS sözlüğü
SUBJECT_KEYWORDS = {
    "Machine Learning and Artificial Intelligence": [
        "deep learning",
        "natural language processing",
        "computer vision",
        "generative ai",
        "machine learning",
        "artificial intelligence",
        "neural networks",
        "ml algorithms",
        "ai-based",
        "supervised learning",
        "unsupervised learning",
        "reinforcement learning",
        "predictive modeling",
        "automated machine learning",
        "machine intelligence"
    ],
    "Network and Distributed Systems": [
        "5g and next-generation networks",
        "cloud computing",
        "blockchain technology",
        "p2p",
        "decentralized systems",
        "distributed computing",
        "network protocols",
        "software-defined networking",
        "sdn",
        "network virtualization",
        "edge computing",
        "network architecture",
        "internet of things",
        "iot"
    ],
    "Cyber Security": [
        "encryption software",
        "secure software development",
        "network security",
        "identity-aware systems",
        "digital forensics",
        "cyber threats",
        "intrusion detection",
        "malware analysis",
        "cyber defense",
        "penetration testing",
        "risk assessment",
        "data privacy",
        "security vulnerabilities",
        "phishing",
        "zero-day"
    ],
    "Big Data Analytics": [
        "big data",
        "data mining",
        "data visualization",
        "data processing systems (hadoop, spark)",
        "time series analysis",
        "structured data",
        "unstructured data",
        "predictive analytics",
        "data warehousing",
        "data lake",
        "etl",
        "real-time analytics",
        "statistical modeling",
        "business intelligence",
        "large-scale data"
    ],
    "Human Computer Interaction": [
        "brain computer interface (bci)",
        "user experience design",
        "augmented and virtual reality (ar/vr)",
        "hci",
        "usability testing",
        "user-centered design",
        "interaction design",
        "human factors",
        "gesture recognition",
        "eye tracking",
        "wearable technology",
        "tangible computing",
        "ux",
        "human-computer collaboration"
    ],
}

def count_keyword_occurrences(text: str, keyword: str) -> int:
    pattern = r"\b" + re.escape(keyword.lower()) + r"\b"
    return len(re.findall(pattern, text))

def get_pdf_from_db(makale_id: int):
    """
    Veritabanından ilgili makale_id'nin pdfFile kolonunu çekip bytes döndürür.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT pdfFile FROM Makale WHERE id = ?", (makale_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]  # BLOB veri
    return None

def guess_subject_area_from_db(makale_id: int) -> str:
    """
    Makale veritabanından PDF'i çek, anahtar kelime analiziyle alanı döndür.
    """
    pdf_data = get_pdf_from_db(makale_id)
    if not pdf_data:
        return "Unknown"

    # PDF'i bellek içi (BytesIO) üzerinden okuyacağız
    pdf_file_like = BytesIO(pdf_data)

    try:
        reader = PyPDF2.PdfReader(pdf_file_like)
        text_content = ""
        for page in reader.pages:
            text_content += page.extract_text() or ""
    except Exception as e:
        print("PDF okuma hatası:", e)
        return "Unknown"

    text_content = text_content.lower()

    best_subject = "Unknown"
    best_count = 0

    for subject_area, keywords in SUBJECT_KEYWORDS.items():
        count = 0
        for kw in keywords:
            count += count_keyword_occurrences(text_content, kw)
        if count > best_count:
            best_count = count
            best_subject = subject_area

    return best_subject

def find_best_reviewer(subject_area: str):
    """
    Verilen alan string'i için en uygun hakemi (Hakem tablosundan) bul.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Hakem")
    hakemler = cursor.fetchall()

    best_hakem = None
    best_score = -1
    subject_lower = subject_area.lower()

    for hakem in hakemler:
        uzmanlik = hakem["uzmanlik"].lower()
        score = 0
        # subject_area kelimesini uzmanlik metninde bulursa +10 puan
        if subject_lower in uzmanlik:
            score += 10
        if score > best_score:
            best_score = score
            best_hakem = hakem

    conn.close()

    if best_hakem:
        return {
            "id": best_hakem["id"],
            "ad": best_hakem["ad"],
            "uzmanlik": best_hakem["uzmanlik"]
        }
    return None
