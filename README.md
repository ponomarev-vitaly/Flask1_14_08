# Инструкция по запуску проекта

1. python3 -m venv <venv_name>
2. source venv_name/bin/activate
3. pip install -r requirements.txt
4. flask db upgrade
5. python app.py

# Миграции

1. flask db migrate -m "...."
2. flask db upgrade