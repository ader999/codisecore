from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import User, Ciudad, CircuitoCreativo


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'es_protagonista', 'es_turista', 'telefono', 'foto_perfil',
            'is_staff', 'is_active'
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'required': False}
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = super().create(validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'es_protagonista', 'es_turista',
            'telefono', 'foto_perfil'
        ]

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Ya existe un usuario registrado con este correo electrónico.")
        return value

    def validate(self, attrs):
        password = attrs.get('password')
        password_confirm = attrs.pop('password_confirm', None)

        if password != password_confirm:
            raise serializers.ValidationError({"password_confirm": "Las contraseñas no coinciden."})

        try:
            validate_password(password)
        except DjangoValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})

        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data, password=password)
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, help_text="Nombre de usuario o correo electrónico")
    password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        username_or_email = attrs.get('username')
        password = attrs.get('password')

        user = None
        if '@' in username_or_email:
            try:
                found_user = User.objects.get(email__iexact=username_or_email)
                user = authenticate(username=found_user.username, password=password)
            except User.DoesNotExist:
                user = None
        else:
            user = authenticate(username=username_or_email, password=password)

        if not user:
            raise serializers.ValidationError("Credenciales inválidas. Por favor verifica tu usuario/correo y contraseña.")

        if not user.is_active:
            raise serializers.ValidationError("Esta cuenta de usuario está desactivada.")

        attrs['user'] = user
        return attrs



class CircuitoCreativoSerializer(serializers.ModelSerializer):
    ciudad_nombre = serializers.ReadOnlyField(source='ciudad.nombre')

    class Meta:
        model = CircuitoCreativo
        fields = [
            'id', 'ciudad', 'ciudad_nombre', 'nombre', 'descripcion',
            'distancia_km', 'duracion_estimada', 'dificultad', 'imagen_mapa'
        ]


class CiudadSerializer(serializers.ModelSerializer):
    circuitos = CircuitoCreativoSerializer(many=True, read_only=True)

    class Meta:
        model = Ciudad
        fields = [
            'id', 'nombre', 'descripcion', 'imagen_portada',
            'latitud_centro', 'longitud_centro', 'circuitos'
        ]
