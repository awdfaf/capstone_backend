import subprocess
import os
import cv2
import time
import multiprocessing


pipeline1 = 'v4l2src device=/dev/video1 ! video/x-raw, width=80, height=60, framerate=9/1, format=UYVY ! videoconvert ! video/x-raw, format=BGR ! appsink'
pipeline2 = 'nvarguscamerasrc sensor-id=0 ! video/x-raw(memory:NVMM), width=640, height=480, framerate=21/1 ! nvvidconv ! video/x-raw, format=BGRx ! videoconvert ! video/x-raw, format=BGR ! appsink'

project_id = 'my-project-383911'

bucket_name = 'awdfaf'



def capture_and_save_1(pipeline, filename, width, height):
 
    while True:

	# Create a VideoCapture object with the camera pipeline
        cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)

        # Record start time
        start_time = time.time()

        while True:
            ret, frame = cap.read()
            if not ret:
                print("Can't receive frame (stream end?). Exiting ...")
                break

            # Save the frame as an image file
            cv2.imwrite(f"{start_time}.jpg", frame)
            print(f"Captured frame")
            local_file_path = f"./{start_time}.jpg"
            upload_to_storage_image(local_file_path, bucket_name, f"{start_time}.jpg")
            
            thermal_image = cv2.imread(local_file_path)
           
            gray_image = cv2.cvtColor(thermal_image, cv2.COLOR_BGR2GRAY)

            output_path = f"{start_time}.jpg"
            cv2.imwrite(output_path, gray_image)

            upload_to_storage_image_gray(output_path, bucket_name, f"gray_{start_time}.jpg")
            if time.time() - start_time > 1:  # Capture duration of 10 seconds
                break


        # Release the VideoCapture object
        cap.release()


def capture_and_save_2(pipeline, filename, width, height):
    # Define the codec and create a VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'XVID')

    # File index
    cnt = 0

    while True:
        
        out = cv2.VideoWriter(f'{filename}.avi', fourcc, 20.0, (width, height))

        # Create a VideoCapture object with the camera pipeline
        cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)

        # Record start time
        start_time = time.time()

        while True:
            ret, frame = cap.read()
            if not ret:
                print("Can't receive frame (stream end?). Exiting ...")
                break

            # Write the frame
            out.write(frame)

            cv2.imshow('frame', frame)
            if cv2.waitKey(1) == ord('q') or time.time() - start_time > 10: # 10 seconds
                break

        # Release everything when job is finished
        cap.release()
        out.release()


        local_file_path = './output2.avi'
        upload_to_storage_video(local_file_path, bucket_name, "1_" + str(cnt) + ".avi")

        cnt += 1




    cv2.destroyAllWindows()




def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    if error:
        raise Exception(f"Command execution failed: {error.decode()}")
    return output.decode()

def gcloud_init():
    run_command("gcloud init")

def authenticate_gcloud():
    run_command("gcloud auth login")

def set_project(project_id):
    run_command(f"gcloud config set project {project_id}")

def access_storage_bucket(bucket_name):
    run_command(f"gsutil ls gs://{bucket_name}")

def upload_to_storage_video(local_file_path, bucket_name, index):
    run_command(f"gsutil cp {local_file_path} gs://{bucket_name}/video/" + str(index))
  
def upload_to_storage_image(local_file_path, bucket_name, index):
    run_command(f"gsutil cp {local_file_path} gs://{bucket_name}/image/" + str(index))
 
def upload_to_storage_image_gray(local_file_path, bucket_name, index):
    run_command(f"gsutil cp {local_file_path} gs://{bucket_name}/image_gray/" + str(index))

if __name__ == "__main__":

    set_project(project_id)
    access_storage_bucket(bucket_name)

    process1 = multiprocessing.Process(target=capture_and_save_1, args=(pipeline1, 'output1', 80, 60))
    process2 = multiprocessing.Process(target=capture_and_save_2, args=(pipeline2, 'output2', 640, 480))

    process1.start()
    process2.start()

    process1.join()
    process2.join()
 

    sleep(2)
    

