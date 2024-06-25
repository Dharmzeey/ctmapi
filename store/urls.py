from django.urls import path
from . import views

urlpatterns = [
    
  path('', views.list_stores, name="list_stores"),
  path('filterstoreplaces/', views.filter_store_place, name="filter_store_place"), #Async request
  path('loadfilteredstores/', views.load_filtered_stores, name="load_filtered_stores"), #Async request
  path('searchstores/', views.search_store, name="search_stores"),
  path('createstore/', views.create_store, name="create_store"),
  path('editstore/', views.edit_store, name="edit_store"),
  path('detailstore/', views.detail_store, name="detail_store"),
  
  path('loadcategories/', views.load_categories, name="load_categories"),
  # path('searchproducts/', views.search_product, name="search_product"),
  path('addproduct/', views.add_product, name="add_product"),
  path('detailproduct/', views.detail_product, name="detail_product"),
  path('editproduct/', views.edit_product, name="edit_product"),
  path('deleteproduct/', views.delete_product, name="delete_product"),
  
]

