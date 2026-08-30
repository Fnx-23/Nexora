"""Serializers for the documents API."""

from rest_framework import serializers

from apps.documents.models import Document


class DocumentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            "id",
            "original_filename",
            "mime_type",
            "size",
            "entity_kind",
            "entity_id",
            "uploaded_by",
            "uploaded_by_name",
            "url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "original_filename",
            "mime_type",
            "size",
            "uploaded_by",
            "uploaded_by_name",
            "url",
            "created_at",
            "updated_at",
        ]

    def get_uploaded_by_name(self, obj):
        if obj.uploaded_by is None:
            return "Unknown"
        return obj.uploaded_by.get_full_name() or obj.uploaded_by.email

    def get_url(self, obj):
        request = self.context.get("request")
        if request and obj.file:
            return request.build_absolute_uri(obj.file.url)
        return None


class DocumentRenameSerializer(serializers.Serializer):
    filename = serializers.CharField(max_length=255, min_length=1)
