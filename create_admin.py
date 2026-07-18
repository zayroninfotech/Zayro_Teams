import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zayro_teams.settings')
django.setup()
from accounts.models import User
if not User.objects.filter(email='admin@zayro.com').exists():
    User.objects.create_superuser(email='admin@zayro.com', username='admin', password='Admin@123', first_name='Admin', last_name='User')
    print('Superuser created: admin@zayro.com / Admin@123')
else:
    print('Superuser already exists')
