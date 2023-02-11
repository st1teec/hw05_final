from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

from .models import Group, Post, User, Follow
from .forms import PostForm, CommentForm
from .const import POSTS_FOR_PAGE, CACHE_TIME


def get_page(request, queryset, per_page):
    return Paginator(queryset, per_page).get_page(request.GET.get('page'))


@cache_page(CACHE_TIME, key_prefix="index_page")
def index(request):
    return render(request, 'posts/index.html', {
        'page_obj': get_page(request, Post.objects.all(), POSTS_FOR_PAGE),
    })


def group_list(request, slug):
    group = get_object_or_404(Group, slug=slug)
    return render(request, 'posts/group_list.html', {
        'group': group,
        'page_obj': get_page(request, group.posts.all(), POSTS_FOR_PAGE),
    })


def profile(request, username):
    author = get_object_or_404(User, username=username)
    following = request.user.is_authenticated and Follow.objects.filter(
        author=author, user=request.user).exists()
    return render(request, 'posts/profile.html', {
        'author': author,
        'page_obj': get_page(request, author.posts.all(), POSTS_FOR_PAGE),
        'following': following
    })


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all()
    form = CommentForm()
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect('posts:post_detail', post_id=post.id)
    return render(request, 'posts/post_detail.html', {
        'post': post,
        'comments': comments,
        'form': form,
    })


@login_required
def post_create(request):
    form = PostForm(request.POST or None)
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', request.user.username)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    return render(request, 'posts/create_post.html', {
        'form': form,
        'post': post,
    })


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post = Post.objects.filter(author__following__user=request.user)
    return render(
        request,
        'posts/follow.html',
        {'page_obj': get_page(request, post, POSTS_FOR_PAGE)}
    )


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(author=author, user=request.user)
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(
        author=author, user=request.user).delete()
    return redirect('posts:follow_index')
