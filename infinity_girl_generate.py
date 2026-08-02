import time
from gemini_exp import random_person_generate, generate_person

txt = input("Введите предпачитаемую девушку, или введите число для генерации рандомных девушек\n> ")
try:
    int(txt)
    for i in range(int(txt)):
        prompt = random_person_generate()
    try:
        print(prompt)
        print(generate_person(prompt))
    except Exception as e:
        print(e)
        
    time.sleep(10)
    
except:
    prompt = txt
    try:
        print(prompt)
        print(generate_person(prompt))
    except Exception as e:
        print(e)
