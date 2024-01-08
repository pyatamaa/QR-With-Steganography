from flask import Flask, render_template, request, send_file
import qrcode
from PIL import Image
from pyzbar.pyzbar import decode
import cv2
from stegano import lsb
import os

app = Flask(__name__)

def polyalphabet_encrypt(text, key):
    result = []
    key_len = len(key)
    for i in range(len(text)):
        char = text[i]
        if char.isalpha():
            key_char = key[i % key_len]
            shift = ord(key_char.lower()) - ord('a')
            if char.isupper():
                result.append(chr((ord(char) + shift - ord('A')) % 26 + ord('A')))
            else:
                result.append(chr((ord(char) + shift - ord('a')) % 26 + ord('a')))
        else:
            result.append(char)
    return ''.join(result)

def generate_qr_code(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img

def read_qr_code(qr_code_path):
    image = cv2.imread(qr_code_path)
    decoded_objects = decode(image)
    decoded_data = ""

    for obj in decoded_objects:
        decoded_data += obj.data.decode('utf-8') + '\n'

    return decoded_data

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/tiket', methods=['GET', 'POST'])
def tiket():
    qr_code_exists = False
    qr_code_path = 'static/qrcode.png'

    if request.method == 'POST':
        first_name = request.form['first_name']
        middle_name = request.form['middle_name']
        last_name = request.form['last_name']
        concert_type = request.form['concert_type']
        concert_price = request.form['concert_price']
        concert_schedule = request.form['concert_schedule']
        concert_location = request.form['concert_location']

        full_name = f"{first_name} {middle_name} {last_name}"
        encrypted_full_name = polyalphabet_encrypt(full_name, "kimbo")

        data_to_embed = f"{encrypted_full_name}\nType: {concert_type}\nPrice: {concert_price}\nSchedule: {concert_schedule}\nLocation: {concert_location}"

        qr_code = generate_qr_code(data_to_embed)

        
        resized_qr_code = qr_code.resize((200, 200), Image.ANTIALIAS)

        resized_qr_code.save(qr_code_path)
        qr_code_exists = True

    return render_template('tiket.html', qr_code_exists=qr_code_exists, qr_code_path=qr_code_path)

@app.route('/download_qr_code')
def download_qr_code():
    return send_file('static/qrcode.png', as_attachment=True)

@app.route('/konfirmasi', methods=['GET', 'POST'])
def konfirmasi():
    qr_code_path = 'static/qrcode.png'
    decoded_data = read_qr_code(qr_code_path)
    
    return render_template('konfirmasi.html', qr_code_data=decoded_data)

@app.route('/upload_security', methods=['POST'])
def upload_security():
    if 'image' not in request.files or 'message' not in request.form:
        return 'Invalid request'

    image = request.files['image']
    message = request.form['message']

    # Simpan gambar yang diupload
    image_path = 'uploads/' + image.filename
    image.save(image_path)

    # Sembunyikan pesan dalam gambar
    enc_image = lsb.hide(image_path, message)
    enc_image_filename = 'enc_' + image.filename
    enc_image_path = 'uploads/' + enc_image_filename
    enc_image.save(enc_image_path)

    # Tautan unduh
    download_link = f'/download/{enc_image_filename}'

    return render_template('keamanan.html', download_link=download_link)

@app.route('/download/<filename>')
def download(filename):
    return send_file('uploads/' + filename, as_attachment=True)

@app.route('/keamanan', methods=['GET', 'POST'])
def keamanan():
    return render_template('keamanan.html')

if __name__ == '__main__':
    app.run(debug=True)