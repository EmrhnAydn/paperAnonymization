from flask import Flask, render_template, request, redirect, url_for, flash, session,send_file, jsonify
import os
import uuid
from io import BytesIO 
from anonymizer import anonymize_pdf

from models import (
    insert_makale, 
    get_makale_by_takip_no_and_email, 
    initialize_database, 
    get_all_makaleler, 
    get_makale_by_id,
    get_messages_by_makale_id,
    insert_message,
    insert_degerlendirme,
    check_assignment,
    get_all_reviewers, 
    update_degerlendirme,
    update_anon_pdf,
    update_evaluation_text,
    update_makale_status,
    update_makale_pdf,
    get_evaluation_by_makale_id,
    get_logs_by_makale_id,
    insert_log,
)

from expertSelector import guess_subject_area_from_db, find_best_reviewer


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

        # Makale kaydını ekle
        insert_makale(takip_numarasi, email, baslik, pdf_data)

        # Eklenen makaleyi takip numarası ve email ile sorgulayarak makale_id'yi alalım
        makale = get_makale_by_takip_no_and_email(takip_numarasi, email)
        if makale:
            makale_id = makale['id']
            # Log kaydı ekleyelim
            insert_log(makale_id, f"Makale yüklendi: {baslik}")
        else:
            flash("Makale bulunamadı, log eklenemedi.", "warning")

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
    makale = None
    evaluation = None
    
    if request.method == 'POST':
        # Eğer revize PDF yükleniyorsa:
        if 'revize_pdf' in request.files:
            takip_numarasi = request.form.get('takip_numarasi')
            email = request.form.get('email')
            pdf_file = request.files.get('revize_pdf')

            if not pdf_file:
                flash("Lütfen revize PDF dosyası yükleyiniz.", "warning")
                return redirect(url_for('makale_durumu'))

            pdf_data = pdf_file.read()
            update_makale_pdf(takip_numarasi, email, pdf_data, "Revised Uploaded")
            flash("Revize edilmiş makale başarıyla yüklendi!", "success")

            makale = get_makale_by_takip_no_and_email(takip_numarasi, email)

        # Yoksa normal sorgulama formu gönderilmişse:
        else:
            takip_numarasi = request.form.get('takip_numarasi')
            email = request.form.get('email')
            makale = get_makale_by_takip_no_and_email(takip_numarasi, email)
            if not makale:
                flash("Bu bilgilere ait bir makale bulunamadı!", "danger")
                return redirect(url_for('makale_durumu'))

    # Makale bulunduysa değerlendirme tablosundan notu çek
    if makale:
        evaluation_row = get_evaluation_by_makale_id(makale['id'])
        if evaluation_row:
            evaluation = evaluation_row["degerlendirme_metin"]

    # Template'e gönder
    return render_template('makale_durum_sorgulama.html', makale=makale, evaluation=evaluation)





@app.route('/yonetici')
def yonetici_paneli():
    # Tüm makaleleri çek
    makaleler = get_all_makaleler()
    # HTML sayfasına gönder
    return render_template('yonetici_paneli.html', makaleler=makaleler)

@app.route('/hakem')
def hakem_paneli():
    reviewers = get_all_reviewers()  # Veritabanından tüm hakemleri al
    return render_template('hakem_paneli.html', reviewers=reviewers)

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
    makale = get_makale_by_id(makale_id)
    if not makale:
        flash("Böyle bir makale bulunamadı!", "danger")
        return redirect(url_for('yonetici_paneli'))  # veya başka bir sayfa

    # URL parametresinden rolu al (örn: ?role=admin veya ?role=author)
    role = request.args.get('role', '')  # varsayılan boş string

    if request.method == 'POST':
        icerik = request.form.get('icerik')
        if icerik:
            # Gönderen = role (eğer role boşsa 'unknown' diyebilirsiniz)
            gonderen = role if role else 'unknown'
            insert_message(makale_id, gonderen, icerik)
            flash("Mesajınız gönderildi.", "success")
        return redirect(url_for('chat', makale_id=makale_id, role=role))

    # GET ise mesajları alıp chat ekranına gönder
    messages = get_messages_by_makale_id(makale_id)
    return render_template('chat.html', makale=makale, messages=messages)



