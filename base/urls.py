from django.urls import path
from . import views

urlpatterns = [
  path('fetchlocation/', views.fetch_location, name="fetch_loaction"),
  
  
  # path('changeviewinginfo/', views.change_viweing_info, name="change_viweing_info"), #Async request
  # path('resetorgeneral/', views.reset_or_general, name="reset_or_general"), #Async request
  # path('onchangeload/', views.on_change_load, name="on_change_load"), #Async request
  path('homepage/', views.homepage, name="homepage"),
  # path('homepagesearch/', views.homepage_search, name="homepage_search"),
  # path('recentlyviewed/', views.recently_viewed, name="recently_viewed"),
  
  # path('makepurchase', views.make_purchase, name="make_purchase"),
]

