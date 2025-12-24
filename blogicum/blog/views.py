from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.core.paginator import Paginator
from blog.models import Post, Category, Comment
from django.utils import timezone
from blog.forms import RegistrationForm, PostForm, CommentForm, ProfileEditForm

User = get_user_model()


def get_published_posts():
    return Post.objects.filter(
        is_published=True,
        category__is_published=True,
        pub_date__lte=timezone.now()
    )


def index(request):
    """Главная страница - 10 последних опубликованных постов с пагинацией"""

    template = 'blog/index.html'

    post_list = get_published_posts().annotate(comment_count=Count('comments')).order_by('-pub_date')

    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, template, {'page_obj': page_obj})


def post_detail(request, post_id):
    """Страница отдельной публикации с комментариями"""

    template = 'blog/detail.html'

    post = get_object_or_404(
        Post,
        pk=post_id
    )

    is_accessible = (
        post.is_published
        and post.category.is_published
        and post.pub_date <= timezone.now()
    )

    if not is_accessible and request.user != post.author:
        from django.http import Http404
        raise Http404("Пост не найден")

    comments = post.comments.select_related('author')
    form = CommentForm() if request.user.is_authenticated else None

    context = {
        'post': post,
        'comments': comments,
        'form': form
    }

    return render(request, template, context)


def category_posts(request, category_slug):
    """Страница категории с пагинацией"""

    template = 'blog/category.html'

    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )

    post_list = (
        get_published_posts()
        .filter(category=category)
    ).order_by('-pub_date')

    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'category': category,
        'post_list': post_list,
        'page_obj': page_obj
    }

    return render(request, template, context)


def register(request):
    """Регистрация пользователя"""

    template = 'registration/registration_form.html'

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = RegistrationForm()

    return render(request, template, {'form': form})


def user_profile(request, username):
    """Страница профиля пользователя с пагинацией"""

    template = 'blog/profile.html'

    profile = get_object_or_404(User, username=username)

    if request.user == profile:
        post_list = Post.objects.filter(author=profile).select_related(
            'category', 'location', 'author'
        ).annotate(comment_count=Count('comments')).order_by('-pub_date')
    else:
        post_list = get_published_posts().filter(author=profile).annotate(comment_count=Count('comments')).order_by('-pub_date')


    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, template, {
        'profile': profile,
        'page_obj': page_obj
    })


@login_required
def edit_profile(request):
    """Редактирование информации профиля"""

    template = 'registration/registration_form.html'

    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('blog:profile', username=request.user.username)
    else:
        form = ProfileEditForm(instance=request.user)

    return render(request, template, {'form': form})


@login_required
def create_post(request):
    """Создание нового поста"""

    template = 'blog/create.html'
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('blog:profile', username=request.user.username)
    else:
        form = PostForm()

    return render(request, template, {'form': form})


@login_required
def edit_post(request, post_id):
    """Редактирование поста"""

    template = 'blog/create.html'
    
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post_id)
    else:
        form = PostForm(instance=post)

    return render(request, template, {'form': form})


@login_required
def delete_post(request, post_id):
    """Удаление поста"""

    template = 'blog/create.html'

    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)

    if request.method == 'POST':
        post.delete()
        return redirect('blog:profile', username=request.user.username)

    form = PostForm(instance=post)

    return render(request, template, {'form': form})


@login_required
def add_comment(request, post_id):
    """Добавление комментария"""

    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
    return redirect('blog:post_detail', post_id=post_id)


@login_required
def edit_comment(request, post_id, comment_id):
    """Редактирование комментария"""

    template = 'blog/comment.html'

    comment = get_object_or_404(Comment, id=comment_id, post_id=post_id)
    if comment.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post_id)
    else:
        form = CommentForm(instance=comment)

    return render(request, template, {
        'form': form,
        'comment': comment
    })


@login_required
def delete_comment(request, post_id, comment_id):
    """Удаление комментария"""

    template = 'blog/comment.html'

    comment = get_object_or_404(Comment, id=comment_id, post_id=post_id)
    if comment.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)

    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id=post_id)

    return render(request, template, {
        'comment': comment
    })
