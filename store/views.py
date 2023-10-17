from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView


from .models import Product, Store
from user.models import Vendor, State, Location, Institution
from utilities.store import load_stores_helper
from utilities2.error_handler import render_errors
from utilities2.token_handler import get_validate_send_token
from utilities2.product_handler import filter_store

from . import serializers as customAPISerializers


class ListStore(generics.ListAPIView):
  serializer_class = customAPISerializers.StoreSerializer
  queryset = Store.objects.filter().order_by("?")
  def list(self, request, *args, **kwargs):
    store_list = super().list(request, *args, **kwargs)
    states = State.objects.all()
    state_serializer = customAPISerializers.StateSerializer(instance=states, many=True)
    data = {"stores": store_list.data, "states": state_serializer.data}
    return Response(data)
list_stores = ListStore.as_view()

# when in the store page and the state is clicked, it loads the location associated with the state and also when the location is clicked, it loads the institution associated with such location
class FilterStorePlace(APIView):
  def get(self, request):
    state = request.data.get('state', None)
    location = request.data.get('location', None)
    if state:
      locations = Location.objects.filter(state__id=state).order_by("name")
      serializer = customAPISerializers.LocationSerializer(instance=locations, many=True)
      return Response({"locations": serializer.data}, status=status.HTTP_200_OK)

    if location:
      institutions = Institution.objects.filter(location__id=location).order_by("name")
      serializer = customAPISerializers.InstitutionSerializer(instance=institutions, many=True)
      return Response({"institutions": serializer.data}, status=status.HTTP_200_OK)
    return Response({"error": "An error occured"}, status=status.HTTP_404_NOT_FOUND)
filter_store_place = FilterStorePlace.as_view()


# This is an async view that will take id of state, location or institution and then returns the store
class LoadFilteredStores(APIView):
  def get(self, request):
    state_id = request.data.get("state", None)
    location_id = request.data.get("location", None)
    institution_id = request.data.get("institution", None)
    context = load_stores_helper(state_id, location_id, institution_id)
    stores = customAPISerializers.StoreSerializer(instance=context["stores"], many=True, context={"request": request})
    place = context["place"]
    data = {"stores": stores.data, "place": place.name}
    return Response(data, status=status.HTTP_200_OK)
load_filtered_stores = LoadFilteredStores.as_view()  


class SearchStore(generics.ListAPIView):
  serializer_class = customAPISerializers.StoreSerializer
  def get_queryset(self):
    q = self.request.data["q"]
    if q:
      return Store.objects.filter(
      Q(store_name__icontains=q),
      owner__active_subscription=True, 
      )
    return super().get_queryset()
search_store = SearchStore.as_view()


