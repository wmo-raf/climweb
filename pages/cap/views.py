from capeditor.renderers import CapXMLRenderer
from capeditor.serializers import AlertSerializer
from rest_framework import generics

from .models import CapAlertPage


class AlertList(generics.ListAPIView):
    serializer_class = AlertSerializer
    serializer_class.Meta.model = CapAlertPage

    renderer_classes = (CapXMLRenderer,)
    queryset = CapAlertPage.objects.live()


class AlertDetail(generics.RetrieveAPIView):
    serializer_class = AlertSerializer
    serializer_class.Meta.model = CapAlertPage

    renderer_classes = (CapXMLRenderer,)
    queryset = CapAlertPage.objects.live()

    lookup_field = "identifier"
