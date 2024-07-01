from django.db.models import Q
from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from utilities.store_filter import filter_store
from store.models import Product
from user.models import State, Location, Institution
from store.serializers import ProductSerializer
from . import serializers as customAPISerializers


"""
THE HOMEPAGE API VIEWS COMMENCES HERE
"""

class FetchStatesView(APIView):
  def get(self, request):
    states = State.objects.all()
    state_serializer = customAPISerializers.StateSerializer(instance=states, many=True)    
    data = {
      "states": state_serializer.data,  
    }
    return Response(data, status=status.HTTP_200_OK)
fetch_states = FetchStatesView.as_view()

class FetchLocationsView(APIView):
  def get(self, request):
    state = request.data.get("state")
    locations = Location.objects.filter(state=state)   
    location_serializer = customAPISerializers.LocationSerializer(instance=locations, many=True)    
    data = {      
      "locations": location_serializer.data,
    }
    return Response(data, status=status.HTTP_200_OK)
fetch_locations = FetchLocationsView.as_view()


class FetchInstitutionsView(APIView):
  def get(self, request):
    location = request.data.get("location")
    institutions = Institution.objects.filter(location=location)
    institution_serializer = customAPISerializers.InstitutionSerializer(instance=institutions, many=True)
    data = {
      "institutions": institution_serializer.data,
    }
    return Response(data, status=status.HTTP_200_OK)
fetch_institutions = FetchInstitutionsView.as_view()

class HomePageView(APIView):
  def get(self, request):
    stores = filter_store(request)
    product = Product.objects.filter(store__in=stores)
    product_serializer = ProductSerializer(instance=product, many=True)
    if len(product_serializer.data) < 1:
      return Response({"message": "No product found"}, status=status.HTTP_200_OK)
    data = {
      "products": product_serializer.data
    }
    return Response(data, status=status.HTTP_200_OK)
homepage = HomePageView.as_view()


class RecentlyViewedView(generics.ListAPIView):
  model = Product
  serializer_class = ProductSerializer
  
  def get_queryset(self):
    # TAKES IN THE UUID OF THE RECENTLY VIEWED PRODUCTS AS A LIST, WHICH IS SENT FROM THE FRONTEND
    recent = self.request.data["recently_viewed"]
    if recent:
      stores = filter_store(self.request)
      qs = Product.objects.filter(uuid__in=recent, store__in=stores)
      return qs
    return Product.objects.none()  
recently_viewed = RecentlyViewedView.as_view()
