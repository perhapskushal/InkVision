from flask import Flask, request, render_template, send_file, jsonify
from PIL import Image
import pytesseract
import os
from werkzeug.utils import secure_filename

# Configure Tesseract path for Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
os.environ['TESSDATA_PREFIX'] = r'C:\Program Files\Tesseract-OCR\tessdata'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def preprocess_image(image_path):
    # Open and convert image to grayscale
    image = Image.open(image_path).convert('L')
    return image

def perform_ocr(image, lang='nep'):
    try:
        # Get text and confidence scores
        text = pytesseract.image_to_string(image, lang='nepali')  # Change to 'nepali'
        data = pytesseract.image_to_data(image, lang='nepali', output_type=pytesseract.Output.DICT)  # Change to 'nepali'
        confidences = [float(conf) for conf in data['conf'] if conf != '-1']
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return text.strip(), avg_confidence / 100
    except Exception as e:
        raise Exception(f"OCR Error: {str(e)}")

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/process', methods=['POST'])
def process_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    file = request.files['image']
    language = request.form.get('language', 'nep')  # Default to Nepali
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    
    try:
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Preprocess image
        processed_image = preprocess_image(filepath)
        
        # Perform OCR
        text, confidence = perform_ocr(processed_image, lang='nep' if language == 'es' else 'eng')
        
        # Generate PDF
        pdf_filename = f'output_{filename}.pdf'
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
        
        # Create PDF
        from reportlab.pdfgen import canvas
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        # Register a Unicode font that supports Nepali (you'll need to provide the font file)
        font_path = os.path.join('static', 'fonts', 'NotoSansDevanagari-Regular.ttf')
        pdfmetrics.registerFont(TTFont('NotoSans', font_path))

        c = canvas.Canvas(pdf_path)
        c.setFont('NotoSans', 12)
        y = 800
        for line in text.split('\n'):
            if line.strip():
                c.drawString(50, y, line)
                y -= 20
        c.save()
        
        return jsonify({
            'success': True,
            'text': text,
            'confidence': confidence,
            'pdf_url': f'/download/{pdf_filename}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(
        os.path.join(app.config['UPLOAD_FOLDER'], filename),
        as_attachment=True
    )

if __name__ == '__main__':
    app.run(debug=True)