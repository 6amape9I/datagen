from google import genai
import os

# Настройте ваш API ключ.
# Лучший способ - использовать переменную окружения.
# Или замените 'os.environ["GOOGLE_API_KEY"]' на ваш ключ в кавычках: "YOUR_API_KEY"
client = genai.Client(api_key="AIzaSyClKGzofOhWAXkx171s2QmDSwz85PIB-wU")

print("Все доступные модели:")
model_names = client.models.list()
for name in model_names:
  print(name.name)