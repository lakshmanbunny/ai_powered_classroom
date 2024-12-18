import os
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
import PyPDF2
try:
    import pymongo
    from bson import ObjectId
except ModuleNotFoundError as e:
    print("The required module 'pymongo' is not installed. Attempting to install it...")
    import subprocess
    subprocess.check_call(["python", "-m", "pip", "install", "pymongo"])
    import pymongo
    from bson import ObjectId
import fitz  # PyMuPDF for table and image extraction
import matplotlib.pyplot as plt
import io
from base64 import b64encode

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Database Connection
client = pymongo.MongoClient("mongodb+srv://bunnylakshman1:3HvrnpTCv7OjTluJ@cluster0.4le9m.mongodb.net/ar?retryWrites=true&w=majority&appName=Cluster0")
db = client['pdf_analysis']
collection = db['documents']

# Ensure upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route: Upload PDF
@app.route('/upload', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Parse the PDF
        pdf_data = extract_pdf_content(file_path)

        # Store in database
        doc_id = collection.insert_one(pdf_data).inserted_id

        return jsonify({'message': 'File uploaded and processed', 'doc_id': str(doc_id)}), 200

    return jsonify({'error': 'Invalid file type'}), 400

# Function: Extract PDF content
def extract_pdf_content(file_path):
    pdf_data = {'text': '', 'tables': [], 'images': []}

    try:
        with fitz.open(file_path) as pdf_document:
            text = ''

            for page_number in range(len(pdf_document)):
                page = pdf_document[page_number]

                # Extract text
                text += page.get_text()

                # Extract tables (mock example, extend as needed)
                for table in page.search_for("table"):
                    pdf_data['tables'].append(f"Table detected on page {page_number + 1}")

                # Extract images
                for img_index, img in enumerate(page.get_images(full=True)):
                    xref = img[0]
                    base_image = pdf_document.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_stream = io.BytesIO(image_bytes)
                    img_data = b64encode(image_stream.getvalue()).decode('utf-8')
                    pdf_data['images'].append({
                        'page': page_number + 1,
                        'image_index': img_index + 1,
                        'data': img_data
                    })

            pdf_data['text'] = text

    except Exception as e:
        print(f"Error reading PDF: {e}")

    return pdf_data

# Route: Fetch PDF Data
@app.route('/document/<doc_id>', methods=['GET'])
def get_document(doc_id):
    try:
        document = collection.find_one({'_id': ObjectId(doc_id)})
        if not document:
            return jsonify({'error': 'Document not found'}), 404

        # Convert ObjectId to string for JSON serialization
        document['_id'] = str(document['_id'])
        return jsonify(document), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route: Q&A Endpoint
@app.route('/ask', methods=['POST'])
def ask_question():
    try:
        data = request.json
        doc_id = data.get('doc_id')
        question = data.get('question')

        if not doc_id or not question:
            return jsonify({'error': 'Missing doc_id or question'}), 400

        document = collection.find_one({'_id': ObjectId(doc_id)})
        if not document:
            return jsonify({'error': 'Document not found'}), 404

        # Simple text-based search for now (can integrate NLP models later)
        text = document.get('text', '')
        if question.lower() in text.lower():
            # Return context around the match (simple example)
            start_idx = text.lower().find(question.lower())
            snippet = text[max(0, start_idx - 50):start_idx + 50 + len(question)]
            return jsonify({'answer': snippet}), 200

        return jsonify({'answer': 'No relevant information found in the document.'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route: Serve the HTML template
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
