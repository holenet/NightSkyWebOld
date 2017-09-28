from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect, render


def register(request):
    if request.user.is_authenticated():
        logout(request)
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = request.POST['username']
            password = request.POST['password1']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('cloud:post_list')
            else:
                return redirect('register')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})
