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
from spleeter.separator import Separator
import librosa
from PIL import Image
from io import BytesIO

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Load the .env file
load_dotenv()

# GCP
bucket_name = 'awdfaf'
service_account_json = os.getenv("KEY_PATH")
storage_client = storage.Client.from_service_account_json(service_account_json)
bucket = storage_client.bucket(bucket_name)

# Create a set with the filenames of the existing files
existing_files = set(os.listdir('video_files/video'))
video_files = set(os.listdir('video_files'))
lock_image = threading.Lock()

running_image = False 

lock_image_downloading = threading.Lock()
running_image_downloading = False 
gcp_images_downloaded = set()
lock_image_downloading_gray = threading.Lock()
running_image_downloading_gray = False 
gcp_images_downloaded_gray = set()
# -----------------------------------------------------------------

video_files_1 = set()


def download_and_process_videos_1():
    global video_files_1
    global existing_files
    global running_image
    while running_image:  
        with lock_image:
            blobs = list(bucket.list_blobs(prefix='video/')) 
            for blob in blobs:
                if not running_image:
                    break
                filename = blob.name.replace('video/', '')
                if filename.startswith('1_') and filename.endswith('.avi') and filename not in video_files_1 and filename not in existing_files:
                    blob.download_to_filename('video_files/video/' + filename)
                    video_files_1.add(filename)
                    yolov7_process = subprocess.run(['python', 'yolov7-main/detect.py', '--weights', './yolov7-main/yolov7.pt', '--classes', '0', '--source', 'video_files/video/' + filename, '--nosave'])
            if not running_image:
                break
        time.sleep(1)
        
def emit_images():
    global running_image
    processed_images = set()  # Set to keep track of processed images
    while running_image:
        for analyzed_filename in os.listdir('./crop'):
            if not running_image:
                break
            if analyzed_filename not in processed_images:
                with open('./crop/' + analyzed_filename, 'rb') as img:
                    encoded_string = base64.b64encode(img.read()).decode('utf-8')
                    socketio.emit('new_image', {"image": encoded_string, "time": time.time()})
                    processed_images.add(analyzed_filename)  # Add processed image to the set
            time.sleep(1)
        if not running_image:
            break
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
            if not running_image_downloading:
                break
        time.sleep(1)
def download_gcp_images_gray():
    global running_image_downloading_gray
    global gcp_images_downloaded_gray
    while running_image_downloading_gray:
        with lock_image_downloading_gray:
            blobs = list(bucket.list_blobs(prefix='image_gray/')) 
            for blob in blobs:
                if not running_image_downloading_gray:
                    break
                filename = blob.name.replace('image_gray/', '')
                if filename.endswith('.jpg') and filename not in gcp_images_downloaded_gray:
                    blob.download_to_filename('crop/' + filename)
                    gcp_images_downloaded_gray.add(filename)
            if not running_image_downloading_gray:
                break
        time.sleep(1)

@socketio.on('start_checking')
def start_checking_image():
    global running_image 
    global running_image_downloading
    global running_image_downloading_gray
    running_image = True 
    running_image_downloading = True 
    running_image_downloading_gray = True 
    socketio.start_background_task(download_and_process_videos_1)
    socketio.start_background_task(download_gcp_images)
    socketio.start_background_task(download_gcp_images_gray)
    socketio.start_background_task(emit_images)
    
  

@socketio.on('stop_checking')
def stop_checking_image():
    global running_image 
    running_image = False 

@socketio.on('clear_images')
def clear_images_image():
    global running_image
    global processed_images 
    processed_images = set()
    if not running_image:
        for filename in os.listdir('./crop'):
            os.remove('./crop/' + filename)
        for filename in os.listdir('./image'):
            os.remove('./image/' + filename)
        for filename in os.listdir('./image_gray'):
            os.remove('./image_gray/' + filename)
        for filename in os.listdir('video_files/video'):
            if filename != '.ipynb_checkpoints':  # Exclude '.ipynb_checkpoints' directory
                path = 'video_files/video/' + filename
                if os.path.isfile(path):
                    os.remove(path)
                elif os.path.isdir(path):  # If it's a directory, remove it with shutil.rmtree
                    shutil.rmtree(path)
    else:
        emit('clear_failed', {"message": "Can't clear images and videos while checking is running."})




# -----------------------------------------------------------------

def run_separator():
    # Prepare to use Splitter
    separator = Separator('spleeter:2stems')

    # Set input folder and output path
    input_folder = "./input_sound_files"
    output_folder = "./output_sound_files"

    # Create the collection folder if it doesn't exist
    collection_folder = "./vocals_collection"
    os.makedirs(collection_folder, exist_ok=True)

    # Get the initial list of files in the input folder
    initial_files = set(os.listdir(input_folder))

    # Process existing files in the input folder
    for file_name in initial_files:
        if file_name.endswith(".wav"):
            # Set input file path
            input_audio_file = os.path.join(input_folder, file_name)

            # Perform voice extraction
            separator.separate_to_file(input_audio_file, output_folder)

            # Delete input audio file
            os.remove(input_audio_file)

    # Collect vocals from output folders
    for result_folder in os.listdir(output_folder):
        result_folder_path = os.path.join(output_folder, result_folder)
        if os.path.isdir(result_folder_path):
            # Get the vocals file path
            vocals_file = os.path.join(result_folder_path, "vocals.wav")

            # Move the vocals file to the collection folder
            shutil.move(vocals_file, os.path.join(collection_folder, f"{result_folder}.wav"))

            # Remove the result folder
            shutil.rmtree(result_folder_path)

    # Check if there are 4 files in vocals_collection
    if len(os.listdir(collection_folder)) == 4:
        max_volume = None
        # Find file with the maximum volume in vocals_collection
        for file in os.listdir(collection_folder):
            if file.endswith('.wav'):
                # Load the audio file
                y, sr = librosa.load(os.path.join(collection_folder, file))

                # Calculate the volume
                volume = librosa.feature.rms(y=y)[0].mean()

                # Update the loudest file if the current volume is higher
                if max_volume is None or volume > max_volume:
                    max_volume = volume
                    loudest_file = file

        # Print the file with the maximum volume
        print("File with the maximum volume:", loudest_file)

        # Reset the collection folder
        shutil.rmtree(collection_folder)
        os.makedirs(collection_folder)
        
        
        return loudest_file


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
                if filename_.endswith('.wav'):
                    blob_.download_to_filename('input_sound_files/' + filename_)
            if not running_sound:
                break
            if first_run_sound:
                time.sleep(15) 
                first_run_sound = False
            result = run_separator()
            socketio.emit('new_result', {"result": result})
        time.sleep(1)

@socketio.on('start_checking_')
def start_checking_sound():
    global running_sound
    global first_run_sound
    running_sound = True
    first_run_sound = True
    socketio.start_background_task(check_files_sound)

@socketio.on('stop_checking_')
def stop_checking_sound():
    global running_sound
    running_sound = False



@app.route('/')
def index():
    return render_template('stream.html')

if __name__ == '__main__':
    socketio.run(app, debug=True)