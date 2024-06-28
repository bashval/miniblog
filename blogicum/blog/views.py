from datetime import datetime
# from django.db.models.base import Model as Model
# from django.db.models.query import QuerySet
from django.forms import BaseModelForm
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView
)

from .models import Post, Category, Comment
from .forms import PostForm, CommentForm
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


class AuthorOnlyMixin(UserPassesTestMixin):
    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user


class PostMixin:
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'


class CommentMixin:
    model = Comment
    template_name = 'blog/comment.html'
    form_class = CommentForm


class PostCreateView(LoginRequiredMixin, PostMixin, CreateView):

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('blog:profile', kwargs={'username': self.request.user})


class PostUpdateView(LoginRequiredMixin, AuthorOnlyMixin, PostMixin, UpdateView):
    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={'pk': self.request.GET.pk})


class PostDeleteView(LoginRequiredMixin, AuthorOnlyMixin, PostMixin, DeleteView):
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


class CommentCreateView(LoginRequiredMixin, CommentMixin, CreateView):
    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.request.GET.post_id
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={'pk':self.request.GET.post_id})


class CommentUpdateView(LoginRequiredMixin, AuthorOnlyMixin, CommentMixin, UpdateView):
    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={'pk':self.request.GET.post_id})

    def get_object(self, queryset=None):
        object = self.model.objects.get(pk=self.request.GET.comment_id)
        return object


class CommentDeleteView(LoginRequiredMixin, AuthorOnlyMixin, CommentMixin, DeleteView):
    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={'pk':self.request.GET.post_id})

    def get_object(self, queryset=None):
        object = self.model.objects.get(id=self.request.GET.comment_id)
        return object


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

'''
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
    )'''


def post_detail(request, post_id):
    template = 'blog/detail.html'
    post = get_object_or_404(
        Post,
        pub_date__lt=datetime.now(),
        is_published=True,
        category__is_published=True,
        pk=post_id
    )
    comments = Comment.objects.select_related(
        'author'
    ).filter(
        post=post_id
    )
    form = CommentForm(request.POST or None)
    if form.is_valid():
        form.save()
    context = {
        'post': post,
        'comments': comments,
        'form': form
    }
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
