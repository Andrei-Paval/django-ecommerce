from store.models import Product

class Cart():
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get('session_key')
        if 'session_key' not in request.session:
            cart = self.session['session_key'] = {}
        self.cart = cart

    def __len__(self):
        return len(self.cart)
    
    def add(self, product, quantity):
        product_id = str(product.id)
        product_qty = str(quantity)
        if product_id in self.cart:
            pass
        else:
            self.cart[product_id] = int(product_qty)
        self.session.modified = True

    def update(self, product, quantity):
        product_id = str(product)
        product_qty = int(quantity)
        self.cart[product_id] = product_qty
        self.session.modified = True
        return self.cart

    def delete(self, product):
        product_id = str(product)
        if product_id in self.cart:
            del self.cart[product_id]
        self.session.modified = True

    def get_products(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        return products

    def get_quantities(self):
        return self.cart

    def get_total(self):
        product_ids = [key for key in self.cart.keys()]
        products = Product.objects.filter(id__in=product_ids)
        for id in product_ids:
            if not products.filter(id=id).exists():
                del self.cart[id]
                self.session.modified = True
        
        total = 0
        for key, value in self.cart.items():
            total += products.get(id=key).price * value
        return total