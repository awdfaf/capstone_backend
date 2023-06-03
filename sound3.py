import os
import shutil
from spleeter.separator import Separator
import librosa

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

    max_volume = None
    loudest_file = None

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


if __name__ == '__main__':
    run_separator()
    