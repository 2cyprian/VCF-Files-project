from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

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

def migrate_database(db):
    """Add new columns to existing database if they don't exist"""
    from sqlalchemy import text
    try:
        with db.engine.connect() as conn:
            conn.execute(text("SELECT group_name FROM vcf_record LIMIT 1"))
    except Exception:
        try:
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE vcf_record ADD COLUMN group_name VARCHAR(100)"))
                conn.commit()
            print("Added group_name column")
        except Exception as e:
            print(f"Error adding group_name column: {e}")
    try:
        with db.engine.connect() as conn:
            conn.execute(text("SELECT upload_method FROM vcf_record LIMIT 1"))
    except Exception:
        try:
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE vcf_record ADD COLUMN upload_method VARCHAR(20) DEFAULT 'manual'"))
                conn.commit()
            print("Added upload_method column")
        except Exception as e:
            print(f"Error adding upload_method column: {e}")
