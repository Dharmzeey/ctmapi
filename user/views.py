from django.contrib.auth import authenticate, login
from django.db import IntegrityError
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from .models import SubscriptionHistory, User, UserInfo, Vendor
from utilities.vendor import create_vendor, has_vendor_profile, view_vendor, activate_vendor_subscription

from utilities2.error_handler import render_errors
from utilities2.token_handler import get_validate_send_token
from utilities2.user_details import return_user_details
from . import serializers as customAPISerializers


class UserCreate(APIView):
  serializer_class = customAPISerializers.UserSerializer
  def post(self, request):
    serializer = self.serializer_class(data=request.data)
    if serializer.is_valid():
      try:
        user = serializer.save()
        tokens = TokenObtainPairSerializer().validate(request.data)
        access_token = tokens['access']
        refresh_token = tokens['refresh']
        data = {
          'message': 'User created successfully',
          'token': access_token,
          # 'refresh_token': refresh_token,
        }
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        return Response(data, status=status.HTTP_201_CREATED)
      except IntegrityError as e:
        return Response({'message': 'User with this email or username already exists.'}, status=status.HTTP_409_CONFLICT)
    return Response({'message': f'{serializer.errors}'}, status=status.HTTP_400_BAD_REQUEST)
user_create = UserCreate.as_view()


class UserLogin(APIView):
  serializer_class = customAPISerializers.UserSerializer
  def post(self, request):
    username = request.data.get("username")
    password = request.data.get("password")
    try:
      user = User.objects.get(username=username)
    except User.DoesNotExist:
      return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    user = authenticate(request, username=username, password=password)
    if user is not None:
      login(request, user)
      refresh = RefreshToken.for_user(user)
      access_token = str(refresh.access_token)
      # ------Checks if the user has added their info------#
      try:
        UserInfo.objects.get(user=user)
      except UserInfo.DoesNotExist:
        data = {"message": "Login successful", "token": access_token}
        return Response(data, status=status.HTTP_200_OK)
      # CALLS THE FUNCTION THAT PROCESSES AND RETURNS USER DATA
      user_details = return_user_details(user, request)            
      data = {"message": "Login successful", "data": user_details, "token": access_token}
      return Response(data, status=status.HTTP_200_OK)
    return Response({"message": "Invalid Credentials",}, status=status.HTTP_401_UNAUTHORIZED)
user_login = UserLogin.as_view()


class UserAddInfo(APIView):
  serializer_class = customAPISerializers.UserInfoSerializer
  permission_classes = [IsAuthenticated]
  
  def post(self, request):
    serializer = self.serializer_class(data=request.data)
    token = get_validate_send_token(request)
    if serializer.is_valid():
      serializer.save(user=request.user, email=request.user.email)
      data = {"message": "Profile created successfully", "data": serializer.data, "token": token}
      return Response(data, status=status.HTTP_201_CREATED)
    data = {"message": render_errors(serializer.errors), "token": token}
    return Response(data, status=status.HTTP_400_BAD_REQUEST)
user_addinfo = UserAddInfo.as_view()


class UserUpdateInfo(APIView):
  serializer_class = customAPISerializers.UserInfoSerializer
  permission_classes = [IsAuthenticated]
  
  def patch(self, request):
    try:
      UserInfo.objects.get(user=request.user)
      user = request.user.user_info
    except UserInfo.DoesNotExist:
      return Response({"message": "Update your user info"}, status=status.HTTP_404_NOT_FOUND)
    serializer = self.serializer_class(instance=user, data=request.data, partial=True, context={'request': request})
    print(serializer)
    token = get_validate_send_token(request)
    if serializer.is_valid():
      serializer.save()
      data = {"message": "Profile updated successfully", "data": serializer.data, "token": token}
      return Response(data, status=status.HTTP_200_OK)
    data = {"message": render_errors(serializer.errors), "token": token}
    return Response(data, status=status.HTTP_400_BAD_REQUEST)
user_updateinfo = UserUpdateInfo.as_view()


class VendorRequest(APIView):
  permission_classes = [IsAuthenticated]
  def post(self, request):
    token = get_validate_send_token(request)
    try:
      UserInfo.objects.get(user=request.user)
    except UserInfo.DoesNotExist:
      return Response({"message": "Please Create Your Profile first", "token": token}, status=status.HTTP_403_FORBIDDEN)      
    try:
      Vendor.objects.get(seller=request.user)
      return Response({"message": "You are already a vendor", "token": token}, status=status.HTTP_409_CONFLICT)
    except Vendor.DoesNotExist:
      create_vendor(request)
      return Response({"message": "Vendor Profile activated", "token": token}, status=status.HTTP_201_CREATED)
    # FROM HERE IT REDIRECTS TO CREATE STORE PAGE
vendor_request = VendorRequest.as_view()


class VendorProfile(APIView):
  serializer_class = customAPISerializers.VendorSerializer
  permission_classes = [IsAuthenticated]
  def get(self, request):
    if has_vendor_profile(request):
      serializer = self.serializer_class(instance=request.user.selling_vendor)
      vendor = view_vendor(request)
      if vendor["latest_sub"] == "Free Trial":
        sub_history = {'sub_date': 'Free Trial'}
      else:
        sub_history = customAPISerializers.SubscriptionHistorySerializer(instance=vendor["latest_sub"]).data
      data = {"data": serializer.data, "token":get_validate_send_token(request), "activated_on": sub_history['sub_date'], "days_remaining": vendor["days_remaining"]}
      return Response(data, status=status.HTTP_200_OK)
    return Response({"message": "You are not a vendor"}, status=status.HTTP_401_UNAUTHORIZED)
vendor_profile = VendorProfile.as_view()


class ActivateSubscription(APIView):
  serializer_class = customAPISerializers.ActivateSubscriptionSerializer
  permission_classes = [IsAuthenticated]
  def post(self, request):
    if request.user.selling_vendor.active_subscription:
      return Response({"message": "You have an existing subscription!!!", "token": get_validate_send_token(request)}, status=status.HTTP_403_FORBIDDEN)
    serializer = self.serializer_class(data=request.data)
    if serializer.is_valid():
      package = serializer.data["package"]
      duration = serializer.data["duration"]
      if activate_vendor_subscription(request, package, duration):
        return Response({"message": f"Congratulations!!! Your {duration} months {package} plan has successfully been activated",  "token": get_validate_send_token(request)}, status=status.HTTP_200_OK)
      return Response({"message": "Payment Failed!!!",  "token": get_validate_send_token(request)}, status=status.HTTP_402_PAYMENT_REQUIRED)
    return Response({"message": "Invalid parameter passed",  "token": get_validate_send_token(request)}, status=status.HTTP_400_BAD_REQUEST)
activate_subscription = ActivateSubscription.as_view()


class SubscriptionHistory(APIView):
  serializer_class = customAPISerializers.SubscriptionHistorySerializer
  model = SubscriptionHistory
  permission_classes = [IsAuthenticated]
  def get(self, request):
    if has_vendor_profile(request):
      vendor = Vendor.objects.get(seller=request.user.id)
      history = self.model.objects.filter(vendor=vendor)
      serializer = self.serializer_class(instance=history, many=True)
      data = {"data": serializer.data, "token": get_validate_send_token(request)}
      return Response(data, status=status.HTTP_200_OK)
subscription_history = SubscriptionHistory.as_view()

