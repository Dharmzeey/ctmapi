import random
from datetime import datetime
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login
from django.conf import settings
from django.db import IntegrityError
import pytz
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import DestroyAPIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from .models import SubscriptionHistory, User, UserInfo, Vendor, EmailVerification, PhoneVerification, ForgotPassword
from utilities.vendor import create_vendor, has_vendor_profile, view_vendor, activate_vendor_subscription

from utilities.error_handler import render_errors
from utilities.user_details import return_user_details
from . import serializers as customAPISerializers


class UserCreateView(APIView):
  serializer_class = customAPISerializers.UserSerializer
  def post(self, request):
    serializer = self.serializer_class(data=request.data)
    if serializer.is_valid():
      try:
        user = serializer.save()
        tokens = TokenObtainPairSerializer().validate(request.data)
        access_token = tokens['access']
        # refresh_token = tokens['refresh']
        data = {
          'message': 'User created successfully',
          'token': access_token,
          # 'refresh_token': refresh_token,
        }
        # login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        login(request, user)
        return Response(data, status=status.HTTP_201_CREATED)
      except IntegrityError:
        return Response({'error': 'User with this email or username already exists.'}, status=status.HTTP_409_CONFLICT)
    data = {"errors": render_errors(serializer.errors)}
    return Response(data, status=status.HTTP_400_BAD_REQUEST)
user_create = UserCreateView.as_view()


class UserLoginView(APIView):
  serializer_class = customAPISerializers.UserLoginSerializer
  def post(self, request):
    serializer = self.serializer_class(data=request.data)
    if serializer.is_valid():
      username = serializer.data.get("username")
      password = serializer.data.get("password")
      try:
        user = User.objects.get(username=username)
      except User.DoesNotExist:
        return Response({"error": "User does not exists"}, status=status.HTTP_404_NOT_FOUND)
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
      return Response({"error": "Invalid Credentials",}, status=status.HTTP_401_UNAUTHORIZED)
    data = {"errors": render_errors(serializer.errors)}
    return Response(data, status=status.HTTP_400_BAD_REQUEST)
user_login = UserLoginView.as_view()


class SendEmailVerificationView(APIView):
  permission_classes = [IsAuthenticated]
  def post(self, request):
    user = request.user
    if user.email_verified:
      return Response({"error": "Email has already been verified"}, status=status.HTTP_401_UNAUTHORIZED)
    try:
      EmailVerification.objects.get(user=user)
      return Response({"message": "Email Verification already sent"}, status=status.HTTP_401_UNAUTHORIZED)
    except EmailVerification.DoesNotExist:
      pin = str(random.randint(100000, 999999))
      # send email succesfully before saving to DB
      send_mail(
        'Campus Trade Mart Email Verification',
        f'Hello {request.user} \nYour verification PIN is {pin}. \nIt will expire in 10 minutes',
        settings.EMAIL_HOST_USER,
        [user.email],
        fail_silently=False,
      )
      EmailVerification.objects.create(user=user, email=user.email, email_verification_pin=pin)
    return Response({"message": "verification PIN sent to email."}, status=status.HTTP_200_OK)
send_email_verificiation = SendEmailVerificationView.as_view()


class VerifyEmailView(APIView):
  permission_classes = [IsAuthenticated]
  serializer_class = customAPISerializers.EmailVeriificationSerializer
  def post(self, request):
    serializer = self.serializer_class(data=request.data)
    if serializer.is_valid():
      user=request.user
      try:
        fetch_pin = EmailVerification.objects.get(user=user)
      except EmailVerification.DoesNotExist:
        return Response({"error": "PIN has not been sent"}, status=status.HTTP_404_NOT_FOUND)
      utc=pytz.UTC
      if fetch_pin.expiry < utc.localize(datetime.now()):
        fetch_pin.delete() # remove the instnace on the Email OTP table if expired
        return Response({"error": "PIN expired"}, status=status.HTTP_401_UNAUTHORIZED)
      if fetch_pin.email_verification_pin == serializer.data['pin']:
        user.email_verified = True
        user.save()
        fetch_pin.delete() # remove the instnace on the Email OTP table 
        return Response({"message": "Email verified successfully"}, status=status.HTTP_200_OK)
      return Response({"error": "Invalid PIN"}, status=status.HTTP_403_FORBIDDEN)
    return Response({"errors": render_errors(serializer.errors)}, status=status.HTTP_404_NOT_FOUND)
verify_email = VerifyEmailView.as_view()


class SendPhoneVerificationView(APIView):
  def post(self, request):
    return Response()


class VerifyPhoneView(APIView):
  def post(self, request):
    return Response()
