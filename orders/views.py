import datetime
import json
import razorpay

from django.shortcuts import render, redirect

from .models import Order, Payment
from cart.models import CartItem
from .forms import OrderForm
from ecom_kart.settings import RZP_KEY_ID, RZP_KEY_SECRET


# Razorpay payment gateway
razorpay_client = razorpay.Client(auth=(RZP_KEY_ID, RZP_KEY_SECRET))


def payments(request):
    body = json.loads(request.body)
    order = Order.objects.get(user=request.user, is_ordered=False, order_number=body.get('order_number'))

    # store transaction details as a Payment object
    payment = Payment(
        user = request.user,
        payment_id = body.get('transaction_id'),
        payment_method = body.get('payment_method'),
        payment_amount = order.order_total,
        payment_status = body.get('payment_status')
    )
    payment.save()

    # update corresponding order
    order.payment = payment
    order.is_ordered = True
    order.save()

    return render(request, 'orders/payments.html')


def place_order(request, total=0, quantity=0):
    current_user = request.user

    # if cart item count = 0, then redirect to store
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('store')

    grand_total = 0
    tax = 0
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    tax = (2 * total) / 100
    grand_total = total + tax

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # store all the billing info
            order_data = Order()
            order_data.user = current_user
            order_data.first_name = form.cleaned_data['first_name']
            order_data.last_name = form.cleaned_data['last_name']
            order_data.phone = form.cleaned_data['phone']
            order_data.email = form.cleaned_data['email']
            order_data.address_line_1 = form.cleaned_data['address_line_1']
            order_data.address_line_2 = form.cleaned_data['address_line_2']
            order_data.country = form.cleaned_data['country']
            order_data.state = form.cleaned_data['state']
            order_data.city = form.cleaned_data['city']
            order_data.order_note = form.cleaned_data['order_note']
            order_data.order_total = grand_total
            order_data.tax = tax
            order_data.ip = request.META.get('REMOTE_ADDR')
            order_data.save()

            # generate order number
            year = int(datetime.date.today().strftime('%Y'))
            month = int(datetime.date.today().strftime('%m'))
            date = int(datetime.date.today().strftime('%d'))
            d = datetime.date(year, month, date)
            current_date = d.strftime('%Y%m%d')
            order_number = current_date + str(order_data.id)
            order_data.order_number = order_number
            order_data.save()

            # Razorpay Payment Data
            DATA = {
                "amount": float(order_data.order_total) * 100,
                "currency": "INR",
                "receipt": "receipt #" + order_number,
                "notes": {
                    "key1": "value3",
                    "key2": "value2"
                }
            }
            razorpay_order = razorpay_client.order.create(data=DATA)
            rzp_order_id = razorpay_order['id']

            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
            context = {
                'order': order,
                'cart_items': cart_items,
                'total': total,
                'tax': tax,
                'grand_total': grand_total,
                'rzp_order_id': rzp_order_id,
                'RZP_KEY_ID': RZP_KEY_ID,
                'rzp_amount': float(order_data.order_total) * 100,
            }

            return render(request, 'orders/payments.html', context)

        return redirect('checkout')
