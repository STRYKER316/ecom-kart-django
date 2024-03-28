from django.shortcuts import redirect, render

from .models import Account

from .forms import RegistrationForm

# Create your views here.

def register(reuqest):
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

    # GET Request
    else:
        form = RegistrationForm()

    context = {
        'form': form
    }

    return render(reuqest, 'accounts/register.html', context)


def login(reuqest):
    return render(reuqest, 'accounts/login.html')


def logout(reuqest):
    return render()
