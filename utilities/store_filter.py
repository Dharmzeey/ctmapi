from store.models import Store

# this function returns stores based on the location parameters passed which can then be further used my the caller
def filter_store(request):
  state = request.data.get("st", None)
  location = request.data.get("lo", None)
  institution = request.data.get("in", None)
  if state and location and institution:
    stores = Store.objects.filter(owner__active_subscription=True, store_state=state, store_location=location, store_institution=institution)
  elif state and location:
    stores = Store.objects.filter(owner__active_subscription=True, store_state=state, store_location=location)
  elif state:
    stores = Store.objects.filter(owner__active_subscription=True, store_state=state)
  elif location:
    stores = Store.objects.filter(owner__active_subscription=True, store_location=location)
  elif institution:
    stores = Store.objects.filter(owner__active_subscription=True, store_institution=institution)
  else:
    stores = Store.objects.filter(owner__active_subscription=True)
  return stores
