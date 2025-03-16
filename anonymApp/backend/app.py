from flask import Flask, render_template, request, redirect, url_for, flash, session,send_file
import os
import uuid
from io import BytesIO 

from models import (
    insert_makale, 
    get_makale_by_takip_no_and_email, 
    initialize_database, 
    get_all_makaleler, 
    get_makale_by_id,
    get_messages_by_makale_id,
    insert_message
)

app = Flask(__name__, template_folder='../frontend/templates')
app.secret_key = "super_secret_key"

initialize_database()  # Tabloların oluşması için (isteğe bağlı otomatik)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/makale-yukle', methods=['GET', 'POST'])
def makale_yukle():
    if request.method == 'POST':
        email = request.form.get('email')
        baslik = request.form.get('baslik')
        pdf_file = request.files.get('pdf_file')

        if not pdf_file:
            flash("Lütfen bir PDF dosyası yükleyiniz.", "warning")
            return redirect(url_for('makale_yukle'))

        pdf_data = pdf_file.read()
        file_size = len(pdf_data)
        takip_numarasi = str(uuid.uuid4())[:8]

        insert_makale(takip_numarasi, email, baslik, pdf_data)

        flash("Makale başarıyla yüklendi!", "success")
        session['last_upload'] = {
            'takip_numarasi': takip_numarasi,
            'file_size': file_size
        }
        return redirect(url_for('makale_yukle'))

    last_upload = session.pop('last_upload', None)
    takip_numarasi = None
    file_size = None
    if last_upload:
        takip_numarasi = last_upload['takip_numarasi']
        file_size = last_upload['file_size']

    return render_template('makale_yukleme.html',
                           takip_numarasi=takip_numarasi,
                           file_size=file_size)


@app.route('/makale-durumu', methods=['GET', 'POST'])
def makale_durumu():
    """
    Sadece makale sorgulama işlevi.
    """
    makale = None

    if request.method == 'POST':
        # Makale Sorgulama
        takip_numarasi = request.form.get('takip_numarasi')
        email = request.form.get('email')

        makale = get_makale_by_takip_no_and_email(takip_numarasi, email)
        if not makale:
            flash("Bu bilgilere ait bir makale bulunamadı!", "danger")
            return redirect(url_for('makale_durumu'))

    return render_template('makale_durum_sorgulama.html', makale=makale)

@app.route('/yonetici')
def yonetici_paneli():
    # Tüm makaleleri çek
    makaleler = get_all_makaleler()
    # HTML sayfasına gönder
    return render_template('yonetici_paneli.html', makaleler=makaleler)

@app.route('/hakem')
def hakem_paneli():
    return render_template('hakem_paneli.html')

@app.route('/makale-sorgula', methods=['GET', 'POST'])
def makale_sorgula():
    if request.method == 'POST':
        takip_numarasi = request.form.get('takip_numarasi')
        email = request.form.get('email')
        makale = get_makale_by_takip_no_and_email(takip_numarasi, email)
        
        if makale:
            return render_template('makale_durum_sorgulama.html', makale=makale)
        else:
            flash("Bu bilgilere ait bir makale bulunamadı!", "danger")
            return redirect(url_for('makale_sorgula'))

    return render_template('makale_durum_sorgulama.html')


@app.route('/download/<int:makale_id>')
def download_pdf(makale_id):
    """
    Makale ID'ye göre PDF verisini çekip indirilebilir hale getirir.
    """
    makale_row = get_makale_by_id(makale_id)
    if makale_row is None:
        flash("Bu ID'ye ait PDF dosyası bulunamadı!", "danger")
        return redirect(url_for('yonetici_paneli'))

    # Satır nesnesi döndüğü için pdf verisi row içindeki 'pdfFile' kolonu olabilir:
    pdf_data = makale_row['pdfFile']

    # BLOB verisini BytesIO ile dosya benzeri nesneye çeviriyoruz
    return send_file(
        BytesIO(pdf_data),
        as_attachment=True,
        download_name=f"makale_{makale_id}.pdf",
        mimetype='application/pdf'
    )



@app.route('/chat/<int:makale_id>', methods=['GET', 'POST'])
def chat(makale_id):
    # Makaleyi bul
    makale = get_makale_by_id(makale_id)
    if not makale:
        flash("Böyle bir makale bulunamadı!", "danger")
        return redirect(url_for('yonetici_paneli'))  # veya başka bir sayfa

    if request.method == 'POST':
        # Yeni mesaj ekleme
        icerik = request.form.get('icerik')
        if icerik:
            # Göndereni admin olarak ekliyoruz
            insert_message(makale_id, 'admin', icerik)
            flash("Mesajınız gönderildi.", "success")
        return redirect(url_for('chat', makale_id=makale_id))

    # GET ise mesajları alıp chat ekranına gönder
    messages = get_messages_by_makale_id(makale_id)
    return render_template('chat.html', makale=makale, messages=messages)


    
if __name__ == '__main__':
    app.run()