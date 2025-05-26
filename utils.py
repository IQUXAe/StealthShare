# StealthShare v0.1 pre1
# Copyright (c) 2025 IQUXAe
# Released under the MIT License. See LICENSE file for details.

import os
import logging
import sys
import locale 

logger = logging.getLogger("StealthShareApp")

FILE_CATEGORIES = {
    "Images": ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.gif', '.webp', '.bmp'],
    "Documents": ['.docx', '.xlsx', '.pptx'],
    "PDF": ['.pdf']
}

LANGUAGES = {
    "ru": {
        "app_title_suffix": "Очистка метаданных",
        "author_credit": "Разработано IQUXAe",
        "status_ready": "Готов к работе",
        "options_title": "Настройки очистки",
        "profile_label": "Профиль очистки:",
        "preserve_icc_label": "Сохранить ICC профиль (для цвета)",
        "sort_by_type_label": "Распределить по папкам вывода",
        "info_title": "Информация",
        "supported_ext_label": "Поддерживаемые расширения:",
        "file_handling_title": "Файлы для очистки",
        "drop_target_label": "Добавьте файлы кнопкой:", 
        "add_files_button": "Добавить файлы...",
        "clear_list_button": "Очистить список",
        "output_dir_label": "Сохранить в:",
        "browse_button": "Обзор...",
        "start_button": "🚀 Начать очистку",
        "processing_button": "⏳ Обработка...",
        "status_files_added": "Добавлено {count} файлов. Всего в списке: {total}.",
        "status_files_not_added": "Новые файлы не добавлены (возможно, уже в списке).",
        "status_list_cleared": "Список файлов очищен.",
        "status_output_dir_selected": "Папка для сохранения: {folder}",
        "status_processing_start": "Начата обработка {count} файлов...",
        "status_processing_file": "Обработка ({current}/{total}): {filename}...",
        "status_completed_summary": "Обработка завершена. Успешно: {success_count} из {total_files}.",
        "status_completed_with_errors": "Обработка завершена. Успешно: {success_count} из {total_files}. Ошибок: {error_count}.",
        "status_no_files_to_process": "Файлы для обработки не были выбраны.",
        "dialog_no_files_title": "Файлы не выбраны",
        "dialog_no_files_message": "Пожалуйста, добавьте файлы для очистки в список.",
        "dialog_no_output_dir_title": "Папка не выбрана",
        "dialog_no_output_dir_message": "Пожалуйста, выберите папку для сохранения.",
        "dialog_output_dir_error_title": "Ошибка папки",
        "dialog_output_dir_error_message": "Папка '{folder}' не существует и не может быть создана: {error}",
        "dialog_report_title_success": "Завершено успешно",
        "dialog_report_title_errors": "Завершено с ошибками",
        "dialog_report_errors_label": "Файлы с ошибками:",
        "dialog_button_ok": "OK",
        "profile_standard_name": "Стандартный",
        "profile_standard_desc": "Удаляет основную приватную информацию (EXIF геолокацию, данные об авторе), сохраняет совместимость.",
        "profile_aggressive_name": "Агрессивный",
        "profile_aggressive_desc": "Пытается удалить максимум метаданных, включая XMP, IPTC, все чанки PNG. Может повлиять на некоторые специфические функции файлов.",
        "profile_exif_only_name": "Только EXIF (для фото)",
        "profile_exif_only_desc": "Удаляет только EXIF-данные из изображений, остальное не трогает.",
        "error_browse_files_title": "Ошибка выбора файлов",
        "error_browse_files_message": "Не удалось открыть диалог: {error}",
        "error_browse_output_dir_title": "Ошибка выбора папки",
        "error_browse_output_dir_message": "Не удалось открыть диалог: {error}",
        "icon_load_warning": "Файл иконки '{icon_name}' не найден по пути: {icon_path}",
        "icon_tcl_error": "Ошибка TclError при установке иконки '{icon_name}': {error}",
        "icon_unknown_error": "Непредвиденная ошибка при установке иконки: {error}",
        "theme_warning": "Не удалось применить предпочтительную тему ttk.",
        "app_run_log": "StealthShare {app_version} запущен. Язык: {lang}. Тема: {theme}",
        "profile_change_log": "Выбран профиль очистки: {profile_name}",
        "files_added_log": "Добавлено {new_files_count} новых файлов. Всего: {total_count}",
        "list_cleared_log": "Список выбранных файлов очищен.",
        "output_dir_selected_log": "Выбрана папка для сохранения: {folder}",
        "batch_start_log": "--- НАЧАЛО ПАКЕТНОЙ ОЧИСТКИ ({count} файлов) ---",
        "file_skipped_not_found_log": "Файл '{filename}' пропущен (не найден).",
        "cleaned_name_error_log": "Не удалось сгенерировать имя для очищенного файла: {filename}",
        "file_processed_success_log": "Успешно обработан: {filename_in} -> {filename_out}",
        "file_processed_error_log": "Ошибка при обработке: {filename}",
        "file_critical_error_log": "Крит. ошибка при очистке '{filename}': {error}",
        "batch_finish_log": "--- ПАКЕТНАЯ ОБРАБОТКА ЗАВЕРШЕНА --- {summary}"

    },
    "en": {
        "app_title_suffix": "Metadata Cleaner",
        "author_credit": "Developed by IQUXAe",
        "status_ready": "Ready",
        "options_title": "Cleaning Settings",
        "profile_label": "Cleaning Profile:",
        "preserve_icc_label": "Preserve ICC Profile (for colors)",
        "sort_by_type_label": "Sort output into subfolders",
        "info_title": "Information",
        "supported_ext_label": "Supported Extensions:",
        "file_handling_title": "Files to Clean",
        "drop_target_label": "Add files using the button:", 
        "add_files_button": "Add Files...",
        "clear_list_button": "Clear List",
        "output_dir_label": "Save to:",
        "browse_button": "Browse...",
        "start_button": "🚀 Start Cleaning",
        "processing_button": "⏳ Processing...",
        "status_files_added": "Added {count} file(s). Total in list: {total}.",
        "status_files_not_added": "No new files added (possibly already in list).",
        "status_list_cleared": "File list cleared.",
        "status_output_dir_selected": "Output folder selected: {folder}",
        "status_processing_start": "Started processing {count} file(s)...",
        "status_processing_file": "Processing ({current}/{total}): {filename}...",
        "status_completed_summary": "Processing complete. Successful: {success_count} of {total_files}.",
        "status_completed_with_errors": "Processing complete. Successful: {success_count} of {total_files}. Errors: {error_count}.",
        "status_no_files_to_process": "No files were selected for processing.",
        "dialog_no_files_title": "No Files Selected",
        "dialog_no_files_message": "Please add files to the list for cleaning.",
        "dialog_no_output_dir_title": "No Output Folder",
        "dialog_no_output_dir_message": "Please select an output folder.",
        "dialog_output_dir_error_title": "Folder Error",
        "dialog_output_dir_error_message": "Folder '{folder}' does not exist and cannot be created: {error}",
        "dialog_report_title_success": "Completed Successfully",
        "dialog_report_title_errors": "Completed with Errors",
        "dialog_report_errors_label": "Files with errors:",
        "dialog_button_ok": "OK",
        "profile_standard_name": "Standard",
        "profile_standard_desc": "Removes common private information (EXIF geolocation, author data), maintains compatibility.",
        "profile_aggressive_name": "Aggressive",
        "profile_aggressive_desc": "Attempts to remove maximum metadata, including XMP, IPTC, all PNG chunks. May affect some specific file functionalities.",
        "profile_exif_only_name": "EXIF Only (for photos)",
        "profile_exif_only_desc": "Removes only EXIF data from images, leaves other data untouched.",
        "error_browse_files_title": "File Selection Error",
        "error_browse_files_message": "Could not open file dialog: {error}",
        "error_browse_output_dir_title": "Folder Selection Error",
        "error_browse_output_dir_message": "Could not open folder dialog: {error}",
        "icon_load_warning": "Icon file '{icon_name}' not found at: {icon_path}",
        "icon_tcl_error": "TclError setting icon '{icon_name}': {error}",
        "icon_unknown_error": "Unexpected error setting icon: {error}",
        "theme_warning": "Could not apply preferred ttk theme.",
        "app_run_log": "StealthShare {app_version} started. Language: {lang}. Theme: {theme}",
        "profile_change_log": "Selected cleaning profile: {profile_name}",
        "files_added_log": "Added {new_files_count} new file(s). Total: {total_count}",
        "list_cleared_log": "Selected files list cleared.",
        "output_dir_selected_log": "Output folder selected: {folder}",
        "batch_start_log": "--- BATCH CLEANING STARTED ({count} files) ---",
        "file_skipped_not_found_log": "File '{filename}' skipped (not found).",
        "cleaned_name_error_log": "Could not generate cleaned filename for: {filename}",
        "file_processed_success_log": "Successfully processed: {filename_in} -> {filename_out}",
        "file_processed_error_log": "Error processing: {filename}",
        "file_critical_error_log": "Critical error cleaning '{filename}': {error}",
        "batch_finish_log": "--- BATCH CLEANING FINISHED --- {summary}"
    }
}

