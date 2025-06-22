from flask import Blueprint, render_template, request, send_file, redirect, url_for, flash
import os
import tempfile
import urllib.parse
import zipfile
from werkzeug.utils import secure_filename
from models import db, VCFRecord
from vcf_utils import (
    format_tanzanian_number,
    extract_phone_numbers_from_csv,
    extract_phone_numbers_from_pdf,
    generate_vcf_content,
    create_multiple_vcf_files
)

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/process', methods=['POST'])
def process_numbers():
    phone_numbers_text = request.form.get('phone_numbers', '').strip()
    user_whatsapp = request.form.get('user_whatsapp', '').strip()
    group_name = request.form.get('group_name', '').strip()
    create_multiple = request.form.get('create_multiple') == 'on'
    contacts_per_file = int(request.form.get('contacts_per_file', 50))
    phone_numbers = []
    upload_method = 'manual'
    if 'file' in request.files:
        file = request.files['file']
        if file and file.filename:
            filename = secure_filename(file.filename)
            file_path = os.path.join(os.environ.get('UPLOAD_FOLDER', 'uploads'), filename)
            file.save(file_path)
            if filename.lower().endswith('.csv'):
                phone_numbers = extract_phone_numbers_from_csv(file_path)
                upload_method = 'csv'
            elif filename.lower().endswith('.pdf'):
                phone_numbers = extract_phone_numbers_from_pdf(file_path)
                upload_method = 'pdf'
            else:
                flash('Unsupported file type. Please upload CSV or PDF files.', 'error')
                return redirect(url_for('main.index'))
            os.unlink(file_path)
    if not phone_numbers and phone_numbers_text:
        phone_numbers = [num.strip() for num in phone_numbers_text.split('\n') if num.strip()]
        upload_method = 'manual'
    if not phone_numbers:
        flash('Please enter phone numbers or upload a valid file.', 'error')
        return redirect(url_for('main.index'))
    seen = set()
    phone_numbers = [x for x in phone_numbers if not (x in seen or seen.add(x))]
    if create_multiple and len(phone_numbers) > contacts_per_file:
        vcf_files = create_multiple_vcf_files(phone_numbers, group_name, contacts_per_file)
        temp_zip = tempfile.NamedTemporaryFile(suffix='.zip', delete=False)
        with zipfile.ZipFile(temp_zip.name, 'w') as zip_file:
            for vcf_file in vcf_files:
                zip_file.write(vcf_file['file_path'], vcf_file['filename'])
                os.unlink(vcf_file['file_path'])
        combined_vcf_content = generate_vcf_content(phone_numbers, group_name)
        vcf_record = VCFRecord(
            vcf_content=combined_vcf_content,
            user_whatsapp=user_whatsapp,
            phone_count=len(phone_numbers),
            group_name=group_name,
            upload_method=upload_method
        )
        db.session.add(vcf_record)
        db.session.commit()
        formatted_whatsapp = format_tanzanian_number(user_whatsapp) if user_whatsapp else None
        whatsapp_link = None
        if formatted_whatsapp:
            whatsapp_number = formatted_whatsapp.replace('+', '')
            message = f"Hello! I've generated {len(vcf_files)} VCF files with {len(phone_numbers)} contacts total. Please find the ZIP file attached."
            whatsapp_link = f"https://wa.me/{whatsapp_number}?text={urllib.parse.quote(message)}"
        return render_template('result.html', 
                             temp_file=temp_zip.name,
                             phone_count=len(phone_numbers),
                             whatsapp_link=whatsapp_link,
                             record_id=vcf_record.id,
                             is_zip=True,
                             file_count=len(vcf_files),
                             vcf_files=vcf_files,
                             group_name=group_name)
    else:
        vcf_content = generate_vcf_content(phone_numbers, group_name)
        vcf_record = VCFRecord(
            vcf_content=vcf_content,
            user_whatsapp=user_whatsapp,
            phone_count=len(phone_numbers),
            group_name=group_name,
            upload_method=upload_method
        )
        db.session.add(vcf_record)
        db.session.commit()
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.vcf', delete=False, encoding='utf-8')
        temp_file.write(vcf_content)
        temp_file.close()
        formatted_whatsapp = format_tanzanian_number(user_whatsapp) if user_whatsapp else None
        whatsapp_link = None
        if formatted_whatsapp:
            whatsapp_number = formatted_whatsapp.replace('+', '')
            message = f"Hello! I've generated a VCF file with {len(phone_numbers)} contacts. Please find the file attached."
            whatsapp_link = f"https://wa.me/{whatsapp_number}?text={urllib.parse.quote(message)}"
        return render_template('result.html', 
                             temp_file=temp_file.name,
                             phone_count=len(phone_numbers),
                             whatsapp_link=whatsapp_link,
                             record_id=vcf_record.id,
                             is_zip=False,
                             group_name=group_name)

@main_bp.route('/download/<path:filename>')
def download_file(filename):
    try:
        if filename.endswith('.zip'):
            return send_file(filename, as_attachment=True, download_name='contacts.zip')
        else:
            return send_file(filename, as_attachment=True, download_name='contacts.vcf')
    finally:
        try:
            os.unlink(filename)
        except:
            pass

@main_bp.route('/history')
def history():
    records = VCFRecord.query.order_by(VCFRecord.timestamp.desc()).limit(50).all()
    return render_template('history.html', records=records)

@main_bp.route('/download_record/<int:record_id>')
def download_record(record_id):
    record = VCFRecord.query.get_or_404(record_id)
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.vcf', delete=False, encoding='utf-8')
    temp_file.write(record.vcf_content)
    temp_file.close()
    try:
        return send_file(temp_file.name, as_attachment=True, 
                        download_name=f'contacts_{record.timestamp.strftime("%Y%m%d_%H%M%S")}.vcf')
    finally:
        try:
            os.unlink(temp_file.name)
        except:
            pass
