from .views import _get_cart_id
from .models import Cart, CartItem


def counter(request):
    cart_count = 0

    if 'admin' in request.path:
        return {}

    try:
        cart = Cart.objects.filter(cart_id=_get_cart_id(request))
        cart_items = CartItem.objects.all().filter(cart=cart[:1])

        for item in cart_items:
            cart_count += item.quantity

    except cart.DoesnotExist:
        pass

    return dict(cart_count=cart_count)