@app.route('/api/find_reviewer', methods=['POST'])
def api_find_reviewer():
    """
    Ajax üzerinden gelen makale_id'yi alır, expertSelector fonksiyonlarını kullanır
    ve JSON formatında alan/hakem bilgisini döndürür.
    """
    data = request.json
    makale_id = data.get('makale_id')
    if not makale_id:
        return jsonify({"error": "Makale ID eksik."}), 400

    # 1) Makalenin alanını belirle
    subject_area = guess_subject_area_from_db(makale_id)

    # 2) Uygun hakemi bul
    best_hakem = find_best_reviewer(subject_area)

    if best_hakem:
        return jsonify({
            "subject_area": subject_area,
            "best_reviewer": {
                "id": best_hakem["id"],
                "ad": best_hakem["ad"],
                "uzmanlik": best_hakem["uzmanlik"]
            }
        })
    else:
        return jsonify({
            "subject_area": subject_area,
            "best_reviewer": None
        })



# app.py (devamı)

@app.route('/api/assign_reviewer', methods=['POST'])
def api_assign_reviewer():
    """
    makale_id ve hakem_id'yi alır, Degerlendirme tablosuna kaydeder.
    """
    data = request.json
    makale_id = data.get('makale_id')
    hakem_id = data.get('hakem_id')

    if not (makale_id and hakem_id):
        return jsonify({"error": "Gerekli parametreler eksik."}), 400

    # Degerlendirme tablosuna ekle
    insert_degerlendirme(makale_id, hakem_id)
    insert_log(makale_id, f"Hakem atandı: {hakem_id}")
    return jsonify({"message": "Hakem başarıyla atandı."})


@app.route('/api/check_assignment', methods=['POST'])
def api_check_assignment():
    """
    Ajax ile makale_id alır, check_assignment() ile daha önce atama yapılmış mı sorgular.
    Eğer atama varsa hakem bilgilerini JSON olarak döndürür.
    Yoksa "assigned": False döndürür.
    """
    data = request.json
    makale_id = data.get('makale_id')
    if not makale_id:
        return jsonify({"error": "makale_id eksik"}), 400

    result = check_assignment(makale_id)
    if result:
        return jsonify({
            "assigned": True,
            "hakem_id": result["hakem_id"],
            "hakem_ad": result["hakem_ad"],
            "hakem_uzmanlik": result["hakem_uzmanlik"],
            "degerlendirme_metin": result["degerlendirme_metin"],
            "tarih": result["tarih"]
        })
    else:
        return jsonify({"assigned": False})
    

@app.route('/api/get_reviewers', methods=['GET'])
def api_get_reviewers():
    """
    Tüm hakemleri JSON formatında döndürür.
    Örn: [ {id: 1, ad: 'Ali', uzmanlik: 'Cyber Security'}, ... ]
    """
    reviewers = get_all_reviewers()
    result = []
    for r in reviewers:
        result.append({
            "id": r["id"],
            "ad": r["ad"],
            "uzmanlik": r["uzmanlik"]
        })
    return jsonify(result)
@app.route('/api/change_reviewer', methods=['POST'])
def api_change_reviewer():
    """
    Gelen makale_id için yeni bir hakem_id ile Degerlendirme tablosunu update eder.
    """
    data = request.json
    makale_id = data.get("makale_id")
    new_hakem_id = data.get("hakem_id")

    if not (makale_id and new_hakem_id):
        return jsonify({"error": "Eksik parametreler"}), 400

    update_degerlendirme(makale_id, new_hakem_id)
    insert_log(makale_id, f"Hakem değiştirildi: {new_hakem_id}")    
    return jsonify({"message": "Hakem başarıyla değiştirildi"})





@app.route('/download-anonymized/<int:makale_id>')
def download_anonymized(makale_id):
    makale = get_makale_by_id(makale_id)
    if not makale or not makale['anonimPdf']:
        flash("Anonimleştirilmiş PDF bulunamadı!", "warning")
        return redirect(url_for('yonetici_paneli'))
    pdf_data = makale['anonimPdf']
    return send_file(
        BytesIO(pdf_data),
        as_attachment=True,
        download_name=f"makale_{makale_id}_anonim.pdf",
        mimetype='application/pdf'
    )


