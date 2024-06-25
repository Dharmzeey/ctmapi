import re
from rest_framework import serializers
from user.models import User, UserInfo, State, Location, Institution, Vendor, SubscriptionHistory
from store.models import Store, Product, ProductImage, Cart, Sales
from .models import Category, SubCategory

# USER, STORE 

class StateSerializer(serializers.ModelSerializer):
  class Meta:
    model = State
    fields = "__all__"

    
class LocationSerializer(serializers.ModelSerializer):
  class Meta:
    model = Location
    fields = "__all__"

    
class InstitutionSerializer(serializers.ModelSerializer):
  class Meta:
    model = Institution
    fields = ["id", "name", "state", "location"]
    depth = 1


class VendorSerializer(serializers.ModelSerializer):
  class Meta:
    model = Vendor
    fields = "__all__"
  def to_representation(self, instance):
    representation = super().to_representation(instance)
    representation['seller'] = instance.seller.username
    return representation
    

    
# store and product related
class CategorySerializer(serializers.ModelSerializer):
  class Meta:
    model = Category
    fields = "__all__"
    
class SubCategorySerializer(serializers.ModelSerializer):
  class Meta:
    model = SubCategory
    fields = "__all__"

class StoreSerializer(serializers.ModelSerializer):
  class Meta:
    model = Store
    fields = "__all__"
    read_only_field = ["owner"]
  
  def to_representation(self, instance):
    representation = super().to_representation(instance)
    representation['owner'] = instance.owner.seller.username
    representation['store_state'] = instance.store_state.name
    representation['store_location'] = instance.store_location.name
    representation['store_institution'] = instance.store_institution.name
    return representation
    
    
class ProductImageSerializer(serializers.ModelSerializer):
  class Meta:
    model = ProductImage
    fields = "__all__"
  
  def to_representation(self, instance):
    representation = super().to_representation(instance)
    representation['product'] = instance.product.title
    return representation
    
    
class ProductSerializer(serializers.ModelSerializer) :
  product_images = ProductImageSerializer(many=True, read_only = True, source='product_image')
  uploaded_images = serializers.ListField(
    child = serializers.ImageField(max_length = 1000000, allow_empty_file = False, use_url = False),
    write_only = True
    )
  
  class Meta:
    model = Product
    fields = ["id", "uuid", "vendor", "store", "title", "description", "thumbnail", "price", "product_images", "uploaded_images"]
    read_only_field = ["uuid", "vendor", "store"]
    
  def to_representation(self, instance):
    representation = super().to_representation(instance)
    representation['vendor'] = instance.vendor.seller.username
    representation['store'] = instance.store.store_name
    return representation

  def create(self, validated_data):
    uploaded_data = validated_data.pop('uploaded_images')
    new_product = Product.objects.create(**validated_data)
    for uploaded_item in uploaded_data:
      ProductImage.objects.create(product = new_product, image = uploaded_item)
    return new_product
  
  def clear_existing_images(self, instance):
    for image in instance.product_image.all():
      image.delete()
  
  def update(self, instance, validated_data):
    uploaded_data = validated_data.pop('uploaded_images', None)
    if uploaded_data:
      self.clear_existing_images(instance) # This clears the existing images
      for uploaded_item in uploaded_data:
        ProductImage.objects.create(product = instance, image = uploaded_item)
    return super().update(instance, validated_data)
