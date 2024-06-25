from datetime import datetime
from django.shortcuts import get_object_or_404, render

from blog.models import Post, Category
from . import constants


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
