from datetime import datetime
from django.shortcuts import get_object_or_404, render
from django.contrib.auth import get_user_model
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView
)

from blog.models import Post, Category
from . import constants


User = get_user_model()


def category_posts(request, category_slug):
    template = 'blog/category.html'
    category = get_object_or_404(
        Category,
        is_published=True,
        slug=category_slug
    )
    post_list = Post.objects.select_related(
        'author',
        'category',
        'location'
    ).filter(
        pub_date__lt=datetime.now(),
        is_published=True,
        category=category,
    )
    context = {
        'post_list': post_list,
        'category': category
    }
    return render(request, template, context)


class PostListView(ListView):
    model = Post
    queryset = Post.objects.select_related(
        'category',
        'location',
        'author'
    ).filter(
        pub_date__lt=datetime.now(),
        is_published=True,
        category__is_published=True
    )
    paginate_by = constants.POSTS_PER_PAGE
    template_name = 'blog/index.html'


def index(request):
    template = 'blog/index.html'
    post_list = Post.objects.select_related(
        'category',
        'location',
        'author'
    ).filter(
        pub_date__lt=datetime.now(),
        is_published=True,
        category__is_published=True
    )[:constants.PAGE_POST_LIMIT]
    context = {'post_list': post_list}
    return render(request, template, context)


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    queryset = Post.objects.select_related(
        'location',
        'category',
        'author'
    ).filter(
        pub_date__lt=datetime.now(),
        is_published=True,
        category__is_published=True
    )


def post_detail(request, id):
    template = 'blog/detail.html'
    post = get_object_or_404(
        Post,
        pub_date__lt=datetime.now(),
        is_published=True,
        category__is_published=True,
        pk=id
    )
    context = {'post': post}
    return render(request, template, context)

def profile(request, username):
    template = 'blog/profile.html'
    author = get_object_or_404(
        User,
        username=username
    )
    page_obj = Post.objects.select_related(
        'category',
        'location',
        'author'
    ).filter(
        is_published=True,
        author=author,
    )
    context = {
        'profile': author,
        'page_obj': page_obj
    }
    return render(request, template, context)


def create_post(request):
    return 'post created'
