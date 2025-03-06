from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from rembg import remove
from PIL import Image
import io

app = Flask(__name__, static_url_path='')
CORS(app)

def optimize_image(image, max_size=800):  # Reduced max size for memory efficiency
    width, height = image.size
    if width > max_size or height > max_size:
        if width > height:
            new_width = max_size
            new_height = int(height * (max_size / width))
        else:
            new_height = max_size
            new_width = int(width * (max_size / height))
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    return image

@app.route('/api/remove-bg', methods=['POST'])
def remove_background():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400
    
    # Strict file size limit
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB limit
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    if size > MAX_FILE_SIZE:
        return jsonify({'error': 'File too large. Maximum size is 5MB'}), 400
    file.seek(0)  # Reset file pointer
        
    try:
        input_image = Image.open(file.stream)
        input_image = optimize_image(input_image)
        
        # Force garbage collection after each operation
        output_image = remove(input_image)
        input_image.close()
        
        img_byte_arr = io.BytesIO()
        output_image.save(img_byte_arr, format='PNG', optimize=True, quality=80)
        output_image.close()
        
        img_byte_arr.seek(0)
        return send_file(
            img_byte_arr,
            mimetype='image/png',
            as_attachment=True,
            download_name='removed_bg.png'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

if __name__ == '__main__':
    app.run(debug=True)