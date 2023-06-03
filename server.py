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

# -----------------------------------------------------------------

def check_files_image():
    global video_files
    global existing_files
    global running_image
    while running_image:  
        with lock_image:
            blobs = list(bucket.list_blobs(prefix='video/')) 
            for blob in blobs:
                if not running_image:
                    break
                filename = blob.name.replace('video/', '')
                if filename.endswith('.avi') and filename not in video_files and filename not in existing_files:
                    blob.download_to_filename('video_files/video/' + filename)
                    video_files.add(filename)
                    yolov7_process = subprocess.run(['python', 'yolov7-main/detect.py', '--weights', './yolov7-main/yolov7.pt', '--classes', '0', '--source', 'video_files/video/' + filename, '--nosave'])
                    for analyzed_filename in os.listdir('./crop'):
                        if not running_image:
                            break
                        with open('./crop/' + analyzed_filename, 'rb') as img:
                            encoded_string = base64.b64encode(img.read()).decode('utf-8')
                            socketio.emit('new_image', {"image": encoded_string, "time": time.time(), "gps": "dummy gps value"})
                            time.sleep(1)
                    if not running_image:
                        break
            if not running_image:
                break
        time.sleep(1)

@socketio.on('start_checking')
def start_checking_image():
    global running_image 
    running_image = True 
    socketio.start_background_task(check_files_image)

@socketio.on('stop_checking')
def stop_checking_image():
    global running_image 
    running_image = False 

@socketio.on('clear_images')
def clear_images_image():
    global running_image
    if not running_image:
        for filename in os.listdir('./crop'):
            os.remove('./crop/' + filename)
    else:
        emit('clear_failed', {"message": "Can't clear images while checking is running."})



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
