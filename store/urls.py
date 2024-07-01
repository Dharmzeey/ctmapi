from django.urls import path
from . import views

urlpatterns = [
  path('', views.list_stores, name="list_stores"),
  path('search-stores/', views.search_store, name="search_stores"),
  path('create-store/', views.create_store, name="create_store"),
  path('detail-store/', views.detail_store, name="detail_store"),
  path('edit-store/', views.edit_store, name="edit_store"),
  path('delete-store/', views.delete_store, name="delete_store"),
  
  path('fetch-categories/', views.fetch_categories, name="fetch_categories"),
  path('fetch-sub-categories/', views.fetch_sub_categories, name="fetch_sub_categories"),
    
  path('search-product-category/', views.search_product_category, name="search_product_category"),
  path('search-product-sub-category/', views.search_product_sub_category, name="search_product_sub_category"),
  
  path('search-products/', views.search_product, name="search_product"),
  path('add-product/', views.add_product, name="add_product"),
  path('detail-product/', views.detail_product, name="detail_product"),
  path('edit-product/', views.edit_product, name="edit_product"),
  path('delete-product/', views.delete_product, name="delete_product"),
  
]

