from flask import Flask
from models import db, migrate_database
from routes import main_bp
from mapscraper import mapscraper_bp
from bizscraper import bizscraper_bp
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vcf_records.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)

with app.app_context():
    db.create_all()
    migrate_database(db)

app.register_blueprint(main_bp)
app.register_blueprint(mapscraper_bp)
app.register_blueprint(bizscraper_bp)

if __name__ == '__main__':
    app.run(debug=True)