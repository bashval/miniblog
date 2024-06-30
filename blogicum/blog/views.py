from datetime import datetime
# from django.db.models.base import Model as Model
# from django.db.models.query import QuerySet
from django.forms import BaseModelForm
from django.http import HttpRequest, HttpResponse
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.db.models import Count
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy, reverse
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


NON_AUTHOR_FILTERS = ({
    'is_published': True,
    'category__is_published': True,
    'pub_date__lt': datetime.now()
})


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
    ).annotate(comment_count=Count('comments'))
    paginator = Paginator(post_list, constants.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'category': category
    }
    return render(request, template, context)


class AuthorOnlyMixin(UserPassesTestMixin):
    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user
    
    def handle_no_permission(self):
        return redirect('blog:post_detail', self.kwargs['pk'])


class PostMixin:
    model = Post
    template_name = 'blog/create.html'

    def get_success_url(self):
        return reverse('blog:profile', kwargs={'username': self.request.user})


class PostCreateView(LoginRequiredMixin, PostMixin, CreateView):
    form_class = PostForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(LoginRequiredMixin, AuthorOnlyMixin, PostMixin, UpdateView):
    form_class = PostForm

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.kwargs['pk']})

    # def handle_no_permission(self):
    #     return redirect('blog:post_detail', self.kwargs['pk'])


class PostDeleteView(LoginRequiredMixin, AuthorOnlyMixin, PostMixin, DeleteView):
    pass


def delete_post(request, pk):
    template = 'blog/create.html'
    instance = get_object_or_404(Post, pk=pk)
    form = PostForm(instance=instance)
    context = {'form': form}
    if request.method == 'POST':
        instance.delete()
        return reverse('blog:profile', kwargs={'username': request.user})
    return render(request, template, context)


class PostListView(ListView):
    model = Post
    template_name = 'blog/index.html'
    queryset = Post.objects.select_related(
        'category',
        'location',
        'author'
    ).filter(
        **NON_AUTHOR_FILTERS
    ).annotate(comment_count=Count('comments'))
    paginate_by = constants.POSTS_PER_PAGE
    ordering = '-pub_date'


class CommentMixin:
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'
    form_class = CommentForm

    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={'pk': self.kwargs['post_id']})


class CommentCreateView(LoginRequiredMixin, CommentMixin, CreateView):

    def dispatch(self, request, *args, **kwargs):
        self.blog_post = get_object_or_404(Post, pk=kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post_id = self.kwargs['post_id']
        return super().form_valid(form)


class CommentUpdateView(LoginRequiredMixin, AuthorOnlyMixin, CommentMixin, UpdateView):
    pass


class CommentDeleteView(LoginRequiredMixin, AuthorOnlyMixin, CommentMixin, DeleteView):
    pass


# def index(request):
#     template = 'blog/index.html'
#     post_list = Post.objects.select_related(
#         'category',
#         'location',
#         'author'
#     ).filter(
#         pub_date__lt=datetime.now(),
#         is_published=True,
#         category__is_published=True
#     )[:constants.PAGE_POST_LIMIT]
#     context = {'post_list': post_list}
#     return render(request, template, context)


def post_detail(request, pk):
    template = 'blog/detail.html'
    post = get_object_or_404(
        Post,
        # pub_date__lt=datetime.now(),
        # is_published=True,
        # category__is_published=True,
        pk=pk
    )
    comments = Comment.objects.select_related(
        'author'
    ).filter(
        post=pk
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


def profile(request, username):
    template = 'blog/profile.html'
    author = get_object_or_404(
        User,
        username=username
    )
    post_list = Post.objects.select_related(
        'category',
        'location',
        'author'
    ).filter(author=author)
    if request.user != author:
        post_list = post_list.filter(**NON_AUTHOR_FILTERS)
    post_list = post_list.annotate(
        comment_count=Count('comments')
    ).order_by('pub_date')
    paginator = Paginator(post_list, constants.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'profile': author,
        'page_obj': page_obj
    }
    return render(request, template, context)


class ProfileUpdateView(UpdateView):
    # model = User
    template_name = 'blog/user.html'
    # slug_field = 'username'
    # slug_url_kwarg = 'username'
    fields = (
        'username',
        'first_name',
        'last_name',
        'email'
    )

    def get_object(self, queryset=None):
        object = get_object_or_404(
            User,
            username=self.request.user)
        return object

    def get_success_url(self):
        return reverse_lazy('blog:profile', kwargs={'username': self.request.user})


# def edit_profile(request, username):
#     return render(request, 'blog/.html')
