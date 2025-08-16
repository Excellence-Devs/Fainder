#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки системы сериализации/десериализации
классов ChatMessage и FileAttachment
"""

import sys
import os
import json
import time
from datetime import datetime

# Добавляем путь к основному файлу
sys.path.append('.')

# Импортируем необходимые классы из основного файла
try:
    from fainder_test import (
        FileType, FileAttachment, StickerAttachment, GifAttachment,
        VideoCircleAttachment, AudioMessageAttachment, VideoAttachment,
        AudioAttachment, ImageAttachment, DocumentAttachment,
        FileOtherAttachment, ChatMessage, save_chat_history, load_chat_history
    )
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    print("Убедитесь, что файл fainder_test.py находится в текущей директории")
    sys.exit(1)

def test_file_attachments():
    """Тестирование сериализации FileAttachment классов"""
    print("=== Тестирование FileAttachment классов ===")
    
    # Тестируем различные типы вложений
    attachments = [
        StickerAttachment("sticker.png", 1024, "http://example.com/sticker.png"),
        GifAttachment("animation.gif", 2048, "http://example.com/animation.gif"),
        VideoCircleAttachment("video.mp4", 5120, "http://example.com/video.mp4", 30),
        AudioMessageAttachment("audio.mp3", 1536, "http://example.com/audio.mp3"),
        VideoAttachment("movie.mp4", 10240, "http://example.com/movie.mp4"),
        AudioAttachment("song.mp3", 3072, "http://example.com/song.mp3"),
        DocumentAttachment("document.pdf", 4096, "http://example.com/document.pdf"),
        FileOtherAttachment("archive.zip", 8192, "http://example.com/archive.zip"),
        ImageAttachment("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==", 2560, "http://example.com/photo.jpg")
    ]
    
    for i, attachment in enumerate(attachments):
        print(f"\nТест {i+1}: {attachment.__class__.__name__}")
        
        # Сериализация
        try:
            serialized = attachment.to_dict()
            print(f"  ✓ Сериализация успешна: {serialized['class_name']}")
        except Exception as e:
            print(f"  ✗ Ошибка сериализации: {e}")
            continue
        
        # Десериализация
        try:
            attachment_class = globals()[serialized['class_name']]
            deserialized = attachment_class.from_dict(serialized)
            print(f"  ✓ Десериализация успешна")
            
            # Проверяем основные атрибуты
            assert deserialized.file_name == attachment.file_name
            assert deserialized.file_size == attachment.file_size
            assert deserialized.url == attachment.url
            assert deserialized.file_type == attachment.file_type
            print(f"  ✓ Атрибуты совпадают")
            
        except Exception as e:
            print(f"  ✗ Ошибка десериализации: {e}")

def test_chat_messages():
    """Тестирование сериализации ChatMessage"""
    print("\n=== Тестирование ChatMessage ===")
    
    # Создаем тестовые сообщения
    messages = []
    
    # Текстовое сообщение пользователя
    msg1 = ChatMessage(
        id="msg_1",
        content="Привет! Как дела?",
        is_user=True,
        is_text=True,
        time=time.time()
    )
    messages.append(msg1)
    
    # Ответ системы
    msg2 = ChatMessage(
        id="msg_2",
        content="Привет! У меня все отлично, спасибо!",
        is_user=False,
        is_text=True,
        time=time.time(),
        reply_to=msg1
    )
    messages.append(msg2)
    
    # Сообщение с файлом
    image_attachment = ImageAttachment(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
        1024, "http://example.com/image.jpg"
    )
    msg3 = ChatMessage(
        id="msg_3",
        content=image_attachment,
        is_user=True,
        is_file=True,
        is_text=False,
        time=time.time()
    )
    messages.append(msg3)
    
    # Системное сообщение
    msg4 = ChatMessage(
        id="msg_4",
        content="Пользователь подключился к чату",
        is_system=True,
        time=time.time()
    )
    messages.append(msg4)
    
    # Тестируем каждое сообщение
    for i, message in enumerate(messages):
        print(f"\nТест сообщения {i+1}: {message.__class__.__name__} (ID: {message.id})")
        
        # Сериализация
        try:
            serialized = message.to_dict()
            print(f"  ✓ Сериализация успешна")
        except Exception as e:
            print(f"  ✗ Ошибка сериализации: {e}")
            continue
        
        # Десериализация
        try:
            deserialized = ChatMessage.from_dict(serialized)
            print(f"  ✓ Десериализация успешна")
            
            # Проверяем основные атрибуты
            assert deserialized.id == message.id
            assert deserialized.is_user == message.is_user
            assert deserialized.is_system == message.is_system
            assert deserialized.is_file == message.is_file
            assert deserialized.is_text == message.is_text
            print(f"  ✓ Атрибуты совпадают")
            
        except Exception as e:
            print(f"  ✗ Ошибка десериализации: {e}")
    
    return messages

def test_chat_history_functions(messages):
    """Тестирование функций save_chat_history и load_chat_history"""
    print("\n=== Тестирование функций истории чата ===")
    
    test_chat_id = "test_chat_123"
    
    # Тестируем сохранение
    try:
        save_chat_history(test_chat_id, messages)
        print(f"  ✓ Сохранение истории чата успешно")
        
        # Проверяем, что файл создался
        if os.path.exists(f"chats/{test_chat_id}.json"):
            print(f"  ✓ Файл chats/{test_chat_id}.json создан")
        else:
            print(f"  ✗ Файл chats/{test_chat_id}.json не найден")
            return
            
    except Exception as e:
        print(f"  ✗ Ошибка сохранения: {e}")
        return
    
    # Тестируем загрузку
    try:
        loaded_messages = load_chat_history(test_chat_id)
        print(f"  ✓ Загрузка истории чата успешна")
        print(f"  ✓ Загружено {len(loaded_messages)} сообщений")
        
        # Проверяем количество сообщений
        if len(loaded_messages) == len(messages):
            print(f"  ✓ Количество сообщений совпадает")
        else:
            print(f"  ✗ Количество сообщений не совпадает: {len(loaded_messages)} != {len(messages)}")
        
        # Проверяем reply_to связи
        reply_found = False
        for msg in loaded_messages:
            if msg.reply_to is not None:
                reply_found = True
                print(f"  ✓ Найдена reply_to связь: {msg.id} -> {msg.reply_to.id}")
                break
        
        if not reply_found:
            print(f"  ! Reply_to связи не найдены (это нормально, если их не было)")
        
    except Exception as e:
        print(f"  ✗ Ошибка загрузки: {e}")
    
    # Очищаем тестовый файл
    try:
        if os.path.exists(f"chats/{test_chat_id}.json"):
            os.remove(f"chats/{test_chat_id}.json")
            print(f"  ✓ Тестовый файл удален")
    except Exception as e:
        print(f"  ! Не удалось удалить тестовый файл: {e}")

def main():
    """Основная функция тестирования"""
    print("Запуск тестов системы сериализации/десериализации")
    print(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        # Тестируем FileAttachment классы
        test_file_attachments()
        
        # Тестируем ChatMessage
        messages = test_chat_messages()
        
        # Тестируем функции истории чата
        test_chat_history_functions(messages)
        
        print("\n" + "=" * 60)
        print("✓ Все тесты завершены!")
        
    except Exception as e:
        print(f"\n✗ Критическая ошибка во время тестирования: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()