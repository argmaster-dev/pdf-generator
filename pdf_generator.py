#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF Generator - Генератор PDF документов из CSV/JSON данных и HTML шаблонов
"""

import os
import json
import sys
import glob
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd

# Настройка кодировки для Windows консоли
if sys.platform == 'win32':
    try:
        # Пытаемся установить UTF-8 для консоли Windows
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except:
        # Если не получилось, используем безопасный вывод без эмодзи
        pass

# Попытка импортировать WeasyPrint с обработкой ошибок
try:
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError) as e:
    WEASYPRINT_AVAILABLE = False
    WEASYPRINT_ERROR = str(e)


def get_data_files(data_dir: str) -> List[str]:
    """Получить список всех CSV и JSON файлов в директории data"""
    csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
    json_files = glob.glob(os.path.join(data_dir, "*.json"))
    return sorted(csv_files + json_files)


def get_template_files(templates_dir: str) -> List[str]:
    """Получить список всех HTML шаблонов в директории templates"""
    html_files = glob.glob(os.path.join(templates_dir, "*.html"))
    return sorted(html_files)


def load_data_file(file_path: str) -> List[Dict[str, Any]]:
    """Загрузить данные из CSV или JSON файла"""
    file_ext = os.path.splitext(file_path)[1].lower()
    
    if file_ext == '.csv':
        df = pd.read_csv(file_path, encoding='utf-8')
        # Конвертируем DataFrame в список словарей
        data = df.to_dict('records')
        return data
    elif file_ext == '.json':
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Если это список, возвращаем как есть
            if isinstance(data, list):
                return data
            # Если это словарь, оборачиваем в список
            elif isinstance(data, dict):
                return [data]
            else:
                return []
    else:
        return []


def get_invoice_ids(data: List[Dict[str, Any]]) -> List[str]:
    """Извлечь список invoice id из данных"""
    invoice_ids = []
    for record in data:
        # Пробуем разные варианты названий полей
        invoice_id = (
            record.get('invoice_id') or 
            record.get('invoiceId') or 
            record.get('id') or 
            record.get('invoice') or
            record.get('Invoice ID') or
            record.get('InvoiceID')
        )
        if invoice_id and str(invoice_id) not in invoice_ids:
            invoice_ids.append(str(invoice_id))
    return sorted(invoice_ids)


def get_record_by_invoice_id(data: List[Dict[str, Any]], invoice_id: str) -> Optional[Dict[str, Any]]:
    """Найти запись по invoice id"""
    for record in data:
        invoice_id_field = (
            record.get('invoice_id') or 
            record.get('invoiceId') or 
            record.get('id') or 
            record.get('invoice') or
            record.get('Invoice ID') or
            record.get('InvoiceID')
        )
        if str(invoice_id_field) == str(invoice_id):
            return record
    return None


def render_template(template_path: str, data: Dict[str, Any]) -> str:
    """Подставить данные в HTML шаблон"""
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
    
    # Простая подстановка: {{key}} -> value
    for key, value in data.items():
        placeholder = f'{{{{{key}}}}}'
        # Дробные числа (суммы) — с двумя знаками и пробелом между разрядами: 2 500,50
        if isinstance(value, float):
            value = f'{value:,.2f}'.replace(',', ' ').replace('.', ',')
        template = template.replace(placeholder, str(value))
    
    return template


def generate_pdf(html_content: str, output_path: str):
    """Сгенерировать PDF из HTML с поддержкой кириллицы"""
    if not WEASYPRINT_AVAILABLE:
        error_msg = f"""
[ОШИБКА] WeasyPrint не может быть загружен!

Причина: {WEASYPRINT_ERROR}

Для Windows требуется установить GTK+ библиотеки.

Инструкции по установке:
1. Скачайте установщик GTK+ с:
   https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases
   
2. Или установите через MSYS2:
   https://www.msys2.org/
   Затем выполните: pacman -S mingw-w64-x86_64-gtk3
   
3. Или используйте conda (если установлен):
   conda install -c conda-forge weasyprint

4. После установки перезапустите терминал и попробуйте снова.

