from django.urls import path
from . import views

app_name = "user"
urlpatterns = [
  
  path('create/', views.user_create, name="user_create"),
  path('login/', views.user_login, name="user_login"),
  
  path('send-email-verification/', views.send_email_verificiation, name="send_email_verificiation"),
  path('verify-email/', views.verify_email, name="verify_email"),
  path('forgot-password/', views.forgot_password, name="forgot_password"),
  path('reset-password/', views.reset_password, name="reset_password"),
  path('create-new-password/', views.create_new_password, name="create_new_password"),
  
  
  path('add-info/', views.add_user_info, name="add_user_info"),
  path('update-info/', views.update_user_info, name="update_user_info"),
  path('delete-user/', views.delete_user_info, name="delete_user_info"),
  
  path('vendor-request/', views.vendor_request, name="vendor_request"),
  path('vendor-profile/', views.vendor_profile, name="vendor_profile"),
  path('activate-subscription/', views.activate_subscription, name="activate_subscription"),
  path('subscription-history/', views.subscription_history, name="subscription_history"),

]

