from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.generics import DestroyAPIView
from rest_framework.views import APIView

from utilities.error_handler import render_errors
from utilities.store_filter import filter_store

from user.models import Vendor

from .models import Product, Store, Category, SubCategory

from . import serializers as customAPISerializers

# This list store is for when the store tab is clicked, it renders all the stores to the user where they can then click a particular on to view more details
class ListStoreView(generics.ListAPIView):
  serializer_class = customAPISerializers.StoreSerializer  
  def get_queryset(self):
    store_result = filter_store(self.request)
    queryset = store_result.order_by("?")
    return queryset    
  
  def list(self, request, *args, **kwargs):
    store_list = super().list(request, *args, **kwargs)
    data = {"stores": store_list.data}
    return Response(data,  status=status.HTTP_200_OK)
list_stores = ListStoreView.as_view()


class CreateStoreView(APIView):
  permission_class = [IsAuthenticated]
  parser_classes = [FormParser, MultiPartParser]
  serializer_class = customAPISerializers.StoreSerializer
    
  def post(self, request):
    try:
      Vendor.objects.get(seller=request.user)
    except Vendor.DoesNotExist:
      return Response({"error": "You are not a vendor"}, status=status.HTTP_403_FORBIDDEN)
    try:
      Store.objects.get(owner=request.user.selling_vendor)
      data = {"error": "Store profile for this user exitst already"}
      return Response(data, status=status.HTTP_409_CONFLICT)
    except Store.DoesNotExist:
      serializer = self.serializer_class(data=request.data, context={'request': request})
      if serializer.is_valid():
        vendor = request.user.selling_vendor
        serializer.save(owner=vendor)
        data = {"data": serializer.data, "message": "Store Information Created"}
        return Response(data, status=status.HTTP_201_CREATED)
      return Response({"errors": render_errors(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)
create_store = CreateStoreView.as_view()


class StoreDetailsView(APIView):
  permission_classes = [IsAuthenticatedOrReadOnly]
  def get(self, request):
    store_name = request.data["store_name"]
    try:
      store = Store.objects.get(store_name__iexact=store_name)
    except Store.DoesNotExist:
      return Response({"error": "No store found"}, status=status.HTTP_404_NOT_FOUND)
    if store.owner.active_subscription == False:
      return Response({"error": "Store not active"}, status=status.HTTP_403_FORBIDDEN)
    products = Product.objects.filter(store=store.id)
    store_serializer = customAPISerializers.StoreSerializer(instance=store, context={'request': request})
    product_serializer = customAPISerializers.ProductSerializer(instance=products, many=True, context={'request': request})
    if request.user.is_authenticated and request.user.user_info.is_vendor and (store.owner.seller == request.user):
      data = {
        "owner": True,
        "store": store_serializer.data,
        "products": product_serializer.data,
      }
    else:
      data = {
        "owner": False,
        "store": store_serializer.data,
        "products": product_serializer.data,
      }  
    return Response(data, status=status.HTTP_200_OK)
detail_store = StoreDetailsView.as_view()


class EditStoreView(APIView):
  permission_classes = [IsAuthenticated]
  serializer_class = customAPISerializers.StoreSerializer
  def patch(self, request):
    # store = get_object_or_404(Store, owner=self.request.user.selling_vendor.id)
    try:
      store = Store.objects.get(owner=self.request.user.selling_vendor)
    except Store.DoesNotExist:
      return Response({"message": "Store has not been created"}, status=status.HTTP_404_NOT_FOUND)
    if store.owner.active_subscription == False:
      return Response({"message": "Store not active"}, status=status.HTTP_404_NOT_FOUND)
    serializer = self.serializer_class(instance=store, data=request.data, partial=True, context={'request': request})
    if serializer.is_valid():
      serializer.save()
      data = {"message": "Store profile updated successfully", "data": serializer.data}
      return Response(data, status=status.HTTP_200_OK)
    data = {"errors": render_errors(serializer.errors)}
    return Response(data, status=status.HTTP_400_BAD_REQUEST)
edit_store = EditStoreView.as_view()


class DeleteStoreView(DestroyAPIView):
  serializer_class = customAPISerializers.StoreSerializer
  permission_classes = [IsAuthenticated]
  def get_object(self):
    try:
      store = Store.objects.get(owner=self.request.user.selling_vendor)
      return store
    except Store.DoesNotExist:
      raise NotFound("Store not found")
delete_store = DeleteStoreView.as_view()


class SearchStoreView(generics.ListAPIView):
  serializer_class = customAPISerializers.StoreSerializer
  def get_queryset(self):
    store_result = filter_store(self.request) # first check and returns the state in the person's location
    # then the search parameter is then run on the returned queryset
    q = self.request.data["q"]
    if q:
      return store_result.filter(
      Q(store_name__icontains=q))
    return super().get_queryset()
  
  def list(self, request, *args, **kwargs):
    store_list = super().list(request, *args, **kwargs)
    data = {"stores": store_list.data}
    return Response(data, status=status.HTTP_200_OK)
search_store = SearchStoreView.as_view()


"""
product api view commences here
"""

class FetchCategoryView(APIView):
  def get(self, request):
    categories = Category.objects.all()
    category_serializer = customAPISerializers.CategorySerializer(instance=categories, many=True, context={'request': request})
    data = {
      "categories": category_serializer.data,
    }
    return Response(data, status=status.HTTP_200_OK)
fetch_categories = FetchCategoryView.as_view()


class FetchSubCategoryView(APIView):
  def get(self, request):
    category = request.data.get("category")
    sub_categories = SubCategory.objects.filter(category=category)
    sub_categories_serializer = customAPISerializers.SubCategorySerializer(instance=sub_categories, many=True)
    data = {
      "subcategories": sub_categories_serializer.data
    }
    return Response(data, status=status.HTTP_200_OK)
fetch_sub_categories = FetchSubCategoryView.as_view()

"""
product api view commences here
"""

class SearchProductCategoryView(generics.ListAPIView):
  serializer_class = customAPISerializers.ProductSerializer
  def get_queryset(self):
    cat = self.request.data["cat"]
    if cat:
      stores = filter_store(self.request)
      return Product.objects.filter(
        category=cat,
        store__in=stores
      )
    return super().get_queryset()
  def list(self, request, *args, **kwargs):
    list_response = super().list(request, *args, **kwargs)
    if len(list_response.data) < 1:
      return Response({"error": "No product found"}, status=status.HTTP_404_NOT_FOUND)
    data = {"products": list_response.data}
    return Response(data, status=status.HTTP_200_OK) 
search_product_category = SearchProductCategoryView.as_view()

class SearchProductSubCategoryView(generics.ListAPIView):
  serializer_class = customAPISerializers.ProductSerializer
  def get_queryset(self):
    sub_cat = self.request.data["sub_cat"]
    if sub_cat:
      stores = filter_store(self.request)
      return Product.objects.filter(
        subcategory=sub_cat,
        store__in=stores
      )
    return super().get_queryset()
  def list(self, request, *args, **kwargs):
    list_response = super().list(request, *args, **kwargs)
    if len(list_response.data) < 1:
      return Response({"error": "No product found"}, status=status.HTTP_404_NOT_FOUND)
    data = {"products": list_response.data}
    return Response(data, status=status.HTTP_200_OK) 
search_product_sub_category = SearchProductSubCategoryView.as_view()


class SearchProductView(generics.ListAPIView):
  serializer_class = customAPISerializers.ProductSerializer
  def get_queryset(self):
    stores = filter_store(self.request)
    q = self.request.data["q"]
    if q:
      return Product.objects.filter(
        Q(title__icontains=q)|
        Q(description__icontains=q),
        store__in=stores
      )
    return super().get_queryset()
  def list(self, request, *args, **kwargs):
    list_response = super().list(request, *args, **kwargs)
    if len(list_response.data) < 1:
      return Response({"error": "No product found"}, status=status.HTTP_404_NOT_FOUND)
    data = {"products": list_response.data}
    return Response(data, status=status.HTTP_200_OK)
search_product = SearchProductView.as_view()


class AddProductView(generics.CreateAPIView):
  permission_classes = [IsAuthenticated]
  parser_classes = (MultiPartParser,)  
  serializer_class = customAPISerializers.ProductSerializer
  
  def create(self, request, *args, **kwargs):
    vendor = self.request.user.selling_vendor
    if vendor.active_subscription == False:
      return Response({"error": "Your store is not active"}, status=status.HTTP_403_FORBIDDEN)
    images = request.FILES.getlist('uploaded_images')
    max_image = int(request.user.selling_vendor.subscription_plan) // 1000
    if len(images) >max_image:
      return Response({"error": f"maximum of {max_image} images allowed"}, status=status.HTTP_400_BAD_REQUEST)
    serializer = self.get_serializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    self.perform_create(serializer) # defined below in this class
    headers = self.get_success_headers(serializer.data)
    data = {"message": "Product added successfully", "data": serializer.data}
    return Response(data, status=status.HTTP_201_CREATED, headers=headers)
  
  def perform_create(self, serializer):
    vendor = self.request.user.selling_vendor
    store = vendor.store_owner
    serializer.save(vendor=vendor, store=store)
add_product = AddProductView.as_view()


class ProductDetailsView(APIView):
  serializer_class = customAPISerializers.ProductSerializer
  def get(self, request):
    store = get_object_or_404(Store, store_name__iexact=request.data['store_name'])
    product = get_object_or_404(Product, uuid=request.data['product_uuid'], store=store)
    if store.owner.active_subscription == False:
      return Response({"error": "Store is not active"}, status=status.HTTP_403_FORBIDDEN)
    product_serializer = self.serializer_class(instance=product, context={'request': request})
    if request.user.is_authenticated and request.user.user_info.is_vendor and (store.owner.seller == request.user):
      data = {
        "owner": True,
        "data": product_serializer.data,
      }
    else:
      data = {
        "owner": False,
        "data": product_serializer.data,
      }  
    return Response(data, status=status.HTTP_200_OK)
detail_product = ProductDetailsView.as_view()


class EditProductView(generics.UpdateAPIView):
  permission_classes = [IsAuthenticated]
  serializer_class = customAPISerializers.ProductSerializer
  parser_classes = (MultiPartParser,)
  
  def get_object(self):
    store = self.request.user.selling_vendor.store_owner
    product = get_object_or_404(Product, uuid=self.request.data['product_uuid'], store=store)
    return product
  
  def update(self, request, *args, **kwargs):
    if request.user.selling_vendor.active_subscription == False:
      return Response({"error": "Store is not active"}, status=status.HTTP_403_FORBIDDEN)
    max_image = int(request.user.selling_vendor.subscription_plan) // 1000
    images = request.FILES.getlist('uploaded_images')
    added_images = request.FILES.getlist('new_images_added')   
    if len(images) > max_image or len(added_images) > max_image:
      return Response({"error": f"maximum of {max_image} images allowed"}, status=status.HTTP_400_BAD_REQUEST)
    db_images = self.get_object().product_image.all().count()
    incoming_new_images = len(added_images)
    total_images = db_images + incoming_new_images
    if added_images and (total_images > max_image):
      return Response({"error": f"maximum of {max_image} images exceeded"}, status=status.HTTP_400_BAD_REQUEST)
    update_response = super().update(request, *args, **kwargs)
    data = {"message": "Product updated", "data": update_response.data}
    return Response(data)
edit_product = EditProductView.as_view()


class DeleteProductView(generics.DestroyAPIView):
  serializer_class = customAPISerializers.ProductSerializer
  permission_classes = [IsAuthenticated]
  def get_object(self):
    store = self.request.user.selling_vendor.store_owner
    product = get_object_or_404(Product, uuid=self.request.data.get('product_uuid'), store=store)
    return product
  
  def destroy(self, request, *args, **kwargs):
    if request.user.selling_vendor.active_subscription == False:
      return Response({"error": "Store is not active"}, status=status.HTTP_403_FORBIDDEN)
    instance = self.get_object()
    self.perform_destroy(instance)
    return Response({"message": "Product deleted"}, status=status.HTTP_204_NO_CONTENT)
delete_product = DeleteProductView.as_view()



# # Make purchase
# class MakePurchaseView(APIView):
#   def post(self, request):
#     product_uuid = request.data["product_uuid"]
#     store_name = request.data["store_name"]
# make_purchase = MakePurchaseView.as_view()