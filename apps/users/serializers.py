from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'password', 'avatar', 'bio')

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'avatar', 'bio', 'is_online', 'last_seen', 'email_notifications')
        read_only_fields = ('id', 'email', 'is_online', 'last_seen')


class UserMiniSerializer(serializers.ModelSerializer):
    """Compact serializer for embedding in messages/rooms."""
    class Meta:
        model = User
        fields = ('id', 'username', 'avatar', 'is_online')
