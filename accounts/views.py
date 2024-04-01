from django.shortcuts import redirect, render
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.http import HttpResponse

from .models import Account

from .forms import RegistrationForm

# Create your views here.

def register(reuqest):
    form = None

    if reuqest.method == 'POST':
        form = RegistrationForm(reuqest.POST)

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

            # User Activation
            current_site = get_current_site(reuqest)
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

    return render(reuqest, 'accounts/register.html', context)


def login(reuqest):
    if reuqest.method == 'POST':
        email = reuqest.POST['email']
        password = reuqest.POST['password']

        user = auth.authenticate(email=email, password=password)

        if user:
            auth.login(reuqest, user)
            messages.success(reuqest, 'You are now logged in')
            return redirect('dashboard')
        else:
            messages.error(reuqest, 'Invalid login credentials')
            return redirect('login')

    # GET Request
    return render(reuqest, 'accounts/login.html')


@login_required(login_url='login')
def logout(reuqest):
    auth.logout(reuqest)
    messages.success(reuqest, 'You are now logged out')
    return redirect('login')


@login_required(login_url='login')
def dashboard(reuqest):
    return render(reuqest, 'accounts/dashboard.html')


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
