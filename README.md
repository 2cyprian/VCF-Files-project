# 📱 VCF Generator - Bulk Tanzanian Phone Numbers Converter

A Flask web application for converting bulk Tanzanian phone numbers into VCF (vCard) files with WhatsApp integration and SQLite storage.

## 🚀 Features

### Core Functionality
- **Multi-Input Processing**: Accept phone numbers via manual input, CSV files, or PDF files
- **Smart Formatting**: Automatically converts Tanzanian numbers to international format (+255...)
- **VCF Generation**: Creates downloadable .vcf contact files with custom group names
- **Batch Processing**: Generate multiple VCF files for easy debugging and management
- **WhatsApp Integration**: One-click WhatsApp sharing with formatted messages
- **History Tracking**: SQLite database stores all generated VCF files with timestamps

### File Upload Support
- **CSV Files**: Extract phone numbers from CSV files with automatic header detection
- **PDF Files**: Extract phone numbers from PDF documents using PyPDF2
- **Manual Input**: Paste multiple phone numbers directly into the textarea

### Advanced Features
- **Group Naming**: Assign custom group names to contact batches
- **Multiple File Creation**: Split large contact lists into manageable batches
- **Duplicate Removal**: Automatically removes duplicate phone numbers
- **Unicode Support**: Full UTF-8 encoding support for international characters
- **Responsive Design**: Mobile-friendly interface with modern UI

## 🎨 Design

The application uses a modern, clean design with a custom color palette:
- **Champagne**: `#f1e0c5` - Warm, elegant background tones
- **Reseda Green**: `#71816d` - Professional accent color
- **White**: Clean, minimalist card backgrounds

## 📋 Requirements

- Python 3.7+
- Flask 2.3+
- SQLAlchemy 2.0+
- PyPDF2 3.0+ (for PDF support)

## ⚡ Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/vcf-generator.git
cd vcf-generator
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## 📖 Usage

### Basic Usage
1. Open the application in your web browser
2. Enter Tanzanian phone numbers (one per line) or upload a CSV/PDF file
3. Optionally enter your WhatsApp number for sharing
4. Add a group name for organized contacts
5. Choose between single file or multiple batch files
6. Click "Generate VCF" to create your contact file
7. Download the generated VCF file or ZIP archive

### Phone Number Formats Supported
- `+255754123456` (International format)
- `0754123456` (National format)
- `754123456` (Local format)
- Various formats with spaces and special characters

### File Upload Options
- **CSV Files**: Any CSV file containing phone numbers in any column
- **PDF Files**: Text-based PDF files with phone numbers
- **Manual Input**: Direct text input with one number per line

## 🗄️ Database Schema

The application uses SQLite to store VCF generation history:

```sql
CREATE TABLE vcf_record (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    vcf_content TEXT NOT NULL,
    user_whatsapp VARCHAR(20),
    phone_count INTEGER,
    group_name VARCHAR(100),
    upload_method VARCHAR(20) DEFAULT 'manual'
);
```

## 📁 Project Structure

```
vcf-generator/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
├── .gitignore           # Git ignore rules
├── templates/           # HTML templates
│   ├── base.html        # Base template with styling
│   ├── index.html       # Main input form
│   ├── result.html      # Download and sharing page
│   └── history.html     # Generation history
├── uploads/             # Temporary file uploads (ignored by git)
└── instance/            # SQLite database location (ignored by git)
```

## 🔧 Configuration

### Environment Variables
- `SECRET_KEY`: Flask secret key (default: 'your-secret-key-here')
- `SQLALCHEMY_DATABASE_URI`: Database connection string
- `MAX_CONTENT_LENGTH`: Maximum file upload size (default: 16MB)

### Customization
- Modify `app.config` in `app.py` for custom settings
- Update CSS variables in `templates/base.html` for design changes
- Adjust batch size and contact limits in the processing functions

## 🚀 Deployment

### Local Development
```bash
python app.py
```

### Production Deployment
For production deployment, consider:
- Using a production WSGI server (Gunicorn, uWSGI)
- Setting up a reverse proxy (Nginx)
- Using environment variables for configuration
- Implementing proper logging and monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Flask framework for the web application foundation
- PyPDF2 for PDF text extraction capabilities
- SQLAlchemy for database management
- The open-source community for inspiration and tools

## 📞 Support

For support, please open an issue on GitHub or contact the maintainers.

## 🔮 Future Enhancements

- [ ] User authentication and multi-user support
- [ ] WhatsApp Business API integration
- [ ] Excel file support (.xlsx)
- [ ] Contact validation and verification
- [ ] Advanced analytics and reporting
- [ ] RESTful API endpoints
- [ ] Docker containerization
- [ ] Cloud deployment templates

---

Made with ❤️ for efficient contact management and WhatsApp marketing.
