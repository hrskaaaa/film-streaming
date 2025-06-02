1. Клонування репозиторію

```bash
git clone https://github.com/your-username/filmstreaming.git
cd filmstreaming

2. Створення та активація віртуального середовища
python -m venv venv
source venv/bin/activate  # або venv\Scripts\activate на Windows

3. Встановлення залежностей
pip install -r requirements.txt

4. Міграції та запуск сервера
python manage.py makemigrations
python manage.py migrate
python manage.py runserver

Перейдіть у браузері на http://127.0.0.1:8000
