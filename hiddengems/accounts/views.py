from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

# View that handles user login
def login_view(request):

    # If user is already logged in, send them to homepage
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        # Get submitted login form data
        form = AuthenticationForm(data=request.POST)

        if form.is_valid():
            # Authenticate the user
            user = form.get_user()
            login(request, user)
            # Redirect to upload page or homepage after login
            return redirect(request.GET.get('next', 'index'))
    else:
        # Show empty login form
        form = AuthenticationForm()

    return render(request, 'accounts/login.html', {'form': form})


# View that handles user signup
def signup_view(request):

    # If user is already logged in, send them to homepage
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        # Get submitted signup form data
        form = UserCreationForm(request.POST)

        if form.is_valid():
            # Save the new user
            user = form.save()
            # Log them in immediately after signup
            login(request, user)
            return redirect('index')
    else:
        # Show empty signup form
        form = UserCreationForm()

    return render(request, 'accounts/signup.html', {'form': form})


# View that logs the user out
def logout_view(request):
    logout(request)
    return redirect('index')
