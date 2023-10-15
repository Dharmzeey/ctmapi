from django.db.models import Q
from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

# from .views import filter_store
from store.models import Product, Store
from user.models import State, Location, Institution
from utilities2.product_handler import show_product_helper
from . import serializers as customAPISerializers

def return_viewing_info(request):
  get_viewing_info = {"viewing_state": request.session.get("viewing_state"), "viewing_location": request.session.get("viewing_location"), "viewing_institution": request.session.get("viewing_institution")}
  viewing_info_serializer = customAPISerializers.ViewingInfoSerializer(data=get_viewing_info)
  if viewing_info_serializer.is_valid():
    viewing_info = viewing_info_serializer.data
    return viewing_info


"""
THE HOMEPAGE API VIEWS COMMENCES HERE
"""
# This will accept the change and set the request.session
class ChangeViewingInfo(APIView):
  def get(self, request):
    state_id = request.query_params.get('state', None)
    location_id = request.query_params.get('location', None)
    institution_id = request.query_params.get('institution', None)
    if state_id:
      # SET THE SESSION OF STATE AND THE POPULATE THE FILTER FOR LOCATION MODEL
      state = State.objects.get(id=state_id)
      request.session["viewing_state"] = str(state)
      request.session.pop("viewing_location", None)
      request.session.pop("viewing_institution", None)      
      locations = Location.objects.filter(state__id=state_id).order_by("name")
      location_serializer = customAPISerializers.LocationSerializer(instance=locations, many=True)
      data = {"locations": location_serializer.data, "viewing_info": return_viewing_info(request)}
      return Response(data, status=status.HTTP_200_OK)
    elif location_id:
      location = Location.objects.get(id=location_id)
      request.session["viewing_location"] = str(location)
      request.session.pop("viewing_institution", None)      
      institutions = Institution.objects.filter(location__id=location_id).order_by("name")
      institution_serializer = customAPISerializers.LocationSerializer(instance=institutions, many=True)
      data = {"institutions": institution_serializer.data, "viewing_info": return_viewing_info(request)}
      return Response(data, status=status.HTTP_200_OK)
    elif institution_id:
      institution = Institution.objects.get(id=institution_id)
      request.session["viewing_institution"] = str(institution)
      return Response({"viewing_info": return_viewing_info(request)}, status=status.HTTP_200_OK)
    else:
      states = State.objects.all()
      state_serializer = customAPISerializers.StateSerializer(instance=states, many=True)
      data = {"states": state_serializer.data, "viewing_info": return_viewing_info(request)}
      return Response(data, status=status.HTTP_200_OK)
    # return Response({"message": "An error occured"}, status=status.HTTP_400_BAD_REQUEST)
change_viweing_info = ChangeViewingInfo.as_view()


class ResetOrGeneralViewingInfo(APIView):
  def get(self, request):
    reset = request.data.get("reset", None)
    general = request.data.get("general", None)
    
    if reset:
      request.session.pop("viewing_state", None)
      request.session.pop("viewing_location", None)
      request.session.pop("viewing_institution", None)
      
    elif general:
      request.session["viewing_institution"] = "General"
      request.session["viewing_location"] = "General"
      request.session["viewing_state"] = "General"
    else:
      return Response({"message": "An error occured"}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"message": "Success"}, status=status.HTTP_200_OK)
reset_or_general = ResetOrGeneralViewingInfo.as_view()


class LoadProductOnChangeViewingInfo(APIView):
  def get(self, request):
    response = show_product_helper(request).data
    response.pop('states') #I am removing states because load product does not need it
    return Response(response, status=status.HTTP_200_OK)
on_change_load = LoadProductOnChangeViewingInfo.as_view()


class HomePage(APIView):
  def get(self, request):
    return show_product_helper(request)
homepage = HomePage.as_view()


class HomePageSearch(generics.ListAPIView):
  serializer_class = customAPISerializers.ProductSerializer
  def get_queryset(self):
    stores = filter_store(self.request, Store)    
    q = self.request.GET.get("q", None)
    if q:
      return Product.objects.filter(
        Q(title__icontains=q)|
        Q(description__icontains=q),
        vendor__active_subscription=True,
        store__in=stores
      )
    return super().get_queryset()
homepage_search = HomePageSearch.as_view()

class RecentlyViewed(generics.ListAPIView):
  model = Product
  serializer_class = customAPISerializers.ProductSerializer
  
  def get_queryset(self):
    # TAKES IN THE UUID OF THE RECENTLY VIEWED PRODUCTS AS A LIST, WHICH IS SENT FROM THE FRONTEND
    recent = self.request.data["recently_viewed"]
    if recent:
      qs = Product.objects.filter(uuid__in=recent)
      return qs
    return Product.objects.none()  
recently_viewed = RecentlyViewed.as_view()


# Make purchase
class MakePurchase(APIView):
  def get(self, request):
    product_uuid = request.data["product_uuid"]
    store_name = request.data["store_name"]
make_purchase = MakePurchase.as_view()