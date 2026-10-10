from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, Post, Comment


class UserRegisterForm(UserCreationForm):
    """Sign-up form: username, names, email + password (handled by UserCreationForm)."""

    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'Email Address'}))
    first_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'placeholder': 'Last Name'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-input'
            })


class UserUpdateForm(forms.ModelForm):
    """Edit basic account info (username, names, email)."""

    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-input'
            })


class ProfileUpdateForm(forms.ModelForm):
    """Edit profile details (bio, avatar, location, website)."""

    bio = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Tell the world about yourself...', 'class': 'form-input'}),
        max_length=500,
        required=False
    )
    location = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'e.g. San Francisco, CA', 'class': 'form-input'}),
        max_length=100,
        required=False
    )
    website = forms.URLField(
        widget=forms.URLInput(attrs={'placeholder': 'https://yourwebsite.com', 'class': 'form-input'}),
        max_length=200,
        required=False
    )
    avatar = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-file-input', 'accept': 'image/*'}))

    class Meta:
        model = Profile
        fields = ['bio', 'avatar', 'location', 'website']


class PostForm(forms.ModelForm):
    """Create a post: required text (max 500 chars) + optional image."""

    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': "What's on your mind?",
            'class': 'post-textarea',
            'id': 'post-content-input',
            'maxlength': '500'
        }),
        max_length=500
    )
    image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'file-input-hidden',
            'id': 'post-image-input',
            'accept': 'image/*'
        })
    )

    class Meta:
        model = Post
        fields = ['content', 'image']


class CommentForm(forms.ModelForm):
    """Write a one-line comment."""

    content = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'Write a comment...',
            'class': 'comment-input',
            'autocomplete': 'off'
        }),
        max_length=500
    )

    class Meta:
        model = Comment
        fields = ['content']
