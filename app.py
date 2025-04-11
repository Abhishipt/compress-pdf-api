from flask import Flask, request, send_file, jsonify
from werkzeug.utils import secure_filename
import os
import subprocess
import uuid
import threading
import time

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 🔄 Auto delete any file after 10 minutes
def delete_file_later(path, delay=600):
    def remove():
        time.sleep(delay)
        if os.path.exists(path):
            os.remove(path)
    threading.Thread(target=remove).start()

# ✅ Keep API alive route (use UptimeRobot ping here)
@app.route('/')
def home():
    return jsonify({'status': 'PDF Compression API is alive 🔥'}), 200

# ✅ Compress PDF using Ghostscript
def compress_pdf_ghostscript(input_path, output_path, quality='screen'):
    try:
        subprocess.run([
            'gs',
            '-sDEVICE=pdfwrite',
            f'-dPDFSETTINGS=/{quality}',
            '-dNOPAUSE',
            '-dBATCH',
            '-dQUIET',
            f'-sOutputFile={output_path}',
            input_path
        ], check=True)
        return True
    except subprocess.CalledProcessError:
        return False

@app.route('/compress', methods=['POST'])
def compress():
    file = request.files.get('file')
    quality_level = int(request.form.get('level', 60))  # Accepts 0-100

    if not file:
        return 'No file uploaded', 400

    # ✅ Clean and save original file
    filename = secure_filename(file.filename)
    file_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_FOLDER, f"{file_id}_{filename}")
    output_path = os.path.join(UPLOAD_FOLDER, f"compressed_{file_id}.pdf")
    file.save(input_path)

    # ✅ Convert level to Ghostscript quality
    if quality_level >= 80:
        quality = 'ebook'     # high quality
    elif quality_level >= 50:
        quality = 'screen'    # medium quality
    else:
        quality = 'default'   # max compression

    # ✅ Compress using Ghostscript
    success = compress_pdf_ghostscript(input_path, output_path, quality)

    if not success or not os.path.exists(output_path):
        return 'Compression failed', 500

    # ✅ Clean up old files later
    delete_file_later(input_path)
    delete_file_later(output_path)

    return send_file(output_path, as_attachment=True, download_name='compressed.pdf', mimetype='application/pdf')

if __name__ == '__main__':
    app.run(debug=False)
