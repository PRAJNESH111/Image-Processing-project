from flask import Flask, render_template, request, send_from_directory
import os
import pytesseract as tess
from PIL import Image
from googletrans import Translator
from gtts import gTTS

app = Flask(__name__)

# Set the Tesseract-OCR path
tess.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'

# Create a directory to store uploaded images and audio files (if they don't exist)
if not os.path.exists('uploads'):
    os.makedirs('uploads')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    # Empty the "uploads" folder before processing
    folder_path = 'uploads'
    print('image'in request.files)
    print('user_text' in request.form)
    print(request.form['user_text'].strip() != '')

    if 'user_text' in request.form and request.form['user_text'].strip() != '':
        # Handle text input
        user_text = request.form['user_text']
        print(user_text)
        selected_language = request.form.get('language')

        # Translate the user-provided text to the selected language
        translator = Translator()
        translated_text = translator.translate(user_text, src='en', dest=selected_language).text

        # Initialize the text-to-speech engine for the selected language
        if selected_language == 'kn':
            tts = gTTS(text=translated_text, lang='kn')
        elif selected_language == 'hi':
            tts = gTTS(text=translated_text, lang='hi')
        else:
            tts = gTTS(text=translated_text, lang='en')

        # Save the audio file
        audio_path = 'uploads/audio_speech.mp3'
        tts.save(audio_path)

        # Wait for the audio file to be saved
        while not os.path.exists(audio_path):
            pass

        return render_template('result.html', text=translated_text, selected_language=selected_language, audio_path=audio_path)


    elif 'image' in request.files:
        # Handle image input
        import pythoncom
        pythoncom.CoInitialize()
        # Get the uploaded image file
        image_file = request.files['image']

        # Save the uploaded image to the 'uploads' directory
        image_path = os.path.join('uploads', image_file.filename)
        image_file.save(image_path)

        # Open the uploaded image for text extraction
        img = Image.open(image_path)
        extracted_text = tess.image_to_string(img)

        # Determine the selected language
        selected_language = request.form.get('language')

        # Translate the extracted text to the selected language
        translator = Translator()
        translated_text = translator.translate(extracted_text, src='en', dest=selected_language).text

        # Initialize the text-to-speech engine for the selected language
        if selected_language == 'kn':
            tts = gTTS(text=translated_text, lang='kn')
        elif selected_language == 'hi':
            tts = gTTS(text=translated_text, lang='hi')
        else:
            tts = gTTS(text=translated_text, lang='en')

        # Save the audio file
        audio_path = 'uploads/audio_speech.mp3'
        tts.save(audio_path)

        # Wait for the audio file to be saved
        while not os.path.exists(audio_path):
            pass

        # Delete the uploaded image after processing (optional)
        os.remove(image_path)

        return render_template('result.html', text=translated_text, selected_language=selected_language, audio_path=audio_path)



@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory('uploads', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))