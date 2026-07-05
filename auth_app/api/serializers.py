from rest_framework import serializers
from django.contrib.auth import get_user_model
User = get_user_model()


class RegisterUserSerializer(serializers.ModelSerializer):
    """Serializer for the register endpoint, takes username/email/password/
    confirmed_password and creates a new User out of it."""
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
        """Check password and confirmed_password are really the same, before
        we save anything to the db."""
        password = self.initial_data.get('password')
        if password and value and password != value:
            raise serializers.ValidationError(
                {'error': 'please enter valid credentials'})
        return value

    def validate_email(self, value):
        """Dont allow register with an email that already exist in the db."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                {'error': 'email is already given'})
        return value

    def save(self):
        """Overwrite the default save() because User.objects.create() cant
        handle repeated_password (its not a real field on the User model),
        and we need set_password() so the password gets hashed properly,
        not saved as plain text."""
        pw = self.validated_data.get('password')
        account = User(
            email=self.validated_data['email'], username=self.validated_data.get(
                'username')
        )
        account.set_password(pw)
        account.save()
        return account
