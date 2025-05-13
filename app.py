from flask import Flask, request, render_template, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import fitz  # PyMuPDF
import json
from io import BytesIO
from datetime import datetime

app = Flask(__name__)
UPLOAD_FOLDER = '/tmp'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def extract_metadata_from_pdf(filepath):
    doc = fitz.open(filepath)
    metadata = doc.metadata
    text = "\n".join([page.get_text() for page in doc])
    return {
        "title": metadata.get("title") or "Extracted Title Placeholder",
        "author": metadata.get("author") or "Unknown Author",
        "date": metadata.get("modDate", "2024")[:4],
        "publisher": "Inferred Publisher",
        "place": "[Place not identified]",
        "subjects": ["General"],
        "description": text[:500]
    }

def generate_marc21(data):
    marc = []
    marc.append("=LDR  00000nam a2200000 a 4500")
    marc.append("=001  [Control Number]")
    marc.append(f"=005  {datetime.now().strftime('%Y%m%d')}      .0")
    marc.append(f"=008  {data['date']}s{data['date']}    xx u     b    000 0 eng  ")
    marc.append(f"=100  1#$a{data['author']}")
    marc.append(f"=245  10$a{data['title']}.")
    marc.append(f"=264  #1$a{data['place']} :$b{data['publisher']},$c{data['date']}")
    marc.append("=300  ##$a1 volume :$billustrations ;$c25 cm")
    marc.append("=336  ##$atext$btxt$2rdacontent")
    marc.append("=337  ##$aunmediated$bn$2rdamedia")
    marc.append("=338  ##$avolume$bnc$2rdacarrier")
    for subject in data.get('subjects', []):
        marc.append(f"=650  #0$a{subject}.")
    return "\n".join(marc)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return "No file uploaded", 400
    file = request.files['file']
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    metadata = extract_metadata_from_pdf(filepath)
    marc_text = generate_marc21(metadata)

    response = {
        "metadata": metadata,
        "marc21": marc_text,
        "marcxml": f"<record><title>{metadata['title']}</title></record>",
        "json": metadata
    }
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
