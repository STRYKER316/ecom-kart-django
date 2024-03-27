from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from cart.models import CartItem
from cart.views import _get_cart_id
from category.models import Category

from .models import Product

# Create your views here.
def store(request, category_slug=None):
    category = None
    products = None
    products_count = None

    if category_slug != None:
        category = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(category=category, is_available=True)
        products_count = products.count()
    else:
        products = Product.objects.all().filter(is_available=True)
        products_count = products.count()

    context = {
        'products': products,
        'products_count': products_count,
    }

    return render(request, 'store/store.html', context)


def product_detail(request, category_slug, product_slug):
    single_product = None
    in_cart = False
    try:
        single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
        in_cart = CartItem.objects.filter(cart__cart_id=_get_cart_id(request), product=single_product).exists()
    except Exception as e:
        raise e

    context = {
        'single_product': single_product,
        'in_cart': in_cart,
    }

    return render(request, 'store/product_detail.html', context)
