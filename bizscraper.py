from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
import sqlite3
import os
import io
import csv
import json
from bizscraper_utils import extract_business_info
from vcf_utils import generate_vcf_content

bizscraper_bp = Blueprint('bizscraper', __name__)
DB_PATH = os.path.join(os.path.dirname(__file__), 'bizscraper_results.db')

def save_to_db(info):
    # Ensure all fields are present for DB insert
    name = info.get('name', '')
    phones = json.dumps(info.get('phones', []))
    emails = json.dumps(info.get('emails', []))
    address = info.get('address', '')
    website = info.get('website', '')
    socials = json.dumps(info.get('socials', {}))
    description = info.get('description', '')
    source_url = info.get('source_url', '')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS results (name TEXT, phones TEXT, emails TEXT, address TEXT, website TEXT, socials TEXT, description TEXT, source_url TEXT)''')
    c.execute('INSERT INTO results VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (
        name, phones, emails, address, website, socials, description, source_url
    ))
    conn.commit()
    conn.close()

def get_results():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Ensure table exists
    c.execute('''CREATE TABLE IF NOT EXISTS results (
        name TEXT, phones TEXT, emails TEXT, address TEXT, website TEXT, socials TEXT, description TEXT, source_url TEXT
    )''')
    c.execute('SELECT name, phones, emails, address, website, socials, description, source_url FROM results')
    rows = c.fetchall()
    conn.close()
    results = []
    for row in rows:
        result = {'name': row[0], 'source_url': row[7]}
        # Only add fields if they are not empty or null
        try:
            phones = json.loads(row[1])
            if phones: result['phones'] = phones
        except Exception:
            pass
        try:
            emails = json.loads(row[2])
            if emails: result['emails'] = emails
        except Exception:
            pass
        if row[3]: result['address'] = row[3]
        if row[4]: result['website'] = row[4]
        try:
            socials = json.loads(row[5])
            if socials: result['socials'] = socials
        except Exception:
            pass
        if row[6]: result['description'] = row[6]
        results.append(result)
    return results

def clear_results():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM results')
    conn.commit()
    conn.close()

@bizscraper_bp.route('/bizscraper', methods=['GET', 'POST'])
def bizscraper():
    info = None
    if request.method == 'POST':
        url = request.form['url']
        try:
            info = extract_business_info(url)
            save_to_db(info)
        except Exception as e:
            flash(f'Error scraping: {e}', 'error')
            return redirect(url_for('bizscraper.bizscraper'))
    results = get_results()
    return render_template('bizscraper.html', info=info, results=results)

@bizscraper_bp.route('/bizscraper/export/csv')
def export_csv():
    results = get_results()
    si = io.StringIO()
    # Collect all possible fields from results
    all_fields = set()
    for r in results:
        all_fields.update(r.keys())
    # Always include these fields in order
    field_order = ['name','phones','emails','address','website','socials','description','source_url']
    fieldnames = [f for f in field_order if f in all_fields]
    cw = csv.DictWriter(si, fieldnames=fieldnames)
    cw.writeheader()
    for r in results:
        row = r.copy()
        if 'phones' in row: row['phones'] = ', '.join(row['phones'])
        if 'emails' in row: row['emails'] = ', '.join(row['emails'])
        if 'socials' in row: row['socials'] = json.dumps(row['socials'])
        cw.writerow(row)
    output = io.BytesIO()
    output.write(si.getvalue().encode('utf-8'))
    output.seek(0)
    return send_file(output, as_attachment=True, download_name='bizscraper_results.csv', mimetype='text/csv')

@bizscraper_bp.route('/bizscraper/export/vcf')
def export_vcf():
    results = get_results()
    vcf_numbers = []
    for r in results:
        if 'phones' in r:
            vcf_numbers.extend(r['phones'])
    vcf_content = generate_vcf_content(vcf_numbers)
    output = io.BytesIO()
    output.write(vcf_content.encode('utf-8'))
    output.seek(0)
    return send_file(output, as_attachment=True, download_name='bizscraper_results.vcf', mimetype='text/vcard')

@bizscraper_bp.route('/bizscraper/export/json')
def export_json():
    results = get_results()
    output = io.BytesIO()
    output.write(json.dumps(results, indent=2).encode('utf-8'))
    output.seek(0)
    return send_file(output, as_attachment=True, download_name='bizscraper_results.json', mimetype='application/json')

@bizscraper_bp.route('/bizscraper/clear', methods=['POST'])
def clear_history():
    clear_results()
    flash('All business scraper history has been deleted.', 'success')
    return redirect(url_for('bizscraper.bizscraper'))
