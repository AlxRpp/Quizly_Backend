from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
User = get_user_model()


class RegisterUserSerializer(serializers.ModelSerializer):
    repeated_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'repeated_password']
        extra_kwargs = {
            'password': {
                'write_only': True
            },
            'email': {
                'required': True
            }
        }

    def validate_repeated_password(self, value):
        password = self.initial_data.get('password')
        if password and value and password != value:
            raise serializers.ValidationError(
                {'error': 'please enter valid credentials'})
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                {'error': 'email is already given'})
        return value

    def save(self):
        pw = self.validated_data.get('password')
        account = User(
            email=self.validated_data['email'], username=self.validated_data.get(
                'username')
        )
        account.set_password(pw)
        account.save()
        return account
