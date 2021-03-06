from botocore.exceptions import ClientError
import os
import boto3
from models.s3file import S3File


class S3Connection:
    def __init__(self):
        self.s3 = self.create_s3_connection()
        self.playsounds_bucket = os.getenv('AWS_BUCKET')
        self.s3_bucket = self.get_bucket()

    def create_s3_connection(self):
        print('Creating AWS S3 connection...')
        s3 = boto3.resource(
            service_name='s3',
            region_name='ap-southeast-1',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )

        # Check if credentials and permissions are correct
        try:
            for _ in s3.buckets.all():
                pass
        except ClientError as e:
            print(f'Client error: {e}')
            return None

        print('AWS S3 connection established')

        return s3

    # Get playsound bucket
    def get_bucket(self):
        print('get_bucket function')
        # exists = True

        # Check if bucket exist. V2
        try:
            self.s3.meta.client.head_bucket(Bucket=self.playsounds_bucket)
            return self.s3.Bucket(self.playsounds_bucket)
        except ClientError as e:
            # If a client error is thrown, then check that it was a 404 error.
            # If it was a 404 error, then the bucket does not exist.
            error_code = e.response['Error']['Code']
            if error_code == '403':
                print('Private bucket. Forbidden Access!')
            elif error_code == '404':
                # exists = False
                print('Bucket does not exist')
                print('Creating bucket...')
                self.create_bucket()
                return self.s3.Bucket(self.playsounds_bucket)

        return None

    # Check if file exists in bucket
    async def check_file(self, filename):
        try:
            self.s3.Object(self.playsounds_bucket, filename).load()
        except ClientError as e:
            return int(e.response['Error']['Code']) != 404
        return True

    # Downloads file from bucket
    async def download_file(self, filename, exists):
        try:
            self.s3_bucket.download_file(filename, filename)
        except ClientError as e:
            if e.response['Error']['Code'] == "404":
                print("The object does not exist")

    # Uploads file to bucket
    def upload_files(self, files):
        file_uploads = []
        for file in files:
            try:
                self.s3_bucket.upload_file(file, file)
                file_uploads.add(S3File(file, '200'))
            except ClientError as e:
                if e.response['Error']['Code'] == '404':
                    print("Bucket does not exist. Called from upload_file")
                elif e.response['Error']['Code'] == '403':
                    print("Insufficient permissions to upload file")
                file_uploads.add(S3File(file, e.response['Code']))
            
        return file_uploads     # Returns status of each file upload

    # Create bucket
    def create_bucket(self):
        self.s3.create_bucket(Bucket=self.playsounds_bucket, CreateBucketConfiguration={
            'LocationConstraint': 'ap-southeast-1'
        })
        print('Bucket created...')
        """
        if playsound_bucket.creation_date:
            print("The bucket exists")
        else:
            print('Bucket does not exist. Creating bucket...')
            # Create the bucket
            s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={
                'LocationConstraint': 'ap-southeast-1'
            })
            print('Bucket created...')
        """