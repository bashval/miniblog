from django.urls import path

from . import views

app_name = 'blog'

urlpatterns = [
    # path('', views.index, name='index'),
    path('', views.PostListView.as_view(), name='index'),
    # path('posts/<int:id>/', views.post_detail, name='post_detail'),
    path('posts/<int:pk>/', views.PostDetailView.as_view(), name='post_detail'),
    path(
        'category/<slug:category_slug>/',
        views.category_posts,
        name='category_posts'
    ),
    path('profile/<username>/', views.profile, name='profile'),
    path('posts/create/', views.PostCreateView.as_view(), name='create_post'),
    # path('profile/<username>/edit/', views.edit_profile, name='edit_profile'),
    path('edit_profile/', views.ProfileUpdateView.as_view(), name='edit_profile'),
]
