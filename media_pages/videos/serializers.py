from rest_framework import serializers
from .models import YoutubePlaylist


class VideoPlaylistSerializer(serializers.ModelSerializer):
    videos = serializers.SerializerMethodField('playlist_items')

    def playlist_items(self, obj):
        return obj.playlist_items(limit=3)

    class Meta:
        model = YoutubePlaylist
        fields = ['videos', 'title']