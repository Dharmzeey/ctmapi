import uuid
from django.core.validators import RegexValidator
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import datetime, timedelta

class State(models.Model):
  name = models.CharField(max_length=20)  
  def __str__(self):
    return self.name
  
  class Meta:
    ordering = ["name"]
  
class Location(models.Model):
  name = models.CharField(max_length=50)
  state = models.ForeignKey(State, on_delete=models.SET_NULL, related_name="location_state", null=True)
  def __str__(self):
    return self.name

class Institution(models.Model):
  name = models.CharField(max_length=100)  
  state = models.ForeignKey(State, on_delete=models.SET_NULL, related_name="institution_state", null=True)
  location = models.ForeignKey(Location, on_delete=models.SET_NULL, related_name="institution_location", null=True)
  def __str__(self):
    return self.name


class User(AbstractUser):
  username = models.CharField(max_length=50, unique=True)
  password = models.CharField(max_length=128)
  email = models.EmailField(unique=True)
  email_verified = models.BooleanField(default=False)
  phone_no_verified = models.BooleanField(default=False)
  created = models.DateTimeField(auto_now_add=True)
  updated = models.DateTimeField(auto_now=True)


def now_plus_10():
  """
  Function that returns current datetime + 10 minutes.
  """
  return datetime.now() + timedelta(minutes=10)

class EmailVerification(models.Model):
  user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="user_email_verification")
  email = models.EmailField()
  email_verification_pin = models.CharField(max_length=6, blank=True, null=True)
  expiry = models.DateTimeField(default=now_plus_10)
  

class PhoneVerification(models.Model):
  user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="user_verify_phone")
  phone = models.CharField(max_length=11, validators=[RegexValidator(r'^0\d{10}$', 'Mobile number should be 11 digits starting with 0.')])
  phone_verification_pin = models.CharField(max_length=6, blank=True, null=True)
  expiry = models.DateTimeField(default=now_plus_10)


class ForgotPassword(models.Model):
  user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="user_forgot_password")
  email = models.EmailField()
  reset_password_pin = models.CharField(max_length=6, blank=True, null=True)
  expiry = models.DateTimeField(default=now_plus_10)
  

class UserInfo(models.Model):
  user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="user_info")
  first_name = models.CharField(max_length=150, null=False)
  last_name = models.CharField(max_length=150, null=False)
  email = models.EmailField(unique=True)
  state = models.ForeignKey(State, on_delete=models.SET_NULL, related_name="user_state", null=True)
  location = models.ForeignKey(Location, on_delete=models.SET_NULL, related_name="user_location", null=True)
  institution = models.ForeignKey(Institution, on_delete=models.SET_NULL, related_name="user_institution", null=True, blank=True)
  address = models.CharField(max_length=255)
  tel = models.CharField(max_length=11, validators=[RegexValidator(r'^0\d{10}$', 'Mobile number should be 11 digits starting with 0.')])
  is_vendor = models.BooleanField(default=False)

  def __str__(self):
    return self.user.username
  

class Vendor(models.Model):
  PACKAGES =(
    (2000, "SPOTLIGHT"),
    (3000, "HIGHLIGHT"),
    (6000, "FEATURED"),
  )

  seller = models.OneToOneField(User, on_delete=models.CASCADE, related_name="selling_vendor", null=True)
  active_subscription = models.BooleanField(default=False)
  subscription_plan = models.IntegerField(choices=PACKAGES)
  subscription_duration = models.IntegerField()
  subscription_expire = models.DateTimeField()
  max_products = models.IntegerField()
  max_images = models.IntegerField()
  allow_video = models.BooleanField(default=False)
  
  DEFAULTS = {
    2000: {"max_products": 5, "max_images": 3, "allow_video": False},
    3000: {"max_products": 7, "max_images": 8, "allow_video": False},
    6000: {"max_products": 50, "max_images": 15, "allow_video": True},
  }
  
  def _deactivate_excess_products(self):
    max_product = self.max_products
    all_product = self.product_vendor.all()
    if all_product.count() > max_product:
      excess_product = all_product[max_product:] # this will filter out the remaining products that exceeds the maximum product, (especially when a user downgrades their plan)
      for product in excess_product:
        product.active = False
        product.save()

  def _activate_other_products(self):
    max_product = self.max_products
    active_products_count = self.product_vendor.all().filter(active=True).count()
    inactive_products = self.product_vendor.all().filter(active=False)
    # this "if" will first know the already active products (then take the count), then will take the inactive products and then activate the remaining products while considering the max_product
    if (inactive_products) and active_products_count < max_product:
      for product in inactive_products[ : max_product - active_products_count ]:
        product.active = True
        product.save()
  def save(self, *args, **kwargs):
    if self.subscription_plan in self.DEFAULTS:
      defaults = self.DEFAULTS[self.subscription_plan]
      self.max_products = defaults['max_products']
      self.max_images = defaults['max_images']
      self.allow_video = defaults['allow_video']
    if self.product_vendor.all().filter(active=True).count() < self.max_products:
      self._activate_other_products()
    else:
      self._deactivate_excess_products()
    super().save(*args, **kwargs)
  
  # THIS PROPERTY CHECKS IF THE SUBSCRIPTION EXPIRY IS BEHIND, IF YES, IT WILL DEACTIVATE THE SUBSCRIPTION
  @property
  def is_subscription_active(self):
    if self.subscription_expire and self.subscription_expire > timezone.now():
      return True
    else:
      self.active_subscription = False
      self.save()
      return False
  
  def __str__(self):
    return f"{self.seller}"


class SubscriptionHistory(models.Model):
  uuid = models.UUIDField(default=uuid.uuid4, editable=False)
  PACKAGES =(
    (2000, "SPOTLIGHT"),
    (3000, "HIGHLIGHT"),
    (6000, "FEATURED"),
  )
  vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, related_name="vendor_subscription", null=True)
  amount_paid = models.DecimalField(max_digits=8, decimal_places=2)
  subscription_plan = models.IntegerField(choices=PACKAGES)
  duration = models.IntegerField()
  expire_on = models.DateTimeField()
  sub_date = models.DateTimeField(auto_now_add=True)
  
  class Meta:
    verbose_name_plural = "Subscription History"
    ordering = ["-sub_date"]
  def __str__(self):
    return f'{self.vendor} - {self.sub_date}'
