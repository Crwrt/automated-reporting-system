#!/usr/bin/env python3
import subprocess
import sys
import os               # стандартная библиотека python для работы с операционной системой
import smtplib
import requests
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# Получаем абсолютный путь к папке проекта, , где находится этот скрипт
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Подробнее:
# __file__ - специальная встроенна переменная python, содержит путь к текущему файлу скрипта
# os.path.abspath(__file__) - преобразует в абсолютный путь (например: '/opt/csv_to_pdf/generate_all_reports.py') - ФУНКЦИЯ БИЛИОТЕКИ os
# os.path.dirname() - получает директорию из пути (убирает имя файла, оставляет '/opt/csv_to_pdf/') - ФУНКЦИЯ БИЛИОТЕКИ os
# Итог: BASE_DIR = '/opt/csv_to_pdf/' - папка где лежит наша программа

# Конфигурация групп
GROUPS = {
    'cameras_oks': {                                                        # os.path.join() ниже объединяет BASE_DIR и относительный путь
        'sh_script': os.path.join(BASE_DIR, 'scripts/generate_oks_csv.sh'), 
        'csv_file': os.path.join(BASE_DIR, 'csv/cameras_oks.csv'),
        'pdf_prefix': 'cameras_oks',
        'group_name_display': 'ОКС',                                        # Отображаемое название группы
        'emails': ['usr1@group1.com', 'usr2@group1.com', 'usr3@group1.com'] # email адреса пользователей группы oks
    },
    'cameras_school': {
        'sh_script': os.path.join(BASE_DIR, 'scripts/generate_school_csv.sh'), 
        'csv_file': os.path.join(BASE_DIR, 'csv/cameras_school.csv'),
        'pdf_prefix': 'cameras_school',
        'group_name_display': 'Школы',                                      # Отображаемое название группы
        'emails': ['usr1@group2.com', 'usr2@group2.com', 'usr3@group2.com'] # email адреса пользователей группы school
    },
    'cameras_gorsvet': {
        'sh_script': os.path.join(BASE_DIR, 'scripts/generate_gorsvet_csv.sh'),
        'csv_file': os.path.join(BASE_DIR, 'csv/cameras_gorsvet.csv'),
        'pdf_prefix': 'cameras_gorsvet',
        'group_name_display': 'Горсвет',
        'emails': ['usr1@group3.com', 'usr2@group3.com', 'usr3@group3.com'] # email адреса пользователей группы gorsvet
    }
}

# Настройки вашего SMTP сервера
SMTP_CONFIG = {
    'server': 'smtp.your-server.com',         # Адрес вашего SMTP сервера
    'port': 465,                              # Порт для SSL
    'username': 'your-email@example.com',     # Ваш email @arhtc.ru
    'password': 'your-password-here',         # Ваш пароль от email
    # 'from_name': 'Администратор Системы',   # Ваше имя которое будет отображаться
    'use_tls': False,                         # Не использовать TLS (используем SSL)
    'use_ssl': True                           # Использовать SSL шифрование
}

# Настройки Telegram бота
TELEGRAM_CONFIG = {
    'bot_token': '123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew23',  	                    # Токен вашего бота, можно узнать у @BotFather
    'chat_id': '-1001234567898'        					                                    # ID чата или канала
}

