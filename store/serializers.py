from rest_framework import serializers
from rest_framework.exceptions import NotFound
from store.models import Store, Product, ProductImage
from .models import Category, SubCategory


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
    
  # def to_representation(self, instance):
  #   representation = super().to_representation(instance)
  #   representation['product'] = instance.product.title
  #   return representation
    

class ProductSerializer(serializers.ModelSerializer) :
  product_images = ProductImageSerializer(many=True, read_only=True, source='product_image')
  uploaded_images = serializers.ListField(
    child = serializers.ImageField(max_length = 1000000, allow_empty_file = False, use_url = False),
    write_only = True
    )
  image_ids_changed = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)
  image_ids_deleted = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)
  new_images_added = serializers.ListField(
    child =  serializers.ImageField(max_length = 1000000, allow_empty_file = False, use_url = False), write_only=True, required=False
  )
  
  class Meta:
    model = Product
    fields = ["id", "uuid", "vendor", "store", "category", "subcategory", "title", "description", "thumbnail", "price", "active" ,"product_images", "uploaded_images", "image_ids_changed", "new_images_added", "image_ids_deleted"]
    read_only_field = ["uuid", "vendor", "store"]
    
  def to_representation(self, instance):
    representation = super().to_representation(instance)
    representation['vendor'] = instance.vendor.seller.username
    representation['store'] = instance.store.store_name
    if instance.category:
      representation['category'] = instance.category.name
    if instance.subcategory:
      representation['subcategory'] = instance.subcategory.name
    return representation

  def create(self, validated_data):
    uploaded_images = validated_data.pop('uploaded_images')
    new_product = Product.objects.create(**validated_data)
    for uploaded_image in uploaded_images:
      ProductImage.objects.create(product=new_product, image=uploaded_image)
    return new_product
  
  def update(self, instance, validated_data):    
    new_images_added = validated_data.pop('new_images_added', None) # incase if the user adds another image when they want to edit product
    uploaded_images = validated_data.pop('uploaded_images', None) # place holder for when image(s) is/are to be edited    
    image_ids_changed = validated_data.pop('image_ids_changed', None) # from the above line, the ids of the image being replaced is sent as a list (array) {must tally with above}
    image_ids_deleted = validated_data.pop('image_ids_deleted', None) #incase if user wants to delete images while editing the product, sent as a list (array)
        
    if image_ids_changed:
      index = 0
      for uploaded_image in uploaded_images:
        try:
          fetched_image = ProductImage.objects.get(id=image_ids_changed[index], product__uuid=instance.uuid)
          fetched_image.image = uploaded_image
          fetched_image.save()
        except:
          raise NotFound("Image not found for edit")
        index += 1
    if new_images_added:
      for new_image in new_images_added:
        ProductImage.objects.create(product=instance, image=new_image)
    if image_ids_deleted:
      for image_id in image_ids_deleted:
        try:
          fetched_image = ProductImage.objects.get(id=image_id, product__uuid=instance.uuid)
          fetched_image.delete()
          fetched_image.save()
        except:
          raise NotFound("Image not found for delete")
    return super().update(instance, validated_data)


class ProductDetailsSerializer(serializers.ModelSerializer):
  product_images = ProductImageSerializer(many=True, read_only=True, source='product_image')
  
  class Meta:
    model = Product
    fields = ["id", "uuid", "vendor", "store", "category", "subcategory", "title", "description", "thumbnail", "price", "active", "product_images"]
    read_only_field = ["uuid", "vendor", "store"]
    
  def to_representation(self, instance):
    representation = super().to_representation(instance)
    representation['vendor'] = instance.vendor.seller.username
    representation['store'] = instance.store.store_name
    if instance.category:
      representation['category'] = instance.category.name
    if instance.subcategory:
      representation['subcategory'] = instance.subcategory.name

    # this below controls if product_images should be shown or not (images will only show on product details)
    show_images = self.context.get('show_images', None)
    if show_images is not None:
      representation.pop('product_images')
    
    # this below controls the rendering of images number based on the store owner plan
    max_images = self.context.get('max_images', None)
    if max_images is not None and len(representation['product_images']) > max_images:
      representation['product_images'] = representation.get('product_images')[:max_images]
    return representation
