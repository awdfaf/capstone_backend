import multiprocessing
import pyaudio
import wave
import os
from time import sleep
from google.cloud import storage
from dotenv import load_dotenv


# Load the .env file
load_dotenv()

# GCP configuration
bucket_name = 'awdfaf'
service_account_json = os.getenv("KEY_PATH")  # Key of the environment variable that stores the path to your json file
storage_client = storage.Client.from_service_account_json(service_account_json)

def upload_file_to_gcp(source_file, destination_blob):
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(destination_blob)
    blob.upload_from_filename(source_file)

def record_audio(mic_index, output_filename):
    num_mics = 1
    output_dir = "./recordings"
    record_seconds = 5
    sample_rate = 48000
    audio = pyaudio.PyAudio()
    streams = []
   
    stream = audio.open(format=pyaudio.paInt16, channels=1, rate=sample_rate, input=True, frames_per_buffer=512, input_device_index=mic_index)
    streams.append(stream)
    print(f"Recording from microphone {mic_index}...")
    frames = [[] for _ in range(num_mics)]
    for i in range(0, int(sample_rate / 512 * record_seconds)):
        for mic in range(num_mics):
            data = streams[mic].read(512)
            frames[mic].append(data)
    print("Recording completed.")

    for mic in range(num_mics):
        streams[mic].stop_stream()
        streams[mic].close()
    audio.terminate()

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, output_filename)
    waveFile = wave.open(output_path, 'wb')
    waveFile.setnchannels(1)
    waveFile.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
    waveFile.setframerate(sample_rate)
    waveFile.writeframes(b''.join(frames[mic]))
    waveFile.close()
    print("Recording saved.")
    
    sleep(1)
    wav_files = os.listdir('./recordings')
    print(wav_files)
    if len(wav_files) == 2 :
        print('hello')
        upload_file_to_gcp(output_path, "sound/" + output_filename)
        sleep(1)
        print("Recording uploaded to Google Cloud Storage.")

def delete_files_in_folder(directory):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')

# Use the function:


if __name__ == '__main__':
    while True:
        delete_files_in_folder("./recordings")

        sleep(1)
        process_mic1 = multiprocessing.Process(target=record_audio, args=(11, "forward.wav"))
        process_mic2 = multiprocessing.Process(target=record_audio, args=(12, "backward.wav"))



        process_mic1.start()
        process_mic2.start()


        process_mic1.join()
        process_mic2.join()



        sleep(3)
