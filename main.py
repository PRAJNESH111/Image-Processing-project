from flask import Flask, render_template, request, send_from_directory, redirect, url_for, session
import os
import pytesseract as tess
from PIL import Image
from deep_translator import GoogleTranslator
from gtts import gTTS
import uuid
import time
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a random secret key

# Set the Tesseract-OCR path
if os.name == 'nt':  # Windows
    tess.pytesseract.tesseract_cmd = r'C:/Program Files/Tesseract-OCR/tesseract'
else:  # Linux (Render)
    tess.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
# Create a directory to store uploaded images and audio files (if they don't exist)
if not os.path.exists('uploads'):
    os.makedirs('uploads')

def cleanup_old_files(directory, max_age_seconds=3600):
    current_time = time.time()
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            if current_time - os.path.getmtime(file_path) > max_age_seconds:
                os.remove(file_path)

def load_users():
    with open('users.json', 'r') as f:
        return json.load(f)

def save_users(users):
    with open('users.json', 'w') as f:
        json.dump(users, f)

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()
        for user in users['users']:
            if user['username'] == username and user['password'] == password:
                session['username'] = username
                return redirect(url_for('index'))
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password != confirm_password:
            return render_template('signup.html', error='Passwords do not match')
        users = load_users()
        for user in users['users']:
            if user['username'] == username:
                return render_template('signup.html', error='Username already exists')
        users['users'].append({'username': username, 'password': password})
        save_users(users)
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/process', methods=['POST'])
def process():
    cleanup_old_files('uploads')  # Clean up old files before processing
    
    selected_language = request.form.get('language')
    
    # Generate a unique filename for the audio file
    unique_filename = f"audio_speech_{uuid.uuid4()}.mp3"
    audio_path = os.path.join('uploads', unique_filename)
    
    if 'user_text' in request.form and request.form['user_text'].strip() != '':
        # Handle text input
        user_text = request.form['user_text'].strip()
        
        try:
            # Translate the user-provided text to the selected language
            translator = GoogleTranslator(source='auto', target=selected_language)
            translated_text = translator.translate(user_text)
            
            if not translated_text:
                raise ValueError("Translation failed: empty result")
            
            # Initialize the text-to-speech engine for the selected language
            tts = gTTS(text=translated_text, lang=selected_language)
            
            # Save the audio file
            tts.save(audio_path)
            
            # Wait for the audio file to be saved
            while not os.path.exists(audio_path):
                time.sleep(0.1)
            
            return render_template('result.html', text=translated_text, selected_language=selected_language, audio_filename=unique_filename, timestamp=int(time.time()))
        
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            return render_template('error.html', error_message=error_message)
    
    elif 'image' in request.files:
        # Handle image input
        image_file = request.files['image']
        
        if image_file.filename == '':
            return render_template('error.html', error_message="No image file selected")
        
        try:
            # Save the uploaded image to the 'uploads' directory
            image_path = os.path.join('uploads', image_file.filename)
            image_file.save(image_path)
            
            # Open the uploaded image for text extraction
            img = Image.open(image_path)
            extracted_text = tess.image_to_string(img)
            
            if not extracted_text.strip():
                raise ValueError("No text extracted from the image")
            
            # Translate the extracted text to the selected language
            translator = GoogleTranslator(source='auto', target=selected_language)
            translated_text = translator.translate(extracted_text)
            
            if not translated_text:
                raise ValueError("Translation failed: empty result")
            
            # Initialize the text-to-speech engine for the selected language
            tts = gTTS(text=translated_text, lang=selected_language)
            
            # Save the audio file
            tts.save(audio_path)
            
            # Wait for the audio file to be saved
            while not os.path.exists(audio_path):
                time.sleep(0.1)
            
            # Delete the uploaded image after processing
            os.remove(image_path)
            
            return render_template('result.html', text=translated_text, selected_language=selected_language, audio_filename=unique_filename, timestamp=int(time.time()))
        
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            return render_template('error.html', error_message=error_message)
    
    else:
        return render_template('error.html', error_message="No text or image provided")

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory('uploads', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
