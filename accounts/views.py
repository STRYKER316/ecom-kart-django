from django.shortcuts import render

from .forms import RegistrationForm

# Create your views here.

def register(reuqest):
    form = RegistrationForm()

    context = {
        'form': form,
    }

    return render(reuqest, 'accounts/register.html', context)


def login(reuqest):
    return render(reuqest, 'accounts/login.html')


def logout(reuqest):
    return render()
