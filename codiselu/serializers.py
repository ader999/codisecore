from rest_framework import serializers
from .models import User, Ciudad, CircuitoCreativo


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'es_protagonista', 'es_turista', 'telefono', 'foto_perfil')
        read_only_fields = ('id', 'es_protagonista', 'es_turista')


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'confirm_password', 'first_name', 'last_name', 'es_protagonista', 'es_turista', 'telefono')

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')

        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class CiudadSerializer(serializers.ModelSerializer):
    circuitos_count = serializers.SerializerMethodField()

    class Meta:
        model = Ciudad
        fields = ('id', 'nombre', 'descripcion', 'imagen_portada', 'latitud_centro', 'longitud_centro', 'circuitos_count')

    def get_circuitos_count(self, obj):
        return obj.circuitos.count()


class CircuitoCreativoListSerializer(serializers.ModelSerializer):
    ciudad_nombre = serializers.CharField(source='ciudad.nombre', read_only=True)

    class Meta:
        model = CircuitoCreativo
        fields = ('id', 'ciudad', 'ciudad_nombre', 'nombre', 'descripcion', 'distancia_km', 'duracion_estimada', 'dificultad')


class CircuitoCreativoSerializer(serializers.ModelSerializer):
    ciudad_nombre = serializers.CharField(source='ciudad.nombre', read_only=True)

    class Meta:
        model = CircuitoCreativo
        fields = '__all__'
        read_only_fields = ('id',)
