from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.http import HttpResponse


import requests

from .models import Account, UserProfile
from cart.models import Cart, CartItem
from orders.models import Order, OrderProduct
from cart.views import _get_cart_id

from .forms import RegistrationForm, UserForm, UserProfileForm


# User Registration
def register(request):
    form = None

    if request.method == 'POST':
        form = RegistrationForm(request.POST)

        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split('@')[0]

            user = Account.objects.create_user(
                first_name=first_name,
                last_name=last_name,
                username=username,
                email=email,
                password=password
            )
            user.phone_number = phone_number
            user.save()

            # User Profile Craetion
            profile = UserProfile()
            profile.user_id = user.id
            profile.profile_picture = 'photos/profile_pictures/default.jpg'
            profile.save()

            # User Activation
            current_site = get_current_site(request)
            mail_subject = 'Please activate your account'
            message = render_to_string('accounts/account_verification_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user)
            })

            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

            return redirect('/accounts/login/?command=verification&email=+email')

    # GET Request
    else:
        form = RegistrationForm()

    context = {
        'form': form
    }

    return render(request, 'accounts/register.html', context)


# User Login
def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = auth.authenticate(email=email, password=password)

        if user:
            try:
                cart = Cart.objects.get(cart_id=_get_cart_id(request))
                is_cart_item_exists = CartItem.objects.filter(cart=cart).exists()

                if is_cart_item_exists:
                    cart_item = CartItem.objects.filter(cart=cart)
                    # Getting the product_variation by cart_id
                    product_variation = []
                    for item in cart_item:
                        variation = item.variations.all()
                        product_variation.append(list(variation))

                    # Get the cart items from the user to access the product variations
                    cart_item = CartItem.objects.filter(user=user)
                    exisiting_variations_list = []
                    id = []
                    for item in cart_item:
                        existing_variation = item.variations.all()
                        exisiting_variations_list.append(list(existing_variation))
                        id.append(item.id)

                    # Check if the product_variation is in the exisiting_variations_list
                    for product in product_variation:
                        if product in exisiting_variations_list:
                            index = exisiting_variations_list.index(product)
                            item_id = id[index]
                            item = CartItem.objects.get(id=item_id)
                            item.quantity += 1
                            item.user = user
                            item.save()
                        else:
                            cart_item = CartItem.objects.filter(cart=cart)
                            for item in cart_item:
                                item.user = user
                                item.save()
            except:
                pass

            auth.login(request, user)
            messages.success(request, 'You are now logged in')

            url = request.META.get('HTTP_REFERER')
            try:
                query = requests.utils.urlparse(url).query
                # next=/cart/checkout/
                params = dict(x.split('=') for x in query.split('&'))
                if 'next' in params:
                    nextPage = params['next']
                    return redirect(nextPage)
            except:
                return redirect('dashboard')
        else:
            messages.error(request, 'Invalid login credentials')
            return redirect('login')

    # GET Request
    return render(request, 'accounts/login.html')


# User Logout
@login_required(login_url='login')
def logout(request):
    auth.logout(request)
    messages.success(request, 'You are now logged out')
    return redirect('login')


# User Dashboard
@login_required(login_url='login')
def dashboard(request):
    orders = Order.objects.order_by('-created_at').filter(user_id=request.user.id, is_ordered=True)
    orders_count = orders.count()
    userprofile = UserProfile.objects.get(user_id=request.user.id)

    context = {
        'orders_count': orders_count,
        'userprofile': userprofile,
    }

    return render(request, 'accounts/dashboard.html', context)


# User Activation
def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)

    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user != None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Your account is now activated!')
        return redirect('login')

    messages.error(request, 'Invalid activation link')
    return redirect('register')


# Forgot Password
def forget_password(request):
    if request.method == 'POST':
        email = request.POST['email']

        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email__exact=email)

            # Password Reset
            current_site = get_current_site(request)
            mail_subject = 'Reset your password'
            message = render_to_string('accounts/reset_password_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user)
            })

            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

            messages.success(request, 'Password reset email has been sent to your email address')
            return redirect('login')

        else:
            messages.error(request, 'Account does not exist')
            return redirect('forget_password')

    return render(request, 'accounts/forget_password.html')


# Reset Password Validation
def reset_password_validate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)

    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user != None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.success(request, 'Please reset your password')
        return redirect('reset_password')
    else:
        messages.error(request, 'This link has been expired')
        return redirect('login')


# Reset Password
def reset_password(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            uid = request.session.get('uid')
            user = Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request, 'Password reset successful')
            return redirect('login')

        else:
            messages.error(request, 'Passwords do not match')
            return redirect('reset_password')

    # GET request
    return render(request, 'accounts/reset_password.html')


# My Orders
@login_required(login_url='login')
def my_orders(request):
    orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at')
    context = {
        'orders': orders
    }
    return render(request, 'accounts/my_orders.html', context)


# Edit Profile
@login_required(login_url='login')
def edit_profile(request):
    userprofile = get_object_or_404(UserProfile, user=request.user)

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=userprofile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated')
            return redirect('edit_profile')

    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=userprofile)

    context = {
        'user_form': user_form,
        'profile_form' : profile_form,
        'userprofile': userprofile,
    }

    return render(request, 'accounts/edit_profile.html', context)


# Change Password
@login_required(login_url='login')
def change_password(request):
    # POST request
    if request.method == 'POST':
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']

        user = Account.objects.get(email__exact=request.user.email)

        if new_password == confirm_password:
            success = user.check_password(current_password)

            if success:
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Password updated successfully')
                return redirect('change_password')

            else:
                messages.error(request, 'Please enter correct current password')
                return redirect('change_password')

        else:
            messages.error(request, 'Passwords do not match')
            return redirect('change_password')

    # GET request
    return render(request, 'accounts/change_password.html')


# Order Detail
@login_required(login_url='login')
def order_detail(request, order_id):
    order_detail = OrderProduct.objects.filter(order__order_number=order_id)
    order = Order.objects.get(order_number=order_id)

    sub_total = 0
    for item in order_detail:
        sub_total += item.product_price * item.quantity

    context = {
        'order_detail': order_detail,
        'order': order,
        'sub_total': sub_total,
    }
    return render(request, 'accounts/order_detail.html', context)