CIS_LANG_CODES_PREFIXES = ['ru', 'uk', 'be', 'kk', 'hy', 'az', 'ky', 'tg', 'uz', 'mo', 'tk', 'ka']

def get_system_language_code():
    try:
        lang_code, _ = locale.getdefaultlocale()
        if lang_code:
            return lang_code.split('_')[0].lower()
    except Exception as e:
        logger.warning(f"Не удалось определить язык системы: {e}")
    return None

def determine_initial_language(prompt_if_unknown=False):
    sys_lang = get_system_language_code()
    if sys_lang:
        if sys_lang in CIS_LANG_CODES_PREFIXES:
            return "ru"
        elif sys_lang == "en": 
            return "en"
        
        if prompt_if_unknown:
            logger.info(f"Язык системы '{sys_lang}' не определен однозначно, потребуется выбор пользователя.")
            return None 
        else:
            logger.info(f"Язык системы '{sys_lang}' не определен как 'ru' или 'en', по умолчанию используется 'en'.")
            return "en" 
    
    return None if prompt_if_unknown else "en"

CLEANING_PROFILES = {
    "profile_standard": { 
        "options": {
            'images': {'exif': True, 'xmp_iptc': False, 'png_chunks': False}, 
            'pdf': {'info_dict': True, 'xmp': False},
            'office': {'core_properties': True, 'custom_properties': False}
        }
    },
    "profile_aggressive": {
        "options": {
            'images': {'exif': True, 'xmp_iptc': True, 'png_chunks': True},
            'pdf': {'info_dict': True, 'xmp': True},
            'office': {'core_properties': True, 'custom_properties': True} 
        }
    },
    "profile_exif_only": {
        "options": {
            'images': {'exif': True, 'xmp_iptc': False, 'png_chunks': False},
            'pdf': {'info_dict': False, 'xmp': False}, 
            'office': {'core_properties': False, 'custom_properties': False}
        }
    }
}

