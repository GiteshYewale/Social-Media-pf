from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
from django.urls import reverse

from .models import Profile, Post, Comment, Like, Follow
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm, PostForm, CommentForm


def register_view(request):
    """SIGN UP: show the form (GET) or create a new user and log them in (POST)."""

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to SocialPulse, {user.username}! Your account has been created.")
            return redirect('profile_edit')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserRegisterForm()

    return render(request, 'social/register.html', {'form': form})


def login_view(request):
    """LOG IN: check username + password, then start the user's session."""

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                next_page = request.GET.get('next', 'home')
                return redirect(next_page)
        messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'social/login.html', {'form': form})


def logout_view(request):
    """LOG OUT: end the session and send the user to the login page."""

    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')


@login_required
def home(request):
    """HOME FEED: shows posts to like/comment on.
    feed_type='following' -> posts from people I follow (+ my own posts).
    feed_type='all'       -> global feed from everyone."""

    feed_type = request.GET.get('feed', 'following')
    post_form = PostForm()
    comment_form = CommentForm()

    # Determine posts to show
    if feed_type == 'following':
        following_users = Follow.objects.filter(follower=request.user).values_list('following', flat=True)
        # Include user's own posts + posts from users they follow
        allowed_users = list(following_users) + [request.user.id]
        posts = Post.objects.filter(author_id__in=allowed_users).select_related('author', 'author__profile').prefetch_related('likes', 'comments')
    else:
        feed_type = 'all'
        posts = Post.objects.all().select_related('author', 'author__profile').prefetch_related('likes', 'comments')

    # Annotate posts with user liked status
    user_liked_post_ids = set(Like.objects.filter(user=request.user).values_list('post_id', flat=True))
    for post in posts:
        post.is_liked = post.id in user_liked_post_ids

    # Suggested users to follow (excluding self and already followed users)
    following_ids = set(Follow.objects.filter(follower=request.user).values_list('following_id', flat=True))
    following_ids.add(request.user.id)
    suggested_users = User.objects.exclude(id__in=following_ids).select_related('profile')[:5]

    context = {
        'posts': posts,
        'post_form': post_form,
        'comment_form': comment_form,
        'feed_type': feed_type,
        'suggested_users': suggested_users,
    }
    return render(request, 'social/home.html', context)


@login_required
def post_create(request):
    """CREATE POST: save the new post (text + optional image) and go back home."""

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, "Your post has been published!")
        else:
            messages.error(request, "Could not publish post. Please check input.")
    return redirect('home')


@login_required
def post_detail(request, pk):
    """POST PAGE: show one full post with all of its comments."""

    post = get_object_or_404(Post.objects.select_related('author', 'author__profile'), pk=pk)
    comments = post.comments.select_related('author', 'author__profile').all()
    comment_form = CommentForm()

    is_liked = Like.objects.filter(user=request.user, post=post).exists()

    context = {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
        'is_liked': is_liked,
    }
    return render(request, 'social/post_detail.html', context)


@login_required
def post_delete(request, pk):
    """DELETE POST: only the post's author is allowed to delete it."""

    post = get_object_or_404(Post, pk=pk)
    if post.author == request.user:
        post.delete()
        messages.success(request, "Post deleted successfully.")
    else:
        messages.error(request, "You are not authorized to delete this post.")
    
    next_url = request.META.get('HTTP_REFERER', 'home')
    return redirect(next_url)


@login_required
def comment_create(request, pk):
    """ADD COMMENT: normal form post, or AJAX (JSON) if sent by fetch/XMLHttpRequest."""

    post = get_object_or_404(Post, pk=pk)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'comment_id': comment.id,
                    'author': comment.author.username,
                    'author_avatar': comment.author.profile.avatar_url,
                    'author_url': reverse('profile', kwargs={'username': comment.author.username}),
                    'content': comment.content,
                    'created_at': comment.created_at.strftime('%b %d, %Y, %I:%M %p'),
                    'comments_count': post.comments.count(),
                })
            messages.success(request, "Comment added!")
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

    next_url = request.META.get('HTTP_REFERER', reverse('post_detail', kwargs={'pk': pk}))
    return redirect(next_url)


