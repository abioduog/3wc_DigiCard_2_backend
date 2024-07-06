import os
from werkzeug.utils import secure_filename
from PIL import Image
from flask import current_app

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def save_file(file, folder):
    filename = secure_filename(file.filename)
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder, filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    file.save(file_path)
    return filename

def resize_image(image_path, max_size=(300, 300)):
    with Image.open(image_path) as img:
        img.thumbnail(max_size)
        img.save(image_path)
