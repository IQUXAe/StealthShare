# StealthShare v0.1 pre1
# Copyright (c) 2025 IQUXAe
# Released under the MIT License. See LICENSE file for details.

import os
import shutil
from PIL import Image, UnidentifiedImageError, PngImagePlugin, ExifTags
import piexif
import pikepdf
from docx import Document as DocxDocument
from openpyxl import load_workbook
from pptx import Presentation
from datetime import datetime, timezone
import tempfile

from utils import logger


def clean_image_metadata(filepath, output_path, options=None):
    filename_base = os.path.basename(filepath)
    if options is None: options = {}
    
    should_clean_exif = options.get('exif', True)
    should_try_clean_xmp_iptc = options.get('xmp_iptc', False) 
    should_aggressively_clean_png = options.get('png_chunks', True)
    should_preserve_icc = options.get('preserve_icc', True)

    logger.info(f"ИЗОБРАЖЕНИЕ: Очистка '{filename_base}', EXIF:{should_clean_exif}, XMP/IPTC:{should_try_clean_xmp_iptc}, PNG_Chunks:{should_aggressively_clean_png}, ICC сохранен:{should_preserve_icc}")
    
    file_ext_lower = os.path.splitext(filepath)[1].lower()

    try:
        if filepath != output_path:
            if not (file_ext_lower in ['.jpg', '.jpeg', '.tif', '.tiff'] and should_clean_exif):
                shutil.copy2(filepath, output_path)
            current_process_path = output_path 
        else:
            current_process_path = filepath 
            if file_ext_lower in ['.jpg', '.jpeg', '.tif', '.tiff'] and should_clean_exif:
                 logger.warning(f"ИЗОБРАЖЕНИЕ: piexif.remove не может работать 'на месте' для '{filename_base}'. EXIF будет удален через Pillow.")

        if file_ext_lower in ['.jpg', '.jpeg', '.tif', '.tiff'] and should_clean_exif:
            if filepath == output_path: 
                temp_fd, temp_name = tempfile.mkstemp(suffix=file_ext_lower)
                os.close(temp_fd)
                try:
                    piexif.remove(filepath, temp_name)
                    shutil.move(temp_name, output_path) 
                    logger.info(f"ИЗОБРАЖЕНИЕ: EXIF удален (piexif, через temp) для '{filename_base}'.")
                    current_process_path = output_path 
                except Exception as e_piexif_inplace:
                    logger.warning(f"ИЗОБРАЖЕНИЕ: Ошибка piexif при удалении EXIF (inplace) для '{filename_base}': {e_piexif_inplace}. Продолжаем с Pillow.")
            else: 
                try:
                    piexif.remove(filepath, output_path)
                    logger.info(f"ИЗОБРАЖЕНИЕ: EXIF удален (piexif) для '{filename_base}'.")
                    current_process_path = output_path
                except Exception as e_piexif:
                    logger.warning(f"ИЗОБРАЖЕНИЕ: Ошибка piexif при удалении EXIF для '{filename_base}': {e_piexif}. Копируем и продолжаем с Pillow.")
                    shutil.copy2(filepath, output_path) 
                    current_process_path = output_path
        
        img = Image.open(current_process_path)
        
        save_params = {}
        icc_profile_data = img.info.get('icc_profile')
        if should_preserve_icc and icc_profile_data:
            save_params['icc_profile'] = icc_profile_data
        elif not should_preserve_icc: 
             save_params['icc_profile'] = b''

        if file_ext_lower in ['.jpg', '.jpeg', '.tif', '.tiff']:
            if should_clean_exif: 
                save_params['exif'] = b''
            elif 'exif' in img.info and not should_clean_exif: 
                 save_params['exif'] = img.info['exif']
            
            if should_try_clean_xmp_iptc:
                logger.info(f"ИЗОБРАЖЕНИЕ: Попытка удаления XMP/IPTC для '{filename_base}' (Pillow).")
            
            quality_val = 95
            if img.format == 'JPEG': 
                quality_val = img.info.get('quality', 95) if hasattr(img, 'info') and 'quality' in img.info else getattr(img, 'quality', 95)
            
            img.save(output_path, format=img.format, quality=quality_val, **save_params)
            logger.info(f"ИЗОБРАЖЕНИЕ: '{filename_base}' пересохранен Pillow.")

        elif file_ext_lower == '.png':
            if should_aggressively_clean_png:
                new_png_info = PngImagePlugin.PngInfo()
                save_params['pnginfo'] = new_png_info 
                logger.info(f"ИЗОБРАЖЕНИЕ: PNG '{filename_base}' агрессивно очищен.")
            else: 
                logger.info(f"ИЗОБРАЖЕНИЕ: PNG '{filename_base}' пересохранен (стандартно).")
            img.save(output_path, **save_params)

        elif file_ext_lower == '.webp':
            if should_clean_exif: save_params['exif'] = b''
            if should_try_clean_xmp_iptc: save_params['xmp'] = b''
            
            save_params['quality'] = img.info.get('quality', 80)
            save_params['lossless'] = img.info.get('lossless', False)
            try:
                img.save(output_path, **save_params)
            except TypeError: 
                 save_params.pop('exif', None); save_params.pop('xmp', None)
                 img.save(output_path, **save_params)
            logger.info(f"ИЗОБРАЖЕНИЕ: WebP '{filename_base}' очищен.")
        
        elif file_ext_lower in ['.gif', '.bmp']:
            if file_ext_lower == '.gif':
                save_params['save_all'] = True
                if 'duration' in img.info: save_params['duration'] = img.info['duration']
                if 'loop' in img.info: save_params['loop'] = img.info.get('loop', 0)
            img.save(output_path, **save_params)
            logger.info(f"ИЗОБРАЖЕНИЕ: '{filename_base}' (GIF/BMP) пересохранен.")
        else: 
            if current_process_path == output_path:
                 img.save(output_path, **save_params) 
                 logger.info(f"ИЗОБРАЖЕНИЕ: Файл '{filename_base}' (тип {file_ext_lower}) пересохранен Pillow.")
        return True
            
    except FileNotFoundError:
        logger.error(f"ИЗОБРАЖЕНИЕ: Файл не найден: '{filepath}'")
        return False
    except UnidentifiedImageError:
        logger.error(f"ИЗОБРАЖЕНИЕ: Не удалось распознать '{filepath}' как изображение.")
        return False
    except Exception as e:
        logger.error(f"ИЗОБРАЖЕНИЕ: Общая ошибка при очистке '{filename_base}': {e}", exc_info=True)
        return False

