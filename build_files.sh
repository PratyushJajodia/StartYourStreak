
set -o errexit
set -o pipefail

pip install -r requirements.txt
python3 manage.py migrate
python3 manage.py collectstatic --noinput