Подробнее: https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation
Также см. файл INSTALL_WINDOWS.md для подробных инструкций.
"""
        raise RuntimeError(error_msg)
    
    # CSS для поддержки кириллицы
    # WeasyPrint использует системные шрифты, DejaVu Sans обычно доступен
    css = CSS(string='''
        @page {
            size: A4;
        }
        body {
            font-family: 'DejaVu Sans', 'Liberation Sans', 'Arial Unicode MS', 'Arial', sans-serif;
        }
    ''')
    
    # Используем FontConfiguration для лучшей поддержки шрифтов
    font_config = FontConfiguration()
    
    # Генерируем PDF
    HTML(string=html_content).write_pdf(
        output_path,
        stylesheets=[css],
        font_config=font_config
    )


def open_pdf(file_path: str):
    """Открыть PDF файл в системной программе"""
    import platform
    import subprocess
    
    if platform.system() == 'Windows':
        os.startfile(file_path)
    elif platform.system() == 'Darwin':  # macOS
        subprocess.run(['open', file_path])
    else:  # Linux
        subprocess.run(['xdg-open', file_path])


def print_menu(title: str, items: List[str], start_num: int = 1):
    """Вывести красивое меню с нумерацией"""
    try:
        print(f"\n{'='*50}")
        print(f"  {title}")
        print(f"{'='*50}")
        for i, item in enumerate(items, start=start_num):
            filename = os.path.basename(item)
            print(f"  {i}. {filename}")
        print(f"{'='*50}\n")
    except UnicodeEncodeError:
        # Fallback для консолей без поддержки UTF-8
        print(f"\n{'='*50}")
        print(f"  {title.encode('ascii', 'replace').decode('ascii')}")
        print(f"{'='*50}")
        for i, item in enumerate(items, start=start_num):
            filename = os.path.basename(item)
            print(f"  {i}. {filename}")
        print(f"{'='*50}\n")


def get_user_choice(prompt: str, max_choice: int) -> int:
    """Получить выбор пользователя с валидацией"""
    while True:
        try:
            choice = input(f"{prompt} (1-{max_choice}): ").strip()
            choice_num = int(choice)
            if 1 <= choice_num <= max_choice:
                return choice_num
            else:
                print(f"[ОШИБКА] Пожалуйста, введите число от 1 до {max_choice}")
        except ValueError:
            print("[ОШИБКА] Пожалуйста, введите корректное число")
        except KeyboardInterrupt:
            print("\n\nПрограмма прервана пользователем")
            sys.exit(0)


def main():
    """Основная функция"""
    # Определяем пути к директориям
    base_dir = Path(__file__).parent
    data_dir = base_dir / "data"
    templates_dir = base_dir / "templates"
    output_dir = base_dir / "output"
    
    # Создаем директории, если их нет
    data_dir.mkdir(exist_ok=True)
    templates_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)
    
    # Проверяем доступность WeasyPrint в начале
    if not WEASYPRINT_AVAILABLE:
        print("\n" + "="*70)
        print("  ОШИБКА: WeasyPrint не может быть загружен!")
        print("="*70)
        print(f"\nПричина: {WEASYPRINT_ERROR}")
        print("\nДля Windows требуется установить GTK+ библиотеки.")
        print("\nИнструкции по установке:")
        print("1. Скачайте установщик GTK+ с:")
        print("   https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases")
        print("\n2. Или установите через MSYS2:")
        print("   https://www.msys2.org/")
        print("   Затем выполните: pacman -S mingw-w64-x86_64-gtk3")
        print("\n3. Или используйте conda (если установлен):")
        print("   conda install -c conda-forge weasyprint")
        print("\nПодробнее: https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation")
        print("\nТакже см. файл INSTALL_WINDOWS.md для подробных инструкций.")
        print("="*70 + "\n")
        return
    
    print("\n" + "="*50)
    print("  PDF Generator - Генератор PDF документов")
    print("="*50)
    
    # Получаем списки файлов
    data_files = get_data_files(str(data_dir))
    template_files = get_template_files(str(templates_dir))
    
    # Проверяем наличие файлов
    if not data_files:
        print(f"\n[ОШИБКА] Не найдено файлов данных в директории {data_dir}")
        print("   Пожалуйста, добавьте CSV или JSON файлы в папку /data")
        return
    
    if not template_files:
        print(f"\n[ОШИБКА] Не найдено HTML шаблонов в директории {templates_dir}")
        print("   Пожалуйста, добавьте HTML файлы в папку /templates")
        return
    
    # Выводим меню выбора файла данных
    print_menu("Доступные файлы с данными", data_files)
    data_choice = get_user_choice("Выберите файл данных", len(data_files))
    selected_data_file = data_files[data_choice - 1]
    
    # Выводим меню выбора шаблона
    print_menu("Доступные HTML шаблоны", template_files)
    template_choice = get_user_choice("Выберите HTML шаблон", len(template_files))
    selected_template = template_files[template_choice - 1]
    
    # Загружаем данные
    print(f"\nЗагрузка данных из {os.path.basename(selected_data_file)}...")
    data = load_data_file(selected_data_file)
    
    if not data:
        print("[ОШИБКА] Не удалось загрузить данные или файл пуст")
        return
    
    # Получаем список invoice id
    invoice_ids = get_invoice_ids(data)
    
    if not invoice_ids:
        print("[ОШИБКА] Не найдено invoice id в данных")
        print("   Убедитесь, что в данных есть поле: invoice_id, invoiceId, id, invoice, Invoice ID или InvoiceID")
        return
    
    # Выводим меню выбора invoice
    print_menu("Доступные чеки (Invoice ID)", invoice_ids)
    invoice_choice = get_user_choice("Выберите invoice ID", len(invoice_ids))
    selected_invoice_id = invoice_ids[invoice_choice - 1]
    
    # Находим запись по invoice id
    record = get_record_by_invoice_id(data, selected_invoice_id)
    
    if not record:
        print(f"[ОШИБКА] Не найдена запись с invoice id = {selected_invoice_id}")
        return
    
    # Генерируем HTML из шаблона
    print(f"\nГенерация HTML из шаблона...")
    html_content = render_template(selected_template, record)
    
    # Генерируем PDF
    output_filename = f"invoice_{selected_invoice_id}.pdf"
    output_path = output_dir / output_filename
    print(f"Генерация PDF...")
    
    try:
        generate_pdf(html_content, str(output_path))
        print(f"[УСПЕХ] PDF успешно создан: {output_path}")
        
        # Открываем PDF
        print(f"Открытие PDF в системной программе...")
        open_pdf(str(output_path))
        print(f"Готово!")
        
    except Exception as e:
        print(f"[ОШИБКА] Ошибка при генерации PDF: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