def clean_pdf_metadata(filepath, output_path, options=None):
    filename_base = os.path.basename(filepath)
    if options is None: options = {}
    should_clean_info_dict = options.get('info_dict', True)
    should_clean_xmp = options.get('xmp', True)
    logger.info(f"PDF: Очистка '{filename_base}', Info:{should_clean_info_dict}, XMP:{should_clean_xmp} (pikepdf)")
    
    try:
        with pikepdf.open(filepath) as pdf:
            was_modified = False
            if should_clean_info_dict:
                if pdf.docinfo:
                    del pdf.docinfo 
                    was_modified = True
                    logger.info(f"PDF: Info-словарь удален для '{filename_base}'.")
            
            if should_clean_xmp:
                if pdf.Root.get("/Metadata"):
                    del pdf.Root.Metadata
                    was_modified = True
                    logger.info(f"PDF: XMP метаданные удалены для '{filename_base}'.")

            if was_modified:
                pdf.save(output_path, fix_metadata_version=False) 
                logger.info(f"PDF: '{filename_base}' сохранен после очистки.")
            elif filepath != output_path: 
                shutil.copy2(filepath, output_path)
                logger.info(f"PDF: '{filename_base}' скопирован (изменений не требовалось).")
            else:
                 logger.info(f"PDF: '{filename_base}' не изменен (метаданных для удаления не было).")
        return True
    except pikepdf.PasswordError:
        logger.error(f"PDF: Файл '{filename_base}' защищен паролем.")
        if filepath != output_path: shutil.copy2(filepath, output_path)
        return False 
    except FileNotFoundError:
        logger.error(f"PDF: Файл не найден: '{filepath}'")
        return False
    except Exception as e:
        logger.error(f"PDF: Ошибка при очистке '{filename_base}': {e}", exc_info=True)
        try:
            if filepath != output_path: shutil.copy2(filepath, output_path)
        except Exception: pass
        return False

def _clear_office_core_properties(props_obj, options, doc_type=""):
    if options.get('core_properties', True):
        logger.info(f"OFFICE ({doc_type}): Очистка основных свойств.")
        now_utc = datetime.now(timezone.utc)
        
        attrs_to_clear = {
            'author': "StealthShare User", 'category': None, 'comments': "",
            'content_status': None, 'created': now_utc, 'identifier': None,
            'keywords': "", 'language': None, 'last_modified_by': "StealthShare",
            'last_printed': None, 'modified': now_utc, 'revision': 1,
            'subject': None, 'title': "", 'version': None
        }
        if doc_type == "XLSX":
            attrs_to_clear['creator'] = "StealthShare User" 
            attrs_to_clear['description'] = ""              
            attrs_to_clear.pop('author', None) 
            attrs_to_clear.pop('comments', None)

        for attr, value in attrs_to_clear.items():
            if hasattr(props_obj, attr):
                try:
                    setattr(props_obj, attr, value)
                except AttributeError: 
                    logger.warning(f"OFFICE ({doc_type}): Не удалось установить свойство '{attr}'.")
        return True
    else:
        logger.info(f"OFFICE ({doc_type}): Очистка основных свойств пропущена.")
        return False
        
