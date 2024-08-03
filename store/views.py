from django.shortcuts import render, redirect
from .models import Product, Order, OrderItem
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.db.models import F, Sum, ExpressionWrapper, DecimalField, Value
from django.db.models.functions import Coalesce
from django import forms
from .forms import SignUpForm, ShippingForm
from cart.cart import Cart
import datetime

def home(request):
    products = Product.objects.all()
    return render(request, 'home.html', {'products': products})

def about(request):
    return render(request, 'about.html', {})

def login_user(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, ("You have been logged in"))
            return redirect('home')
        else:
            messages.error(request, ("Login failed"))
            return redirect('login')
    else:
        return render(request, 'login.html', {})

def logout_user(request):
    logout(request)
    messages.success(request, ("You have been logged out"))
    return redirect('home')

def register_user(request):
    form = SignUpForm()
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']

            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, ("You have registered successfully"))
            return redirect('home')
        else:
            messages.error(request, ("Register failed"))
            return redirect('register')
    else:
        return render(request, 'register.html', {'form': form})

def product(request, pk):
    product = Product.objects.get(id=pk)
    return render(request, 'product.html', {'product': product})

def checkout(request):
    if not request.user.is_authenticated:
        messages.success(request, 'You have to be logged in to order')
        return redirect('login')
    
    cart = Cart(request)
    cart_products = cart.get_products
    quantities = cart.get_quantities
    cart_total = cart.get_total()
    shipping_form = ShippingForm(request.POST or None)
    return render(request, "checkout.html", {"cart_products": cart_products, "quantities": quantities, "cart_total": cart_total, "shipping_form": shipping_form})

def process_order(request):
    if request.POST:
        if not request.user.is_authenticated:
            messages.success(request, 'You have to be logged in to order')
            return redirect('login')
    
        cart = Cart(request)
        cart_products = cart.get_products
        quantities = cart.get_quantities
        cart_total = cart.get_total()

        user = None
        if request.user.is_authenticated:
            user = request.user

        shipping_address = f'Main: {request.POST['shipping_address1']}\n'
        shipping_address += f'Second: {request.POST['shipping_address2']}\n'
        shipping_address += f'Country: {request.POST['shipping_country']}\n'
        shipping_address += f'State: {request.POST['shipping_state']}\n'
        shipping_address += f'City: {request.POST['shipping_city']}\n'
        shipping_address += f'Zipcode: {request.POST['shipping_zipcode']}'
        
        new_order = Order(
            user=user,
            full_name=request.POST['shipping_full_name'],
            email=request.POST['shipping_email'],
            shipping_address=shipping_address,
        )
        new_order.save()

        for product in cart_products():
            product_id = product.id
            product_price = product.price
            product_quantity = quantities()[str(product_id)]
            new_item = OrderItem(
                user=user,
                order_id=new_order.pk,
                product_id=product_id,
                price=product_price,
                quantity=product_quantity
            )
            new_item.save()

        if "session_key" in request.session.keys():
            del request.session["session_key"]
            
        messages.success(request, 'Order Placed')
        
    return redirect('home')

def not_shipped_dash(request):
    if request.user.is_authenticated:
        if request.user.is_superuser and request.POST:
            id = request.POST['id']
            order = Order.objects.filter(id=id)
            order.update(shipped=True, date_shipped=datetime.datetime.now())
            messages.success(request, "Shipping Status Updated")
            return redirect('not_shipped_dash')

        if request.user.is_superuser:
            orders = Order.objects.filter(shipped=False).annotate(
                total_price=Coalesce(
                    Sum(F('orderitem__price') * F('orderitem__quantity')),
                    Value(0),
                    output_field=DecimalField()
                )
            )
            return render(request, 'not_shipped_dash.html', {'orders': orders})
        else:
            orders = Order.objects.filter(shipped=False, user_id = request.user.id).annotate(
                total_price=Coalesce(
                    Sum(F('orderitem__price') * F('orderitem__quantity')),
                    Value(0),
                    output_field=DecimalField()
                )
            )
            return render(request, 'not_shipped_dash.html', {'orders': orders})
        
    else:
        messages.success(request, 'Access Denied')
        return redirect('home')

def shipped_dash(request):
    if request.user.is_authenticated:
        if request.user.is_superuser and request.POST:
            id = request.POST['id']
            order = Order.objects.filter(id=id)
            order.update(shipped=False, date_shipped=None)
            messages.success(request, "Shipping Status Updated")
            return redirect('shipped_dash')

        if request.user.is_superuser:
            orders = Order.objects.filter(shipped=True).annotate(
                total_price=Coalesce(
                    Sum(F('orderitem__price') * F('orderitem__quantity')),
                    Value(0),
                    output_field=DecimalField()
                )
            )
            return render(request, 'shipped_dash.html', {'orders': orders})
        else:
            orders = Order.objects.filter(shipped=True, user_id = request.user.id).annotate(
                total_price=Coalesce(
                    Sum(F('orderitem__price') * F('orderitem__quantity')),
                    Value(0),
                    output_field=DecimalField()
                )
            )
            return render(request, 'shipped_dash.html', {'orders': orders})
    else:
        messages.success(request, 'Access Denied')
        return redirect('home')

def orders(request, pk):
    if request.user.is_authenticated:
        if request.POST and request.user.is_superuser:
            status = request.POST['shipping_status']
            if status == "true":
                order = Order.objects.filter(id=pk)
                order.update(shipped=True, date_shipped=datetime.datetime.now())
            else:
                order = Order.objects.filter(id=pk)
                order.update(shipped=False, date_shipped=None)
            messages.success(request, 'Shipping Status Updated')

        order = Order.objects.get(id=pk)
        items = OrderItem.objects.filter(order=pk)

        if not request.user.is_superuser and order.user.pk != request.user.pk:
            return redirect('home')

        return render(request, 'orders.html', {
            'order': order,
            'items': items,
        })
    else:
        messages.success(request, 'Access Denied')
        return redirect('home')