@app.route('/api/get_assigned_makaleler/<int:hakem_id>', methods=['GET'])
def api_get_assigned_makaleler(hakem_id):
    from models import get_assigned_makaleler_for_hakem
    makaleler = get_assigned_makaleler_for_hakem(hakem_id)
    result = [
        {
            "makale_id": row["makale_id"],
            "baslik": row["makale_baslik"],
            "durum": row["durum"],  # <-- DURUM ALANI EKLENDİ
            "degerlendirme_metin": row["degerlendirme_metin"],
            "tarih": row["degerlendirme_tarih"],
            "anonim_pdf_exists": bool(row["anon_pdf"])
        }
        for row in makaleler
    ]
    return jsonify(result)


@app.route('/api/request_revision', methods=['POST'])
def api_request_revision():
    data = request.json
    makale_id = data.get('makale_id')
    degerlendirme_text = data.get('degerlendirme_text')
    
    if not (makale_id and degerlendirme_text is not None):
        return jsonify({"error": "Eksik parametreler"}), 400

    update_evaluation_text(makale_id, degerlendirme_text)
    # Durumu "Request a Revision" yerine onay bekliyor şeklinde güncelliyoruz
    update_makale_status(makale_id, "Pending Revision Approval")
    insert_log(makale_id, "Revize talebi gönderildi, onay bekliyor.")
    return jsonify({"message": "Revize talebi onay için gönderildi."})

    
@app.route('/revize-yukle', methods=['GET', 'POST'])
def revize_yukle():
    """
    Revize edilmiş makaleyi yüklemek için ayrı bir ekran.
    GET isteğinde takip_numarasi ve email query parametreleriyle form önceden doldurulabilir.
    POST isteğinde PDF dosyası alınıp makale kaydı güncellenir.
    """
    revize_notu = None  # Hakemin yazdığı değerlendirme metnini burada tutacağız
    makale = None
    
    if request.method == 'POST':
        takip_numarasi = request.form.get('takip_numarasi')
        email = request.form.get('email')
        pdf_file = request.files.get('pdf_file')

        if not pdf_file:
            flash("Lütfen revize PDF dosyası yükleyiniz.", "warning")
            return redirect(url_for('revize_yukle'))

        pdf_data = pdf_file.read()
        # Revize dosyayı güncelle, durumunu "Revised Uploaded" yap
        update_makale_pdf(takip_numarasi, email, pdf_data, "Revised Uploaded")
        flash("Revize edilmiş makale başarıyla yüklendi!", "success")

        # İşlem bitince durumu görebilmesi için makale_durumu sayfasına yönlendir
        return redirect(url_for('makale_durumu'))
    
    else:
        # GET isteği: takip_numarasi ve email query parametrelerinden gelebilir
        takip_numarasi = request.args.get('takip_numarasi', '')
        email = request.args.get('email', '')

        # Eğer takip_numarasi ve email doluysa veritabanından makaleyi bul
        if takip_numarasi and email:
            makale = get_makale_by_takip_no_and_email(takip_numarasi, email)
            if makale:
                # Değerlendirme tablosundan revize notunu çek
                evaluation_row = get_evaluation_by_makale_id(makale['id'])
                if evaluation_row:
                    revize_notu = evaluation_row["degerlendirme_metin"]
    
    # revize_yukle.html'e makale bilgilerini ve revize notunu gönder
    return render_template(
        'revize_yukle.html',
        takip_numarasi=takip_numarasi,
        email=email,
        revize_notu=revize_notu
    )

@app.route('/api/complete_evaluation', methods=['POST'])
def api_complete_evaluation():
    data = request.json
    makale_id = data.get('makale_id')
    degerlendirme_text = data.get('degerlendirme_text')
    
    if not (makale_id and degerlendirme_text is not None):
        return jsonify({"error": "Eksik parametreler"}), 400

    update_evaluation_text(makale_id, degerlendirme_text)
    # Durumu "Conclusion" yerine onay bekliyor şeklinde güncelliyoruz
    update_makale_status(makale_id, "Pending Conclusion Approval")
    insert_log(makale_id, "Makale sonuçlandırma talebi gönderildi, onay bekliyor.")
    return jsonify({"message": "Sonuçlandırma talebi onay için gönderildi."})

