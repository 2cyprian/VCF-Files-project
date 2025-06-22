from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from models import db
from mapscraper_utils import scrape_osm, scrape_google_maps
import csv
import io
from vcf_utils import generate_vcf_content

mapscraper_bp = Blueprint('mapscraper', __name__)

# SQLite model for scraped results (simple, not using SQLAlchemy for brevity)
import sqlite3
import os
DB_PATH = os.path.join(os.path.dirname(__file__), 'mapscraper_results.db')

def save_results_to_db(results):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS results (name TEXT, phone TEXT, address TEXT, website TEXT, lat TEXT, lon TEXT)''')
    for r in results:
        c.execute('INSERT INTO results VALUES (?, ?, ?, ?, ?, ?)', (r['name'], r['phone'], r['address'], r['website'], r['lat'], r['lon']))
    conn.commit()
    conn.close()

def get_results_from_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Ensure table exists
    c.execute('''CREATE TABLE IF NOT EXISTS results (
        name TEXT, phone TEXT, address TEXT, website TEXT, lat TEXT, lon TEXT
    )''')
    c.execute('SELECT name, phone, address, website, lat, lon FROM results')
    rows = c.fetchall()
    conn.close()
    return [dict(zip(['name','phone','address','website','lat','lon'], row)) for row in rows]

def clear_results_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM results')
    conn.commit()
    conn.close()

@mapscraper_bp.route('/mapscraper', methods=['GET', 'POST'])
def mapscraper():
    results = []
    if request.method == 'POST':
        source = request.form['source']
        location = request.form['location']
        category = request.form['category']
        subcategory = request.form['subcategory']
        serpapi_key = request.form.get('serpapi_key', '')
        clear_results_db()
        if source == 'osm':
            results = scrape_osm(location, category, subcategory)
        elif source == 'google':
            if not serpapi_key:
                flash('SerpAPI key required for Google Maps scraping.', 'error')
                return redirect(url_for('mapscraper.mapscraper'))
            results = scrape_google_maps(location, category, subcategory, serpapi_key)
        save_results_to_db(results)
    else:
        results = get_results_from_db()
    return render_template('mapscraper.html', results=results)

@mapscraper_bp.route('/mapscraper/export/csv')
def export_csv():
    results = get_results_from_db()
    si = io.StringIO()
    cw = csv.DictWriter(si, fieldnames=['name','phone','address','website','lat','lon'])
    cw.writeheader()
    cw.writerows(results)
    output = io.BytesIO()
    output.write(si.getvalue().encode('utf-8'))
    output.seek(0)
    return send_file(output, as_attachment=True, download_name='mapscraper_results.csv', mimetype='text/csv')

@mapscraper_bp.route('/mapscraper/export/vcf')
def export_vcf():
    results = get_results_from_db()
    phone_numbers = [r['phone'] for r in results if r['phone']]
    vcf_content = generate_vcf_content(phone_numbers)
    output = io.BytesIO()
    output.write(vcf_content.encode('utf-8'))
    output.seek(0)
    return send_file(output, as_attachment=True, download_name='mapscraper_results.vcf', mimetype='text/vcard')
