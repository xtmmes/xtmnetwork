from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Comment, Follow
from .utils import paginator


def index(request):
    post_list = Post.objects.select_related('author', 'group')
    context = {
        'page_obj': paginator(request, post_list),
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('author')
    context = {
        'group': group,
        'page_obj': paginator(request, post_list),
        'title': group.title,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.select_related('group')
    paginator(request, post_list)
    posts_amount = author.posts.count()
    following = (
        request.user.is_authenticated
        and Follow.objects.filter(
            user__username=request.user, author__username=username).exists())
    context = {
        'author': author,
        'page_obj': paginator(request, post_list),
        'following': following,
        'posts_amount': posts_amount
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    author_posts = post.author.posts.count()
    num_author_posts = Post.objects.filter(author=author_posts).count()
    comment_form = CommentForm(request.POST or None)
    comments = Comment.objects.select_related('post', 'author')
    context = {
        'post': post,
        'author_posts': author_posts,
        'posts_count': num_author_posts,
        'form': comment_form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    )
    if not form.is_valid():
        return render(request, 'posts/post_create.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', username=post.author.username)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post.pk)

    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if not form.is_valid():
        return render(request, 'posts/post_create.html',
                      {'form': form, 'post': post})
    form.save()
    return redirect('posts:post_detail', post.pk)


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
    """Посты авторов,на которых подписан текущий пользователь, не более 10"""
    user = request.user
    posts = Post.objects.filter(author__following__user=user)
    page_obj = paginator(posts, request)
    template = 'posts/follow.html'
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect("posts:profile", username=username)


@login_required
def profile_unfollow(request, username):
    """Функция отписаться от некого автора"""
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username)