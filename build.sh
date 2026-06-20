#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input

python manage.py migrate

python manage.py loaddata accounts.json || true
python manage.py loaddata activities.json || true
python manage.py loaddata reports.json || true
python manage.py loaddata workflows.json || true

python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()

user, created = User.objects.get_or_create(
    username='renderadmin',
    defaults={
        'email': 'admin@gmail.com',
        'is_staff': True,
        'is_superuser': True,
    }
)

user.set_password('Render@123')
user.is_staff = True
user.is_superuser = True
user.is_active = True
user.save()

print('Render admin ready')
"