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
from arabic_ocr_backend import settings

secret_key = settings.SECRET_KEY
hashing_alg = settings.HASHING_ALG
model_backend = settings.MODEL_BACKEND

jobs_dict = dict()

model_conn = None

def generate_model_callback(uuid):
    def handle_model_callback(result):
        job_uuid = uuid
        decoded_result =  pickle.loads(result)
        jobs_dict[job_uuid] = decoded_result

    return handle_model_callback

# Create your views here.
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def arabic_ocr(req):
    global model_conn
    if model_conn == None or not model_conn.ping():
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
            encoded_job_id = jwt.encode({"user_id": req.user.id, "uuid": job_uuid},
                                    secret_key, algorithm=hashing_alg)
            
            return Response({'job_token': encoded_job_id})
        
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated, JobJWTPermission])
def check_for_job(req):
    # Access the 'uuid' element in the job jwt payload
    job_uuid = req.job.payload['uuid']
    if job_uuid in jobs_dict:
        return Response({'results': jobs_dict[job_uuid]})
    return Response({'results': "Not Done"}, status=status.HTTP_202_ACCEPTED)
