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
    path('create_post/', views.create_post, name='create_post'),
]
