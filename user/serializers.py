import re
from rest_framework import serializers
from user.models import User, UserInfo, Vendor, SubscriptionHistory

# USER RELATED SERIALIZERS

class UserSerializer(serializers.ModelSerializer):
  password = serializers.CharField(min_length=8, max_length=150, write_only=True, error_messages={
    'required': 'Please enter a password',
    'min_length': 'Password must be at least 8 characters long',
    'max_length': 'Password must be no more than 128 characters long',
    'invalid': 'Please enter a valid password'
  })
  username = serializers.CharField(min_length=4, max_length=150, error_messages={
    'required': 'Please enter a username',
    'min_length': 'Username must be at least 4 characters long',
    'max_length': 'Username must be no more than 150 characters long',
    'invalid': 'Please enter a valid username',
  })
  
  
  class Meta:
    model = User
    fields = ['username', 'password', 'email']
      
  def create(self, validated_data):
    password = validated_data.pop("password")
    user = super().create(validated_data)
    user.set_password(password)
    user.save()
    return user
  
  def validate_username(self, value):
    pattern = r'^[a-zA-Z0-9_]+$'  #Only alphanumeric characters and underscores are allowed
    if not re.match(pattern, value):
      raise serializers.ValidationError("Invalid username. Please use only alphanumeric characters and underscores.")
    return value


class UserLoginSerializer(serializers.Serializer):
  username = serializers.CharField(min_length=4, max_length=150, error_messages={
    'required': 'Please enter a username',
    'min_length': 'Username must be at least 4 characters long',
    'max_length': 'Username must be no more than 150 characters long',
    'invalid': 'Please enter a valid username',
  })
  password = serializers.CharField(min_length=8, max_length=150, error_messages={
    'required': 'Please enter a password',
    'min_length': 'Password must be at least 8 characters long',
    'max_length': 'Password must be no more than 128 characters long',
    'invalid': 'Please enter a valid password'
  })


class EmailVeriificationSerializer(serializers.Serializer):
  pin = serializers.CharField(min_length=6, max_length=6)
  

class ForgotPasswordSerializer(serializers.Serializer):
  username = serializers.CharField()
  email = serializers.EmailField()
  
  
class ResetPasswordSerializer(serializers.Serializer):
  username = serializers.CharField()
  email = serializers.EmailField()
  pin = serializers.CharField(min_length=6, max_length=6)
  

class CreateNewPasswordSerializer(serializers.Serializer):
  username = serializers.CharField()
  email = serializers.EmailField()
  pin = serializers.CharField(min_length=6, max_length=6)
  password = serializers.CharField(min_length=8, max_length=150, error_messages={
    'required': 'Please enter a password',
    'min_length': 'Password must be at least 8 characters long',
    'max_length': 'Password must be no more than 128 characters long',
    'invalid': 'Please enter a valid password'
  })  

  
class UserInfoSerializer(serializers.ModelSerializer):
  # email = serializers.SerializerMethodField(readonly=True)
  class Meta:
    model = UserInfo
    fields = ["first_name", "last_name", "email", "state", "location", "institution", "address", "tel"]
    read_only_fields = ["email"]
  
  def to_representation(self, instance):
    representation = super().to_representation(instance)
    representation['state'] = instance.state.name
    representation['location'] = instance.location.name
    representation['institution'] = instance.institution.name
    return representation


class VendorSerializer(serializers.ModelSerializer):
  class Meta:
    model = Vendor
    # fields = "__all__"
    exclude = ("allow_video",)
  
  def to_representation(self, instance):
    representation = super().to_representation(instance)
    representation['seller'] = instance.seller.username
    return representation
    
    
class ActivateSubscriptionSerializer(serializers.Serializer):
  PACKAGES =(
    (2000, "SPOTLIGHT"),
    (3000, "HIGHLIGHT"),
    (6000, "FEATURED"),
  )
  package = serializers.ChoiceField(choices=PACKAGES)
  duration = serializers.IntegerField() # in months


class SubscriptionHistorySerializer(serializers.ModelSerializer):
  class Meta:
    model = SubscriptionHistory
    fields = "__all__"
  
  def to_representation(self, instance):
    representation = super().to_representation(instance)
    representation['vendor'] = instance.vendor.seller.username
    return representation
    