""" coding=utf-8 """
from rest_framework import serializers
from .models import Bill, Product, BillProduct
from django.contrib.auth.models import User


class RegistrationSerializer(serializers.ModelSerializer):
    """ Serializador de clase para registrar usuarios """

    # Campos para validacion
    email = serializers.CharField(max_length=60, min_length=6)
    username = serializers.CharField(max_length=60, min_length=6)
    password = serializers.CharField(max_length=150, write_only=True)

    class Meta:
        """ clase meta """

        model = User
        fields = ('first_name', 'last_name', 'email', 'username', 'password')

    def validate(self, args):
        """
        Validar
        :param args:
        """
        email = args.get('email', None)
        username = args.get('username', None)
        # password = args.get('password', None)
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({'email': 'email already exists'})

        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError({'username': 'username already exists'})

        return super(RegistrationSerializer, self).validate(args)

    def create(self, validated_data):
        """
        Crear
        :param validated_data:
        """
        return User.objects.create_user(**validated_data)


class BillSerializer(serializers.ModelSerializer):
    """ Serializador modelo Bill """

    class Meta:
        """ clase meta """
        model = Bill
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    """ Serializador modelo Product """

    class Meta:
        """ clase meta """
        model = Product
        fields = '__all__'


class BillProductSerializer(serializers.ModelSerializer):
    """ Serializador modelo BillProduct """

    class Meta:
        """ clase meta """
        model = BillProduct
        fields = '__all__'
