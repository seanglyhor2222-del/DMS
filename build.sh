#!/usr/bin/env bash

pip install -r requirements.txt

python manage.py collectstatic --noinput

python manage.py migrate

python manage.py loaddata accounts.json
python manage.py loaddata activities.json
python manage.py loaddata reports.json
python manage.py loaddata workflows.json