import pandas as pd
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import csv
from datetime import datetime
import sys
import os

# Регистрируем шрифт с поддержкой русского языка
pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
main_font = 'DejaVuSans'
bold_font = 'DejaVuSans-Bold'

def format_datetime(datetime_str):
    """
    Функция для форматирования даты и времени
    Преобразует время в формат с ведущим нулем для часов (02:12 вместо 2:12)
    """
    try:
        # Пробуем разные форматы даты
        dt = datetime.strptime(datetime_str, '%d.%m.%Y %H:%M')
        return dt.strftime('%d.%m.%Y %H:%M')
    except ValueError:
        try:
            dt = datetime.strptime(datetime_str, '%d.%m.%Y %H:%M:%S')
            return dt.strftime('%d.%m.%Y %H:%M')
        except ValueError:
            try:
                dt = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
                return dt.strftime('%d.%m.%Y %H:%M')
            except:
                # Если не удалось распарсить, возвращаем исходную строку
                return datetime_str

def wrap_text(text, max_length=40):
    """Переносит длинный текст на несколько строк"""
    if not isinstance(text, str):
        text = str(text)
    
    if len(text) <= max_length:
        return text
    
    # Разбиваем текст на слова
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        if len(current_line + " " + word) <= max_length:
            current_line += " " + word if current_line else word
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    return "\n".join(lines)

def get_column_widths(data):
    """Автоматически определяет ширину столбцов"""
    if not data:
        return [100, 200, 100]  # Значения по умолчанию
    
    num_cols = len(data[0])
    col_widths = []
    
    for col_idx in range(num_cols):
        max_len = 0
        for row in data:
            if col_idx < len(row):
                cell_content = str(row[col_idx])
                # Учитываем длину текста
                text_length = len(cell_content) * 5
                max_len = max(max_len, text_length)
        
        # Устанавливаем разумные пределы для ширины столбцов
        if col_idx == 0:  # ID камеры
            width = 80
        elif col_idx == 1:  # Название камеры
            width = min(max(100, max_len), 250)  # Шире для названий
        else:  # Дата
            width = 100
        
        col_widths.append(width)
    
    return col_widths

def csv_to_pdf(csv_file, pdf_file):
    # Читаем CSV файл с указанием кодировки и разделителем - точкой с запятой
    df = pd.read_csv(csv_file, encoding='utf-8', delimiter=';')
    
    # ЗАМЕНЯЕМ НАЗВАНИЯ СТОЛБЦОВ НА РУССКИЕ
    df = df.rename(columns={
        'CameraID': 'ID камеры',
        'CameraName': 'Камера', 
        'NotAvailable': 'Дата'
    })
    
    # ФОРМАТИРУЕМ ДАТУ В ТРЕТЬЕМ СТОЛБЦЕ
    df['Дата'] = df['Дата'].apply(format_datetime)
    
    # ОБРАБАТЫВАЕМ ДЛИННЫЕ НАЗВАНИЯ КАМЕР - ПЕРЕНОСИМ НА НЕСКОЛЬКО СТРОК
    df['Камера'] = df['Камера'].apply(wrap_text)

    # Создаем PDF документ
    doc = SimpleDocTemplate(pdf_file, pagesize=A4)
    
    # Подготавливаем данные для таблицы
    data = [df.columns.tolist()] + df.values.tolist()
    
    # ОПРЕДЕЛЯЕМ ШИРИНУ СТОЛБЦОВ
    col_widths = get_column_widths(data)
    
    # Создаем таблицу с автоматическим определением ширины столбцов
    table = Table(data, repeatRows=1)  # repeatRows=1 повторяет заголовки на каждой странице
    
    # Стилизуем таблицу
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), bold_font),  # Жирный шрифт для заголовков таблицы
        ('FONTNAME', (0, 1), (-1, -1), main_font),  # Основной шрифт для данных
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Выравнивание по вертикали по центру
        ('WORDWRAP', (0, 0), (-1, -1)),  # Включаем перенос слов
    ])
    table.setStyle(style)
    
    # Собираем документ
    elements = []
    
    # Добавляем заголовок с русским шрифтом
    styles = getSampleStyleSheet()
    styles['Heading2'].fontName = bold_font  # Устанавливаем русский шрифт для заголовка
    title = Paragraph(f"Отчет от {datetime.now().strftime('%d-%m-%Y %H:%M')}", styles['Heading2'])
    elements.append(title)
    elements.append(table)
    
    doc.build(elements)

if __name__ == "__main__":
    # Проверяем аргументы командной строки
    if len(sys.argv) != 3:
        print("Использование: python3 csv_to_pdf.py входной.csv выходной.pdf")
        print("Пример: python3 csv_to_pdf.py отчет.csv отчет.pdf")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    # Проверяем существование входного файла
    if not os.path.exists(input_file):
        print(f"Ошибка: файл {input_file} не найден")
        sys.exit(1)
    
    # Вызываем функцию конвертации
    csv_to_pdf(input_file, output_file)
    print(f"Успешно сконвертирован {input_file} в {output_file}")
