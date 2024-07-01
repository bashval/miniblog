from datetime import datetime
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views.generic import (
    ListView,
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


class AuthorOnlyMixin(UserPassesTestMixin):
    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user

    def handle_no_permission(self):
        post_id = self.kwargs.get('post_id', self.kwargs.get('pk'))
        return redirect('blog:post_detail', post_id)


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


class PostUpdateView(AuthorOnlyMixin, PostMixin, UpdateView):
    form_class = PostForm

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.kwargs['pk']})


class PostDeleteView(AuthorOnlyMixin, PostMixin, DeleteView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = PostForm(instance=self.object)
        context['form'] = form
        return context


class PostListView(ListView):
    template_name = 'blog/index.html'
    queryset = Post.objects.select_related(
        'category',
        'location',
        'author'
    ).filter(
        **NON_AUTHOR_FILTERS
    ).annotate(comment_count=Count('comments'))
    paginate_by = constants.POSTS_PER_PAGE
    ordering = ('-pub_date',)


class CommentMixin:
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'
    form_class = CommentForm

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'pk': self.kwargs['post_id']}
        )


class CommentCreateView(LoginRequiredMixin, CommentMixin, CreateView):

    def dispatch(self, request, *args, **kwargs):
        self.blog_post = get_object_or_404(Post, pk=kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post_id = self.kwargs['post_id']
        return super().form_valid(form)


class CommentUpdateView(AuthorOnlyMixin, CommentMixin, UpdateView):
    pass


class CommentDeleteView(AuthorOnlyMixin, CommentMixin, DeleteView):
    pass


class ProfileUpdateView(UpdateView):
    template_name = 'blog/user.html'
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
        return reverse('blog:profile', kwargs={'username': self.request.user})


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
    ).order_by('-pub_date')

    paginator = Paginator(post_list, constants.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'profile': author,
        'page_obj': page_obj
    }
    return render(request, template, context)


def post_detail(request, pk):
    template = 'blog/detail.html'
    if request.user.is_authenticated:
        post = get_object_or_404(
            Post,
            Q(author=request.user) | (
                Q(pub_date__lt=datetime.now())
                & Q(is_published=True)
                & Q(category__is_published=True)
            ),
            pk=pk,
        )
    else:
        post = get_object_or_404(
            Post,
            **NON_AUTHOR_FILTERS,
            pk=pk,
        )
    comments = Comment.objects.select_related(
        'author'
    ).filter(post=pk)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        form.save()
    context = {
        'post': post,
        'comments': comments,
        'form': form
    }
    return render(request, template, context)


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
    ).annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date')
    paginator = Paginator(post_list, constants.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'category': category
    }
    return render(request, template, context)
