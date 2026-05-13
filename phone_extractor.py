import re
from typing import List, Set, Dict, Optional
from collections import Counter
import os
import json
import datetime

try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox, filedialog
except ImportError:
    tk = None
    ttk = scrolledtext = messagebox = filedialog = None

try:
    if tk is None:
        raise ImportError
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    DND_FILES = None
    TkinterDnD = None
    HAS_DND = False

TEXT_END = tk.END if tk is not None else "end"


class PhoneExtractorApp:
    VERSION = "3.0"

    def __init__(self, root):
        self.root = root
        self.root.title(f"Извлечение номеров телефонов v{self.VERSION}")
        self.root.geometry("1500x920")
        self.root.minsize(1200, 700)

        # Данные
        self.extracted_phones: List[str] = []          # Все извлечённые (с дубликатами)
        self.current_display_phones: List[str] = []    # Текущий список для отображения
        self.search_results: List[str] = []
        self.is_searching: bool = False
        self.duplicate_details: Dict[str, int] = {}    # Номер -> количество вхождений
        self.extraction_stats: Dict = {}               # Статистика последнего извлечения
        self.history: List[Dict] = []                   # История операций

        self._build_gui()
        self.update_info_panel()

    def _build_gui(self):
        """Построение всего GUI"""
        style = ttk.Style()
        style.configure('Title.TLabel', font=('Arial', 14, 'bold'))
        style.configure('Stats.TLabel', font=('Arial', 10, 'bold'))
        style.configure('Action.TButton', padding=5)

        # Основной фрейм
        main_frame = ttk.Frame(self.root, padding="8")
        main_frame.grid(row=0, column=0, sticky="nsew")

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=2)
        main_frame.columnconfigure(1, weight=3)
        main_frame.rowconfigure(2, weight=1)

        # Заголовок
        title_label = ttk.Label(
            main_frame,
            text=f"Извлечение и форматирование номеров телефонов v{self.VERSION}",
            style='Title.TLabel'
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(5, 10))

        # Верхняя панель кнопок
        file_buttons_frame = ttk.Frame(main_frame)
        file_buttons_frame.grid(row=1, column=0, columnspan=2, pady=5)

        ttk.Button(file_buttons_frame, text="📂 Загрузить файл",
                   command=self.load_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_buttons_frame, text="💾 Сохранить результат",
                   command=self.save_results).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_buttons_frame, text="📋 Вставить из буфера",
                   command=self.paste_from_clipboard).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_buttons_frame, text="📜 История операций",
                   command=self.show_history).pack(side=tk.LEFT, padx=5)

        # Левая панель — ввод текста
        left_frame = ttk.LabelFrame(
            main_frame,
            text="Исходный текст (можно перетащить файл)" if HAS_DND else "Исходный текст",
            padding="5"
        )
        left_frame.grid(row=2, column=0, sticky="nsew", padx=(0, 5))

        self.input_text = scrolledtext.ScrolledText(left_frame, width=50, height=25, wrap=tk.WORD)
        self.input_text.pack(fill=tk.BOTH, expand=True)

        # Счётчик символов под полем ввода
        self.input_counter_label = ttk.Label(left_frame, text="Символов: 0 | Строк: 0", font=('Arial', 8))
        self.input_counter_label.pack(anchor=tk.W, pady=(2, 0))
        self.input_text.bind('<KeyRelease>', self._update_input_counter)

        if HAS_DND:
            self.input_text.drop_target_register(DND_FILES)
            self.input_text.dnd_bind('<<Drop>>', self.on_drop_input)

        # Правая панель
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=2, column=1, sticky="nsew", padx=(5, 0))

        notebook = ttk.Notebook(right_frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Вкладка 1: Основные настройки
        main_tab = ttk.Frame(notebook, padding="5")
        notebook.add(main_tab, text="⚙️ Основные настройки")

        # Вкладка 2: Поиск и фильтры
        search_tab = ttk.Frame(notebook, padding="5")
        notebook.add(search_tab, text="🔍 Поиск и фильтры")

        # Вкладка 3: Статистика
        stats_tab = ttk.Frame(notebook, padding="5")
        notebook.add(stats_tab, text="📊 Статистика")

        self._build_main_tab(main_tab)
        self._build_search_tab(search_tab)
        self._build_stats_tab(stats_tab)
        self.notebook = notebook

    # ────────────────────────────────────────────────────────────
    # Вкладка 1: Основные настройки
    # ────────────────────────────────────────────────────────────
    def _build_main_tab(self, parent):
        # Контейнер с прокруткой для настроек
        canvas = tk.Canvas(parent, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Настройки маски
        mask_frame = ttk.LabelFrame(scroll_frame, text="Настройки замены символами (маска)", padding="5")
        mask_frame.pack(fill=tk.X, pady=3)

        # Начало номера
        start_frame = ttk.Frame(mask_frame)
        start_frame.pack(fill=tk.X, pady=2)
        ttk.Label(start_frame, text="Начало:", width=10).pack(side=tk.LEFT, padx=5)
        ttk.Label(start_frame, text="Заменить", width=8).pack(side=tk.LEFT)
        self.start_digits = ttk.Spinbox(start_frame, from_=0, to=11, width=5)
        self.start_digits.set(0)
        self.start_digits.pack(side=tk.LEFT, padx=2)
        ttk.Label(start_frame, text="цифр на").pack(side=tk.LEFT, padx=2)
        self.start_mask = ttk.Entry(start_frame, width=10)
        self.start_mask.pack(side=tk.LEFT, padx=2)

        # Середина номера
        middle_frame = ttk.Frame(mask_frame)
        middle_frame.pack(fill=tk.X, pady=2)
        ttk.Label(middle_frame, text="Середина:", width=10).pack(side=tk.LEFT, padx=5)
        ttk.Label(middle_frame, text="С позиции", width=8).pack(side=tk.LEFT)
        self.middle_position = ttk.Spinbox(middle_frame, from_=0, to=11, width=5)
        self.middle_position.set(0)
        self.middle_position.pack(side=tk.LEFT, padx=2)
        ttk.Label(middle_frame, text="заменить").pack(side=tk.LEFT, padx=2)
        self.middle_digits = ttk.Spinbox(middle_frame, from_=0, to=11, width=5)
        self.middle_digits.set(0)
        self.middle_digits.pack(side=tk.LEFT, padx=2)
        ttk.Label(middle_frame, text="на").pack(side=tk.LEFT, padx=2)
        self.middle_mask = ttk.Entry(middle_frame, width=10)
        self.middle_mask.pack(side=tk.LEFT, padx=2)

        # Конец номера
        end_frame = ttk.Frame(mask_frame)
        end_frame.pack(fill=tk.X, pady=2)
        ttk.Label(end_frame, text="Конец:", width=10).pack(side=tk.LEFT, padx=5)
        ttk.Label(end_frame, text="Заменить", width=8).pack(side=tk.LEFT)
        self.end_digits = ttk.Spinbox(end_frame, from_=0, to=11, width=5)
        self.end_digits.set(0)
        self.end_digits.pack(side=tk.LEFT, padx=2)
        ttk.Label(end_frame, text="цифр на").pack(side=tk.LEFT, padx=2)
        self.end_mask = ttk.Entry(end_frame, width=10)
        self.end_mask.pack(side=tk.LEFT, padx=2)

        examples_text = (
            "Примеры:  Начало: 2 цифры → ** результат: **785550015 | "
            "Конец: 4 цифры → ** результат: +7978555** | "
            "Середина: поз.5, 3 цифры → XXX результат: +7978XXX0015"
        )
        ttk.Label(mask_frame, text=examples_text, font=('Arial', 8),
                  foreground='blue', wraplength=600).pack(pady=2)

        # Формат вывода
        format_frame = ttk.LabelFrame(scroll_frame, text="Формат вывода", padding="5")
        format_frame.pack(fill=tk.X, pady=3)

        self.output_format = tk.StringVar(value="column")
        formats = [
            ("В столбик", "column"),
            ("Запятая без пробела", "comma_no_space"),
            ("Запятая с пробелом", "comma_with_space"),
            ("Точка с запятой без пробела", "semicolon_no_space"),
            ("Точка с запятой с пробелом", "semicolon_with_space"),
            ("Пробел", "space"),
            ("Табуляция", "tab"),
        ]
        # Размещаем в две колонки для экономии места
        format_inner = ttk.Frame(format_frame)
        format_inner.pack(fill=tk.X)
        for i, (text, value) in enumerate(formats):
            col = i % 2
            row = i // 2
            ttk.Radiobutton(format_inner, text=text, variable=self.output_format,
                            value=value).grid(row=row, column=col, sticky=tk.W, padx=5)

        # Формат номера (новый функционал)
        phone_format_frame = ttk.LabelFrame(scroll_frame, text="Формат номера", padding="5")
        phone_format_frame.pack(fill=tk.X, pady=3)

        self.phone_format = tk.StringVar(value="plus7")
        phone_formats = [
            ("+7XXXXXXXXXX", "plus7"),
            ("8XXXXXXXXXX", "eight"),
            ("+7 (XXX) XXX-XX-XX", "formatted"),
            ("7XXXXXXXXXX", "seven"),
        ]
        pf_inner = ttk.Frame(phone_format_frame)
        pf_inner.pack(fill=tk.X)
        for i, (text, value) in enumerate(phone_formats):
            col = i % 2
            row = i // 2
            ttk.Radiobutton(pf_inner, text=text, variable=self.phone_format,
                            value=value, command=self.update_display).grid(
                row=row, column=col, sticky=tk.W, padx=5)

        # Дополнительные опции
        options_frame = ttk.LabelFrame(scroll_frame, text="Дополнительные опции", padding="5")
        options_frame.pack(fill=tk.X, pady=3)

        self.remove_duplicates = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Удалять дубликаты",
                        variable=self.remove_duplicates,
                        command=self.update_display).pack(anchor=tk.W)

        # Добавить префикс/суффикс (новый функционал)
        prefix_frame = ttk.Frame(options_frame)
        prefix_frame.pack(fill=tk.X, pady=2)
        ttk.Label(prefix_frame, text="Префикс:").pack(side=tk.LEFT, padx=5)
        self.prefix_entry = ttk.Entry(prefix_frame, width=12)
        self.prefix_entry.pack(side=tk.LEFT, padx=2)
        ttk.Label(prefix_frame, text="Суффикс:").pack(side=tk.LEFT, padx=5)
        self.suffix_entry = ttk.Entry(prefix_frame, width=12)
        self.suffix_entry.pack(side=tk.LEFT, padx=2)

        # Режим извлечения
        extraction_mode_frame = ttk.LabelFrame(options_frame, text="Режим извлечения", padding="5")
        extraction_mode_frame.pack(fill=tk.X, pady=3)

        self.extraction_mode = tk.StringVar(value="russia_only")
        ttk.Radiobutton(extraction_mode_frame, text="Только российские (+7, 8)",
                        variable=self.extraction_mode, value="russia_only").pack(anchor=tk.W)
        ttk.Radiobutton(extraction_mode_frame, text="Все международные номера",
                        variable=self.extraction_mode, value="international").pack(anchor=tk.W)

        # Сортировка
        sort_frame = ttk.Frame(options_frame)
        sort_frame.pack(fill=tk.X, pady=2)
        ttk.Label(sort_frame, text="Сортировка:").pack(side=tk.LEFT, padx=5)
        self.sort_order = tk.StringVar(value="none")
        ttk.Radiobutton(sort_frame, text="По возрастанию", variable=self.sort_order,
                        value="asc", command=self.update_display).pack(side=tk.LEFT, padx=3)
        ttk.Radiobutton(sort_frame, text="По убыванию", variable=self.sort_order,
                        value="desc", command=self.update_display).pack(side=tk.LEFT, padx=3)
        ttk.Radiobutton(sort_frame, text="Без сортировки", variable=self.sort_order,
                        value="none", command=self.update_display).pack(side=tk.LEFT, padx=3)

        # Кнопки управления
        button_frame = ttk.Frame(scroll_frame)
        button_frame.pack(fill=tk.X, pady=5)

        ttk.Button(button_frame, text="🔍 Извлечь номера",
                   command=self.extract_phones).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🎭 Применить маску",
                   command=self.apply_mask).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="📋 Копировать результат",
                   command=self.copy_results).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🗑️ Очистить",
                   command=self.clear_all).pack(side=tk.LEFT, padx=5)

        # Результаты
        result_frame = ttk.LabelFrame(scroll_frame, text="Результаты (извлечённые номера)", padding="5")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=3)

        self.output_text = scrolledtext.ScrolledText(result_frame, width=45, height=12, wrap=tk.WORD)
        self.output_text.pack(fill=tk.BOTH, expand=True)

        # Статистика
        self.stats_label = ttk.Label(scroll_frame, text="Найдено номеров: 0", style='Stats.TLabel')
        self.stats_label.pack(pady=3)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Прокрутка колесом мыши
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    # ────────────────────────────────────────────────────────────
    # Вкладка 2: Поиск и фильтры
    # ────────────────────────────────────────────────────────────
    def _build_search_tab(self, parent):
        # Поиск
        search_frame = ttk.LabelFrame(parent, text="Поиск по номеру", padding="5")
        search_frame.pack(fill=tk.X, pady=3)

        search_input_frame = ttk.Frame(search_frame)
        search_input_frame.pack(fill=tk.X, pady=2)
        ttk.Label(search_input_frame, text="Найти:").pack(side=tk.LEFT, padx=5)
        self.search_entry = ttk.Entry(search_input_frame, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.search_entry.bind('<KeyRelease>', self.on_search_change)
        ttk.Button(search_input_frame, text="🔍 Найти",
                   command=self.search_phones).pack(side=tk.LEFT, padx=2)
        ttk.Button(search_input_frame, text="✖ Сбросить",
                   command=self.reset_search).pack(side=tk.LEFT, padx=2)

        # Режим поиска — горизонтально
        search_options_frame = ttk.Frame(search_frame)
        search_options_frame.pack(fill=tk.X, pady=2)
        self.search_mode = tk.StringVar(value="contains")
        for text, val in [("Содержит", "contains"), ("Начинается с", "starts"),
                          ("Заканчивается на", "ends"), ("Точное совпадение", "exact")]:
            ttk.Radiobutton(search_options_frame, text=text, variable=self.search_mode,
                            value=val, command=self.search_phones).pack(side=tk.LEFT, padx=5)

        self.search_info_label = ttk.Label(search_frame, text="", foreground="blue", font=('Arial', 9))
        self.search_info_label.pack(pady=2)

        # Результаты поиска
        search_results_frame = ttk.LabelFrame(parent, text="Результаты поиска", padding="5")
        search_results_frame.pack(fill=tk.BOTH, expand=True, pady=3)

        self.search_results_text = scrolledtext.ScrolledText(search_results_frame, height=12, wrap=tk.WORD)
        self.search_results_text.pack(fill=tk.BOTH, expand=True)

        search_results_buttons = ttk.Frame(parent)
        search_results_buttons.pack(fill=tk.X, pady=2)
        ttk.Button(search_results_buttons, text="📋 Копировать найденные",
                   command=self.copy_search_results).pack(side=tk.LEFT, padx=2)
        ttk.Button(search_results_buttons, text="💾 Сохранить найденные",
                   command=self.save_search_results).pack(side=tk.LEFT, padx=2)
        ttk.Button(search_results_buttons, text="📊 Показать в основных",
                   command=self.show_search_in_main).pack(side=tk.LEFT, padx=2)

        # Исключения
        exclusions_frame = ttk.LabelFrame(parent, text="Исключения номеров", padding="5")
        exclusions_frame.pack(fill=tk.X, pady=3)

        ttk.Label(exclusions_frame, text="Номера для исключения (по одному на строке):").pack(anchor=tk.W)
        self.exclusions_text = scrolledtext.ScrolledText(exclusions_frame, height=4, wrap=tk.WORD)
        self.exclusions_text.pack(fill=tk.BOTH, expand=True, pady=2)

        exclusions_buttons_frame = ttk.Frame(exclusions_frame)
        exclusions_buttons_frame.pack(fill=tk.X, pady=2)
        ttk.Button(exclusions_buttons_frame, text="Применить",
                   command=self.update_display).pack(side=tk.LEFT, padx=2)
        ttk.Button(exclusions_buttons_frame, text="Очистить",
                   command=self.clear_exclusions).pack(side=tk.LEFT, padx=2)
        ttk.Button(exclusions_buttons_frame, text="Загрузить",
                   command=self.load_exclusions).pack(side=tk.LEFT, padx=2)
        ttk.Button(exclusions_buttons_frame, text="Сохранить",
                   command=self.save_exclusions).pack(side=tk.LEFT, padx=2)

    # ────────────────────────────────────────────────────────────
    # Вкладка 3: Статистика
    # ────────────────────────────────────────────────────────────
    def _build_stats_tab(self, parent):
        info_panel_frame = ttk.LabelFrame(parent, text="📊 Подробная информация об обработке", padding="10")
        info_panel_frame.pack(fill=tk.BOTH, expand=True)

        self.info_panel = scrolledtext.ScrolledText(
            info_panel_frame, height=25, wrap=tk.WORD,
            font=('Courier New', 10), bg='#f0f0f0'
        )
        self.info_panel.pack(fill=tk.BOTH, expand=True)
        self.info_panel.config(state='disabled')

        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="🔄 Обновить статистику",
                   command=self.update_info_panel).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📋 Копировать статистику",
                   command=self.copy_stats).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="💾 Экспорт в JSON",
                   command=self.export_stats_json).pack(side=tk.LEFT, padx=5)

    # ────────────────────────────────────────────────────────────
    # Обработка файлов и ввода
    # ────────────────────────────────────────────────────────────
    def _update_input_counter(self, event=None):
        content = self.input_text.get("1.0", TEXT_END).rstrip('\n')
        chars = len(content)
        lines = content.count('\n') + 1 if content else 0
        self.input_counter_label.config(text=f"Символов: {chars} | Строк: {lines}")

    def on_drop_input(self, event):
        """Обработка drag and drop файла"""
        files = self.root.tk.splitlist(event.data)
        if files:
            file_path = files[0].strip('{}')
            self.load_file_content(file_path)

    def load_file(self):
        """Загрузка файла"""
        file_path = filedialog.askopenfilename(
            title="Выберите файл",
            filetypes=[
                ("Текстовые файлы", "*.txt"),
                ("CSV файлы", "*.csv"),
                ("Все файлы", "*.*")
            ]
        )
        if file_path:
            self.load_file_content(file_path)

    def load_file_content(self, file_path):
        """Загрузка содержимого файла"""
        try:
            encodings = ['utf-8', 'cp1251', 'windows-1251', 'latin-1']
            content = None
            used_encoding = None

            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    used_encoding = encoding
                    break
                except UnicodeDecodeError:
                    continue

            if content is not None:
                self.input_text.delete("1.0", TEXT_END)
                self.input_text.insert("1.0", content)
                self._update_input_counter()
                size_kb = os.path.getsize(file_path) / 1024
                messagebox.showinfo(
                    "Успех",
                    f"Файл загружен: {os.path.basename(file_path)}\n"
                    f"Кодировка: {used_encoding}\n"
                    f"Размер: {size_kb:.1f} КБ"
                )
            else:
                messagebox.showerror("Ошибка", "Не удалось прочитать файл")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при загрузке файла: {str(e)}")

    def save_results(self):
        """Сохранение результатов в файл"""
        if not self.current_display_phones:
            messagebox.showwarning("Предупреждение", "Нет данных для сохранения!")
            return

        file_path = filedialog.asksaveasfilename(
            title="Сохранить результаты",
            defaultextension=".txt",
            filetypes=[
                ("Текстовые файлы", "*.txt"),
                ("CSV файлы", "*.csv"),
                ("Все файлы", "*.*")
            ]
        )

        if file_path:
            try:
                content = self.output_text.get("1.0", TEXT_END).strip()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("Успех", f"Файл сохранён: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при сохранении: {str(e)}")

    def paste_from_clipboard(self):
        """Вставка текста из буфера обмена"""
        try:
            clipboard_content = self.root.clipboard_get()
            self.input_text.delete("1.0", TEXT_END)
            self.input_text.insert("1.0", clipboard_content)
            self._update_input_counter()
            messagebox.showinfo("Успех", "Текст вставлен из буфера обмена")
        except tk.TclError:
            messagebox.showwarning("Предупреждение", "Буфер обмена пуст или содержит неподдерживаемые данные")

    def copy_results(self):
        """Копирование результатов в буфер обмена"""
        content = self.output_text.get("1.0", TEXT_END).strip()
        if not content or content == "Номера не найдены":
            messagebox.showwarning("Предупреждение", "Нет результатов для копирования!")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        messagebox.showinfo("Успех", "Результаты скопированы в буфер обмена")

    # ────────────────────────────────────────────────────────────
    # Извлечение номеров
    # ────────────────────────────────────────────────────────────
    def extract_phones(self):
        """Извлечение номеров из текста"""
        text = self.input_text.get("1.0", TEXT_END)

        if not text.strip():
            messagebox.showwarning("Предупреждение", "Введите текст для обработки!")
            return

        extraction_mode = self.extraction_mode.get()

        if extraction_mode == "russia_only":
            found_phones = self.extract_russian_phones(text)
        else:
            found_phones = self.extract_international_phones(text)

        # found_phones — список (с дублями в порядке нахождения)
        self.extracted_phones = found_phones

        # Подсчёт дубликатов по каноническому номеру, а не по исходному написанию
        self.duplicate_details = self.get_duplicate_details(found_phones)

        # Сохраняем
        self.current_display_phones = found_phones.copy()

        # Обработка
        processed_phones = self.process_phones(found_phones)

        # Отображение
        self.display_results(processed_phones)

        # Статистика
        original_count = len(found_phones)
        unique_count = self.count_unique_phones(found_phones)
        dup_count = original_count - unique_count
        processed_count = len(processed_phones)

        stats_parts = [f"Найдено: {original_count}"]
        if dup_count > 0:
            stats_parts.append(f"дубликатов: {dup_count}")
        stats_parts.append(f"отображено: {processed_count}")
        self.stats_label.config(text=" | ".join(stats_parts))

        # Сохраняем статистику
        self.extraction_stats = {
            'total_found': original_count,
            'unique': unique_count,
            'duplicates': dup_count,
            'displayed': processed_count,
            'mode': extraction_mode,
        }

        # Добавляем в историю
        self._add_history("Извлечение номеров", f"Найдено {original_count}, уникальных {unique_count}")

        self.update_info_panel()

    def extract_russian_phones(self, text: str) -> List[str]:
        """Извлечение российских номеров с высокой точностью.

        Использует один мощный паттерн вместо множества перекрывающихся,
        с word boundary для избежания ложных срабатываний.
        """
        # Единый паттерн, покрывающий все основные форматы:
        # +7/8 с необязательными скобками, пробелами, дефисами, точками
        pattern = (
            r'(?<!\d)'                         # не часть большего числа
            r'(?:'
            r'\+7|8'                            # начало: +7 или 8
            r')'
            r'[\s\-\.]*'                        # возможный разделитель
            r'\(?'                              # возможная открывающая скобка
            r'(\d{3})'                          # код оператора (3 цифры)
            r'\)?'                              # возможная закрывающая скобка
            r'[\s\-\.]*'                        # возможный разделитель
            r'(\d{3})'                          # первые 3 цифры
            r'[\s\-\.]*'                        # возможный разделитель
            r'(\d{2})'                          # следующие 2 цифры
            r'[\s\-\.]*'                        # возможный разделитель
            r'(\d{2})'                          # последние 2 цифры
            r'(?!\d)'                           # не часть большего числа
        )

        # Также ловим сплошные номера: +79781234567, 79781234567 или 89781234567
        pattern_solid = (
            r'(?<!\d)'
            r'(?:\+7|7|8)'
            r'(\d{10})'
            r'(?!\d)'
        )

        # Ещё формат: 7 978 123 45 67 (без + но с разделителями)
        pattern_seven = (
            r'(?<!\d)'
            r'7[\s\-\.]'                        # 7 с обязательным разделителем
            r'\(?'
            r'(\d{3})'
            r'\)?'
            r'[\s\-\.]*'
            r'(\d{3})'
            r'[\s\-\.]*'
            r'(\d{2})'
            r'[\s\-\.]*'
            r'(\d{2})'
            r'(?!\d)'
        )

        candidates = []

        def is_overlapping(start, end):
            for s, e in occupied_ranges:
                if start < e and end > s:
                    return True
            return False

        # Паттерн 1: с разделителями (наиболее точный — приоритет при одинаковой позиции)
        for m in re.finditer(pattern, text):
            digits = m.group(1) + m.group(2) + m.group(3) + m.group(4)
            phone = '7' + digits
            if self.validate_phone_number(phone):
                candidates.append((m.start(), m.end(), 0, '+' + phone))

        # Паттерн 2: сплошной
        for m in re.finditer(pattern_solid, text):
            phone = '7' + m.group(1)
            if self.validate_phone_number(phone):
                candidates.append((m.start(), m.end(), 1, '+' + phone))

        # Паттерн 3: начинающийся с 7 (без +) с разделителями
        for m in re.finditer(pattern_seven, text):
            digits = m.group(1) + m.group(2) + m.group(3) + m.group(4)
            phone = '7' + digits
            if self.validate_phone_number(phone):
                candidates.append((m.start(), m.end(), 2, '+' + phone))

        found_phones = []
        # Храним занятые диапазоны (start, end) чтобы не дублировать перекрывающиеся совпадения.
        occupied_ranges = []
        for start, end, _priority, phone in sorted(candidates, key=lambda item: (item[0], item[2], item[1])):
            if not is_overlapping(start, end):
                found_phones.append(phone)
                occupied_ranges.append((start, end))

        return found_phones

    def extract_international_phones(self, text: str) -> List[str]:
        """Извлечение международных номеров"""
        # С разделителями
        pattern_sep = (
            r'(?<!\d)'
            r'\+\d{1,3}'
            r'[\s\-\.\(\)]*\d{1,4}'
            r'[\s\-\.\(\)]*\d{1,4}'
            r'[\s\-\.]*\d{1,4}'
            r'[\s\-\.]*\d{0,4}'
            r'(?!\d)'
        )
        # Сплошной
        pattern_solid = r'(?<!\d)\+\d{8,15}(?!\d)'

        candidates = []
        for priority, pattern in enumerate((pattern_sep, pattern_solid)):
            for m in re.finditer(pattern, text):
                normalized = self.normalize_international_phone(m.group(0))
                if normalized and self.validate_international_phone(normalized):
                    candidates.append((m.start(), m.end(), priority, normalized))

        found_phones = []
        occupied_ranges = []

        def is_overlapping(start, end):
            for s, e in occupied_ranges:
                if start < e and end > s:
                    return True
            return False

        for start, end, _priority, phone in sorted(candidates, key=lambda item: (item[0], item[2], item[1])):
            if not is_overlapping(start, end):
                found_phones.append(phone)
                occupied_ranges.append((start, end))

        return found_phones

    def normalize_international_phone(self, phone: str) -> Optional[str]:
        """Нормализация международного номера"""
        phone = phone.strip()
        if phone.count('+') > 1 or '+' in phone[1:]:
            return None

        digits = re.sub(r'\D', '', phone)

        if phone.startswith('+'):
            return '+' + digits if digits else None

        return '+' + digits if len(digits) >= 10 else None

    def validate_international_phone(self, phone: str) -> bool:
        """Валидация международного номера (E.164)"""
        if not phone or not phone.startswith('+'):
            return False

        digits = phone[1:]
        if not digits.isdigit():
            return False

        if len(digits) < 8 or len(digits) > 15:
            return False

        # Все одинаковые цифры
        if len(set(digits)) == 1:
            return False

        # Одна цифра повторяется > 70%
        for digit in '0123456789':
            if digits.count(digit) > len(digits) * 0.7:
                return False

        return True

    def normalize_phone(self, phone: str) -> Optional[str]:
        """Нормализация российского номера -> 11 цифр начиная с 7"""
        digits = re.sub(r'\D', '', phone)

        if digits.startswith('8') and len(digits) == 11:
            digits = '7' + digits[1:]

        if digits.startswith('7') and len(digits) == 11:
            return digits

        return None

    def is_valid_phone(self, phone: str) -> bool:
        """Базовая валидация российского номера"""
        return (
            phone is not None
            and len(phone) == 11
            and phone.startswith('7')
            and phone.isdigit()
        )

    def validate_phone_number(self, phone: str) -> bool:
        """Расширенная валидация для исключения ложных срабатываний"""
        if not self.is_valid_phone(phone):
            return False

        # Слишком мало уникальных цифр (например 77777777777)
        if len(set(phone)) <= 3:
            return False

        # Последовательные цифры
        if self.is_sequential(phone):
            return False

        return True

    def is_sequential(self, phone: str) -> bool:
        """Проверка на длинную последовательность цифр"""
        sequential_count = 0
        for i in range(len(phone) - 1):
            if int(phone[i + 1]) == int(phone[i]) + 1 or int(phone[i + 1]) == int(phone[i]) - 1:
                sequential_count += 1
            else:
                sequential_count = 0

            if sequential_count >= 6:
                return True

        return False

    # ────────────────────────────────────────────────────────────
    # Форматирование номера
    # ────────────────────────────────────────────────────────────
    def format_phone_number(self, phone: str) -> str:
        """Форматирование номера в выбранный формат"""
        # Извлекаем чистые 11 цифр
        digits = re.sub(r'[^\d]', '', phone)
        if digits.startswith('8') and len(digits) == 11:
            digits = '7' + digits[1:]

        if len(digits) != 11 or not digits.startswith('7'):
            return phone  # Не российский — возвращаем как есть

        fmt = self.phone_format.get()
        if fmt == "plus7":
            return '+' + digits
        elif fmt == "eight":
            return '8' + digits[1:]
        elif fmt == "formatted":
            return f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
        elif fmt == "seven":
            return digits
        return '+' + digits

    def format_phone(self, phone: str) -> str:
        """Базовое форматирование (для маски)"""
        if phone.startswith('7') and not phone.startswith('+'):
            return '+' + phone
        return phone

    # ────────────────────────────────────────────────────────────
    # Обработка: дубликаты, исключения, сортировка
    # ────────────────────────────────────────────────────────────
    def process_phones(self, phones: List[str]) -> List[str]:
        """Обработка: удаление дубликатов (с сохранением порядка), исключения, сортировка"""
        result = phones.copy()

        # Исключения
        exclusions = self.get_exclusion_list()
        if exclusions:
            exclusion_keys = {self.get_phone_identity_key(p) for p in exclusions}
            result = [p for p in result if self.get_phone_identity_key(p) not in exclusion_keys]

        # Удаление дубликатов с сохранением порядка
        if self.remove_duplicates.get():
            seen = set()
            unique = []
            for p in result:
                phone_key = self.get_phone_identity_key(p)
                if phone_key not in seen:
                    seen.add(phone_key)
                    unique.append(p)
            result = unique

        # Сортировка
        sort_order = self.sort_order.get()
        if sort_order == "asc":
            result = sorted(result)
        elif sort_order == "desc":
            result = sorted(result, reverse=True)

        # Форматирование номеров
        result = [self.format_phone_number(p) for p in result]

        # Префикс / суффикс
        prefix = self.prefix_entry.get()
        suffix = self.suffix_entry.get()
        if prefix or suffix:
            result = [f"{prefix}{p}{suffix}" for p in result]

        return result

    @staticmethod
    def get_phone_identity_key(phone: str) -> str:
        """Канонический ключ для сравнения одинаковых номеров в разных форматах."""
        phone = str(phone).strip()
        if re.search(r'[^0-9+\s().-]', phone):
            return phone

        cleaned = re.sub(r'[^\d+]', '', phone)
        digits = cleaned[1:] if cleaned.startswith('+') else cleaned

        if len(digits) == 10:
            return '+7' + digits
        if digits.startswith('8') and len(digits) == 11:
            return '+7' + digits[1:]
        if digits.startswith('7') and len(digits) == 11:
            return '+' + digits
        if cleaned.startswith('+') and 8 <= len(digits) <= 15:
            return '+' + digits

        return phone

    @staticmethod
    def is_canonical_phone_key(phone: str) -> bool:
        """Проверка, что строка похожа на канонический ключ телефона."""
        return bool(re.fullmatch(r'\+\d{8,15}', phone))

    def get_duplicate_details(self, phones: List[str]) -> Dict[str, int]:
        """Подсчёт вхождений одинаковых номеров с учётом разных форматов записи."""
        counts = Counter()
        labels = {}

        for phone in phones:
            phone_key = self.get_phone_identity_key(phone)
            counts[phone_key] += 1
            labels.setdefault(phone_key, phone_key)

        return {labels[phone_key]: count for phone_key, count in counts.items()}

    def count_unique_phones(self, phones: List[str]) -> int:
        return len({self.get_phone_identity_key(phone) for phone in phones})

    def get_exclusion_list(self) -> Set[str]:
        """Получение нормализованного списка исключений"""
        exclusions_text = self.exclusions_text.get("1.0", TEXT_END).strip()
        if not exclusions_text:
            return set()

        exclusions = set()
        for line in exclusions_text.split('\n'):
            line = line.strip()
            if not line:
                continue

            candidates = self.extract_russian_phones(line) + self.extract_international_phones(line)
            if not candidates:
                candidates = [line]

            for candidate in candidates:
                phone_key = self.get_phone_identity_key(candidate)
                if self.is_canonical_phone_key(phone_key):
                    exclusions.add(phone_key)

        return exclusions

    # ────────────────────────────────────────────────────────────
    # Отображение
    # ────────────────────────────────────────────────────────────
    def update_display(self):
        """Обновление отображения"""
        if self.current_display_phones:
            phones = self.process_phones(self.current_display_phones)
            self.display_results(phones)

            total = len(self.current_display_phones)
            displayed = len(phones)
            excluded = total - displayed
            if excluded > 0:
                self.stats_label.config(text=f"Отображено: {displayed} (убрано: {excluded})")
            else:
                self.stats_label.config(text=f"Отображено: {displayed}")

        self.update_info_panel()

    def display_results(self, phones: List[str]):
        """Отображение результатов"""
        self.output_text.delete("1.0", TEXT_END)

        if not phones:
            self.output_text.insert("1.0", "Номера не найдены")
            return

        format_type = self.output_format.get()
        separators = {
            "column": "\n",
            "comma_no_space": ",",
            "comma_with_space": ", ",
            "semicolon_no_space": ";",
            "semicolon_with_space": "; ",
            "space": " ",
            "tab": "\t",
        }
        sep = separators.get(format_type, "\n")
        self.output_text.insert("1.0", sep.join(phones))

    # ────────────────────────────────────────────────────────────
    # Маска
    # ────────────────────────────────────────────────────────────
    def apply_mask(self):
        """Применение маски"""
        if not self.extracted_phones:
            messagebox.showwarning("Предупреждение", "Сначала извлеките номера!")
            return

        try:
            start_count = int(self.start_digits.get())
            start_mask_str = self.start_mask.get().strip()
            middle_pos = int(self.middle_position.get())
            middle_count = int(self.middle_digits.get())
            middle_mask_str = self.middle_mask.get().strip()
            end_count = int(self.end_digits.get())
            end_mask_str = self.end_mask.get().strip()
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректные числовые значения!")
            return

        if start_count == 0 and middle_count == 0 and end_count == 0:
            messagebox.showwarning("Предупреждение", "Задайте хотя бы одну замену!")
            return

        masked_phones = []
        for phone in self.extracted_phones:
            formatted = self.format_phone(phone)
            result = self.apply_advanced_mask(
                formatted,
                start_count, start_mask_str,
                middle_pos, middle_count, middle_mask_str,
                end_count, end_mask_str
            )
            if result:
                masked_phones.append(result)

        self.current_display_phones = masked_phones
        processed_phones = self.process_phones(masked_phones)
        self.display_results(processed_phones)

        self.stats_label.config(text=f"С маской: {len(masked_phones)} → отображено: {len(processed_phones)}")
        self._add_history("Маска", f"Обработано {len(masked_phones)} номеров")
        self.update_info_panel()

    def apply_advanced_mask(self, phone: str, start_count: int, start_mask: str,
                            middle_pos: int, middle_count: int, middle_mask: str,
                            end_count: int, end_mask: str) -> str:
        """Применение расширенной маски"""
        if phone.startswith('+'):
            phone_digits = phone[1:]
            prefix = '+'
        else:
            phone_digits = phone
            prefix = ''

        result = list(phone_digits)

        if start_count > 0 and start_mask:
            result = list(start_mask) + result[start_count:]

        if end_count > 0 and end_mask:
            result = result[:-end_count] + list(end_mask)

        if middle_count > 0 and middle_mask and middle_pos >= 0:
            if middle_pos < len(result):
                result = result[:middle_pos] + list(middle_mask) + result[middle_pos + middle_count:]

        return prefix + ''.join(result)

    # ────────────────────────────────────────────────────────────
    # Поиск
    # ────────────────────────────────────────────────────────────
    def on_search_change(self, event):
        if self.current_display_phones:
            self.search_phones()

    def search_phones(self):
        """Поиск номеров"""
        if not self.current_display_phones:
            messagebox.showwarning("Предупреждение", "Сначала извлеките номера!")
            return

        search_query = self.search_entry.get().strip()
        if not search_query:
            self.reset_search()
            return

        search_normalized = re.sub(r'[^\d+*]', '', search_query)
        processed_phones = self.process_phones(self.current_display_phones)

        search_mode = self.search_mode.get()
        found_phones = []

        for phone in processed_phones:
            phone_digits = re.sub(r'[^\d+]', '', phone)

            if search_mode == "contains":
                if '*' in search_normalized:
                    pattern = self.build_search_pattern(search_normalized)
                    if re.search(pattern, phone_digits):
                        found_phones.append(phone)
                elif search_normalized in phone_digits:
                    found_phones.append(phone)
            elif search_mode == "starts":
                if phone_digits.startswith(search_normalized):
                    found_phones.append(phone)
            elif search_mode == "ends":
                if phone_digits.endswith(search_normalized):
                    found_phones.append(phone)
            elif search_mode == "exact":
                if phone_digits == search_normalized or phone == search_normalized:
                    found_phones.append(phone)

        self.search_results = found_phones
        self.is_searching = True

        self.search_results_text.delete('1.0', TEXT_END)
        if found_phones:
            self.search_results_text.insert('1.0', '\n'.join(found_phones))
        else:
            self.search_results_text.insert('1.0', 'Ничего не найдено')

        total_count = len(processed_phones)
        found_count = len(found_phones)

        if found_count > 0:
            self.search_info_label.config(
                text=f"Найдено: {found_count} из {total_count}",
                foreground="green"
            )
        else:
            self.search_info_label.config(
                text=f"Ничего не найдено (всего: {total_count})",
                foreground="red"
            )

        self.update_info_panel()

    @staticmethod
    def build_search_pattern(search_normalized: str) -> str:
        """Преобразование пользовательского wildcard-запроса в безопасный regex."""
        return re.escape(search_normalized).replace(r'\*', '.*')

    def reset_search(self):
        """Сброс поиска"""
        self.search_entry.delete(0, TEXT_END)
        self.search_results = []
        self.is_searching = False
        self.search_info_label.config(text="")
        self.search_results_text.delete('1.0', TEXT_END)
        if self.current_display_phones:
            self.update_display()

    def copy_search_results(self):
        if not self.search_results:
            messagebox.showwarning("Предупреждение", "Нет результатов поиска для копирования!")
            return
        search_text = self.search_results_text.get('1.0', TEXT_END).strip()
        self.root.clipboard_clear()
        self.root.clipboard_append(search_text)
        messagebox.showinfo("Успех", f"Скопировано {len(self.search_results)} номеров")

    def save_search_results(self):
        if not self.search_results:
            messagebox.showwarning("Предупреждение", "Нет результатов поиска для сохранения!")
            return

        file_path = filedialog.asksaveasfilename(
            title="Сохранить результаты поиска",
            defaultextension=".txt",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
        )

        if file_path:
            try:
                search_text = self.search_results_text.get('1.0', TEXT_END).strip()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(search_text)
                messagebox.showinfo("Успех", f"Сохранено {len(self.search_results)} номеров")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка: {str(e)}")

    def show_search_in_main(self):
        """Показать результаты поиска в основном окне"""
        if not self.search_results:
            messagebox.showwarning("Предупреждение", "Нет результатов поиска!")
            return

        self.display_results(self.search_results)
        self.stats_label.config(text=f"Показаны результаты поиска: {len(self.search_results)} номеров")
        # Переключаемся на первую вкладку
        self.notebook.select(0)

    # ────────────────────────────────────────────────────────────
    # Исключения
    # ────────────────────────────────────────────────────────────
    def clear_exclusions(self):
        self.exclusions_text.delete("1.0", TEXT_END)
        self.update_display()

    def load_exclusions(self):
        file_path = filedialog.askopenfilename(
            title="Выберите файл со списком исключений",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
        )
        if file_path:
            try:
                encodings = ['utf-8', 'cp1251', 'windows-1251', 'latin-1']
                content = None
                for encoding in encodings:
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            content = f.read()
                        break
                    except UnicodeDecodeError:
                        continue
                if content is not None:
                    self.exclusions_text.delete("1.0", TEXT_END)
                    self.exclusions_text.insert("1.0", content)
                    self.update_display()
                    messagebox.showinfo("Успех", "Список исключений загружен")
                else:
                    messagebox.showerror("Ошибка", "Не удалось прочитать файл")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка: {str(e)}")

    def save_exclusions(self):
        content = self.exclusions_text.get("1.0", TEXT_END).strip()
        if not content:
            messagebox.showwarning("Предупреждение", "Список исключений пуст!")
            return

        file_path = filedialog.asksaveasfilename(
            title="Сохранить список исключений",
            defaultextension=".txt",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("Успех", "Список исключений сохранён")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка: {str(e)}")

    # ────────────────────────────────────────────────────────────
    # Очистка
    # ────────────────────────────────────────────────────────────
    def clear_all(self):
        """Очистка всех полей"""
        self.input_text.delete("1.0", TEXT_END)
        self.output_text.delete("1.0", TEXT_END)
        self.extracted_phones = []
        self.current_display_phones = []
        self.search_results = []
        self.duplicate_details = {}
        self.extraction_stats = {}
        self.is_searching = False
        self.search_entry.delete(0, TEXT_END)
        self.search_info_label.config(text="")
        self.stats_label.config(text="Найдено номеров: 0")
        self._update_input_counter()
        self.update_info_panel()

    # ────────────────────────────────────────────────────────────
    # Статистика
    # ────────────────────────────────────────────────────────────
    def update_info_panel(self):
        """Обновление панели статистики"""
        self.info_panel.config(state='normal')
        self.info_panel.delete('1.0', TEXT_END)

        if not self.current_display_phones:
            info_text = (
                "\n"
                "╔══════════════════════════════════════════════════════╗\n"
                "║        СТАТИСТИКА ОБРАБОТКИ НОМЕРОВ                 ║\n"
                "╚══════════════════════════════════════════════════════╝\n"
                "\n"
                "Статус: Ожидание обработки\n"
                "Действие: Загрузите текст и нажмите «Извлечь номера»\n"
                "\n"
                "Доступные операции:\n"
                "  * Извлечение номеров из текста\n"
                "  * Применение масок\n"
                "  * Удаление дубликатов\n"
                "  * Сортировка\n"
                "  * Исключение номеров\n"
                "  * Поиск по номерам\n"
            )
        else:
            total_extracted = len(self.extracted_phones)
            current_display = len(self.current_display_phones)
            unique_phones = self.count_unique_phones(self.current_display_phones)
            duplicates_count = current_display - unique_phones

            # Точный подсчёт: сколько убрано исключениями, сколько — дубликатами
            exclusions = self.get_exclusion_list()
            excluded_count = len(exclusions)
            exclusion_keys = {self.get_phone_identity_key(p) for p in exclusions}

            phones_after_exclusions = [
                p for p in self.current_display_phones
                if self.get_phone_identity_key(p) not in exclusion_keys
            ]
            removed_by_exclusions = current_display - len(phones_after_exclusions)

            processed = self.process_phones(self.current_display_phones)
            after_processing = len(processed)

            if self.remove_duplicates.get():
                removed_by_dedup = len(phones_after_exclusions) - self.count_unique_phones(phones_after_exclusions)
            else:
                removed_by_dedup = 0

            # Детали дубликатов
            dup_details_lines = []
            if self.duplicate_details:
                dups_sorted = sorted(
                    [(phone, count) for phone, count in self.duplicate_details.items() if count > 1],
                    key=lambda x: x[1], reverse=True
                )
                for phone, count in dups_sorted[:15]:
                    dup_details_lines.append(f"   {phone}: {count} раз")
                if len(dups_sorted) > 15:
                    dup_details_lines.append(f"   ... и ещё {len(dups_sorted) - 15} номеров")

            dup_details_text = '\n'.join(dup_details_lines) if dup_details_lines else "   Дубликатов нет"

            # Коды стран
            country_codes: Dict[str, int] = {}
            for phone in self.current_display_phones:
                if phone.startswith('+'):
                    # Определяем код страны
                    digits = phone[1:]
                    if digits.startswith('7'):
                        code = '+7'
                    elif digits.startswith('1'):
                        code = '+1'
                    elif digits.startswith('380'):
                        code = '+380'
                    elif digits.startswith('375'):
                        code = '+375'
                    elif digits.startswith('49'):
                        code = '+49'
                    else:
                        code = '+' + digits[:2]
                    country_codes[code] = country_codes.get(code, 0) + 1

            codes_lines = []
            for code in sorted(country_codes.keys()):
                count = country_codes[code]
                pct = (count / current_display * 100) if current_display > 0 else 0
                codes_lines.append(f"   {code}: {count} ({pct:.1f}%)")
            codes_display = '\n'.join(codes_lines) if codes_lines else "   Нет данных"

            # Поиск
            search_status = ""
            if self.is_searching:
                search_query = self.search_entry.get()
                mode_names = {
                    "contains": "содержит",
                    "starts": "начинается с",
                    "ends": "заканчивается на",
                    "exact": "точное совпадение",
                }
                mode_text = mode_names.get(self.search_mode.get(), "")
                search_status = (
                    f"\n"
                    f"🔍 ПОИСК:\n"
                    f"   Режим: {mode_text}\n"
                    f"   Запрос: «{search_query}»\n"
                    f"   Найдено: {len(self.search_results)} номеров\n"
                )

            sort_names = {
                'asc': 'По возрастанию',
                'desc': 'По убыванию',
                'none': 'Без сортировки',
            }
            sort_text = sort_names.get(self.sort_order.get(), '?')

            info_text = (
                "\n"
                "╔══════════════════════════════════════════════════════╗\n"
                "║        СТАТИСТИКА ОБРАБОТКИ НОМЕРОВ                 ║\n"
                "╚══════════════════════════════════════════════════════╝\n"
                "\n"
                "📊 ОБЩАЯ ИНФОРМАЦИЯ:\n"
                f"   Всего извлечено:      {total_extracted}\n"
                f"   Уникальных:           {unique_phones}\n"
                f"   Дубликатов:           {duplicates_count}\n"
                "\n"
                "📋 ДЕТАЛИ ДУБЛИКАТОВ:\n"
                f"{dup_details_text}\n"
                "\n"
                "🌍 РАСПРЕДЕЛЕНИЕ ПО КОДАМ:\n"
                f"{codes_display}\n"
                "\n"
                "🔧 ОБРАБОТКА:\n"
                f"   В текущем списке:     {current_display}\n"
                f"   Удалено исключениями: {removed_by_exclusions}\n"
                f"   Удалено дубликатов:   {removed_by_dedup}\n"
                f"   После обработки:      {after_processing}\n"
                "\n"
                "🚫 ИСКЛЮЧЕНИЯ:\n"
                f"   В списке исключений:  {excluded_count} номеров\n"
                f"   Удалено:              {removed_by_exclusions} номеров\n"
                "\n"
                "📋 НАСТРОЙКИ:\n"
                f"   Удаление дубликатов:  {'Вкл' if self.remove_duplicates.get() else 'Выкл'}\n"
                f"   Сортировка:           {sort_text}\n"
                f"   Формат вывода:        {self.get_format_name()}\n"
                f"   Формат номера:        {self.phone_format.get()}\n"
                f"{search_status}"
                "\n"
                "═══════════════════════════════════════════════════════\n"
                f"Итого отображено: {after_processing} номеров\n"
            )

        self.info_panel.insert('1.0', info_text)
        self.info_panel.config(state='disabled')

    def get_format_name(self) -> str:
        format_names = {
            "column": "В столбик",
            "comma_no_space": "Запятая (без пробела)",
            "comma_with_space": "Запятая (с пробелом)",
            "semicolon_no_space": "Точка с запятой (без пробела)",
            "semicolon_with_space": "Точка с запятой (с пробелом)",
            "space": "Пробел",
            "tab": "Табуляция",
        }
        return format_names.get(self.output_format.get(), "Неизвестно")

    def copy_stats(self):
        """Копирование статистики в буфер обмена"""
        self.info_panel.config(state='normal')
        content = self.info_panel.get('1.0', TEXT_END).strip()
        self.info_panel.config(state='disabled')
        if content:
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            messagebox.showinfo("Успех", "Статистика скопирована")

    def export_stats_json(self):
        """Экспорт статистики в JSON"""
        if not self.extraction_stats:
            messagebox.showwarning("Предупреждение", "Нет данных для экспорта!")
            return

        file_path = filedialog.asksaveasfilename(
            title="Экспорт статистики",
            defaultextension=".json",
            filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")]
        )
        if file_path:
            try:
                data = {
                    'extraction_stats': self.extraction_stats,
                    'duplicate_details': self.duplicate_details,
                    'total_phones': len(self.current_display_phones),
                    'timestamp': datetime.datetime.now().isoformat(),
                }
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                messagebox.showinfo("Успех", f"Статистика экспортирована: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка: {str(e)}")

    # ────────────────────────────────────────────────────────────
    # История операций
    # ────────────────────────────────────────────────────────────
    def _add_history(self, action: str, details: str):
        """Добавить запись в историю"""
        self.history.append({
            'time': datetime.datetime.now().strftime('%H:%M:%S'),
            'action': action,
            'details': details,
        })
        # Храним максимум 50 записей
        if len(self.history) > 50:
            self.history = self.history[-50:]

    def show_history(self):
        """Показать историю операций"""
        if not self.history:
            messagebox.showinfo("История", "История операций пуста")
            return

        win = tk.Toplevel(self.root)
        win.title("История операций")
        win.geometry("500x400")

        text = scrolledtext.ScrolledText(win, wrap=tk.WORD, font=('Courier New', 10))
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        for entry in reversed(self.history):
            text.insert(TEXT_END, f"[{entry['time']}] {entry['action']}: {entry['details']}\n")

        text.config(state='disabled')


def main():
    if tk is None:
        raise SystemExit("Tkinter is not installed. Install python3-tk or use a Python build with Tk support.")

    if HAS_DND:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    PhoneExtractorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
