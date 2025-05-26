# StealthShare v0.1 pre1
# Copyright (c) 2025 IQUXAe
# Released under the MIT License. See LICENSE file for details.

import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
import os
import sys 
import threading
import logging
from datetime import datetime

from utils import (
    get_cleaned_filename, 
    get_file_extension, 
    get_file_category, 
    get_supported_extensions_string,
    CLEANING_PROFILES,
    LANGUAGES,
    determine_initial_language,
    get_profile_display_names,
    get_profile_description
)
from metadata_cleaner import clean_metadata

logger = logging.getLogger("StealthShareApp")
logger.setLevel(logging.INFO) 

if logger.hasHandlers():
    logger.handlers.clear()

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s - %(message)s', datefmt='%H:%M:%S')
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

CONFIG_LANG_FILE = "stealthshare_lang.cfg"

def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__)) # Используем директорию скрипта
    return os.path.join(base_path, relative_path)


class StealthShareApp:
    def __init__(self, root_window):
        self.app_version = "v0.1 pre1"
        self.root = root_window 
        
        self.current_lang_code = self.load_language_preference()
        if not self.current_lang_code:
            self.current_lang_code = determine_initial_language()
            if not self.current_lang_code: # Если все еще None (т.е. prompt_if_unknown=True и язык неясен)
                self.current_lang_code = self.prompt_language_selection()
        self.strings = LANGUAGES.get(self.current_lang_code, LANGUAGES["en"]) # Запасной вариант - английский
        self.save_language_preference()

        self.root.title(f"StealthShare {self.app_version} - {self.strings.get('app_title_suffix', 'Metadata Cleaner')}")
        
        self.set_app_icon() 

        self.root.configure(bg="#2b2b2b")

        window_width = 850 
        window_height = 620 # Немного увеличим для Combobox языка
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = int(screen_width/2 - window_width / 2)
        center_y = int(screen_height/2 - window_height / 2)
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        self.root.minsize(750, 500) 

        self.selected_files = [] 
        self.output_dir = tk.StringVar()
        
        default_output_dir = os.path.join(os.path.expanduser("~"), "Documents", "StealthShare_Cleaned")
        self.output_dir.set(default_output_dir)

        self.author_credit_text = self.strings.get('author_credit', "Developed by IQUXAe")
        self.default_status_text = f"{self.author_credit_text}  |  StealthShare {self.app_version}"
        self.status_message = tk.StringVar()
        self.status_message.set(self.default_status_text)
        
        self.preserve_icc_var = tk.BooleanVar(value=True)
        self.sort_output_by_type_var = tk.BooleanVar(value=False)
        
        profile_keys = list(get_profile_display_names(self.strings).keys())
        self.current_profile_key = tk.StringVar(value=profile_keys[0] if profile_keys else "")


        self.setup_styles()

        self.root.columnconfigure(1, weight=3) 
        self.root.columnconfigure(0, weight=1) 
        self.root.rowconfigure(0, weight=1)    

        left_panel = ttk.Frame(self.root, style="LeftPanel.TFrame") 
        left_panel.grid(row=0, column=0, sticky="nswe", padx=(10,5), pady=10)
        left_panel.columnconfigure(0, weight=1) 

        right_panel = ttk.Frame(self.root, style="RightPanel.TFrame")
        right_panel.grid(row=0, column=1, sticky="nswe", padx=(5,10), pady=10)
        right_panel.columnconfigure(0, weight=1) 
        right_panel.rowconfigure(0, weight=1)    
        
        self.create_options_panel(left_panel) 
        self.create_info_panel(left_panel) 

        self.create_file_handling_panel(right_panel) 
        
        action_frame = ttk.Frame(right_panel, style="Action.TFrame") 
        action_frame.grid(row=1, column=0, sticky="ew", pady=(10,0)) 
        action_frame.columnconfigure(0, weight=1) 

        self.start_button = ttk.Button(action_frame, command=self.start_cleaning_thread, style="Accent.TButton", padding=(10,10))
        self.start_button.pack(pady=(5,5)) 
        
        self.progress_var = tk.DoubleVar()
        self.progressbar = ttk.Progressbar(action_frame, variable=self.progress_var, maximum=100, length=300)
        
        self.status_bar_frame = tk.Frame(self.root, relief=tk.SUNKEN, bd=1, bg="#1c1c1c") 
        self.status_bar_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.status_label = ttk.Label(self.status_bar_frame, textvariable=self.status_message, style="Status.TLabel")
        self.status_label.pack(fill=tk.X, padx=10, pady=3)

        self.update_ui_text() # Первоначальная установка текстов
        logger.info(self.strings.get("app_run_log", "StealthShare {app_version} started. Language: {lang}. Theme: {theme}").format(
            app_version=self.app_version, lang=self.current_lang_code, theme=self.style.theme_use()
        ))

    def prompt_language_selection(self):
        # Простой диалог для выбора языка, если он не определен
        # В будущем можно сделать красивее
        lang_dialog = tk.Toplevel(self.root)
        lang_dialog.title("Select Language / Выберите язык")
        lang_dialog.geometry("300x150")
        lang_dialog.transient(self.root)
        lang_dialog.grab_set()
        lang_dialog.resizable(False, False)
        
        ttk.Label(lang_dialog, text="Please select a language:").pack(pady=10)
        
        selected_lang = tk.StringVar(value="en")
        
        ttk.Radiobutton(lang_dialog, text="English", variable=selected_lang, value="en").pack(anchor=tk.W, padx=20)
        ttk.Radiobutton(lang_dialog, text="Русский", variable=selected_lang, value="ru").pack(anchor=tk.W, padx=20)
        
        def _confirm_lang():
            self.current_lang_code = selected_lang.get()
            lang_dialog.destroy()

        ttk.Button(lang_dialog, text="OK", command=_confirm_lang).pack(pady=10)
        
        self.root.wait_window(lang_dialog) # Ждем закрытия диалога
        return self.current_lang_code if hasattr(self, 'current_lang_code') and self.current_lang_code else "en"


    def load_language_preference(self):
        try:
            config_path = get_resource_path(CONFIG_LANG_FILE)
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    lang_code = f.read().strip()
                    if lang_code in LANGUAGES:
                        logger.info(f"Загружен язык из настроек: {lang_code}")
                        return lang_code
        except Exception as e:
            logger.error(f"Ошибка загрузки настроек языка: {e}")
        return None

    def save_language_preference(self):
        try:
            config_path = get_resource_path(CONFIG_LANG_FILE)
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(self.current_lang_code)
            logger.info(f"Настройки языка сохранены: {self.current_lang_code}")
        except Exception as e:
            logger.error(f"Ошибка сохранения настроек языка: {e}")


    def set_app_icon(self):
        try:
            icon_name = "stealthshare_icon.png" 
            icon_path = get_resource_path(icon_name)
            
            if os.path.exists(icon_path):
                if icon_path.lower().endswith(".png"):
                    photo = tk.PhotoImage(file=icon_path)
                    self.root.iconphoto(True, photo) 
                elif icon_path.lower().endswith(".ico") and os.name == 'nt': 
                    self.root.iconbitmap(default=icon_path)
                logger.info(f"Иконка приложения установлена: {icon_path}")
            else:
                logger.warning(self.strings.get("icon_load_warning", "Icon file '{icon_name}' not found at: {icon_path}").format(icon_name=icon_name, icon_path=icon_path))
        except tk.TclError as e:
            logger.error(self.strings.get("icon_tcl_error", "TclError setting icon '{icon_name}': {error}").format(icon_name=icon_name, error=e))
        except Exception as e:
            logger.error(self.strings.get("icon_unknown_error", "Unexpected error setting icon: {error}").format(error=e))

    def setup_styles(self):
        self.style = ttk.Style()
        try:
            if 'clam' in self.style.theme_names(): self.style.theme_use('clam')
            elif 'alt' in self.style.theme_names(): self.style.theme_use('alt')
            elif os.name == 'nt' and 'vista' in self.style.theme_names(): self.style.theme_use('vista')
        except tk.TclError: logger.warning(self.strings.get("theme_warning", "Could not apply preferred ttk theme."))

        bg_color = "#2b2b2b" 
        fg_color = "#cccccc" 
        entry_bg = "#3c3f41"
        entry_fg = fg_color
        button_bg_main = "#0078d4" 
        button_fg_main = "white"
        frame_bg = "#313131" 
        label_frame_label_fg = "#a0a0a0"
        select_bg = button_bg_main 
        select_fg = button_fg_main
        border_color = "#4a4a4a"

        self.root.configure(bg=bg_color)

        self.style.configure("TLabel", padding=5, font=('Segoe UI', 9), background=frame_bg, foreground=fg_color)
        self.style.configure("TButton", padding=(10, 7), font=('Segoe UI', 9, 'bold'), relief=tk.FLAT, borderwidth=0)
        self.style.map("TButton",
            background=[('pressed', '#005a9e'), ('active', '#006cbf'), ('!disabled', button_bg_main)],
            foreground=[('!disabled', button_fg_main)]
        )
        self.style.configure("TEntry", padding=(7,6), font=('Segoe UI', 10), 
                             fieldbackground=entry_bg, foreground=entry_fg, 
                             relief=tk.SOLID, borderwidth=1, bordercolor=border_color, insertbackground=fg_color)
        self.style.map("TEntry", bordercolor=[('focus', button_bg_main)])

        self.style.configure("TLabelframe", padding=10, background=frame_bg, relief=tk.SOLID, borderwidth=1, bordercolor=border_color)
        self.style.configure("TLabelframe.Label", font=('Segoe UI', 10, 'bold'), padding=(0,0,0,6), background=frame_bg, foreground=label_frame_label_fg)
        
        self.style.configure("TCheckbutton", font=('Segoe UI', 9), padding=(5,4), background=frame_bg, foreground=fg_color)
        self.style.map("TCheckbutton",
            indicatorcolor=[('selected', button_bg_main), ('!selected', entry_bg)],
            foreground=[('active', button_bg_main)], 
            background=[('active', "#4f4f4f")] 
        )
        
        self.style.configure("TCombobox", font=('Segoe UI', 10), padding=5)
        self.style.map("TCombobox", 
                       fieldbackground=[('readonly', entry_bg), ('disabled', entry_bg)], 
                       foreground=[('readonly', entry_fg), ('disabled', 'gray50')],
                       selectbackground=[('readonly', entry_bg)], 
                       selectforeground=[('readonly', entry_fg)],
                       arrowcolor=[('readonly', fg_color)],
                       bordercolor=[('readonly', border_color), ('focus', button_bg_main)]
                       )
        self.root.option_add('*TCombobox*Listbox.background', entry_bg)
        self.root.option_add('*TCombobox*Listbox.foreground', fg_color)
        self.root.option_add('*TCombobox*Listbox.selectBackground', select_bg)
        self.root.option_add('*TCombobox*Listbox.selectForeground', select_fg)
        self.root.option_add('*TCombobox*Listbox.font', ('Segoe UI', 10))

        self.style.configure("Status.TLabel", font=('Segoe UI', 9), padding=(5,3), anchor=tk.W, background="#1c1c1c", foreground="#909090")
        self.status_label_default_fg = "#909090" 

        self.style.configure("Accent.TButton", font=('Segoe UI', 10, 'bold'), padding=(15,10), relief=tk.FLAT, borderwidth=0)
        self.style.map("Accent.TButton",
            background=[('pressed', '#004085'), ('active', '#006cbf'), ('!disabled', button_bg_main)],
            foreground=[('!disabled', button_fg_main)]
        )
        self.style.configure("Header.TLabel", font=('Segoe UI', 9, 'bold'), background=frame_bg, foreground=fg_color)
        
        self.style.configure("LeftPanel.TFrame", background=frame_bg)
        self.style.configure("RightPanel.TFrame", background=bg_color) 
        self.style.configure("Action.TFrame", background=bg_color)

        self.root.option_add("*Listbox.background", entry_bg)
        self.root.option_add("*Listbox.foreground", fg_color)
        self.root.option_add("*Listbox.selectBackground", select_bg)
        self.root.option_add("*Listbox.selectForeground", select_fg)
        self.root.option_add("*Listbox.font", ('Segoe UI', 9))
        self.root.option_add("*Listbox.relief", tk.SOLID) 
        self.root.option_add("*Listbox.borderwidth", 1)
        self.root.option_add("*Listbox.highlightThickness", 1) 
        self.root.option_add("*Listbox.highlightBackground", frame_bg) 
        self.root.option_add("*Listbox.highlightColor", button_bg_main)      
        
        self.style.configure("Vertical.TScrollbar", background=entry_bg, troughcolor=frame_bg, bordercolor=frame_bg, arrowcolor=fg_color, relief=tk.FLAT)
        self.style.map("Vertical.TScrollbar", background=[('active', button_bg_main)])
        self.style.configure("Horizontal.TScrollbar", background=entry_bg, troughcolor=frame_bg, bordercolor=frame_bg, arrowcolor=fg_color, relief=tk.FLAT)
        self.style.map("Horizontal.TScrollbar", background=[('active', button_bg_main)])
    
    def create_language_selector(self, parent):
        lang_frame = ttk.Frame(parent, style="LeftPanel.TFrame") # Используем стиль родителя
        lang_frame.pack(fill=tk.X, pady=(5,10), padx=5)
        
        self.lang_label_widget = ttk.Label(lang_frame, text=self.strings.get("language_label", "Language:"), style="TLabel") # Явно стиль
        self.lang_label_widget.pack(side=tk.LEFT, padx=(0,5))

        self.language_var = tk.StringVar(value="Русский" if self.current_lang_code == "ru" else "English")
        lang_options = ["Русский", "English"]
        
        self.lang_combobox = ttk.Combobox(lang_frame, textvariable=self.language_var, values=lang_options, state="readonly", width=12, font=('Segoe UI', 9))
        self.lang_combobox.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.lang_combobox.bind("<<ComboboxSelected>>", self.on_language_change)


    def create_options_panel(self, parent):
        self.options_frame_widget = ttk.LabelFrame(parent) # Имя сохраняем для update_ui_text
        self.options_frame_widget.pack(fill=tk.X, pady=(0,15), ipady=10, padx=5)
        self.options_frame_widget.columnconfigure(0, weight=1)

        self.profile_label_widget = ttk.Label(self.options_frame_widget)
        self.profile_label_widget.pack(anchor=tk.W, padx=5, pady=(5,2))
        
        profile_display_names = list(get_profile_display_names(self.strings).values())
        self.profile_keys_ordered = list(get_profile_display_names(self.strings).keys()) # Сохраняем порядок ключей

        # Устанавливаем текущее значение Combobox на основе ключа и отображаемых имен
        current_profile_display_name = get_profile_display_names(self.strings).get(self.current_profile_key.get())
        if not current_profile_display_name and profile_display_names: # Если ключ не найден, берем первый
            self.current_profile_key.set(self.profile_keys_ordered[0])
            current_profile_display_name = profile_display_names[0]
        
        self.profile_combobox_var = tk.StringVar(value=current_profile_display_name)

        self.profile_combobox = ttk.Combobox(self.options_frame_widget, textvariable=self.profile_combobox_var, 
                                             values=profile_display_names, state="readonly", width=25, font=('Segoe UI', 10))
        self.profile_combobox.pack(fill=tk.X, padx=5, pady=(0,10))
        self.profile_combobox.bind("<<ComboboxSelected>>", self.on_profile_change)

        self.profile_description_label = ttk.Label(self.options_frame_widget, 
                                                 wraplength=parent.winfo_reqwidth() - 40, justify=tk.LEFT, 
                                                 font=('Segoe UI', 8), style="Secondary.TLabel")
        
        labelframe_bg = self.style.lookup("TLabelframe", "background")
        self.style.configure("Secondary.TLabel", foreground="#a0a0a0", background=labelframe_bg) 
        self.profile_description_label.pack(fill=tk.X, padx=5, pady=(0,10))

        self.preserve_icc_checkbutton = ttk.Checkbutton(self.options_frame_widget, variable=self.preserve_icc_var)
        self.preserve_icc_checkbutton.pack(anchor=tk.W, padx=5, pady=3)
        self.sort_output_checkbutton = ttk.Checkbutton(self.options_frame_widget, variable=self.sort_output_by_type_var)
        self.sort_output_checkbutton.pack(anchor=tk.W, padx=5, pady=3)
        
        def _update_profile_desc_wrap(event):
            if self.profile_description_label.winfo_exists():
                 self.profile_description_label.config(wraplength=event.width - 30) 
        self.options_frame_widget.bind("<Configure>", _update_profile_desc_wrap)
        
        self.create_language_selector(parent) # Добавляем выбор языка под опциями

    def on_profile_change(self, event=None):
        selected_display_name = self.profile_combobox_var.get()
        # Находим ключ профиля по отображаемому имени
        profile_display_map = get_profile_display_names(self.strings)
        for key, display_name in profile_display_map.items():
            if display_name == selected_display_name:
                self.current_profile_key.set(key)
                break
        
        description = get_profile_description(self.current_profile_key.get(), self.strings)
        self.profile_description_label.config(text=description)
        logger.info(self.strings.get("profile_change_log", "Selected cleaning profile: {profile_name}").format(profile_name=selected_display_name))


    def on_language_change(self, event=None):
        selected_lang_display = self.language_var.get()
        new_lang_code = "ru" if selected_lang_display == "Русский" else "en"
        
        if new_lang_code != self.current_lang_code:
            self.current_lang_code = new_lang_code
            self.strings = LANGUAGES[self.current_lang_code]
            self.save_language_preference()
            self.update_ui_text()
            logger.info(f"Язык изменен на: {self.current_lang_code}")


    def update_ui_text(self):
        self.root.title(f"StealthShare {self.app_version} - {self.strings.get('app_title_suffix', 'Metadata Cleaner')}")
        self.author_credit_text = self.strings.get('author_credit', "Developed by IQUXAe")
        self.default_status_text = f"{self.author_credit_text}  |  StealthShare {self.app_version}"
        if self.status_message.get() == "" or "Готов к работе" in self.status_message.get() or "Ready" in self.status_message.get() or "Разработано IQUXAe" in self.status_message.get(): # Обновляем только если это стандартное сообщение
             self.status_message.set(self.default_status_text)


        self.options_frame_widget.config(text=self.strings.get("options_title", "Cleaning Settings"))
        self.profile_label_widget.config(text=self.strings.get("profile_label", "Cleaning Profile:"))
        
        profile_display_names = list(get_profile_display_names(self.strings).values())
        self.profile_keys_ordered = list(get_profile_display_names(self.strings).keys())
        self.profile_combobox.config(values=profile_display_names)
        
        current_profile_display = get_profile_display_names(self.strings).get(self.current_profile_key.get(), profile_display_names[0] if profile_display_names else "")
        self.profile_combobox_var.set(current_profile_display)
        self.profile_description_label.config(text=get_profile_description(self.current_profile_key.get(), self.strings))

        self.preserve_icc_checkbutton.config(text=self.strings.get("preserve_icc_label", "Preserve ICC Profile (for colors)"))
        self.sort_output_checkbutton.config(text=self.strings.get("sort_by_type_label", "Sort output into subfolders"))

        if hasattr(self, 'lang_label_widget'): # Обновляем метку выбора языка
            self.lang_label_widget.config(text=self.strings.get("language_label", "Language:"))

        if hasattr(self, 'info_frame_widget'):
            self.info_frame_widget.config(text=self.strings.get("info_title", "Information"))
        if hasattr(self, 'supported_ext_title_label'):
            self.supported_ext_title_label.config(text=self.strings.get("supported_ext_label", "Supported Extensions:"))
        
        if hasattr(self, 'file_handling_frame_widget'):
            self.file_handling_frame_widget.config(text=self.strings.get("file_handling_title", "Files to Clean"))
        if hasattr(self, 'drop_target_info_label'):
             self.drop_target_info_label.config(text=self.strings.get("drop_target_label", "Add files using the button:"))
        if hasattr(self, 'browse_files_button_widget'):
             self.browse_files_button_widget.config(text=self.strings.get("add_files_button", "Add Files..."))
        if hasattr(self, 'clear_files_button_widget'):
             self.clear_files_button_widget.config(text=self.strings.get("clear_list_button", "Clear List"))
        if hasattr(self, 'output_dir_text_label'):
             self.output_dir_text_label.config(text=self.strings.get("output_dir_label", "Save to:"))
        if hasattr(self, 'browse_output_dir_button_widget'):
            self.browse_output_dir_button_widget.config(text=self.strings.get("browse_button", "Browse..."))
        
        self.start_button.config(text=self.strings.get("start_button", "🚀 Start Cleaning"))


    def create_info_panel(self, parent):
        self.info_frame_widget = ttk.LabelFrame(parent, text=self.strings.get("info_title", "Information"))
        self.info_frame_widget.pack(fill=tk.BOTH, expand=True, pady=(5,0), padx=5)
        self.info_frame_widget.columnconfigure(0, weight=1) 
        self.info_frame_widget.rowconfigure(1, weight=1) 

        self.supported_ext_title_label = ttk.Label(self.info_frame_widget, style="Header.TLabel")
        self.supported_ext_title_label.grid(row=0, column=0, sticky="nw", padx=5, pady=(5,2))
        
        supported_ext_str = get_supported_extensions_string()
        self.ext_message_widget = tk.Message(self.info_frame_widget, text=supported_ext_str, 
                                 font=('Segoe UI', 8), 
                                 bg=self.style.lookup("TLabelframe", "background"), 
                                 fg=self.style.lookup("TLabel", "foreground"), 
                                 anchor='nw', width=parent.winfo_reqwidth() - 40) 
        self.ext_message_widget.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0,5))
        
        def _configure_msg_width(event):
            if self.ext_message_widget.winfo_exists():
                self.ext_message_widget.configure(width=event.width - 20) 
        self.info_frame_widget.bind("<Configure>", _configure_msg_width, add="+")

    def create_file_handling_panel(self, parent_frame):
        parent_frame.columnconfigure(0, weight=1) 
        parent_frame.rowconfigure(0, weight=1)    

        self.file_handling_frame_widget = ttk.LabelFrame(parent_frame)
        self.file_handling_frame_widget.grid(row=0, column=0, sticky="nswe", pady=(0,10), ipady=5)
        
        self.file_handling_frame_widget.columnconfigure(0, weight=1) 
        self.file_handling_frame_widget.rowconfigure(1, weight=3) 
        self.file_handling_frame_widget.rowconfigure(3, weight=0) 
        self.file_handling_frame_widget.rowconfigure(4, weight=0) 

        self.drop_target_info_label = ttk.Label(self.file_handling_frame_widget)
        self.drop_target_info_label.grid(row=0, column=0, columnspan=2, sticky=tk.W, padx=5, pady=(5,2))
        
        listbox_frame = ttk.Frame(self.file_handling_frame_widget, style="RightPanel.TFrame") 
        listbox_frame.grid(row=1, column=0, columnspan=2, sticky=tk.NSEW, padx=5, pady=5)
        listbox_frame.columnconfigure(0, weight=1)
        listbox_frame.rowconfigure(0, weight=1)

        self.selected_files_listbox = tk.Listbox(listbox_frame, selectmode=tk.EXTENDED, exportselection=False) 
        self.selected_files_listbox.grid(row=0, column=0, sticky=tk.NSEW)
        
        files_scrollbar_y = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.selected_files_listbox.yview, style="Vertical.TScrollbar")
        files_scrollbar_y.grid(row=0, column=1, sticky="ns")
        self.selected_files_listbox.config(yscrollcommand=files_scrollbar_y.set)
        
        browse_buttons_frame = ttk.Frame(self.file_handling_frame_widget)
        browse_buttons_frame.grid(row=3, column=0, columnspan=2, pady=(5,10), sticky="ew")
        browse_buttons_frame.columnconfigure(0, weight=1) 
        browse_buttons_frame.columnconfigure(1, weight=1)

        self.browse_files_button_widget = ttk.Button(browse_buttons_frame, command=self.browse_files)
        self.browse_files_button_widget.pack(side=tk.LEFT, padx=(0,5), expand=True, fill=tk.X)
        self.clear_files_button_widget = ttk.Button(browse_buttons_frame, command=self.clear_selected_files)
        self.clear_files_button_widget.pack(side=tk.LEFT, padx=(5,0), expand=True, fill=tk.X)

        output_dir_frame = ttk.Frame(self.file_handling_frame_widget) 
        output_dir_frame.grid(row=4, column=0, columnspan=2, pady=(5,5), sticky="ew")
        output_dir_frame.columnconfigure(1, weight=1) 

        self.output_dir_text_label = ttk.Label(output_dir_frame)
        self.output_dir_text_label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.output_dir_entry = ttk.Entry(output_dir_frame, textvariable=self.output_dir)
        self.output_dir_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        self.browse_output_dir_button_widget = ttk.Button(output_dir_frame, command=self.browse_output_dir, width=10)
        self.browse_output_dir_button_widget.grid(row=0, column=2, padx=(8,5), pady=5)
      
    def add_files_to_list(self, filepaths_to_add):
        new_files_added_count = 0
        for f_path in filepaths_to_add:
            if f_path not in self.selected_files:
                self.selected_files.append(f_path)
                self.selected_files_listbox.insert(tk.END, os.path.basename(f_path))
                new_files_added_count += 1
        
        if new_files_added_count > 0:
            msg = self.strings.get("status_files_added", "Added {count} file(s). Total in list: {total}.").format(count=new_files_added_count, total=len(self.selected_files))
            logger.info(msg)
            self._update_status_message(msg)
        else:
            self._update_status_message(self.strings.get("status_files_not_added", "No new files added (possibly already in list)."))


    def _update_status_message(self, message, temp_fg_color=None, is_temporary=True, duration=7000):
        self.status_message.set(message)
        current_bg = self.status_bar_frame['bg']
        text_color = temp_fg_color if temp_fg_color else ("#cccccc" if is_temporary else self.status_label_default_fg) 

        if self.status_label.winfo_exists(): 
            self.status_label.configure(foreground=text_color, background=current_bg)

            if is_temporary:
                self.root.after(duration, lambda: {
                    self.status_message.set(self.default_status_text),
                    self.status_label.configure(foreground=self.status_label_default_fg, background=current_bg) if self.status_label.winfo_exists() else None
                })

    def browse_files(self):
        try:
            image_ext_list = "*.jpg *.jpeg *.png *.tiff *.tif *.gif *.webp *.bmp"
            supported_files_desc = self.strings.get("filedialog_supported_all", "Supported Files") + f" ({image_ext_list} *.pdf *.docx *.xlsx *.pptx)"
            all_files_desc = self.strings.get("filedialog_all_files", "All Files") + " (*.*)"
            filetypes = [(supported_files_desc, f"{image_ext_list} *.pdf *.docx *.xlsx *.pptx"), (all_files_desc, "*.*")]
            
            dialog_title = self.strings.get("filedialog_select_files_title", "Select files to clean (multiple)")
            filenames = filedialog.askopenfilenames(title=dialog_title, filetypes=filetypes)
            if filenames:
                self.add_files_to_list(list(filenames))
        except Exception as e: 
            messagebox.showerror(self.strings.get("error_browse_files_title", "File Selection Error"), 
                                 self.strings.get("error_browse_files_message", "Could not open file dialog: {error}").format(error=e))
            logger.error(f"Ошибка при вызове диалога выбора файлов: {e}")

    def clear_selected_files(self):
        self.selected_files.clear()
        self.selected_files_listbox.delete(0, tk.END)
        logger.info(self.strings.get("list_cleared_log", "Selected files list cleared."))
        self._update_status_message(self.strings.get("status_list_cleared", "File list cleared."))

    def browse_output_dir(self):
        try:
            initial_dir = self.output_dir.get() if self.output_dir.get() and os.path.isdir(self.output_dir.get()) else os.path.expanduser("~")
            dialog_title = self.strings.get("filedialog_select_output_dir_title", "Select Output Folder")
            dirname = filedialog.askdirectory(title=dialog_title, initialdir=initial_dir)
            if dirname:
                self.output_dir.set(dirname)
                msg = self.strings.get("status_output_dir_selected", "Output folder selected: {folder}").format(folder=dirname)
                logger.info(msg)
                self._update_status_message(msg)
        except Exception as e: 
            messagebox.showerror(self.strings.get("error_browse_output_dir_title", "Folder Selection Error"),
                                 self.strings.get("error_browse_output_dir_message", "Could not open folder dialog: {error}").format(error=e))


    def get_current_cleaning_options_from_profile(self):
        profile_key = self.current_profile_key.get()
        profile_data = CLEANING_PROFILES.get(profile_key)
        if not profile_data: # Fallback to first profile if key is somehow invalid
            profile_key = list(CLEANING_PROFILES.keys())[0]
            profile_data = CLEANING_PROFILES[profile_key]
            
        profile_options = profile_data['options']
        
        final_options = {
            'images': profile_options.get('images', {}).copy(),
            'pdf': profile_options.get('pdf', {}).copy(),
            'office': profile_options.get('office', {}).copy()
        }
        if 'images' in final_options: # Глобальная опция ICC перезаписывает профиль
            final_options['images']['preserve_icc'] = self.preserve_icc_var.get()
        
        return final_options

    def start_cleaning_thread(self):
        if not self.selected_files:
            messagebox.showwarning(self.strings.get("dialog_no_files_title", "No Files Selected"), 
                                 self.strings.get("dialog_no_files_message", "Please add files to the list for cleaning."))
            return
        output_dir = self.output_dir.get()
        if not output_dir: 
            messagebox.showwarning(self.strings.get("dialog_no_output_dir_title", "No Output Folder"), 
                                 self.strings.get("dialog_no_output_dir_message", "Please select an output folder."))
            return
        
        if not os.path.isdir(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
            except OSError as e: 
                messagebox.showerror(self.strings.get("dialog_output_dir_error_title", "Folder Error"), 
                                     self.strings.get("dialog_output_dir_error_message", "Folder '{folder}' does not exist and cannot be created: {error}").format(folder=output_dir, error=e))
                return

        self.start_button.config(state=tk.DISABLED, text=self.strings.get("processing_button", "⏳ Processing..."))
        self.progressbar.pack(pady=(10,5), fill=tk.X, padx=20, expand=True) 
        self.progress_var.set(0)
        
        files_to_process = list(self.selected_files) 
        current_cleaning_options = self.get_current_cleaning_options_from_profile()
        sort_output = self.sort_output_by_type_var.get()

        status_msg = self.strings.get("status_processing_start", "Started processing {count} file(s)...").format(count=len(files_to_process))
        self._update_status_message(status_msg, temp_fg_color="#75baff", is_temporary=False) 
        
        thread = threading.Thread(target=self.perform_batch_cleaning, args=(files_to_process, output_dir, current_cleaning_options, sort_output), daemon=True)
        thread.start()

    def perform_batch_cleaning(self, files_to_process, base_output_dir, cleaning_options, sort_output):
        total_files = len(files_to_process)
        processed_count = 0
        success_count = 0
        error_list = [] 

        for i, filepath in enumerate(files_to_process):
            current_filename_base = os.path.basename(filepath)
            
            status_msg_file = self.strings.get("status_processing_file", "Processing ({current}/{total}): {filename}...").format(current=i+1, total=total_files, filename=current_filename_base)
            self.root.after(0, self._update_status_message, status_msg_file, "#75baff", False)

            if not os.path.exists(filepath): 
                logger.warning(self.strings.get("file_skipped_not_found_log", "File '{filename}' skipped (not found).").format(filename=current_filename_base))
                error_list.append((current_filename_base, "не найден"))
                processed_count +=1
                self.root.after(0, self.update_progress_gui, processed_count, total_files)
                continue

            file_ext = get_file_extension(filepath)
            file_category = get_file_category(file_ext) if sort_output else None
            
            cleaned_filepath = get_cleaned_filename(filepath, base_output_dir, 
                                                    sort_into_subdirs=sort_output, 
                                                    file_category=file_category)
            if not cleaned_filepath: 
                logger.error(self.strings.get("cleaned_name_error_log", "Could not generate cleaned filename for: {filename}").format(filename=current_filename_base))
                error_list.append((current_filename_base, "ошибка имени вых. файла"))
                processed_count +=1
                self.root.after(0, self.update_progress_gui, processed_count, total_files)
                continue
            
            try:
                success_op = clean_metadata(filepath, cleaned_filepath, file_ext, cleaning_options)
                if success_op:
                    success_count += 1
                    logger.info(self.strings.get("file_processed_success_log", "Successfully processed: {filename_in} -> {filename_out}").format(filename_in=current_filename_base, filename_out=os.path.basename(cleaned_filepath)))
                else: 
                    logger.error(self.strings.get("file_processed_error_log", "Error processing: {filename}").format(filename=current_filename_base))
                    error_list.append((current_filename_base, "ошибка очистки"))
            except Exception as e: 
                logger.critical(self.strings.get("file_critical_error_log", "Critical error cleaning '{filename}': {error}").format(filename=current_filename_base, error=e), exc_info=True)
                error_list.append((current_filename_base, f"критическая ошибка ({type(e).__name__})"))
            
            processed_count += 1
            self.root.after(0, self.update_progress_gui, processed_count, total_files)
            
        self.root.after(0, self.finalize_batch_cleaning, total_files, success_count, error_list)

    def update_progress_gui(self, processed_count, total_files):
        if total_files > 0:
            progress_percent = (processed_count / total_files) * 100
            self.progress_var.set(progress_percent)
        else: 
            self.progress_var.set(0)

    def show_report_dialog(self, title, summary, detailed_errors_list):
        report_dialog = tk.Toplevel(self.root)
        report_dialog.title(title)
        report_dialog.configure(bg=self.root['bg'])
        report_dialog.minsize(450, 250) 
        report_dialog.transient(self.root) 
        report_dialog.grab_set() 

        report_dialog.columnconfigure(0, weight=1)
        report_dialog.rowconfigure(1, weight=1) 

        summary_label = ttk.Label(report_dialog, text=summary, font=('Segoe UI', 10), wraplength=420, justify=tk.LEFT, style="Dialog.TLabel")
        self.style.configure("Dialog.TLabel", background=self.root['bg'], foreground=self.style.lookup("TLabel","foreground"))
        summary_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        if detailed_errors_list:
            errors_frame = ttk.Frame(report_dialog, style="Dialog.TFrame") 
            self.style.configure("Dialog.TFrame", background=self.root['bg'])
            errors_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
            errors_frame.columnconfigure(0, weight=1)
            errors_frame.rowconfigure(0, weight=1)

            ttk.Label(errors_frame, text=self.strings.get("dialog_report_errors_label", "Files with errors:"), font=('Segoe UI', 9, 'bold'), style="Dialog.TLabel").pack(anchor=tk.W, pady=(5,2))
            
            error_text_widget = tk.Text(errors_frame, height=10, width=60, wrap=tk.WORD, 
                                        relief=tk.FLAT, borderwidth=1,
                                        bg=self.style.lookup("TEntry", "fieldbackground"), 
                                        fg=self.style.lookup("TEntry", "foreground"),
                                        font=('Courier New', 9),
                                        highlightthickness=0) 
            error_text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True) 
            
            scrollbar_errors = ttk.Scrollbar(errors_frame, orient=tk.VERTICAL, command=error_text_widget.yview, style="Vertical.TScrollbar")
            scrollbar_errors.pack(side=tk.RIGHT, fill=tk.Y) 
            error_text_widget.config(yscrollcommand=scrollbar_errors.set)

            for filename, reason in detailed_errors_list:
                error_text_widget.insert(tk.END, f"- {filename}: {reason}\n")
            error_text_widget.config(state=tk.DISABLED)
        
        ttk.Button(report_dialog, text=self.strings.get("dialog_button_ok", "OK"), command=report_dialog.destroy, style="Accent.TButton").grid(row=2, column=0, pady=10)

    def finalize_batch_cleaning(self, total_files, success_count, error_list):
        self.start_button.config(state=tk.NORMAL, text=self.strings.get("start_button", "🚀 Start Cleaning"))
        self.progressbar.pack_forget() 
        
        status_key = "status_completed_summary"
        title_key = "dialog_report_title_success"
        status_fg_color = "#77cc77" 

        if error_list: 
            status_key = "status_completed_with_errors"
            title_key = "dialog_report_title_errors"
            status_fg_color = "#ffcc66" 
            logger.warning(f"Файлы с ошибками: {error_list}")
            summary_msg_for_dialog = self.strings.get(status_key, "").format(success_count=success_count, total_files=total_files, error_count=len(error_list))
            self.show_report_dialog(self.strings.get(title_key, "Report"), summary_msg_for_dialog, error_list)
        elif total_files > 0 : 
            summary_msg_for_dialog = self.strings.get(status_key, "").format(success_count=success_count, total_files=total_files)
            messagebox.showinfo(self.strings.get(title_key, "Success"), summary_msg_for_dialog) 
        else: 
            summary_msg_for_dialog = self.strings.get("status_no_files_to_process", "No files were selected for processing.")
            status_fg_color = self.status_label_default_fg
        
        final_status_text = self.strings.get(status_key, "{summary}").format(
            success_count=success_count, total_files=total_files, error_count=len(error_list), summary=summary_msg_for_dialog
        )
        if total_files == 0 : final_status_text = summary_msg_for_dialog # если не было файлов
        
        self._update_status_message(final_status_text, temp_fg_color=status_fg_color)
        logger.info(self.strings.get("batch_finish_log", "--- BATCH CLEANING FINISHED --- {summary}").format(summary=final_status_text))

if __name__ == '__main__': 
    root = tk.Tk() 
    app = StealthShareApp(root) 
    root.mainloop()
