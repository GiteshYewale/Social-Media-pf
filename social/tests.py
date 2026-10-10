from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Profile, Post, Comment, Like, Follow


class SocialPlatformTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='user1', password='password123', email='user1@example.com')
        self.user2 = User.objects.create_user(username='user2', password='password123', email='user2@example.com')

    def test_profile_signal_creation(self):
        """Test that profile is automatically created when a user registers."""
        self.assertIsNotNone(self.user1.profile)
        self.assertEqual(self.user1.profile.user.username, 'user1')
        self.assertIn('user1', self.user1.profile.avatar_url)

    def test_post_creation_and_like(self):
        """Test post creation and like functionality."""
        self.client.login(username='user1', password='password123')
        
        # Create post
        post = Post.objects.create(author=self.user1, content="Hello World Test Post")
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(post.likes_count, 0)

        # Toggle like via AJAX
        response = self.client.post(
            reverse('toggle_like', kwargs={'pk': post.id}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data['liked'])
        self.assertEqual(json_data['likes_count'], 1)

        # Toggle like off
        response = self.client.post(
            reverse('toggle_like', kwargs={'pk': post.id}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        json_data = response.json()
        self.assertFalse(json_data['liked'])
        self.assertEqual(json_data['likes_count'], 0)

    def test_follow_system(self):
        """Test follow and unfollow functionality."""
        self.client.login(username='user1', password='password123')

        # Follow user2 via AJAX
        response = self.client.post(
            reverse('toggle_follow', kwargs={'username': 'user2'}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data['following'])
        self.assertEqual(json_data['followers_count'], 1)
        self.assertTrue(Follow.objects.filter(follower=self.user1, following=self.user2).exists())

        # Unfollow user2
        response = self.client.post(
            reverse('toggle_follow', kwargs={'username': 'user2'}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        json_data = response.json()
        self.assertFalse(json_data['following'])
        self.assertEqual(json_data['followers_count'], 0)

    def test_comment_creation_and_deletion(self):
        """Test comment creation and deletion via AJAX."""
        self.client.login(username='user1', password='password123')
        post = Post.objects.create(author=self.user2, content="User2 Post")

        # Create comment
        response = self.client.post(
            reverse('comment_create', kwargs={'pk': post.id}),
            {'content': 'Nice post!'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data['status'], 'success')
        self.assertEqual(json_data['content'], 'Nice post!')

        comment_id = json_data['comment_id']
        self.assertEqual(Comment.objects.count(), 1)

        # Delete comment
        response = self.client.post(
            reverse('comment_delete', kwargs={'pk': comment_id}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), 0)

    def test_feed_access_login_required(self):
        """Test that unauthenticated users are redirected to login."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)
