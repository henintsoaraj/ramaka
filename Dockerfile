FROM python:3.12-slim

WORKDIR /app

# 1. D'abord les dépendances seules (couche réutilisée si elles ne changent pas)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Ensuite le code
COPY . .

# 3. Un utilisateur sans privilèges
RUN useradd --create-home ramaka
USER ramaka

EXPOSE 8000
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]