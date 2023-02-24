from django.shortcuts import render

# Create your views here.
from rest_framework.response import Response

from rest_framework import generics
from capeditor.models import Alert
from capeditor.serializers import AlertSerializer
from rest_framework_xml.renderers import XMLRenderer



class AlertList(generics.ListAPIView):
    # queryset = Alert.objects.all()
    # serializer_class = AlertSerializer
    renderer_classes = (XMLRenderer,)

    def get(self, request, format=None):
        pages = Alert.objects.all()
        serializer = AlertSerializer(pages, many=True)
        return Response(serializer.data)
