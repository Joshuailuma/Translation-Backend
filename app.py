from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from google.cloud import speech, translate_v2 as translate, texttospeech
import base64
import tempfile
import os
import ffmpeg
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

app = Flask(__name__)
app.config["SECRET_KEY"] = "my-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["JWT_SECRET_KEY"] = "my-jwt-key"
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

CORS(app, origins=["https://prod.mobile.buildwithseamless.co"], supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins="*")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "client-credentials.json"

speech_client = speech.SpeechClient() # For speech(audio) to text
translate_client = translate.Client()
tts_client = texttospeech.TextToSpeechClient() # For text to speech(audio)

SUPPORTED_FORMATS = ["wav", "webm", "mp4", "m4a"]

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# Create DB Tables
with app.app_context():
    db.create_all()

# User Registration
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data["username"]
    password = data["password"]


    if User.query.filter_by(username=username).first():
        return jsonify({"message": "User already exists"}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
    new_user = User(username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data["username"]
    password = data["password"]

    user = User.query.filter_by(username=username).first()
    if user and bcrypt.check_password_hash(user.password, password):
        token = create_access_token(identity=username)
        return jsonify({"token": token})

    return jsonify({"message": "Invalid credentials"}), 401

def convert_audio_to_wav(input_path, output_path):
    """ Convert any audio format to WAV (LINEAR16) using FFmpeg """
    try:
        ffmpeg.input(input_path).output(output_path, format='wav', ar=16000, ac=1).run(overwrite_output=True)
        return True
    except Exception as e:
        print(f"Error converting file: {e}")
        return False

@app.route('/speech-to-text', methods=['POST'])
def speech_to_text():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    audio_file = request.files['file']
    filename = audio_file.filename.lower()
    file_extension = filename.split('.')[-1]
    input_language = request.form.get("input_language", "en-US")

    if file_extension not in SUPPORTED_FORMATS:
        return jsonify({"error": "Unsupported file format"}), 400

    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as temp_input:
        audio_file.save(temp_input.name)

    temp_wav_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name

    if file_extension != "wav":
        if not convert_audio_to_wav(temp_input.name, temp_wav_path):
            return jsonify({"error": "Error converting audio"}), 500
    else:
        temp_wav_path = temp_input.name

    with open(temp_wav_path, "rb") as f:
        audio_content = f.read()

    audio = speech.RecognitionAudio(content=audio_content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code=input_language
    )

    response = speech_client. recognize(config=config, audio=audio)

    os.remove(temp_input.name)
    os.remove(temp_wav_path)

    transcript = response.results[0].alternatives[0].transcript if response.results else "No transcription found"
    print("Result is "+transcript)
    return jsonify({"transcript": transcript})

@app.route('/translate', methods=['POST'])
def translate_text():
    data = request.json
    text = data.get("text")
    target_language = data.get("target_language", "es")

    translation = translate_client.translate(text, target_language=target_language)
    return jsonify({"translated_text": translation['translatedText']})

@app.route('/text-to-speech', methods=['POST'])
def text_to_speech():

    data = request.json
    text = data.get("text")
    language_code = data.get("language_code", "es-US")

    input_text = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code, ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

    response = tts_client.synthesize_speech(input=input_text, voice=voice, audio_config=audio_config)

    audio_base64 = base64.b64encode(response.audio_content).decode("utf-8")
    return jsonify({"audio": audio_base64})

@socketio.on('send_message')
def handle_message(data):

    text = data.get("text")
    target_language = data.get("target_language", "es")

    translation = translate_client.translate(text, target_language=target_language)
    emit('receive_translation', {"translated_text": translation['translatedText']}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
