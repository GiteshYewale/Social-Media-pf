from django.urls import path
from . import views

# Each URL maps "what the browser types" -> "which view function runs".
# e.g. /login/  ->  views.login_view
urlpatterns = [
    # --- Authentication ---
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    # --- Posts ---
    path('post/create/', views.post_create, name='post_create'),
    path('post/<int:pk>/', views.post_detail, name='post_detail'),
    path('post/<int:pk>/delete/', views.post_delete, name='post_delete'),
    path('post/<int:pk>/like/', views.toggle_like, name='toggle_like'),
    path('post/<int:pk>/comment/', views.comment_create, name='comment_create'),
    path('comment/<int:pk>/delete/', views.comment_delete, name='comment_delete'),
    # --- Profiles & people ---
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('profile/<str:username>/follow/', views.toggle_follow, name='toggle_follow'),
    path('explore/', views.explore_users, name='explore'),
    path('search/', views.search_view, name='search'),
]