class CreateStore(APIView):
  permission_class = [IsAuthenticated]
  parser_classes = [FormParser, MultiPartParser]
  serializer_class = customAPISerializers.StoreSerializer
  def get(self, request):
    institution = Institution.objects.all()
    serializer = customAPISerializers.InstitutionSerializer(instance=institution, many=True)
    return Response({"data": serializer.data}, status=status.HTTP_200_OK)
  
  def post(self, request):
    try:
      Vendor.objects.get(seller=request.user)
    except Vendor.DoesNotExist:
      return Response({"message": "You are not a vendor"}, status=status.HTTP_403_FORBIDDEN)
    try:
      Store.objects.get(owner=request.user.selling_vendor)
      data = {"message": "Store for this user exitst already"}
      return Response(data, status=status.HTTP_409_CONFLICT)
    except Store.DoesNotExist:
      serializer = self.serializer_class(data=request.data, context={'request': request})
      if serializer.is_valid():
        vendor = request.user.selling_vendor
        serializer.save(owner=vendor)
        data = {"data": serializer.data, "message": "Store Information Created", "token": get_validate_send_token(request)}
        return Response(data, status=status.HTTP_201_CREATED)
      return Response({"message": str(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)
create_store = CreateStore.as_view()


class EditStore(APIView):
  permission_classes = [IsAuthenticated]
  serializer_class = customAPISerializers.StoreSerializer
  def patch(self, request):
    store = get_object_or_404(Store, owner=self.request.user.selling_vendor.id)
    if store.owner.active_subscription == False:
      return Response({"message": "Store not active"}, status=status.HTTP_404_NOT_FOUND)
    serializer = self.serializer_class(instance=store, data=request.data, partial=True, context={'request': request})
    if serializer.is_valid():
      serializer.save()
      data = {"message": "Store profile updated successfully", "data": serializer.data}
      return Response(data, status=status.HTTP_200_OK)
    data = {"message": render_errors(serializer.errors)}
    return Response(data, status=status.HTTP_400_BAD_REQUEST)
edit_store = EditStore.as_view()


class StoreDetails(APIView):
  permission_classes = [IsAuthenticatedOrReadOnly]
  def get(self, request):
    store_name = request.data["store_name"]
    try:
      store = Store.objects.get(store_name__iexact=store_name)
    except Store.DoesNotExist:
      return Response({"message": "No store found"}, status=status.HTTP_404_NOT_FOUND)
    if store.owner.active_subscription == False:
      return Response({"message": "Store not active"}, status=status.HTTP_403_FORBIDDEN)
    products = Product.objects.filter(store=store.id)
    store_serializer = customAPISerializers.StoreSerializer(instance=store, context={'request': request})
    product_serializer = customAPISerializers.ProductSerializer(instance=products, many=True, context={'request': request})
    if request.user.is_authenticated and request.user.user_info.is_vendor and (store.owner.seller == request.user):
      owner = Store.objects.get(owner__seller=request.user.id, store_name__iexact=store_name)
      data = {
        "owner": True,
        "store": store_serializer.data,
        "products": product_serializer.data,
      }
    else:
      data = {  
        "store": store_serializer.data,
        "products": product_serializer.data,
      }  
    return Response(data, status=status.HTTP_200_OK)
detail_store = StoreDetails.as_view()


"""
product api view commences here
"""

class SearchProduct(generics.ListAPIView):
  serializer_class = customAPISerializers.ProductSerializer
  def get_queryset(self):
    stores = filter_store(self.request, Store)
    q = self.request.data["q"]
    if q:
      return Product.objects.filter(
        Q(title__icontains=q)|
        Q(description__icontains=q),
        vendor__active_subscription=True,
        store__in=stores
      )
    return super().get_queryset()
  def list(self, request, *args, **kwargs):
    list_response = super().list(request, *args, **kwargs)
    if len(list_response.data) < 1:
      return Response({"message": "No product found"}, status=status.HTTP_204_NO_CONTENT)
    return list_response
search_product = SearchProduct.as_view()


class AddProduct(generics.CreateAPIView):
  permission_classes = [IsAuthenticated]
  parser_classes = (MultiPartParser,)  
  serializer_class = customAPISerializers.ProductSerializer
  
  def create(self, request, *args, **kwargs):
    vendor = self.request.user.selling_vendor
    if vendor.active_subscription == False:
      return Response({"message": "Your store is not active"}, status=status.HTTP_403_FORBIDDEN)
    images = request.FILES.getlist('uploaded_images')
    max_image = int(request.user.selling_vendor.subscription_plan) // 1000
    if len(images) >max_image:
      return Response({"message": f"maximum of {max_image} images allowed"}, status=status.HTTP_400_BAD_REQUEST)
    serializer = self.get_serializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    self.perform_create(serializer)
    headers = self.get_success_headers(serializer.data)
    data = {"message": "Product added successfully", "data": serializer.data, "token": get_validate_send_token(request)}
    return Response(data, status=status.HTTP_201_CREATED, headers=headers)
  
  def perform_create(self, serializer):
    vendor = self.request.user.selling_vendor
    store = vendor.store_owner
    serializer.save(vendor=vendor, store=store)
add_product = AddProduct.as_view()


class ProductDetails(generics.RetrieveAPIView):
  serializer_class = customAPISerializers.ProductSerializer
  def get_object(self):
    store = get_object_or_404(Store, store_name__iexact=self.request.data['store_name'])
    product = get_object_or_404(Product, uuid=self.request.data['product_uuid'], store=store)
    return product
  
  def retrieve(self, request, *args, **kwargs):
    store = get_object_or_404(Store, store_name__iexact=request.data['store_name'])  
    if store.owner.active_subscription == False:
      return Response({"message": "Store is not active"}, status=status.HTTP_403_FORBIDDEN)
    return super().retrieve(request, *args, **kwargs)
detail_product = ProductDetails.as_view()


class EditProduct(generics.UpdateAPIView):
  permission_classes = [IsAuthenticated]
  serializer_class = customAPISerializers.ProductSerializer
  parser_classes = (MultiPartParser,)
  
  def get_object(self):
    store = self.request.user.selling_vendor.store_owner
    product = get_object_or_404(Product, uuid=self.request.data['product_uuid'], store=store)
    return product
  
  def update(self, request, *args, **kwargs):
    if request.user.selling_vendor.active_subscription == False:
      return Response({"message": "Store is not active"}, status=status.HTTP_403_FORBIDDEN)
    update_response = super().update(request, *args, **kwargs)
    data = {"message": "Product updated", "data": update_response.data}
    return Response(data)
edit_product = EditProduct.as_view()


class DeleteProduct(generics.DestroyAPIView):
  serializer_class = customAPISerializers.ProductSerializer
  permission_classes = [IsAuthenticated]
  def get_object(self):
    store = self.request.user.selling_vendor.store_owner
    product = get_object_or_404(Product, uuid=self.request.data['product_uuid'], store=store)
    return product
  
  def destroy(self, request, *args, **kwargs):
    if request.user.selling_vendor.active_subscription == False:
      return Response({"message": "Store is not active"}, status=status.HTTP_403_FORBIDDEN)
    instance = self.get_object()
    self.perform_destroy(instance)
    return Response({"message": "Product deleted"}, status=status.HTTP_204_NO_CONTENT)
delete_product = DeleteProduct.as_view()
