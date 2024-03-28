from django.shortcuts import render

# Create your views here.

def register(reuqest):
    return render(reuqest, 'accounts/register.html')


def login(reuqest):
    return render(reuqest, 'accounts/login.html')


def logout(reuqest):
    return render()
