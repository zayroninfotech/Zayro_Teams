import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zayro_teams.settings')
django.setup()

from accounts.models import User

# Read credentials from environment (set before running this script)
username = os.environ.get('ADMIN_USERNAME', 'superadmin')
email    = os.environ.get('ADMIN_EMAIL', 'superadmin@zayro.com')
password = os.environ.get('ADMIN_PASSWORD')

if not password:
    raise SystemExit("ERROR: Set ADMIN_PASSWORD environment variable before running this script.")

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(
        email=email,
        username=username,
        password=password,
        first_name='Super',
        last_name='Admin'
    )
    print('Superuser created!')
    print(f'  Username : {username}')
    print(f'  Email    : {email}')
else:
    print('Superuser already exists')
