import os
import uuid
from flask import Flask, request, send_file, jsonify, render_template_string
from flask_cors import CORS
from pdf2docx import Converter

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    with open(os.path.join(os.path.dirname(__file__), 'index.html'), 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/convert', methods=['POST'])
def convert():
    if 'file' not in request.files:
        return jsonify({'error': 'No se recibió ningún archivo.'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'Nombre de archivo vacío.'}), 400

    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Solo se aceptan archivos PDF.'}), 400

    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    if file_size > MAX_FILE_SIZE:
        return jsonify({'error': 'El archivo excede el límite de 10MB.'}), 400

    uid = str(uuid.uuid4())
    pdf_path = os.path.join(UPLOAD_FOLDER, f'{uid}.pdf')
    docx_path = os.path.join(UPLOAD_FOLDER, f'{uid}.docx')

    try:
        file.save(pdf_path)

        cv = Converter(pdf_path)
        cv.convert(docx_path, start=0, end=None)
        cv.close()

        original_name = os.path.splitext(file.filename)[0]
        download_name = f'{original_name}.docx'

        response = send_file(
            docx_path,
            as_attachment=True,
            download_name=download_name,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        return response

    except Exception as e:
        return jsonify({'error': f'Error durante la conversión: {str(e)}'}), 500

    finally:
        # Delete both files after sending
        for path in [pdf_path, docx_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass

if __name__ == '__main__':
    app.run(debug=True, port=5000)
