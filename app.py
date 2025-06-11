from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import re
import os
import tempfile
import urllib.parse
import csv
import io
import zipfile
from werkzeug.utils import secure_filename
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vcf_records.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

# Database Model
class VCFRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    vcf_content = db.Column(db.Text, nullable=False)
    user_whatsapp = db.Column(db.String(20))
    phone_count = db.Column(db.Integer)
    group_name = db.Column(db.String(100))
    upload_method = db.Column(db.String(20), default='manual')  # manual, csv, pdf
    
    def __repr__(self):
        return f'<VCFRecord {self.id} - {self.timestamp}>'

# Database Migration Function
def migrate_database():
    """Add new columns to existing database if they don't exist"""
    from sqlalchemy import text
    
    try:
        # Check if group_name column exists
        with db.engine.connect() as conn:
            conn.execute(text("SELECT group_name FROM vcf_record LIMIT 1"))
    except Exception:
        # Add group_name column
        try:
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE vcf_record ADD COLUMN group_name VARCHAR(100)"))
                conn.commit()
            print("Added group_name column")
        except Exception as e:
            print(f"Error adding group_name column: {e}")
    
    try:
        # Check if upload_method column exists
        with db.engine.connect() as conn:
            conn.execute(text("SELECT upload_method FROM vcf_record LIMIT 1"))
    except Exception:
        # Add upload_method column
        try:
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE vcf_record ADD COLUMN upload_method VARCHAR(20) DEFAULT 'manual'"))
                conn.commit()
            print("Added upload_method column")
        except Exception as e:
            print(f"Error adding upload_method column: {e}")

# Create tables and migrate
with app.app_context():
    db.create_all()
    migrate_database()

def format_tanzanian_number(phone_number):
    """Format Tanzanian phone number to international format"""
    # Remove all non-digit characters
    cleaned = re.sub(r'\D', '', phone_number)
    
    # Handle different Tanzanian number formats
    if cleaned.startswith('255'):
        return '+' + cleaned
    elif cleaned.startswith('0'):
        return '+255' + cleaned[1:]
    elif len(cleaned) == 9:  # 9 digits without country code
        return '+255' + cleaned
    else:
        return '+255' + cleaned  # Default case

def extract_phone_numbers_from_csv(file_path):
    """Extract phone numbers from CSV file"""
    phone_numbers = []
    try:
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            # Try to detect if file has headers
            sample = csvfile.read(1024)
            csvfile.seek(0)
            sniffer = csv.Sniffer()
            has_header = sniffer.has_header(sample)
            
            reader = csv.reader(csvfile)
            if has_header:
                next(reader)  # Skip header row
            
            for row in reader:
                for cell in row:
                    # Look for phone number patterns
                    numbers = re.findall(r'[\d\+\-\(\)\s]{9,}', str(cell))
                    for number in numbers:
                        cleaned = re.sub(r'\D', '', number)
                        if len(cleaned) >= 9:  # Minimum phone number length
                            phone_numbers.append(number.strip())
    except Exception as e:
        print(f"Error reading CSV: {e}")
    return phone_numbers

