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
from PIL import Image
from io import BytesIO
from base64 import b64encode
import random

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Load the .env file
load_dotenv()

# GCP
bucket_name = 'awdfaf'
service_account_json = os.getenv("KEY_PATH")
storage_client = storage.Client.from_service_account_json(service_account_json)
bucket = storage_client.bucket(bucket_name)

lock_image = threading.Lock()
running_image = False 

lock_image_downloading = threading.Lock()
running_image_downloading = False 
gcp_images_downloaded = set()

video_files_1 = set()

@socketio.on('start_checking_image')
def start_checking_image():
    global running_image 
    global running_image_downloading
  
    running_image = True 
    running_image_downloading = True 

    socketio.start_background_task(download_gcp_images)
    socketio.start_background_task(emit_images)
    
@socketio.on('stop_checking_image')
def stop_checking_image():
    global running_image 
    global running_image_downloading

    running_image = False 
    running_image_downloading = False

@socketio.on('clear_images')
def clear_images_image():
    global running_image
    global gcp_images_downloaded 

    if not running_image:
        gcp_images_downloaded = set()
        for filename in os.listdir('./crop'):
            os.remove('./crop/' + filename)
    else:
        emit('clear_failed', {"message": "Can't clear images and videos while checking is running."})

def emit_images():
    global running_image
    processed_images = set()  
    while running_image:
        for analyzed_filename in os.listdir('./crop'):
            if not running_image:
                break
            if analyzed_filename not in processed_images:
                with open('./crop/' + analyzed_filename, 'rb') as img:
                    encoded_string = "data:image/jpeg;base64," + base64.b64encode(img.read()).decode('utf-8')
                    socketio.emit('new_image', {"image": encoded_string, "time": time.time()})
                    processed_images.add(analyzed_filename)  
                time.sleep(1)
        time.sleep(1)

def download_gcp_images():
    global running_image_downloading
    global gcp_images_downloaded
    while running_image_downloading:
        with lock_image_downloading:
            blobs = list(bucket.list_blobs(prefix='image/')) 
            for blob in blobs:
                if not running_image_downloading:
                    break
                filename = blob.name.replace('image/', '')
                if filename.endswith('.jpg') and filename not in gcp_images_downloaded:
                    blob.download_to_filename('crop/' + filename)
                    gcp_images_downloaded.add(filename)
        time.sleep(1)



# -----------------------------------------------------------------




existing_files_sound = set(os.listdir('input_sound_files'))
lock_sound = threading.Lock()
running_sound = False
first_run_sound = True

def check_files_sound():
    global running_sound
    global first_run_sound
    while running_sound:
        with lock_sound:
            blobs_ = list(bucket.list_blobs(prefix='sound/'))
            for blob_ in blobs_:
                if not running_sound:
                    break
                filename_ = blob_.name.replace('sound/', '')
                if filename_.endswith('.mp3'):
                    local_path = 'input_sound_files/' + filename_
                    blob_.download_to_filename(local_path)
                    if filename_ == 'north.mp3':
                        result = "현재 드론으로부터 '북쪽' 방향입니다"
                    elif filename_ == 'south.mp3':
                        result = "현재 드론으로부터 '남쪽' 방향입니다"
                    else:
                        result = 'Unknown direction'
                    socketio.emit('new_result', {"result": result})
                    # After emitting the result, remove the file
                    os.remove(local_path)
            if not running_sound:
                break
            if first_run_sound:
                time.sleep(15)
                first_run_sound = False
        time.sleep(1)

@socketio.on('start_checking_sound')
def start_checking_sound():
    global running_sound
    global first_run_sound
    running_sound = True
    first_run_sound = True
    socketio.start_background_task(check_files_sound)

@socketio.on('stop_checking_sound')
def stop_checking_sound():
    global running_sound
    running_sound = False

@socketio.on('clear_sound')
def clear_sound():
    # Reset the div where the audio player is displayed
    socketio.emit('clear_audio')



# --------------------------------------------------------
# GPS simulation variables
lock_gps = threading.Lock()
running_gps = False

@socketio.on('start_gps_tracking')
def start_gps_tracking():
    global running_gps
    running_gps = True
    socketio.start_background_task(gps_thread)

@socketio.on('stop_gps_tracking')
def stop_gps_tracking():
    global running_gps
    running_gps = False

def gps_thread():
    # For this example, we simulate GPS coordinates by slightly adjusting a fixed point.
    lat = 35.1345
    lng = 129.1061
    while running_gps:
        with lock_gps:
            # Randomize coordinates
            lat += random.uniform(-0.0001, 0.0001)
            lng += random.uniform(-0.0001, 0.0001)
            socketio.emit('new_coordinates', {'lat': lat, 'lng': lng})
        time.sleep(1)


@app.route('/')
def index():
    return render_template('stream.html')

if __name__ == '__main__':
    socketio.run(app, debug=True)