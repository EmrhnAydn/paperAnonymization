# pdfBluring.py
import cv2
import pdf2image
import numpy as np
from PIL import Image
import img2pdf
import os
from io import BytesIO

def blur_pdf_images(pdf_bytes, poppler_path=r"YOUR PATH AND/poppler-24.08.0\Library\bin"): #USE poppler-24.08.0
    """
    PDF içindeki sayfalardaki yüzleri bulanıklaştırarak yeni bir PDF döndürür.

    Parameters:
        pdf_bytes (bytes): Giriş PDF dosyasının byte verisi.
        poppler_path (str): Poppler kütüphanesinin yüklü olduğu dizin.

    Returns:
        bytes: Blurlanmış PDF dosyasının byte verisi.
    """
    # PDF'i sayfa görsellerine çevirme
    pages = pdf2image.convert_from_bytes(pdf_bytes, dpi=300, poppler_path=poppler_path)
    
    processed_images = []
    # Haar Cascade yüz tespit modelini yükleme
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    
    temp_files = []
    
    for i, page in enumerate(pages):
        # PIL Image'den OpenCV formatına (RGB -> BGR) çevirme
        open_cv_image = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)
        
        # Yüz tespiti için gri tonlamaya çevirme
        gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
        
        # Yüz tespiti
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        
        # Tespit edilen yüzleri blurlama
        for (x, y, w, h) in faces:
            face_region = open_cv_image[y:y+h, x:x+w]
            blurred_face = cv2.GaussianBlur(face_region, (99, 99), 30)
            open_cv_image[y:y+h, x:x+w] = blurred_face
        
        # İşlenmiş sayfayı PIL Image formatına çevirme
        processed_image = Image.fromarray(cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2RGB))
        processed_images.append(processed_image)
        
        # Geçici dosya olarak kaydetme
        temp_filename = f"temp_page_{i}.jpg"
        processed_image.save(temp_filename, "JPEG")
        temp_files.append(temp_filename)
    
    # Geçici kaydedilen sayfalardan yeni PDF oluşturma
    blurred_pdf_bytes = img2pdf.convert(temp_files)
    
    # Geçici dosyaları silme
    for temp_file in temp_files:
        os.remove(temp_file)
    
    return blurred_pdf_bytes
