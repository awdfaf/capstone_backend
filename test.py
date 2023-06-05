from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import base64
from google.cloud import storage
import os
from dotenv import load_dotenv
import subprocess
import time
import shutil
import threading

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Load the .env file
load_dotenv()

# GCP
bucket_name = 'awdfaf'
service_account_json = os.getenv("KEY_PATH")
storage_client = storage.Client.from_service_account_json(service_account_json)
bucket = storage_client.bucket(bucket_name)

video_files = set(os.listdir('video_files'))
lock = threading.Lock()

def check_files():
    global video_files
    while True:
        with lock:
            blobs = list(bucket.list_blobs(prefix='video/')) 
            for blob in blobs:
                filename = blob.name
                if filename.endswith('.avi') and filename not in video_files:
                    blob.download_to_filename('video_files/' + filename)
                    video_files.add(filename)

                    # Perform YOLOv7 analysis using detect.py
                    yolov7_process = subprocess.run(['python', 'yolov7-main/detect.py', '--weights', './yolov7-main/yolov7.pt', '--classes', '0', '--source', 'video_files/' + filename])

                    # Process the analyzed images from yolov7/crop folder
                    for analyzed_filename in os.listdir('./crop'):
                        with open('./crop/' + analyzed_filename, 'rb') as img:
                            encoded_string = base64.b64encode(img.read()).decode('utf-8')
                            socketio.emit('new_image', {"image": encoded_string})
                            time.sleep(1)

                        # Move the analyzed file to another directory
                        #shutil.move('./crop/' + analyzed_filename, './crop_processed/' + analyzed_filename)
                    
                    # Clear the yolov7/crop folder to make sure there's no residual files
                    # for file in os.listdir('yolov7-main/crop'):
                    #     os.remove('yolov7-main/crop/' + file)

                    break
        time.sleep(1)

@app.route('/')
def index():
    return render_template('main.html')

@socketio.on('start_checking')
def start_checking():
    socketio.start_background_task(check_files)

if __name__ == '__main__':
    socketio.run(app, debug=True)