def _clear_office_custom_properties(doc_obj, options, doc_type=""):
    if options.get('custom_properties', False): 
        logger.info(f"OFFICE ({doc_type}): Попытка очистки пользовательских свойств.")
        try:
            if doc_type == "DOCX" and hasattr(doc_obj, 'part') and hasattr(doc_obj.part, 'custom_props_part') and doc_obj.part.custom_props_part is not None:
                logger.warning(f"DOCX: Глубокая очистка custom_properties для '{doc_type}' требует сложной XML-манипуляции и пока не реализована.")
                return False 
            elif doc_type == "XLSX" and hasattr(doc_obj, 'custom_properties'): 
                logger.warning(f"XLSX: Глубокая очистка custom_properties для '{doc_type}' требует доп. исследования API и пока не реализована.")
                return False
            elif doc_type == "PPTX" and hasattr(doc_obj, 'custom_properties'): 
                logger.warning(f"PPTX: Глубокая очистка custom_properties для '{doc_type}' требует доп. исследования API и пока не реализована.")
                return False
            return True 
        except Exception as e_custom:
            logger.error(f"OFFICE ({doc_type}): Ошибка при попытке очистки custom_properties: {e_custom}")
            return False
    return True 

def clean_docx_metadata(filepath, output_path, options=None):
    filename_base = os.path.basename(filepath)
    if options is None: options = {}
    logger.info(f"DOCX: Очистка '{filename_base}' с опциями: {options}")
    try:
        doc = DocxDocument(filepath)
        core_cleaned = _clear_office_core_properties(doc.core_properties, options, "DOCX")
        custom_cleaned_attempt = _clear_office_custom_properties(doc, options, "DOCX")
        doc.save(output_path)
        return core_cleaned 
    except Exception as e:
        logger.error(f"DOCX: Ошибка '{filename_base}': {e}", exc_info=True)
        return False

def clean_xlsx_metadata(filepath, output_path, options=None):
    filename_base = os.path.basename(filepath)
    if options is None: options = {}
    logger.info(f"XLSX: Очистка '{filename_base}' с опциями: {options}")
    try:
        workbook = load_workbook(filepath)
        core_cleaned = _clear_office_core_properties(workbook.properties, options, "XLSX")
        custom_cleaned_attempt = _clear_office_custom_properties(workbook, options, "XLSX")
        workbook.save(output_path)
        return core_cleaned
    except Exception as e:
        logger.error(f"XLSX: Ошибка '{filename_base}': {e}", exc_info=True)
        return False

def clean_pptx_metadata(filepath, output_path, options=None):
    filename_base = os.path.basename(filepath)
    if options is None: options = {}
    logger.info(f"PPTX: Очистка '{filename_base}' с опциями: {options}")
    try:
        prs = Presentation(filepath)
        core_cleaned = _clear_office_core_properties(prs.core_properties, options, "PPTX")
        custom_cleaned_attempt = _clear_office_custom_properties(prs, options, "PPTX")
        prs.save(output_path)
        return core_cleaned
    except Exception as e:
        logger.error(f"PPTX: Ошибка '{filename_base}': {e}", exc_info=True)
        return False

def clean_metadata(filepath, output_path, file_extension, cleaning_options_from_profile):
    filename_base = os.path.basename(filepath)
    logger.debug(f"ДИСПЕТЧЕР: Обработка '{filename_base}', расширение: '{file_extension}'. Используются опции из профиля.")
    
    processed = False
    image_extensions = ['.jpg', '.jpeg', '.tiff', '.tif', '.png', '.gif', '.webp', '.bmp']
    
    options_for_type = {} 

    if file_extension in image_extensions:
        options_for_type = cleaning_options_from_profile.get('images', {}).copy() 
        processed = clean_image_metadata(filepath, output_path, options=options_for_type)
    elif file_extension == '.pdf':
        options_for_type = cleaning_options_from_profile.get('pdf', {})
        processed = clean_pdf_metadata(filepath, output_path, options=options_for_type)
    elif file_extension == '.docx':
        options_for_type = cleaning_options_from_profile.get('office', {})
        processed = clean_docx_metadata(filepath, output_path, options=options_for_type)
    elif file_extension == '.xlsx':
        options_for_type = cleaning_options_from_profile.get('office', {})
        processed = clean_xlsx_metadata(filepath, output_path, options=options_for_type)
    elif file_extension == '.pptx':
        options_for_type = cleaning_options_from_profile.get('office', {})
        processed = clean_pptx_metadata(filepath, output_path, options=options_for_type)
    else:
        logger.warning(f"ДИСПЕТЧЕР: Неподдерживаемый тип '{file_extension}'. Файл '{filename_base}' будет скопирован.")
        try:
            if filepath != output_path: shutil.copy2(filepath, output_path)
            else: logger.info(f"ДИСПЕТЧЕР: Исходный и целевой пути совпадают для '{filename_base}'.")
            return True 
        except Exception as e:
            logger.error(f"ДИСПЕТЧЕР: Ошибка копирования '{filename_base}': {e}", exc_info=True)
            return False
    
    if not processed:
        logger.error(f"ДИСПЕТЧЕР: Очистка не удалась для '{filename_base}'.")
    return processed
