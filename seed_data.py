import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'social_project.settings')
django.setup()

from django.contrib.auth.models import User
from social.models import Profile, Post, Comment, Like, Follow

def seed():
    print("Seeding database...")

    # Create Superuser / Admin if not exists
    if not User.objects.filter(username='admin').exists():
        admin = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        admin.first_name = "System"
        admin.last_name = "Admin"
        admin.save()
        admin.profile.bio = "Platform administrator and lead engineer at SocialPulse."
        admin.profile.location = "San Francisco, CA"
        admin.profile.website = "https://socialpulse.app"
        admin.profile.save()
        print("Created admin user (admin / admin123)")

    # Create demo users
    users_data = [
        {
            'username': 'alex_dev',
            'first_name': 'Alex',
            'last_name': 'Rivers',
            'email': 'alex@example.com',
            'bio': 'Full-stack developer building modern web apps & open source tools. 🚀 Python, JS, UI/UX fan.',
            'location': 'Seattle, WA',
            'website': 'https://alexrivers.dev'
        },
        {
            'username': 'sophia_code',
            'first_name': 'Sophia',
            'last_name': 'Chen',
            'email': 'sophia@example.com',
            'bio': 'AI researcher and frontend enthusiast. Coffee lover ☕️ | Photography 📸',
            'location': 'New York, NY',
            'website': 'https://sophiachen.io'
        },
        {
            'username': 'marcus_design',
            'first_name': 'Marcus',
            'last_name': 'Vance',
            'email': 'marcus@example.com',
            'bio': 'UI/UX Designer crafting beautiful digital experiences and design systems.',
            'location': 'Austin, TX',
            'website': 'https://marcusvance.design'
        },
        {
            'username': 'elena_tech',
            'first_name': 'Elena',
            'last_name': 'Rostova',
            'email': 'elena@example.com',
            'bio': 'Cybersecurity analyst & cloud architect. Tech blogger and podcast host.',
            'location': 'Chicago, IL',
            'website': 'https://elenatech.com'
        },
    ]

    users = {}
    for u_data in users_data:
        user, created = User.objects.get_or_create(
            username=u_data['username'],
            defaults={
                'email': u_data['email'],
                'first_name': u_data['first_name'],
                'last_name': u_data['last_name'],
            }
        )
        if created:
            user.set_password('password123')
            user.save()
            user.profile.bio = u_data['bio']
            user.profile.location = u_data['location']
            user.profile.website = u_data['website']
            user.profile.save()
            print(f"Created user: {user.username}")
        users[user.username] = user

    alex = users['alex_dev']
    sophia = users['sophia_code']
    marcus = users['marcus_design']
    elena = users['elena_tech']

    # Follow relationships
    follows = [
        (alex, sophia),
        (alex, marcus),
        (sophia, alex),
        (sophia, elena),
        (marcus, alex),
        (elena, alex),
        (elena, sophia),
    ]
    for follower, following in follows:
        Follow.objects.get_or_create(follower=follower, following=following)

    print("Created follow relationships.")

    # Posts
    posts_data = [
        {
            'author': alex,
            'content': "Just launched Task 2 SocialPulse platform! Built with Django on the backend and clean vanilla HTML/CSS/JS on the frontend. Dynamic likes, follows, and instant AJAX comments are super snappy! ⚡️"
        },
        {
            'author': sophia,
            'content': "Working on neural net architectures today. Never forget: simple models with clean, structured data often outperform complex architectures with noisy inputs! 🧠💻 #AI #DataScience"
        },
        {
            'author': marcus,
            'content': "Minimalist design isn't about removing features—it's about adding clarity. Color hierarchy and consistent spacing are key to effortless UX."
        },
        {
            'author': elena,
            'content': "Reminder for developer teams: always sanitize user inputs and enable CSRF protection on form endpoints. Security should be baked in from line one!"
        },
        {
            'author': alex,
            'content': "What is your favorite Python web framework in 2026? Django remains top tier for full-featured web applications!"
        }
    ]

    created_posts = []
    for p_data in posts_data:
        post, created = Post.objects.get_or_create(
            author=p_data['author'],
            content=p_data['content']
        )
        created_posts.append(post)

    print(f"Created {len(created_posts)} posts.")

    # Likes
    likes = [
        (sophia, created_posts[0]),
        (marcus, created_posts[0]),
        (elena, created_posts[0]),
        (alex, created_posts[1]),
        (marcus, created_posts[1]),
        (alex, created_posts[2]),
        (sophia, created_posts[3]),
        (marcus, created_posts[4]),
    ]
    for user, post in likes:
        Like.objects.get_or_create(user=user, post=post)

    print("Created post likes.")

    # Comments
    comments_data = [
        (sophia, created_posts[0], "Awesome job Alex! The UI looks super smooth."),
        (marcus, created_posts[0], "Great layout and typography! Love the color palette."),
        (alex, created_posts[1], "Totally agree Sophia! Data quality > model complexity every time."),
        (elena, created_posts[2], "Spot on Marcus. Clarity brings speed and delight to users."),
        (sophia, created_posts[4], "Django 100%! The built-in admin & ORM save so much boilerplate."),
    ]
    for author, post, content in comments_data:
        Comment.objects.get_or_create(author=author, post=post, content=content)

    print("Created comments.")
    print("Database seeding finished successfully!")

if __name__ == '__main__':
    seed()