@app.route('/show_result/<int:makale_id>')
def show_result(makale_id):
    makale = get_makale_by_id(makale_id)
    evaluation_row = get_evaluation_by_makale_id(makale_id)
    evaluation_text = evaluation_row["degerlendirme_metin"] if evaluation_row else ""
    return render_template('show_result.html', makale=makale, evaluation_text=evaluation_text)

@app.route('/api/anonymize_pdf', methods=['POST'])
def api_anonymize_pdf():
    data = request.json
    makale_id = data.get('makale_id')
    anon_institutions = data.get('anonymize_institutions', False)
    anon_people = data.get('anonymize_people', False)
    anonymize_images = data.get('anonymize_images', False)
    
    if not makale_id:
        return jsonify({"error": "makale_id eksik"}), 400
    
    # 1) Makaleyi veritabanından çekme
    makale = get_makale_by_id(makale_id)
    if not makale:
        return jsonify({"error": "Makale bulunamadı"}), 404
    
    original_pdf_bytes = makale["pdfFile"]
    
    # 2) Anonimleştirme işlemleri
    if anonymize_images:
        # Eğer görsel anonimleştirme diğer seçeneklerden (kurum/kişi) biriyle birlikte seçildiyse
        if anon_institutions or anon_people:
            key = "ThisIsA16ByteKey"
            # Önce metin anonimleştirmesini yapıyoruz
            temp_pdf_bytes = anonymize_pdf(
                original_pdf_bytes, 
                key,
                anonymize_institutions=anon_institutions,
                anonymize_people=anon_people
            )
            # Ardından görsel anonimleştirme yapılır
            from pdfBluring import blur_pdf_images
            anonymized_bytes = blur_pdf_images(temp_pdf_bytes)
        else:
            # Sadece görsel anonimleştirme yapılacaksa
            from pdfBluring import blur_pdf_images
            anonymized_bytes = blur_pdf_images(original_pdf_bytes)
    else:
        # Görsel anonimleştirme seçili değilse, sadece metin anonimleştirme işlemi yapılır
        key = "ThisIsA16ByteKey"
        anonymized_bytes = anonymize_pdf(
            original_pdf_bytes, 
            key,
            anonymize_institutions=anon_institutions,
            anonymize_people=anon_people
        )
    
    # 3) Ortaya çıkan anonim PDF’yi veritabanında anonimPdf kolonuna kaydetme
    update_anon_pdf(makale_id, anonymized_bytes)
    
    return jsonify({"success": True, "message": "Anonimleştirme işlemi tamamlandı."})



@app.route('/api/approve_submission', methods=['POST'])
def api_approve_submission():
    data = request.json
    makale_id = data.get("makale_id")
    approval_type = data.get("type")  # "revision" veya "conclusion"
    
    if not makale_id or not approval_type:
        return jsonify({"error": "Gerekli parametreler eksik."}), 400

    makale = get_makale_by_id(makale_id)
    if not makale:
        return jsonify({"error": "Makale bulunamadı."}), 404

    current_status = makale["durum"]
    if approval_type == "revision":
        if current_status != "Pending Revision Approval":
            return jsonify({"error": "Bu makale için revize talebi onaylanamaz."}), 400
        # Admin onayı verildiğinde durumu Request a Revision olarak güncelliyoruz
        new_status = "Request a Revision"
    elif approval_type == "conclusion":
        if current_status != "Pending Conclusion Approval":
            return jsonify({"error": "Bu makale için sonuçlandırma talebi onaylanamaz."}), 400
        # Admin onayı verildiğinde durumu Conclusion olarak güncelliyoruz
        new_status = "Conclusion"
    else:
        return jsonify({"error": "Geçersiz onay türü."}), 400

    update_makale_status(makale_id, new_status)
    insert_log(makale_id, f"Admin onayı ile makale '{new_status}' olarak güncellendi.")
    return jsonify({"message": f"Makale {new_status} olarak onaylandı."})



@app.route('/api/get_logs', methods=['POST'])
def api_get_logs():
    data = request.json
    makale_id = data.get('makale_id')
    if not makale_id:
        return jsonify({"error": "makale_id eksik"}), 400

    logs = get_logs_by_makale_id(makale_id)
    result = []
    for row in logs:
        result.append({
            "tarih": row["tarih"],
            "mesaj": row["mesaj"]
        })
    return jsonify(result)




if __name__ == '__main__':
    app.run()