from django.contrib import admin
from .models import Product, Order, OrderItem
from django.contrib.auth.models import User

admin.site.register(Product)
admin.site.register(Order)
admin.site.register(OrderItem)

class OrderItemInline(admin.StackedInline):
    model = OrderItem
    extra = 0


class OrderAdmin(admin.ModelAdmin):
    model = Order
    readonly_fields = ['date_ordered', 'date_shipped']
    inlines = [OrderItemInline]


admin.site.unregister(Order)
admin.site.register(Order, OrderAdmin)