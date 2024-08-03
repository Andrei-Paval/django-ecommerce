from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import pre_save
from django.dispatch import receiver
import datetime


class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(default=0, decimal_places=2, max_digits=10)
    description = models.CharField(max_length=500, default='', blank=True, null=True)
    image = models.ImageField(upload_to='uploads/product')

    def __str__(self):
        return self.name


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    full_name = models.CharField(max_length=250)
    email = models.EmailField(max_length=100)
    shipping_address = models.TextField(max_length=5000)
    date_ordered = models.DateTimeField(auto_now_add=True)
    shipped = models.BooleanField(default=False)
    date_shipped = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f'Order - {str(self.id)}'


@receiver(pre_save, sender=Order)
def set_shipped_date_on_update(sender, instance, **kwargs):
    if instance.pk:
        obj = sender._default_manager.get(pk=instance.pk)
        print(obj)
        print(instance)
        if instance.shipped and not obj.shipped:
            instance.date_shipped = datetime.datetime.now()
        elif not instance.shipped and obj.shipped:
            instance.date_shipped = None


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'Order Item - {str(self.id)}'
