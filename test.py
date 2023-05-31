import os
from google.cloud import storage
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

# GCP 설정
bucket_name = 'awdfaf'
service_account_json = os.getenv("KEY_PATH")
storage_client = storage.Client.from_service_account_json(service_account_json)
source_file_name = './files/0.jpg'    # GCP에 업로드할 파일 절대경로
destination_blob_name = '0.jpg'    # 업로드할 파일을 GCP에 저장할 때의 이름
bucket = storage_client.get_bucket(bucket_name)
blob = bucket.blob(destination_blob_name)
blob.upload_from_filename(source_file_name)
# source_blob_name = '0.jpg'    # GCP에 저장되어 있는 파일 명
# destination_file_name = './files/0.jpg'    # 다운받을 파일을 저장할 경로("local/path/to/file")
# bucket = storage_client.bucket(bucket_name)
# blob = bucket.blob(source_blob_name)
# blob.download_to_filename(destination_file_name)