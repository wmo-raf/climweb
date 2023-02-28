from django.views.generic import ListView, DetailView
from django_filters.rest_framework.backends import DjangoFilterBackend
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response

from .models import YoutubePlaylist
from .serializers import VideoPlaylistSerializer


class YoutubePlaylistView(ListView):
    model = YoutubePlaylist
    template_name = "playlist_list.html"
    context_object_name = "playlists"


class YoutubePlaylistItemsView(DetailView):
    model = YoutubePlaylist
    template_name = 'playlist_items.html'
    context_object_name = 'playlist'


class VideoView(RetrieveModelMixin, GenericAPIView):
    queryset = YoutubePlaylist.objects.all()
    serializer_class = VideoPlaylistSerializer
    filter_backends = [DjangoFilterBackend, ]
    filterset_fields = ['service', ]
    renderer_classes = [TemplateHTMLRenderer]

    def get(self, request, *args, **kwargs):
        result = get_object_or_404(self.queryset, pk=kwargs['pk'])
        serializer = self.get_serializer(result)

        return Response({'result': serializer.data}, template_name='videos_include.html')