def send_telegram_message(message):     # функция отправки сообщений в телеграмм
    """Отправляет сообщение в Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_CONFIG['bot_token']}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CONFIG['chat_id'],
            'text': message,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, data=payload, timeout=10)
        if response.status_code == 200:
            print("[SUCCESS] Уведомление отправлено в Telegram")
            return True
        else:
            print(f"[ERROR] Ошибка Telegram API: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Ошибка отправки в Telegram: {e}")
        return False

def send_email(to_emails, subject, body, attachment_path=None):  #функция отправки сообщейни по email
    """Отправляет email с вложением"""
    try:
        # Создаем сообщение
        msg = MIMEMultipart()
        msg['From'] = SMTP_CONFIG['username']
        msg['To'] = ', '.join(to_emails)
        msg['Subject'] = subject
        
        # Добавляем текст письма
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Добавляем вложение если указано
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as file:
                part = MIMEApplication(file.read(), Name=os.path.basename(attachment_path))
            part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
            msg.attach(part)
            print(f"[INFO] Вложение добавлено: {os.path.basename(attachment_path)}")
        
        # Подключаемся к SMTP серверу с SSL
        print(f"[INFO] Подключение к SMTP серверу {SMTP_CONFIG['server']}:{SMTP_CONFIG['port']}...")
        server = smtplib.SMTP_SSL(SMTP_CONFIG['server'], SMTP_CONFIG['port'])
        
        # Логинимся
        print(f"[INFO] Аутентификация пользователя {SMTP_CONFIG['username']}...")
        server.login(SMTP_CONFIG['username'], SMTP_CONFIG['password'])
        
        # Отправляем письмо
        print(f"[INFO] Отправка письма на {len(to_emails)} адресов...")
        server.send_message(msg)
        server.quit()
        
        print(f"[SUCCESS] Email отправлен на {len(to_emails)} адресов")
        return True
        
    except Exception as e:
        print(f"[ERROR] Ошибка отправки email: {e}")
        return False

def run_command(command, description):
    """Запускает команду и обрабатывает ошибки"""
    print(f"[INFO] {description}...")
    try:
       # Для Python 3.6 используем Popen вместо capture_output
        result = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            universal_newlines=True  # аналог text=True
        )
        print(f"[SUCCESS] {description} завершено успешно")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Ошибка при {description}: {e}")
        if e.stderr:
            print(f"Детали: {e.stderr}")
        return False

def generate_group_report(group_name, config):
    """Генерирует отчет для одной группы и возвращает данные для email"""
    print(f"\n" + "="*60)
    print(f"ОБРАБОТКА ГРУППЫ: {group_name}")
    print("="*60)
    
    timestamp = datetime.now().strftime('%d%m%Y_%H%M')
    csv_file = config['csv_file']
    pdf_file = f"pdf/{config['pdf_prefix']}_{timestamp}.pdf"
    
    # Шаг 1: Генерация CSV
    if not run_command(config['sh_script'], f"Генерация CSV для {group_name}"):
        return None
    
    # Проверяем что CSV файл создался
    if not os.path.exists(csv_file):
        print(f"[ERROR] CSV файл не найден: {csv_file}")
        return None

    # Подсчитываем количество неработающих камер (строки без заголовка)
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # Вычитаем 1 для заголовка, если файл не пустой
            broken_cameras_count = len(lines) - 1 if len(lines) > 0 else 0
        print(f"[INFO] Неработающих камер: {broken_cameras_count}")
    except Exception as e:
        print(f"[ERROR] Ошибка подсчета камер: {e}")
        broken_cameras_count = 0
    
    # Шаг 2: Конвертация в PDF
    if not run_command(f"python3 {os.path.join(BASE_DIR, 'csv_to_pdf.py')} {csv_file} {pdf_file}", f"Конвертация {group_name} в PDF"):
        return None
    
    print(f"[SUCCESS] Отчет для {group_name} создан: {pdf_file}")

    # Возвращаем данные для email
    return {
        'pdf_file': pdf_file,
        'broken_cameras_count': broken_cameras_count,
        'group_name_display': config['group_name_display']
    }

def main():
    # Создаем директории если их нет
    os.makedirs('scripts', exist_ok=True)
    os.makedirs('csv', exist_ok=True)
    os.makedirs('pdf', exist_ok=True)

    current_date = datetime.now().strftime('%d.%m.%Y')
    current_time = datetime.now().strftime('%H:%M')
    
    print("ЗАПУСК ГЕНЕРАЦИИ И ОТПРАВКИ ОТЧЕТОВ")
    print(f"Время запуска: {current_date} {current_time}")
    print(f"Отправка от: {SMTP_CONFIG['username']}")

    # Отправляем уведомление о начале работы
    start_message = f"🚀 <b>Запуск генерации отчетов</b>\n📅 {current_date} {current_time}\n\nНачинаю обработку {len(GROUPS)} групп..."
    send_telegram_message(start_message)
    
    success_count = 0
    failed_groups = []
    detailed_results = []
    
    # Обрабатываем каждую группу
    for group_name, config in GROUPS.items():
        report_data = generate_group_report(group_name, config)
        
        # Проверяем что report_data - это словарь, а не True/False
        if report_data and isinstance(report_data, dict):
            # Шаг 3: Отправка email с вашим шаблоном
            subject = f"Неработающие камеры {current_date} {report_data['group_name_display']}"
            
            body = f"""На {current_date} {report_data['broken_cameras_count']} камер не передают сигнал.

Подробный отчет во вложении.

Отчет сгенерирован: {current_date} {current_time}"""
            
            print(f"[INFO] Отправка отчета {group_name} на {len(config['emails'])} адресов...")
            
            if send_email(config['emails'], subject, body, report_data['pdf_file']):
                print(f"[SUCCESS] Отчет {group_name} отправлен успешно")
                success_count += 1
                detailed_results.append(f"✅ {report_data['group_name_display']}: {report_data['broken_cameras_count']} камер")
            else:
                print(f"[ERROR] Ошибка отправки отчета {group_name}")
                failed_groups.append(group_name)
                detailed_results.append(f"❌ {report_data['group_name_display']}: ошибка отправки")
        else:
            print(f"[ERROR] Ошибка генерации отчета для {group_name}")
            failed_groups.append(group_name)
            detailed_results.append(f"❌ {config['group_name_display']}: ошибка генерации")

    # Формируем итоговое сообщение для Telegram
    if success_count == len(GROUPS):
        status_icon = "✅"
        status_text = "УСПЕШНО"
    elif success_count > 0:
        status_icon = "⚠️"
        status_text = "ЧАСТИЧНО УСПЕШНО"
    else:
        status_icon = "❌"
        status_text = "С ОШИБКАМИ"
    
    results_text = "\n".join(detailed_results)
    summary_message = f"""
{status_icon} <b>Отчеты сгенерированы {status_text}</b>
Результаты:
{results_text}

✅ Успешно: {success_count}/{len(GROUPS)}
🕒 Завершено: {datetime.now().strftime('%H:%M')}
"""
    
    # Отправляем итоговое уведомление в Telegram
    send_telegram_message(summary_message)
    
    # Итоги
    print(f"\n" + "="*60)
    print("ИТОГИ ГЕНЕРАЦИИ ОТЧЕТОВ:")
    print(f"Успешно: {success_count}/{len(GROUPS)}")
    if failed_groups:
        print(f"С ошибками: {', '.join(failed_groups)}")
    print("="*60)

if __name__ == "__main__":
    main()
