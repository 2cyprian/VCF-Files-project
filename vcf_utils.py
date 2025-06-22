import re
import csv
import os
import tempfile
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

def format_tanzanian_number(phone_number):
    cleaned = re.sub(r'\D', '', phone_number)
    if cleaned.startswith('255'):
        return '+' + cleaned
    elif cleaned.startswith('0'):
        return '+255' + cleaned[1:]
    elif len(cleaned) == 9:
        return '+255' + cleaned
    else:
        return '+255' + cleaned

def extract_phone_numbers_from_csv(file_path):
    phone_numbers = []
    try:
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            sample = csvfile.read(1024)
            csvfile.seek(0)
            sniffer = csv.Sniffer()
            has_header = sniffer.has_header(sample)
            reader = csv.reader(csvfile)
            if has_header:
                next(reader)
            for row in reader:
                for cell in row:
                    numbers = re.findall(r'[\d\+\-\(\)\s]{9,}', str(cell))
                    for number in numbers:
                        cleaned = re.sub(r'\D', '', number)
                        if len(cleaned) >= 9:
                            phone_numbers.append(number.strip())
    except Exception as e:
        print(f"Error reading CSV: {e}")
    return phone_numbers

def extract_phone_numbers_from_pdf(file_path):
    phone_numbers = []
    if not PDF_SUPPORT:
        return phone_numbers
    try:
        with open(file_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            patterns = [
                r'\+255\d{9}',
                r'0\d{9}',
                r'\d{9}',
                r'\+255\s\d{3}\s\d{3}\s\d{3}',
                r'0\d{2}\s\d{3}\s\d{4}',
            ]
            for pattern in patterns:
                matches = re.findall(pattern, text)
                phone_numbers.extend(matches)
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return phone_numbers

def generate_vcf_content(phone_numbers, group_name=None):
    """Generate VCF content from list of phone numbers, iPhone compatible (vCard 3.0)"""
    vcf_lines = []
    vcf_lines.append('\ufeff')
    for i, number in enumerate(phone_numbers, 1):
        formatted_number = format_tanzanian_number(number)
        contact_name = f"{group_name} {i:03d}" if group_name else f"Contact {i:03d}"
        if ' ' in contact_name:
            parts = contact_name.split(' ', 1)
            last, first = parts[1], parts[0]
        else:
            last, first = '', contact_name
        vcf_lines.extend([
            "BEGIN:VCARD",
            "VERSION:3.0",
            f"N:{last};{first};;;",
            f"FN:{contact_name}",
            f"TEL;TYPE=CELL:{formatted_number}",
            "END:VCARD"
        ])
    return '\r\n'.join(vcf_lines)

def create_multiple_vcf_files(phone_numbers, group_name=None, contacts_per_file=50):
    files = []
    total_contacts = len(phone_numbers)
    for i in range(0, total_contacts, contacts_per_file):
        batch_numbers = phone_numbers[i:i + contacts_per_file]
        batch_name = f"{group_name}_batch_{i//contacts_per_file + 1}" if group_name else f"contacts_batch_{i//contacts_per_file + 1}"
        vcf_content = generate_vcf_content(batch_numbers, batch_name)
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
