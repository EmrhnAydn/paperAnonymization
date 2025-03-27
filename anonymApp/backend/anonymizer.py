import re
import fitz  # PyMuPDF
from pdfminer.high_level import extract_text
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from io import BytesIO
import tempfile
import os


def encrypt_text_short(plain_text, key):
    key_bytes = key.encode('utf-8')  # Key 16, 24 veya 32 bayt olmalı
    cipher = AES.new(key_bytes, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(plain_text.encode('utf-8'), AES.block_size))
    encrypted_full = cipher.iv + ct_bytes  # IV + Ciphertext
    short_hex = encrypted_full.hex()[:16]  # Yalnızca ilk 16 karakter
    return short_hex


def _search_and_redact(doc, texts_to_encrypt, key):
    """
    doc (fitz.Document): PyMuPDF ile açtığımız PDF dokümanı
    texts_to_encrypt (set): PDF içinde arayacağımız metinler
    key (str): AES şifreleme anahtarı
    """
    for page_index in range(len(doc)):
        page = doc[page_index]
        for text in texts_to_encrypt:
            areas = page.search_for(text)
            for rect in areas:
                enc_text = encrypt_text_short(text, key)
                page.add_redact_annot(rect, text=enc_text, fill=(1, 1, 1))

    # Redaksiyonları uygulama (silme) aşaması
    for page in doc:
        page.apply_redactions()


def anonymize_pdf(pdf_bytes, key, anonymize_institutions=False, anonymize_people=False):
    """
    pdf_bytes: Veritabanından okuduğumuz PDF'in ham byte verisi
    key: AES şifreleme anahtarı (örnek: 16 bayt uzunluğunda bir string)
    anonymize_institutions: True ise kurum bilgilerini anonimleştirelim
    anonymize_people: True ise kişi bilgilerini anonimleştirelim

    Dönüş: Anonimleştirilmiş PDF'in bytes verisi
    """

    # 1) pdfminer'ın metin çıkarma fonksiyonu ham bytes yerine dosya yoluna ihtiyaç duyuyor.
    #    Bu nedenle geçici bir dosyaya yazalım:
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_bytes)
        tmp.flush()
        tmp_name = tmp.name  # Dosya yolumuz

    try:
        # 2) pdfminer ile text çıkar
        pdf_text = extract_text(tmp_name)

    finally:
        # Geçici dosyayı sildiğimizden emin olalım
        if os.path.exists(tmp_name):
            os.remove(tmp_name)

    # 3) fitz ile PDF'i hafızaya aç (PyMuPDF)
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    # 4) Anonimleştirilecek metinleri toplayacağımız set
    texts_to_encrypt = set()

    # a) Kurum bilgileri
    if anonymize_institutions:
        institution_pattern = re.compile(r'\b(university|institute|faculty|department)\b', re.IGNORECASE)
        locations_pattern = re.compile(r'\b(India|Turkey|United\s?States|USA|UK|England|France|Germany|Malaysia)\b', re.IGNORECASE)

        for match in institution_pattern.findall(pdf_text):
            texts_to_encrypt.add(match)
        for match in locations_pattern.findall(pdf_text):
            texts_to_encrypt.add(match)

    # b) Kişi bilgileri
    if anonymize_people:
        # E-postalar
        emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', pdf_text)
        for e in emails:
            texts_to_encrypt.add(e)

        # Basit isim-önek regex (çok basit bir örnek)
        names = re.findall(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', pdf_text)
        for n in names:
            texts_to_encrypt.add(n)

    # 5) Redaksiyon işlemi (eğer anonimleştirecek bir şey varsa)
    if texts_to_encrypt:
        _search_and_redact(doc, texts_to_encrypt, key)

    # 6) Bellekteki PDF'i tekrar bytes'a dönüştür
    anonymized_pdf_bytes = doc.write()
    doc.close()
    return anonymized_pdf_bytes