verify_phone = VerifyPhoneView.as_view()


class ForgotPasswordView(APIView):
  def post(self, request):
    serializer_class = customAPISerializers.ForgotPasswordSerializer
    serializer = serializer_class(data=request.data)
    if serializer.is_valid():
      try:
        user = User.objects.get(username=serializer.data['username'], email=serializer.data['email'])
        if ForgotPassword.objects.filter(user=user).exists(): # checks if the password PIN has been sent 
          return Response({"error": "password reset PIN already sent"}, status=status.HTTP_409_CONFLICT)
        pin = str(random.randint(100000, 999999))
        # send email succesfully before saving to DB
        send_mail(
          'Campus Trade Mart Password Reset',
          f'Hello {user} \nYour password reset PIN is {pin}. \nIt will expire in 10 minutes',
          settings.EMAIL_HOST_USER,
          [user.email],
          fail_silently=False,
        )
        ForgotPassword.objects.create(user=user, email=user.email, reset_password_pin=pin)
        return Response({"message": "password reset PIN sent to email."}, status=status.HTTP_200_OK)
      except User.DoesNotExist:
        return Response({"error": "User information not found"}, status=status.HTTP_404_NOT_FOUND)
    return Response({"errors": render_errors(serializer.errors)}, status=status.HTTP_404_NOT_FOUND)
forgot_password = ForgotPasswordView.as_view()


class ResetPasswordView(APIView):
  serializer_class = customAPISerializers.ResetPasswordSerializer
  def post(self, request):
    serializer = self.serializer_class(data=request.data)
    if serializer.is_valid():
      try:
        user = User.objects.get(username=serializer.data['username'], email=serializer.data['email'])
        fetch_pin = ForgotPassword.objects.get(user=user, email=serializer.data['email'])
      except ForgotPassword.DoesNotExist:
        return Response({"error": "password reset PIN has not been sent"}, status=status.HTTP_404_NOT_FOUND)
      except User.DoesNotExist:
        return Response({"error": "User information not found"}, status=status.HTTP_404_NOT_FOUND)
      utc=pytz.UTC
      if fetch_pin.expiry < utc.localize(datetime.now()):
        fetch_pin.delete() # remove the instnace on the Email OTP table if expired
        return Response({"error": "password reset PIN expired"}, status=status.HTTP_401_UNAUTHORIZED)
      if fetch_pin.reset_password_pin == serializer.data['pin']:
        return Response({"message": "password reset PIN verified successfully"}, status=status.HTTP_200_OK) # after this, the next page to be shown to the user is where the user will fill in their new password
      return Response({"error": "Invalid PIN"}, status=status.HTTP_403_FORBIDDEN)
    return Response({"errors": render_errors(serializer.errors)}, status=status.HTTP_404_NOT_FOUND)
reset_password = ResetPasswordView.as_view()


class CreateNewPasswordView(APIView):
  serializer_class = customAPISerializers.CreateNewPasswordSerializer
  def post(self, request):
    serializer = self.serializer_class(data=request.data)
    if serializer.is_valid():
      try:
        user = User.objects.get(username=serializer.data['username'], email=serializer.data['email'])
        try:
          fetch_pin = ForgotPassword.objects.get(user=user, email=serializer.data['email'], reset_password_pin=serializer.data['pin'])
        except ForgotPassword.DoesNotExist:
          return Response({"error": "Could not reset password as PIN is invalid or User info invalid"}, status=status.HTTP_403_FORBIDDEN)
        user.set_password(serializer.data['password'])
        user.save()
        fetch_pin.delete()
      except User.DoesNotExist:
        return Response({"error": "User information not found"}, status=status.HTTP_404_NOT_FOUND)
      return Response({"message": "password changed successfully"}, status=status.HTTP_200_OK) 
    return Response({"errors": render_errors(serializer.errors)}, status=status.HTTP_404_NOT_FOUND)
create_new_password = CreateNewPasswordView.as_view()


class AddUserInfoView(APIView):
  serializer_class = customAPISerializers.UserInfoSerializer
  permission_classes = [IsAuthenticated]
  
  def post(self, request):
    serializer = self.serializer_class(data=request.data)
    if not request.user.email_verified:
      return Response({"error": "Email not verified"}, status=status.HTTP_401_UNAUTHORIZED)
    if serializer.is_valid():
      try:
        serializer.save(user=request.user, email=request.user.email)
      except IntegrityError:
        data = {"error": "User profile already exists"}
        return Response(data, status=status.HTTP_409_CONFLICT)
      data = {"message": "Profile created successfully", "data": serializer.data}
      return Response(data, status=status.HTTP_201_CREATED)
    data = {"errors": render_errors(serializer.errors)}
    return Response(data, status=status.HTTP_400_BAD_REQUEST)
