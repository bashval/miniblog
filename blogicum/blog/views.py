from datetime import datetime
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView
)

from .mixins import AuthorOnlyMixin, PostMixin, CommentMixin
from .models import Post, Category, Comment
from .forms import PostForm, CommentForm
from . import constants


User = get_user_model()


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
    queryset = Post.published.select_related(
        'category',
        'location',
        'author'
    )
    paginate_by = constants.POSTS_PER_PAGE
    ordering = ('-pub_date',)


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


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'blog/user.html'
    fields = (
        'username',
        'first_name',
        'last_name',
        'email'
    )

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse('blog:profile', kwargs={'username': self.request.user})


def profile(request, username):
    template = 'blog/profile.html'
    author = get_object_or_404(
        User,
        username=username
    )
    if author == request.user:
        model_manager = Post.objects
    else:
        model_manager = Post.published
    post_list = model_manager.select_related(
        'category',
        'location',
        'author'
    ).filter(author=author).order_by('-pub_date')

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
    user_id = request.user.id if request.user.is_authenticated else None
    post = get_object_or_404(
        Post,
        Q(author_id=user_id) | (
            Q(pub_date__lt=datetime.now())
            & Q(is_published=True)
            & Q(category__is_published=True)
        ),
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


class CategoryPostListView(ListView):
    template_name = 'blog/category.html'
    paginate_by = constants.POSTS_PER_PAGE

    def get_queryset(self):
        queryset = Post.published.select_related(
            'author',
            'category',
            'location'
        ).filter(
            category__slug=self.kwargs['category_slug']
        ).order_by('-pub_date')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = get_object_or_404(
            Category,
            is_published=True,
            slug=self.kwargs['category_slug']
        )
        context['category'] = category
        return context
