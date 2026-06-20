#!/usr/bin/env bash

pip install -r requirements.txt

python manage.py collectstatic --noinput

python manage.py migrate

python manage.py loaddata accounts.json
python manage.py loaddata activities.json
python manage.py loaddata reports.json
python manage.py loaddata workflows.json


#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input

python manage.py migrate

python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()

if not User.objects.filter(username='renderadmin').exists():
    User.objects.create_superuser(
        username='renderadmin',
        email='admin@gmail.com',
        password='Render@123'
    )
    print('Superuser created')
else:
    print('Superuser already exists')
"