from django.urls import path
from . import views

urlpatterns = [
  
  path('user/create/', views.user_create, name="user_create"), # This will be done via browser
  path('user/login/', views.user_login, name="user_login"),
  path('user/addinfo/', views.user_addinfo, name="user_addinfo"),
  path('user/updateinfo/', views.user_updateinfo, name="user_updateinfo"),
  path('user/vendorrequest/', views.vendor_request, name="vendor_request"),
  path("user/vendorprofile/", views.vendor_profile, name="vendor_profile"),
  path("user/activatesubscription/", views.activate_subscription, name="activate_subscription"),
  path("user/subscriptionhistory/", views.subscription_history, name="subscription_history"),

]

