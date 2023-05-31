from flask import Flask, jsonify # Flask
from flask_cors import CORS
import os
import time
from google.cloud import storage
from dotenv import load_dotenv
from datetime import datetime
import base64
from PIL import Image
from io import BytesIO


app = Flask(__name__)
CORS(app)
# ----------------------------------------------------------------
# Load the .env file
load_dotenv()

# GCP 설정
bucket_name = 'awdfaf'
service_account_json = os.getenv("KEY_PATH")
storage_client = storage.Client.from_service_account_json(service_account_json)
bucket = storage_client.bucket(bucket_name)

checking_status = False
image_info = []

@app.route('/start', methods=['POST'])
def start_checking():
    global checking_status
    checking_status = True
    return jsonify({"status": "started"}), 200

@app.route('/stop', methods=['POST'])
def stop_checking():
    global checking_status
    checking_status = False
    return jsonify({"status": "stopped"}), 200

@app.route('/reset', methods=['POST'])
def reset_images():
    global image_info
    image_info = []
    return jsonify({"status": "reset"}), 200


@app.route('/check_for_images', methods=['POST'])
def check_for_images():
    global checking_status
    global image_info

    if not checking_status:
        return jsonify({"status": "not started"}), 200

    for blob in bucket.list_blobs():
        filename = blob.name
        if filename.endswith('.jpg') and filename not in [info['name'] for info in image_info]:
            blob.download_to_filename('img_files/' + filename)
            with Image.open('img_files/' + filename) as img:
                buffered = BytesIO()
                img.save(buffered, format="JPEG")
                img_str = base64.b64encode(buffered.getvalue())
                encoded_string = img_str.decode('utf-8')
            image_info.append({"name": filename, "image": encoded_string, "time": time.ctime()})
    return jsonify(image_info), 200

# ----------------------------------------------------------------


@app.route('/users')
def users():
	# users 데이터를 Json 형식으로 반환한다
    return {"members": [{ "id" : 1, "name" : "yerin" },
                        { "id" : 2, "name" : "dalkong" }]}
    
    
    
    
if __name__ == "__main__":
    app.run(debug = True)