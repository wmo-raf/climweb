from rest_framework import serializers
from capeditor.models import Alert, AlertArea


class AlertAreaSerializer(serializers.ModelSerializer):
    alert_areas = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = AlertArea
        fields = ['alert_areas']

class AlertSerializer(serializers.ModelSerializer):
    alert_areas = AlertAreaSerializer()

    class Meta:
        model = Alert
        # fields = ['identifier', 'sender', 'sent', 'status', 'message_type', 'scope', 'source', 'restriction', 'code', 'note', 'language', 'category', 'event', 'urgency', 'severity', 'certainty', 'audience']
        fields = '__all__'
        depth = 1
        


    # def to_representation(self, instance):
    #     """
    #     Override the default to_representation() method to return only non-null fields.
    #     """
    #     data = super(AlertSerializer, self).to_representation(instance)
    #     return {key: value for key, value in data.items() if value is not None}