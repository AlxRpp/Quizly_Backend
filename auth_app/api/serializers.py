from rest_framework import serializers
from django.contrib.auth import get_user_model
User = get_user_model()


class RegisterUserSerializer(serializers.ModelSerializer):
    """Creates a User from username/email/password/confirmed_password."""
    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirmed_password']
        extra_kwargs = {
            'password': {
                'write_only': True
            },
            'email': {
                'required': True
            }
        }

    def validate_confirmed_password(self, value):
        """Raises ValidationError if password and confirmed_password differ."""
        password = self.initial_data.get('password')
        if password and value and password != value:
            raise serializers.ValidationError(
                {'error': 'please enter valid credentials'})
        return value

    def validate_email(self, value):
        """Raises ValidationError if the email is already registered."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                {'error': 'email is already given'})
        return value

    def save(self):
        """Create the User with a hashed password via set_password().

        Overrides the default save() because confirmed_password isn't a
        real model field and ModelSerializer's default save() wouldn't
        hash the password.
        """
        pw = self.validated_data.get('password')
        account = User(
            email=self.validated_data['email'], username=self.validated_data.get(
                'username')
        )
        account.set_password(pw)
        account.save()
        return account
