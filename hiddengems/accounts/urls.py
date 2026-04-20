from django.urls import path
from . import views

# URL patterns for user authentication
urlpatterns = [
    # Login page
    path('login/', views.login_view, name='login'),

    # Signup page
    path('signup/', views.signup_view, name='signup'),

    # Logout
    path('logout/', views.logout_view, name='logout'),
]
