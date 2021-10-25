import asyncio
import os
from pathlib import Path
import boto3
from Models.s3file import S3File
from botocore.exceptions import ClientError
import functools


class S3Bucket:
    def __init__(self):
        pass
        # self.s3 = self.create_s3_connection()
        # self.bucket_name = os.getenv('AWS_BUCKET')
        # self.bucket = self.get_bucket()

        # print('Created variables')

    # Async function for listing the files from bucket
    def get_files(cls, ctx):
        server = ctx.message.guild.id 

        bucket_name = os.getenv('AWS_BUCKET')
        bucket = cls.get_bucket2(bucket_name)  

        # f = lambda x: Path(x).with_suffix("").as_posix().__str__().split('/')[1] if (len(Path(x).with_suffix("").as_posix().__str__().split('/')) > 1)
        
        to_return = [cls.get_filename(obj.key) for obj in bucket.objects.filter(Delimiter='/', Prefix=f"{server}/") if cls.get_filename(obj.key)]

        """
        for items in bucket.objects.filter(Delimiter='/', Prefix=f"{server}/"):
            print(items.head_object)
        """

        return to_return
        """
        for obj in bucket.objects.filter(Delimiter='/', Prefix=f"{server}/"):
            print(Path(obj.key).with_suffix('').as_posix().__str__().split('/')[1])
        """
    def get_filename(cls, x):
        str_list = Path(x).with_suffix("").as_posix().__str__().split('/')
        if len(str_list) > 1:
            return str_list[1]

    def upload_files(cls, ctx, files):
        print('upload_files')
        # loop = asyncio.get_running_loop()
        server = ctx.message.guild.id
        # TODO: Try creating connection in the function that is using it. instead of creating a global one, then passing it
        # connection = cls.create_connection()
        bucket_name = os.getenv('AWS_BUCKET')
        # bucket = cls.get_bucket(connection, bucket_name)
        # bucket = "test"
        bucket = cls.get_bucket2(bucket_name)

        print('val of bucket: ', bucket)
        # print('val of connection: ', connection)

        file_uploads = []
        for file in files:
            try:
                print('value of file ', file)
                bucket.upload_file(file, f"{server}/{file}")
                print('bucket uploaded file')
                file_uploads.append(S3File(file, '200'))
                print(f'Added bucket result: {file_uploads}')
            except ClientError as e:
                if e.response['Error']['Code'] == '404':
                    print("Bucket does not exist. Called from upload_file")
                elif e.response['Error']['Code'] == '403':
                    print("Insufficient permissions to upload file")
                file_uploads.append(S3File(file, e.response['Code']))
                # TODO: If response code is 200, then save the details in DB

        print('Finished uploading, returning file_uploads')
        return file_uploads     # Returns status of each file upload

    @classmethod
    async def upload_files2(cls, files):
        loop = asyncio.get_event_loop()

        partial = functools.partial(cls.upload_files, cls, files)
        data = await loop.run_in_executor(None, partial)

        if data:
            return data

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
    def get_bucket(self, s3, bucket_name: str):
        print('get_bucket function')

        # Check if bucket exist. V2
        try:
            s3.meta.client.head_bucket(Bucket=bucket_name)
            return s3.Bucket(bucket_name)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '403':
                print('Private bucket. Forbidden Access!')
            elif error_code == '404':
                print('Bucket does not exist')
                print('Creating bucket...')
                self.create_bucket(bucket_name)
                return s3.Bucket(bucket_name)

        return None

    # Get playsound bucket, v2
    def get_bucket2(self, bucket_name: str):
        print('get_bucket2 function')

        s3 = self.create_s3_connection()
        
        try:
            s3.meta.client.head_bucket(Bucket=bucket_name)
            return s3.Bucket(bucket_name)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '403':
                print('Private bucket. Forbidden Access!')
            elif error_code == '404':
                print('Bucket does not exist')
                print('Creating bucket...')
                self.create_bucket(bucket_name)
                return s3.Bucket(bucket_name)

        return None

    # Downloads file from bucket
    async def download_file(self, filename):
        try:
            self.bucket.download_file(filename, filename)
        except ClientError as e:
            if e.response['Error']['Code'] == "404":
                print("The object does not exist")

    # Check if file exists in bucket
    async def check_file(self, filename):
        try:
            self.s3.Object(self.playsounds_bucket, filename).load()
        except ClientError as e:
            return int(e.response['Error']['Code']) != 404
        return True

    # Create bucket
    def create_bucket(self, bucket_name: str):
        self.s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={
            'LocationConstraint': 'ap-southeast-1'
        })
        print('Bucket created...')

    # Get file from bucket
    # TODO: Get from specific server folder in bucket
    def get_playsound(self, name):
        bucket_name = os.getenv('AWS_BUCKET')
        bucket = self.get_bucket2(bucket_name)

        playsound = bucket.Object(name).get()['Body'].read() 
        return playsound



        