from rest_framework import status
from rest_framework.response import Response


from store.models import Store, Product
from user.models import State, UserInfo
from store.serializers import ProductSerializer
from user.serializers import StateSerializer

def set_viewing_location(request):
  try:
    if request.user.is_authenticated:
      request.user.user_info
  except UserInfo.DoesNotExist:
      return None
    # return redirect(reverse_lazy("profile_create"))
  
  if request.user.is_authenticated and (request.user.user_info.institution or request.user.user_info.location or request.user.user_info.state):
    viewing_institution = request.session.get("viewing_institution", None)
    viewing_location = request.session.get("viewing_location", None)
    viewing_state = request.session.get("viewing_state", None)
    # THE SESSION WILL GET ASSIGNED IF THEY DO NOT EXIST ELSE IT JUST PASS
    if request.user.user_info.institution:
      if not viewing_institution and not viewing_location and not viewing_state:
        request.session["viewing_institution"] = str(request.user.user_info.institution)
        request.session["viewing_location"] = str(request.user.user_info.location)
        request.session["viewing_state"] = str(request.user.user_info.state)
    elif request.user.user_info.location:
      if not viewing_location and not viewing_state:
        request.session["viewing_location"] =  str(request.user.user_info.location)
        request.session["viewing_state"] = str(request.user.user_info.state)
    elif request.user.user_info.state:
      if not viewing_state:
        request.session["viewing_state"] = str(request.user.user_info.state)
  return 1

def filter_store(request, model):
  # This call will set the vieweing details in the session especially for user who has their details filled
  set_viewing_location(request)
  viewing_institution = request.session.get("viewing_institution", None)
  viewing_location = request.session.get("viewing_location", None)
  viewing_state = request.session.get("viewing_state", None)
  
  if viewing_institution == "General" or viewing_location == "General" or viewing_state == "General":
    store = model.objects.all()
  elif viewing_institution:
    store = model.objects.filter(store_state__name=viewing_state, store_location__name=viewing_location, store_institution__name=viewing_institution)
  elif viewing_location:
    store = model.objects.filter(store_state__name=viewing_state, store_location__name=viewing_location)
  elif viewing_state:
    store = model.objects.filter(store_state__name=viewing_state)
  else:
    store = model.objects.all()
  return store


# Displays the products based on viewing details
def show_product_helper(request):
  stores = filter_store(request, Store)
  random_products = Product.objects.filter(vendor__active_subscription=True, store__in=stores).order_by("?")[:5]
  random = Product.objects.filter(id__in=random_products) # This line is to use the model ordering whieh is by (vendor subscription plan first and then -created at)
  random_product_serializer = ProductSerializer(instance=random, many=True, context={"request": request})
  
  recent_products = Product.objects.filter(vendor__active_subscription=True, store__in=stores).order_by("-created_at")[:5]
  recent = Product.objects.filter(id__in=recent_products) # This line is to use the model ordering whieh is by (vendor subscription plan first and then -created at)
  recent_product_serializer = ProductSerializer(instance=recent, many=True, context={"request": request})
  states = State.objects.all()
  state_serializer = StateSerializer(instance=states, many=True)
  data = {
    "random_products": random_product_serializer.data,
    "recent_products": recent_product_serializer.data,
    "states": state_serializer.data
  }
  return Response(data, status=status.HTTP_200_OK)
