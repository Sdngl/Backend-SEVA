from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from .serializers import ChatSerializer
from ai.chatbot import chat
from ai.client import AIServiceError,AIInvalidResponse,AIRateLimited
class ChatView(APIView):
    permission_classes=[IsAuthenticated]
    @extend_schema(request=ChatSerializer,responses={200:dict})
    def post(self,r):
        s=ChatSerializer(data=r.data); s.is_valid(raise_exception=True)
        try: data=chat(**s.validated_data); return Response({'success':True,'data':data,'error':None})
        except AIServiceError as e:
            code,status='AI_SERVICE_UNAVAILABLE',503
            if isinstance(e,AIInvalidResponse): code,status='AI_INVALID_RESPONSE',502
            if isinstance(e,AIRateLimited): code,status='AI_RATE_LIMITED',429
            return Response({'success':False,'data':None,'error':{'code':code,'message':str(e)}},status=status)
