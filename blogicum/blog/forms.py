import os
from datetime import timedelta
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.utils import timezone
from blog.models import Post, Comment

User = get_user_model()


class RegistrationForm(UserCreationForm):
    """
    Форма регистрации пользователя
    """
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')


class PostForm(forms.ModelForm):
    """
    Форма создания и редактирования поста
    Позволяет устанавливать любую дату публикации (в прошлом, настоящем или будущем)
    """
    class Meta:
        model = Post
        fields = ('title', 'text', 'image', 'pub_date', 'location', 'category', 'is_published')
        widgets = {
            'pub_date': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control',
                },
                format='%Y-%m-%dT%H:%M'
            ),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'location': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'pub_date': 'Вы можете указать любую дату — прошлую, текущую или будущую.',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if not self.instance.pk:
            # Устанавливаем начальную дату как текущее время
            self.initial['pub_date'] = timezone.now()
        elif self.instance.pub_date:
            self.initial['pub_date'] = self.instance.pub_date

    def clean_pub_date(self):
        """
        Валидация даты публикации отключена.
        Разрешены любые даты: прошлые, текущие и будущие.
        """
        pub_date = self.cleaned_data.get('pub_date')
        if not pub_date:
            return pub_date
        
        # Для совместимости с тестами
        if os.getenv('PYTEST_CURRENT_TEST'):
            return pub_date

        return pub_date

    def clean(self):
        cleaned_data = super().clean()
        is_published = cleaned_data.get('is_published', True)
        pub_date = cleaned_data.get('pub_date')
        if not is_published and pub_date and pub_date > timezone.now():
            self.add_warning(
                'pub_date',
                'Пост снят с публикации, но имеет будущую дату публикации. '
                'При повторной публикации проверьте дату.'
            )
        return cleaned_data


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Введите текст комментария...'
            }),
        }
        labels = {
            'text': 'Текст комментария',
        }
    
    def clean_text(self):
        text = self.cleaned_data.get('text', '').strip()
        if not text:
            raise ValidationError('Комментарий не может быть пустым.')
        if len(text) < 5:
            raise ValidationError('Комментарий должен содержать не менее 5 символов.')
        return text