add_user_info = AddUserInfoView.as_view()


class UpdateUserInfoView(APIView):
  serializer_class = customAPISerializers.UserInfoSerializer
  permission_classes = [IsAuthenticated]
  
  def patch(self, request):
    try:
      UserInfo.objects.get(user=request.user)
      user = request.user.user_info
    except UserInfo.DoesNotExist:
      return Response({"error": "Add your user information"}, status=status.HTTP_404_NOT_FOUND)
    serializer = self.serializer_class(instance=user, data=request.data, partial=True, context={'request': request})
    if serializer.is_valid():
      serializer.save()
      data = {"message": "Profile updated successfully", "data": serializer.data}
      return Response(data, status=status.HTTP_200_OK)
    data = {"errors": render_errors(serializer.errors)}
    return Response(data, status=status.HTTP_400_BAD_REQUEST)
update_user_info = UpdateUserInfoView.as_view()


class DeleteUserInfoView(DestroyAPIView):
  serializer_class = customAPISerializers.UserSerializer
  permission_classes = [IsAuthenticated]
  def get_object(self):
    user = self.request.user
    if not user.is_authenticated:
      raise PermissionDenied("User cannot be deleted")
    return user
delete_user_info = DeleteUserInfoView.as_view()


class VendorRequestView(APIView):
  permission_classes = [IsAuthenticated]
  def post(self, request):
    try:
      UserInfo.objects.get(user=request.user)
    except UserInfo.DoesNotExist:
      return Response({"error": "Please Create Your Profile first"}, status=status.HTTP_403_FORBIDDEN)      
    try:
      Vendor.objects.get(seller=request.user)
      return Response({"error": "You are already a vendor"}, status=status.HTTP_409_CONFLICT)
    except Vendor.DoesNotExist:
      create_vendor(request)
      return Response({"message": "Vendor Profile activated"}, status=status.HTTP_201_CREATED)
    # FROM HERE IT REDIRECTS TO CREATE STORE PAGE
vendor_request = VendorRequestView.as_view()


class VendorProfileView(APIView):
  serializer_class = customAPISerializers.VendorSerializer
  # permission_classes = [IsAuthenticated]
  def get(self, request):
    if has_vendor_profile(request):
      serializer = self.serializer_class(instance=request.user.selling_vendor)
      vendor = view_vendor(request)
      if vendor["latest_sub"] == "Free Trial":
        sub_history = {'sub_date': 'Free Trial'}
      else:
        sub_history = customAPISerializers.SubscriptionHistorySerializer(instance=vendor["latest_sub"]).data
      data = {"data": serializer.data, "activated_on": sub_history['sub_date'], "days_remaining": vendor["days_remaining"]}
      return Response(data, status=status.HTTP_200_OK)
    return Response({"error": "You are not a vendor"}, status=status.HTTP_401_UNAUTHORIZED)
vendor_profile = VendorProfileView.as_view()


class ActivateSubscriptionView(APIView):
  serializer_class = customAPISerializers.ActivateSubscriptionSerializer
  permission_classes = [IsAuthenticated]
  def post(self, request):
    if request.user.selling_vendor.active_subscription:
      return Response({"error": "You have an existing subscription!!!"}, status=status.HTTP_403_FORBIDDEN)
    serializer = self.serializer_class(data=request.data)
    if serializer.is_valid():
      package = serializer.data["package"]
      duration = serializer.data["duration"]
      if activate_vendor_subscription(request, package, duration):
        return Response({"message": f"Congratulations!!! Your {duration} months {package} plan has successfully been activated"}, status=status.HTTP_200_OK)
      return Response({"error": "Payment Failed!!!"}, status=status.HTTP_402_PAYMENT_REQUIRED)
    return Response({"errors": render_errors(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)
activate_subscription = ActivateSubscriptionView.as_view()


class SubscriptionHistoryView(APIView):
  serializer_class = customAPISerializers.SubscriptionHistorySerializer
  model = SubscriptionHistory
  permission_classes = [IsAuthenticated]
  def get(self, request):
    if has_vendor_profile(request):
      vendor = Vendor.objects.get(seller=request.user.id)
      history = self.model.objects.filter(vendor=vendor)
      serializer = self.serializer_class(instance=history, many=True)
      data = {"data": serializer.data}
      return Response(data, status=status.HTTP_200_OK)
subscription_history = SubscriptionHistoryView.as_view()

