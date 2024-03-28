from django.shortcuts import redirect, render
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required

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

            messages.success(reuqest, 'Registration Successful')

            return redirect('register')

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
            # messages.success(reuqest, 'You are now logged in')
            return redirect('home')
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