def get_profile_display_names(lang_strings):
    return {
        "profile_standard": lang_strings.get("profile_standard_name", "Standard"),
        "profile_aggressive": lang_strings.get("profile_aggressive_name", "Aggressive"),
        "profile_exif_only": lang_strings.get("profile_exif_only_name", "EXIF Only (Photos)")
    }

def get_profile_description(profile_key, lang_strings):
    desc_key_map = {
        "profile_standard": "profile_standard_desc",
        "profile_aggressive": "profile_aggressive_desc",
        "profile_exif_only": "profile_exif_only_desc"
    }
    return lang_strings.get(desc_key_map.get(profile_key, ""), "No description available.")

def get_file_category(file_extension):
    for category, extensions in FILE_CATEGORIES.items():
        if file_extension in extensions:
            return category
    return "Other_Files"

def get_cleaned_filename(original_filepath, output_dir, sort_into_subdirs=False, file_category=None):
    if not original_filepath or not isinstance(original_filepath, str):
        logger.error("Оригинальный путь к файлу не предоставлен или имеет неверный тип.")
        return None
    
    final_output_dir = output_dir
    if sort_into_subdirs and file_category:
        final_output_dir = os.path.join(output_dir, file_category)

    if not os.path.isdir(final_output_dir):
        try:
            os.makedirs(final_output_dir, exist_ok=True)
        except OSError as e:
            logger.error(f"Выходная директория '{final_output_dir}' не существует и не может быть создана: {e}")
            return None

    try:
        base_name = os.path.basename(original_filepath)
        name, ext = os.path.splitext(base_name)
        cleaned_name = f"{name}_cleaned{ext}"
        return os.path.join(final_output_dir, cleaned_name)
    except Exception as e:
        logger.error(f"Ошибка при создании имени очищенного файла для '{original_filepath}': {e}")
        return None

def get_file_extension(filepath):
    if not filepath or not isinstance(filepath, str):
        return ""
    try:
        _, ext = os.path.splitext(filepath)
        return ext.lower()
    except Exception as e:
        logger.warning(f"Не удалось получить расширение для файла '{filepath}': {e}")
        return ""

def get_supported_extensions_list():
    all_ext = []
    for cat_ext in FILE_CATEGORIES.values():
        all_ext.extend(cat_ext)
    return sorted(list(set(ext.lstrip('.') for ext in all_ext)))

def get_supported_extensions_string():
    return ", ".join(get_supported_extensions_list())

if __name__ == '__main__':
    if not logger.hasHandlers():
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
    
    logger.info("--- Тестирование utils.py (многоязычность) ---")
    
    initial_lang_ru = determine_initial_language() 
    logger.info(f"Определенный язык (по умолчанию en, если не ru/cis): {initial_lang_ru}")
    
    ru_strings = LANGUAGES["ru"]
    en_strings = LANGUAGES["en"]

    logger.info(f"Профили RU: {list(get_profile_display_names(ru_strings).values())}")
    logger.info(f"Профили EN: {list(get_profile_display_names(en_strings).values())}")
    logger.info(f"Описание 'Стандартный' RU: {get_profile_description('profile_standard', ru_strings)}")
    logger.info(f"Описание 'Standard' EN: {get_profile_description('profile_standard', en_strings)}")