def extract_phone_numbers_from_pdf(file_path):
    """Extract phone numbers from PDF file"""
    phone_numbers = []
    if not PDF_SUPPORT:
        return phone_numbers
    
    try:
        with open(file_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            
            # Extract phone numbers using regex
            patterns = [
                r'\+255\d{9}',  # +255xxxxxxxxx
                r'0\d{9}',      # 0xxxxxxxxx
                r'\d{9}',       # xxxxxxxxx
                r'\+255\s\d{3}\s\d{3}\s\d{3}',  # +255 xxx xxx xxx
                r'0\d{2}\s\d{3}\s\d{4}',        # 0xx xxx xxxx
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text)
                phone_numbers.extend(matches)
                
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return phone_numbers

def generate_vcf_content(phone_numbers, group_name=None):
    """Generate VCF content from list of phone numbers"""
    vcf_content = ""
    
    for i, number in enumerate(phone_numbers, 1):
        formatted_number = format_tanzanian_number(number)
        contact_name = f"{group_name} {i:03d}" if group_name else f"Contact {i:03d}"
        vcf_content += f"""BEGIN:VCARD
VERSION:3.0
FN:{contact_name}
TEL;TYPE=CELL:{formatted_number}
END:VCARD

"""
    
    return vcf_content

def create_multiple_vcf_files(phone_numbers, group_name=None, contacts_per_file=50):
    """Create multiple VCF files for easy debugging"""
    files = []
    total_contacts = len(phone_numbers)
    
    for i in range(0, total_contacts, contacts_per_file):
        batch_numbers = phone_numbers[i:i + contacts_per_file]
        batch_name = f"{group_name}_batch_{i//contacts_per_file + 1}" if group_name else f"contacts_batch_{i//contacts_per_file + 1}"
        
        vcf_content = generate_vcf_content(batch_numbers, batch_name)
        
        # Create temporary file with UTF-8 encoding
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.vcf', delete=False, encoding='utf-8')
        temp_file.write(vcf_content)
        temp_file.close()
        
        files.append({
            'file_path': temp_file.name,
            'filename': f"{batch_name}.vcf",
            'contact_count': len(batch_numbers),
            'batch_number': i//contacts_per_file + 1
        })
    
    return files

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_numbers():
    phone_numbers_text = request.form.get('phone_numbers', '').strip()
    user_whatsapp = request.form.get('user_whatsapp', '').strip()
    group_name = request.form.get('group_name', '').strip()
    create_multiple = request.form.get('create_multiple') == 'on'
    contacts_per_file = int(request.form.get('contacts_per_file', 50))
    
    phone_numbers = []
    upload_method = 'manual'
    
    # Check if file was uploaded
    if 'file' in request.files:
        file = request.files['file']
        if file and file.filename:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Extract phone numbers based on file type
            if filename.lower().endswith('.csv'):
                phone_numbers = extract_phone_numbers_from_csv(file_path)
                upload_method = 'csv'
            elif filename.lower().endswith('.pdf'):
                if PDF_SUPPORT:
                    phone_numbers = extract_phone_numbers_from_pdf(file_path)
                    upload_method = 'pdf'
                else:
                    flash('PDF support not available. Please install PyPDF2.', 'error')
                    return redirect(url_for('index'))
            else:
                flash('Unsupported file type. Please upload CSV or PDF files.', 'error')
                return redirect(url_for('index'))
            
            # Clean up uploaded file
            os.unlink(file_path)
    
    # If no file or no numbers from file, use manual input
    if not phone_numbers and phone_numbers_text:
        phone_numbers = [num.strip() for num in phone_numbers_text.split('\n') if num.strip()]
        upload_method = 'manual'
    
    if not phone_numbers:
        flash('Please enter phone numbers or upload a valid file.', 'error')
        return redirect(url_for('index'))
    
    # Remove duplicates while preserving order
    seen = set()
    phone_numbers = [x for x in phone_numbers if not (x in seen or seen.add(x))]
    
    if create_multiple and len(phone_numbers) > contacts_per_file:
        # Create multiple VCF files
        vcf_files = create_multiple_vcf_files(phone_numbers, group_name, contacts_per_file)
        
        # Create a ZIP file containing all VCF files
        temp_zip = tempfile.NamedTemporaryFile(suffix='.zip', delete=False)
        with zipfile.ZipFile(temp_zip.name, 'w') as zip_file:
            for vcf_file in vcf_files:
                zip_file.write(vcf_file['file_path'], vcf_file['filename'])
                # Clean up individual VCF files
                os.unlink(vcf_file['file_path'])
        
        # Save to database (save the combined content)
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
        
        # Format user WhatsApp number for chat link
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
        # Create single VCF file
        vcf_content = generate_vcf_content(phone_numbers, group_name)
        
        # Save to database
        vcf_record = VCFRecord(
            vcf_content=vcf_content,
            user_whatsapp=user_whatsapp,
            phone_count=len(phone_numbers),
            group_name=group_name,
            upload_method=upload_method
        )
        db.session.add(vcf_record)
        db.session.commit()
          # Create temporary file for download
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.vcf', delete=False, encoding='utf-8')
        temp_file.write(vcf_content)
        temp_file.close()
        
        # Format user WhatsApp number for chat link
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

@app.route('/download/<path:filename>')
def download_file(filename):
    try:
        # Determine if it's a ZIP file or VCF file
        if filename.endswith('.zip'):
            return send_file(filename, as_attachment=True, download_name='contacts.zip')
        else:
            return send_file(filename, as_attachment=True, download_name='contacts.vcf')
    finally:
        # Clean up temporary file after download
        try:
            os.unlink(filename)
        except:
            pass

@app.route('/history')
def history():
    records = VCFRecord.query.order_by(VCFRecord.timestamp.desc()).limit(50).all()
    return render_template('history.html', records=records)

@app.route('/download_record/<int:record_id>')
def download_record(record_id):
    record = VCFRecord.query.get_or_404(record_id)
    
    # Create temporary file with UTF-8 encoding
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.vcf', delete=False, encoding='utf-8')
    temp_file.write(record.vcf_content)
    temp_file.close()
    
    try:
        return send_file(temp_file.name, as_attachment=True, 
                        download_name=f'contacts_{record.timestamp.strftime("%Y%m%d_%H%M%S")}.vcf')
    finally:
        # Clean up temporary file after download
        try:
            os.unlink(temp_file.name)
        except:
            pass

if __name__ == '__main__':
    app.run(debug=True)