import os
import shutil
import wave
import math
from spleeter.separator import Separator

def run_separator():
    # Prepare to use Splitter
    separator = Separator('spleeter:2stems')

    # Set input folder and output path
    input_folder = "./input_sound_files"
    output_folder = "./output_sound_files"

    # Get the initial list of files in the input folder
    initial_files = set(os.listdir(input_folder))

    # Create the collection folder if it doesn't exist
    collection_folder = "./vocals_collection"
    if not os.path.exists(collection_folder):
        os.makedirs(collection_folder)

    while True:
        # Check for new files in the input folder
        current_files = set(os.listdir(input_folder))
        new_files = current_files - initial_files

        # Iterate over new files
        for file_name in new_files:
            if file_name.endswith(".wav"):
                # Set input file path
                input_audio_file = os.path.join(input_folder, file_name)

                # Perform voice extraction
                separator.separate_to_file(input_audio_file, output_folder)

                # Delete input audio file
                os.remove(input_audio_file)

        # Update the initial file list
        initial_files = current_files

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

        # Find file with the maximum volume in vocals_collection
        find_file_with_max_volume()

def find_file_with_max_volume():
    collection_folder = "./vocals_collection"

    # Get all WAV files in the collection folder
    wav_files = [file for file in os.listdir(collection_folder) if file.endswith(".wav")]

    max_volume = float("-inf")
    max_volume_file = None

    # Iterate over WAV files
    for file_name in wav_files:
        file_path = os.path.join(collection_folder, file_name)
        with wave.open(file_path, 'r') as wav:
            # Get the maximum amplitude
            max_amplitude = max(abs(float(sample)) for sample in wav.readframes(wav.getnframes()))

            # Calculate the volume (dBFS)
            volume = 20 * math.log10(max_amplitude / float(wav.getsampwidth()))

            # Check if it's the maximum volume so far
            if volume > max_volume:
                max_volume = volume
                max_volume_file = file_name

    if max_volume_file:
        print("File with the maximum volume:", max_volume_file)
    # else:
    #     print("No WAV files found in the collection folder.")

if __name__ == '__main__':
    run_separator()
