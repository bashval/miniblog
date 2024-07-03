from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
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
    queryset = Post.objects.published_or_author().select_related(
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


class ProfilePostListView(ListView):
    template_name = 'blog/profile.html'
    paginate_by = constants.POSTS_PER_PAGE

    def get_queryset(self):
        queryset = Post.objects.published_or_author(
            author_id=self.request.user.id or None
        ).filter(
            author__username=self.kwargs['username']
        ).select_related(
            'category',
            'location',
            'author'
        ).order_by('-pub_date')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = get_object_or_404(
            User,
            username=self.kwargs['username']
        )
        context['profile'] = profile
        return context


def post_detail(request, pk):
    template = 'blog/detail.html'
    post = get_object_or_404(
        Post.objects.published_or_author(
            request.user.id or None
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
        queryset = Post.objects.published_or_author().select_related(
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
