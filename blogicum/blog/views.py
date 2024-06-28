from datetime import datetime
from django.db.models.base import Model as Model
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404, render
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView
)

from .models import Post, Category
from .forms import PostForm
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


class PostCreateView(CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('blog:profile', kwargs={'username': self.request.user})


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


# class AuthorListView(ListView):


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


class ProfileUpdateView(UpdateView):
    model = User
    template_name = 'blog/user.html'
    fields = (
        'username',
        'first_name',
        'last_name',
        'email'
    )

    def get_object(self, queryset=None):
        object = self.model.objects.get(username=self.request.user)
        return object

    def get_success_url(self):
        return reverse_lazy('blog:profile', kwargs={'username': self.request.user})


def edit_profile(request, username):
    return render(request, 'blog/.html')
