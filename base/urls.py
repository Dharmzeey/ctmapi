from django.urls import path
from . import views

urlpatterns = [
  path('fetch-states/', views.fetch_states, name="fetch_states"),
  path('fetch-locations/', views.fetch_locations, name="fetch_locations"),
  path('fetch-institutions/', views.fetch_institutions, name="fetch_institutions"),
  
  path('recently-viewed/', views.recently_viewed, name="recently_viewed"),
  
  path('homepage/', views.homepage, name="homepage"),
  # path('makepurchase', views.make_purchase, name="make_purchase"),
]

