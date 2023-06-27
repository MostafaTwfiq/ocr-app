from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import ImageSerializer
import numpy as np
import uuid
import jwt
import rpyc
from io import BytesIO
from .job_jwt_permission import JobJWTPermission
import pickle
import boto3
import datetime
import json
import pytz
import configparser
import os
from arabic_ocr_backend import settings

secret_key = settings.SECRET_KEY
hashing_alg = settings.HASHING_ALG
model_backend = settings.MODEL_BACKEND

config = configparser.ConfigParser()
config.read(os.path.join('ocr_api', 'aws_s3_config.ini'))
RESULTS_EXP_DAYS = config.getint('aws', 'RESULT_EXP_DAYS')
PRESIGNED_URL_EXP_SECOND = config.getint('aws', 'PRESIGNED_URL_EXP_SECOND')

# Create a timezone object for UTC+2
timezone = pytz.timezone(config.get('aws', 'TIMEZONE'))

model_conn = None
AWS = settings.AWS
s3 = None
if AWS['AWS_ACCESS_KEY_ID'] == None or settings.AWS['AWS_SECRET_ACCESS_KEY'] == None or settings.AWS['AWS_S3_REGION_NAME'] == None:
    s3 = boto3.client('s3') # This means the session bt default  will be created using the role assigned to the EC2 instance
else:
    s3 = boto3.client('s3', aws_access_key_id=settings.AWS['AWS_ACCESS_KEY_ID'], aws_secret_access_key=settings.AWS['AWS_SECRET_ACCESS_KEY'], 
                                region_name=settings.AWS['AWS_S3_REGION_NAME'])
bucket_name = settings.AWS['AWS_STORAGE_BUCKET_NAME']

def generate_model_callback(uuid):
    def handle_model_callback(result):
        job_uuid = uuid
        decoded_result =  pickle.loads(result)
        try:
            expiration_date = datetime.datetime.now(timezone) + datetime.timedelta(days=RESULTS_EXP_DAYS)
            file_name = str(job_uuid) + '.txt'
            s3.upload_fileobj(BytesIO(str(json.dumps(decoded_result)).encode('utf-8')), bucket_name, file_name, ExtraArgs={'Expires': expiration_date})
        except Exception as e:
            print(e)

    return handle_model_callback

# Create your views here.
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def arabic_ocr(req):
    global model_conn
    if model_conn == None or model_conn.closed:
        try:
            model_conn = rpyc.connect(model_backend['HOST'], model_backend['PORT'])
            rpyc.BgServingThread(model_conn)
        except:
            return Response({'message': 'Please try again after a while.'}, status=503)

    serializer = ImageSerializer(data=req.data)
    if serializer.is_valid():
        job_uuid = str(uuid.uuid4())
        
        images = serializer.validated_data['images']
        images_list = []
        for image in images:
            np_image = np.array(bytearray(image.read()), dtype=np.uint8)
            images_list.append(np_image)

        buffer = BytesIO()
        pickle.dump(images_list, buffer)
        model_status = model_conn.root.register_task(buffer.getvalue(), generate_model_callback(job_uuid))

        if model_status:
            encoded_job_id = jwt.encode({"user_id": req.user.id, "uuid": job_uuid, 
                                         "exp": datetime.datetime.now() + datetime.timedelta(days=RESULTS_EXP_DAYS)}, 
                                         secret_key, algorithm=hashing_alg)
            
            return Response({'job_token': encoded_job_id})
        
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated, JobJWTPermission])
def check_for_job(req):
    # Access the 'uuid' element in the job jwt payload
    job_uuid = req.job.payload['uuid']
    try:
        url = s3.generate_presigned_url(
        ClientMethod='get_object',
        Params={
            'Bucket': bucket_name,
            'Key': job_uuid + '.txt'
        },
        ExpiresIn=PRESIGNED_URL_EXP_SECOND
        )
        return Response({'results': url})
    except Exception as e:
        return Response({'results': "Not Done"})
