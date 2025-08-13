from PIL import Image, ImageEnhance

def process_image(input_path, output_path):
    # Открываем изображение
    img = Image.open(input_path).convert('RGB')

    # 1. Делаем бледным (понижаем контраст и насыщенность)
    img = ImageEnhance.Color(img).enhance(0.7)  # Меньше насыщенности
    img = ImageEnhance.Contrast(img).enhance(0.9)  # Меньше контраста

    # 2. Сжимаем (JPEG с низким качеством)
    temp_path = output_path
    img.save(temp_path, "JPEG", quality=30)

# Пример использования:
process_image("input.png", "output.jpg")