@login_required
def comment_delete(request, pk):
    """DELETE COMMENT: the comment's author OR the post's author may delete it."""

    comment = get_object_or_404(Comment, pk=pk)
    post_pk = comment.post.id
    if comment.author == request.user or comment.post.author == request.user:
        comment.delete()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'comments_count': Comment.objects.filter(post_id=post_pk).count()
            })
        messages.success(request, "Comment deleted.")
    else:
        messages.error(request, "You cannot delete this comment.")
    
    next_url = request.META.get('HTTP_REFERER', reverse('post_detail', kwargs={'pk': post_pk}))
    return redirect(next_url)


@login_required
def toggle_like(request, pk):
    """LIKE / UNLIKE: if I already liked the post -> remove the like, else add it."""

    post = get_object_or_404(Post, pk=pk)
    like_qs = Like.objects.filter(user=request.user, post=post)
    
    if like_qs.exists():
        like_qs.delete()
        liked = False
    else:
        Like.objects.create(user=request.user, post=post)
        liked = True

    likes_count = post.likes.count()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'liked': liked,
            'likes_count': likes_count
        })

    next_url = request.META.get('HTTP_REFERER', 'home')
    return redirect(next_url)


@login_required
def toggle_follow(request, username):
    """FOLLOW / UNFOLLOW: same toggle idea as like, but for people."""

    target_user = get_object_or_404(User, username=username)

    if target_user == request.user:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': 'You cannot follow yourself.'}, status=400)
        messages.warning(request, "You cannot follow yourself.")
        return redirect('profile', username=username)

    follow_qs = Follow.objects.filter(follower=request.user, following=target_user)

    if follow_qs.exists():
        follow_qs.delete()
        is_following = False
    else:
        Follow.objects.create(follower=request.user, following=target_user)
        is_following = True

    followers_count = target_user.followers_set.count()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'following': is_following,
            'followers_count': followers_count
        })

    return redirect('profile', username=username)


@login_required
def profile_view(request, username):
    """PROFILE PAGE: avatar, bio, follower counts and that user's posts."""

    user_obj = get_object_or_404(User.objects.select_related('profile'), username=username)
    posts = user_obj.posts.all().select_related('author', 'author__profile').prefetch_related('likes', 'comments')

    # Annotate posts with user liked status
    user_liked_post_ids = set(Like.objects.filter(user=request.user).values_list('post_id', flat=True))
    for post in posts:
        post.is_liked = post.id in user_liked_post_ids

    followers_count = user_obj.followers_set.count()
    following_count = user_obj.following_set.count()
    is_following = Follow.objects.filter(follower=request.user, following=user_obj).exists() if request.user != user_obj else False

    context = {
        'profile_user': user_obj,
        'posts': posts,
        'followers_count': followers_count,
        'following_count': following_count,
        'is_following': is_following,
        'comment_form': CommentForm(),
    }
    return render(request, 'social/profile.html', context)


@login_required
def profile_edit(request):
    """EDIT PROFILE: two forms side by side - account (u_form) + profile (p_form)."""

    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('profile', username=request.user.username)
        else:
            messages.error(request, "Please correct errors in the form.")
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form,
    }
    return render(request, 'social/profile_edit.html', context)


@login_required
def explore_users(request):
    """EXPLORE: search people by name/username, or show the first 20 users."""

    query = request.GET.get('q', '').strip()
    if query:
        users = User.objects.filter(
            Q(username__icontains=query) | 
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query)
        ).exclude(id=request.user.id).select_related('profile')
    else:
        users = User.objects.exclude(id=request.user.id).select_related('profile')[:20]

    # Annotate follow state
    following_ids = set(Follow.objects.filter(follower=request.user).values_list('following_id', flat=True))
    for user in users:
        user.is_followed = user.id in following_ids
        user.followers_count_num = user.followers_set.count()

    context = {
        'users': users,
        'query': query,
    }
    return render(request, 'social/explore.html', context)


@login_required
def search_view(request):
    """SEARCH: find matching posts AND matching people for one query."""

    query = request.GET.get('q', '').strip()
    posts = []
    users = []

    if query:
        posts = Post.objects.filter(
            Q(content__icontains=query) | Q(author__username__icontains=query)
        ).select_related('author', 'author__profile').prefetch_related('likes', 'comments')
        
        users = User.objects.filter(
            Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query)
        ).select_related('profile')

        user_liked_post_ids = set(Like.objects.filter(user=request.user).values_list('post_id', flat=True))
        for post in posts:
            post.is_liked = post.id in user_liked_post_ids

    context = {
        'query': query,
        'posts': posts,
        'users': users,
        'comment_form': CommentForm(),
    }
    return render(request, 'social/search_results.html', context)
