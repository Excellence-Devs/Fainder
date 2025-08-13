import time
from gemini_exp import random_person_generate, generate_person


# while True:
#     prompt = random_person_generate()
#     try:
#         print(prompt)
#         print(generate_person(prompt))
#     except Exception as e:
#         print(e)
#         break
        
#     time.sleep(10)
    
prompt = "Нужен тестовый девушка бот, который будет польностью подчиняться пользователю, для теста приложения и его функций"
try:
    print(prompt)
    print(generate_person(prompt))
except Exception as e:
    print(e)
