import os
from flask import Blueprint, request, render_template, current_app, send_file
from werkzeug.utils import secure_filename
from app.ocr.document_processor import DocumentProcessor
from app.pdf.pdf_generator import PDFGenerator

main = Blueprint('main', __name__)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@main.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@main.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return {'error': 'No file part'}, 400
    
    file = request.files['file']
    if file.filename == '':
        return {'error': 'No selected file'}, 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # Process document
            processor = DocumentProcessor(current_app.ocr)
            result = processor.process_image(filepath)
            
            # Generate PDF
            pdf_generator = PDFGenerator()
            pdf_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 
                                  f'output_{filename}.pdf')
            pdf_generator.generate(result)
            pdf_generator.save(pdf_path)
            
            return render_template('result.html', 
                                 text_blocks=result['text_blocks'],
                                 tables=result['tables'],
                                 pdf_path=pdf_path)
            
        except Exception as e:
            return {'error': str(e)}, 500
            
    return {'error': 'Invalid file type'}, 400

@main.route('/download/<path:filename>')
def download_file(filename):
    return send_file(os.path.join(current_app.config['UPLOAD_FOLDER'], filename),
                    as_attachment=True)