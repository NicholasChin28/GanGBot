import boto3
import os
from botocore.exceptions import ClientError

from dotenv import load_dotenv
# Represents connection to AWS S3
# Add a deconstructor if init has any errors? 
# Refer to: https://stackoverflow.com/questions/1507082/python-is-it-bad-form-to-raise-exceptions-within-init
# https://stackoverflow.com/questions/4730435/exception-passing-in-python

# TODO: Use settings file instead of constantly using load_dotenv() in every .py file
# https://pypi.org/project/simple-settings/
# python-settings (pip module)

load_dotenv()

class AwsS3:
    def __init__(self) -> None:
        # Try to init connection to AWS S3 based on .env file
        # If failed, return error
        try:
            self.s3 = self.create_s3_connection()
        except Exception as f:
            print('Exception occurred in __init__')
            raise


    def create_s3_connection(self):
        print('Creating AWS S3 connection...')
        s3 = boto3.resource(
            service_name='s3',
            region_name='bad',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )

        try:
            for _ in s3.buckets.all():
                pass
        except Exception as e:
            print('Exception occurred')
            # return Exception
            # raise Exception
            print(e)
            raise