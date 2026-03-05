import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from tkinterdnd2 import DND_FILES, TkinterDnD
import re
from typing import List, Set, Tuple
import os


class PhoneExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Извлечение номеров телефонов v2.3")
        self.root.geometry("1450x900")
        
        # Инициализация переменных ДО создания GUI
        self.extracted_phones = []
        self.current_display_phones = []
        self.search_results = []
        self.is_searching = False
        
        # Создаем основной фрейм
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Настройка весов для растягивания
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Заголовок
        title_label = ttk.Label(main_frame, text="Извлечение и форматирование номеров телефонов v2.3", 
                                font=('Arial', 14, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Кнопки для файлов (вверху)
        file_buttons_frame = ttk.Frame(main_frame)
        file_buttons_frame.grid(row=1, column=0, columnspan=2, pady=5)
        
        ttk.Button(file_buttons_frame, text="📂 Загрузить файл", 
                  command=self.load_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_buttons_frame, text="💾 Сохранить результат", 
                  command=self.save_results).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_buttons_frame, text="📋 Вставить из буфера", 
                  command=self.paste_from_clipboard).pack(side=tk.LEFT, padx=5)
        
        # Левая панель - ввод текста
        left_frame = ttk.LabelFrame(main_frame, text="Исходный текст (можно перетащить файл сюда)", padding="5")
        left_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
        self.input_text = scrolledtext.ScrolledText(left_frame, width=55, height=25, wrap=tk.WORD)
        self.input_text.pack(fill=tk.BOTH, expand=True)
        
        # Настройка Drag and Drop для input_text
        self.input_text.drop_target_register(DND_FILES)
        self.input_text.dnd_bind('<<Drop>>', self.on_drop_input)
        
        # Правая панель - результаты и настройки
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=2, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
        # Создаем вкладки
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
        
        # ═══════════════════════════════════════════════════════════
        # ВКЛАДКА 1: ОСНОВНЫЕ НАСТРОЙКИ
        # ═══════════════════════════════════════════════════════════
        
        # ═══════════════════════════════════════════════════════════
        # ВКЛАДКА 1: ОСНОВНЫЕ НАСТРОЙКИ
        # ═══════════════════════════════════════════════════════════
        
        # Настройки маски - НОВАЯ ВЕРСИЯ
        mask_frame = ttk.LabelFrame(main_tab, text="Настройки замены символами (маска)", padding="5")
        mask_frame.pack(fill=tk.X, pady=5)
        
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
        
        # Примеры использования
        examples_text = "Примеры:\n" \
                       "Начало: 2 цифры → *=  результат: *=785550015\n" \
                       "Конец: 4 цифры → *=  результат: +7978555*=\n" \
                       "Середина: позиция 5, 3 цифры → XXX  результат: +7978XXX0015"
        
        ttk.Label(mask_frame, text=examples_text, font=('Arial', 8), 
                 justify=tk.LEFT, foreground='blue').pack(pady=5)
        
        # Настройки формата вывода
        format_frame = ttk.LabelFrame(main_tab, text="Формат вывода", padding="5")
        format_frame.pack(fill=tk.X, pady=5)
        
        self.output_format = tk.StringVar(value="column")
        ttk.Radiobutton(format_frame, text="В столбик", variable=self.output_format, 
                       value="column").pack(anchor=tk.W)
        ttk.Radiobutton(format_frame, text="В строку (запятая без пробела)", variable=self.output_format, 
                       value="comma_no_space").pack(anchor=tk.W)
        ttk.Radiobutton(format_frame, text="В строку (запятая с пробелом)", variable=self.output_format, 
                       value="comma_with_space").pack(anchor=tk.W)
        ttk.Radiobutton(format_frame, text="В строку (точка с запятой без пробела)", variable=self.output_format, 
                       value="semicolon_no_space").pack(anchor=tk.W)
        ttk.Radiobutton(format_frame, text="В строку (точка с запятой с пробелом)", variable=self.output_format, 
                       value="semicolon_with_space").pack(anchor=tk.W)
        ttk.Radiobutton(format_frame, text="В строку (пробел)", variable=self.output_format, 
                       value="space").pack(anchor=tk.W)
        ttk.Radiobutton(format_frame, text="Табуляция", variable=self.output_format, 
                       value="tab").pack(anchor=tk.W)
        
        # Дополнительные опции
        options_frame = ttk.LabelFrame(main_tab, text="Дополнительные опции", padding="5")
        options_frame.pack(fill=tk.X, pady=5)
        
        self.remove_duplicates = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Удалять дубликаты", 
                       variable=self.remove_duplicates,
                       command=self.update_display).pack(anchor=tk.W)
        
        # Режим извлечения номеров
        extraction_mode_frame = ttk.LabelFrame(options_frame, text="Режим извлечения", padding="5")
        extraction_mode_frame.pack(fill=tk.X, pady=5)
        
        self.extraction_mode = tk.StringVar(value="russia_only")
        ttk.Radiobutton(extraction_mode_frame, text="Только российские номера (+7, 8)", 
                       variable=self.extraction_mode, value="russia_only").pack(anchor=tk.W)
        ttk.Radiobutton(extraction_mode_frame, text="Все международные номера (любые коды стран)", 
                       variable=self.extraction_mode, value="international").pack(anchor=tk.W)
        
        ttk.Label(extraction_mode_frame, text="💡 Совет: Международный режим может извлечь больше номеров,\nно также может захватить ложные числа.", 
                 font=('Arial', 8), foreground='blue').pack(anchor=tk.W, pady=2)
        
        # Сортировка
        sort_frame = ttk.Frame(options_frame)
        sort_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(sort_frame, text="Сортировка:").pack(side=tk.LEFT, padx=5)
        
        self.sort_order = tk.StringVar(value="asc")
        ttk.Radiobutton(sort_frame, text="По возрастанию", variable=self.sort_order, 
                       value="asc", command=self.update_display).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(sort_frame, text="По убыванию", variable=self.sort_order, 
                       value="desc", command=self.update_display).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(sort_frame, text="Без сортировки", variable=self.sort_order, 
                       value="none", command=self.update_display).pack(side=tk.LEFT, padx=5)
        
        # Кнопки управления
        button_frame = ttk.Frame(main_tab)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="🔍 Извлечь номера", 
                  command=self.extract_phones).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🎭 Применить маску", 
                  command=self.apply_mask).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🗑️ Очистить", 
                  command=self.clear_all).pack(side=tk.LEFT, padx=5)
        
        # Результаты
        result_frame = ttk.LabelFrame(main_tab, text="Результаты (все извлеченные номера)", padding="5")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.output_text = scrolledtext.ScrolledText(result_frame, width=45, height=15, wrap=tk.WORD)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Статистика
        self.stats_label = ttk.Label(main_tab, text="Найдено номеров: 0", font=('Arial', 10, 'bold'))
        self.stats_label.pack(pady=5)
        
        # ═══════════════════════════════════════════════════════════
        # ВКЛАДКА 2: ПОИСК И ФИЛЬТРЫ
        # ═══════════════════════════════════════════════════════════
        
        # ═══════════════════════════════════════════════════════════
        # ВКЛАДКА 2: ПОИСК И ФИЛЬТРЫ
        # ═══════════════════════════════════════════════════════════
        
        # Поиск по номеру
        search_frame = ttk.LabelFrame(search_tab, text="Поиск по номеру", padding="5")
        search_frame.pack(fill=tk.X, pady=5)
        
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
        
        # Опции поиска
        search_options_frame = ttk.Frame(search_frame)
        search_options_frame.pack(fill=tk.X, pady=2)
        
        self.search_mode = tk.StringVar(value="contains")
        ttk.Radiobutton(search_options_frame, text="Содержит", variable=self.search_mode, 
                       value="contains", command=self.search_phones).pack(anchor=tk.W, padx=5)
        ttk.Radiobutton(search_options_frame, text="Начинается с", variable=self.search_mode, 
                       value="starts", command=self.search_phones).pack(anchor=tk.W, padx=5)
        ttk.Radiobutton(search_options_frame, text="Заканчивается на", variable=self.search_mode, 
                       value="ends", command=self.search_phones).pack(anchor=tk.W, padx=5)
        ttk.Radiobutton(search_options_frame, text="Точное совпадение", variable=self.search_mode, 
                       value="exact", command=self.search_phones).pack(anchor=tk.W, padx=5)
        
        # Информация о поиске
        self.search_info_label = ttk.Label(search_frame, text="", foreground="blue", font=('Arial', 9))
        self.search_info_label.pack(pady=2)
        
        # Результаты поиска
        search_results_frame = ttk.LabelFrame(search_tab, text="Результаты поиска", padding="5")
        search_results_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.search_results_text = scrolledtext.ScrolledText(search_results_frame, height=15, wrap=tk.WORD)
        self.search_results_text.pack(fill=tk.BOTH, expand=True)
        
        # Кнопки для работы с результатами поиска
        search_results_buttons = ttk.Frame(search_tab)
        search_results_buttons.pack(fill=tk.X, pady=2)
        
        ttk.Button(search_results_buttons, text="📋 Копировать найденные", 
                  command=self.copy_search_results).pack(side=tk.LEFT, padx=2)
        ttk.Button(search_results_buttons, text="💾 Сохранить найденные", 
                  command=self.save_search_results).pack(side=tk.LEFT, padx=2)
        ttk.Button(search_results_buttons, text="📊 Показать в основных результатах", 
                  command=self.show_search_in_main).pack(side=tk.LEFT, padx=2)
        
        # Исключения
        exclusions_frame = ttk.LabelFrame(search_tab, text="Исключения номеров", padding="5")
        exclusions_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(exclusions_frame, text="Номера для исключения (по одному на строке):").pack(anchor=tk.W, pady=2)
        
        self.exclusions_text = scrolledtext.ScrolledText(exclusions_frame, height=5, wrap=tk.WORD)
        self.exclusions_text.pack(fill=tk.BOTH, expand=True, pady=2)
        
        exclusions_buttons_frame = ttk.Frame(exclusions_frame)
        exclusions_buttons_frame.pack(fill=tk.X, pady=2)
        
        ttk.Button(exclusions_buttons_frame, text="Применить исключения", 
                  command=self.update_display).pack(side=tk.LEFT, padx=2)
        ttk.Button(exclusions_buttons_frame, text="Очистить исключения", 
                  command=self.clear_exclusions).pack(side=tk.LEFT, padx=2)
        ttk.Button(exclusions_buttons_frame, text="Загрузить список", 
                  command=self.load_exclusions).pack(side=tk.LEFT, padx=2)
        ttk.Button(exclusions_buttons_frame, text="Сохранить список", 
                  command=self.save_exclusions).pack(side=tk.LEFT, padx=2)
        
        # ═══════════════════════════════════════════════════════════
        # ВКЛАДКА 3: СТАТИСТИКА
        # ═══════════════════════════════════════════════════════════
        
        # Информационная панель
        info_panel_frame = ttk.LabelFrame(stats_tab, text="📊 Подробная информация об обработке", padding="10")
        info_panel_frame.pack(fill=tk.BOTH, expand=True)
        
        # Создаем текстовое поле для информации
        self.info_panel = scrolledtext.ScrolledText(info_panel_frame, height=25, wrap=tk.WORD,
                                                     font=('Courier New', 10), bg='#f0f0f0')
        self.info_panel.pack(fill=tk.BOTH, expand=True)
        
        # Делаем поле только для чтения
        self.info_panel.config(state='disabled')
        
        # Кнопка обновления
        ttk.Button(stats_tab, text="🔄 Обновить статистику", 
                  command=self.update_info_panel).pack(pady=5)
        
        # Начальный текст
        self.update_info_panel()
    
    def on_drop_input(self, event):
        """Обработка drag and drop файла"""
        files = self.root.tk.splitlist(event.data)
        if files:
            file_path = files[0]
            # Убираем фигурные скобки если есть
            file_path = file_path.strip('{}')
            self.load_file_content(file_path)
    
    def load_file(self):
        """Загрузка файла"""
        file_path = filedialog.askopenfilename(
            title="Выберите файл",
            filetypes=[
                ("Текстовые файлы", "*.txt"),
                ("Все файлы", "*.*")
            ]
        )
        if file_path:
            self.load_file_content(file_path)
    
    def load_file_content(self, file_path):
        """Загрузка содержимого файла"""
        try:
            # Пробуем разные кодировки
            encodings = ['utf-8', 'cp1251', 'windows-1251', 'latin-1']
            content = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if content:
                self.input_text.delete("1.0", tk.END)
                self.input_text.insert("1.0", content)
                messagebox.showinfo("Успех", f"Файл загружен: {os.path.basename(file_path)}")
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
                content = self.output_text.get("1.0", tk.END).strip()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("Успех", f"Файл сохранен: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при сохранении: {str(e)}")
    
    def paste_from_clipboard(self):
        """Вставка текста из буфера обмена"""
        try:
            clipboard_content = self.root.clipboard_get()
            self.input_text.delete("1.0", tk.END)
            self.input_text.insert("1.0", clipboard_content)
            messagebox.showinfo("Успех", "Текст вставлен из буфера обмена")
        except:
            messagebox.showwarning("Предупреждение", "Буфер обмена пуст")
    
    def update_display(self):
        """Обновление отображения при изменении опций сортировки или дубликатов"""
        if self.current_display_phones:
            # Всегда показываем ВСЕ обработанные номера в основном окне
            # независимо от того, идет ли поиск
            phones = self.process_phones(self.current_display_phones)
            self.display_results(phones)
            
            # Подсчет исключенных
            excluded_count = len(self.current_display_phones) - len(phones)
            if excluded_count > 0:
                self.stats_label.config(text=f"Отображено номеров: {len(phones)} (исключено: {excluded_count})")
            else:
                self.stats_label.config(text=f"Отображено номеров: {len(phones)}")
        
        # Обновляем информационную панель
        self.update_info_panel()
    
    def get_exclusion_list(self) -> Set[str]:
        """Получение списка номеров для исключения"""
        exclusions_text = self.exclusions_text.get("1.0", tk.END).strip()
        if not exclusions_text:
            return set()
        
        exclusions = set()
        lines = exclusions_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Нормализуем номер для исключения
            # Убираем все кроме цифр и +
            cleaned = re.sub(r'[^\d+]', '', line)
            
            # Приводим к формату +7XXXXXXXXXX
            if cleaned.startswith('8') and len(cleaned) == 11:
                cleaned = '+7' + cleaned[1:]
            elif cleaned.startswith('7') and len(cleaned) == 11:
                cleaned = '+' + cleaned
            elif not cleaned.startswith('+'):
                # Пробуем добавить +7
                if len(cleaned) == 10:
                    cleaned = '+7' + cleaned
            
            if cleaned:
                exclusions.add(cleaned)
        
        return exclusions
    
    def clear_exclusions(self):
        """Очистка списка исключений"""
        self.exclusions_text.delete("1.0", tk.END)
        self.update_display()
    
    def load_exclusions(self):
        """Загрузка списка исключений из файла"""
        file_path = filedialog.askopenfilename(
            title="Выберите файл со списком исключений",
            filetypes=[
                ("Текстовые файлы", "*.txt"),
                ("Все файлы", "*.*")
            ]
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
                
                if content:
                    self.exclusions_text.delete("1.0", tk.END)
                    self.exclusions_text.insert("1.0", content)
                    self.update_display()
                    messagebox.showinfo("Успех", f"Список исключений загружен")
                else:
                    messagebox.showerror("Ошибка", "Не удалось прочитать файл")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при загрузке: {str(e)}")
    
    def save_exclusions(self):
        """Сохранение списка исключений в файл"""
        exclusions_content = self.exclusions_text.get("1.0", tk.END).strip()
        
        if not exclusions_content:
            messagebox.showwarning("Предупреждение", "Список исключений пуст!")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Сохранить список исключений",
            defaultextension=".txt",
            filetypes=[
                ("Текстовые файлы", "*.txt"),
                ("Все файлы", "*.*")
            ]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(exclusions_content)
                messagebox.showinfo("Успех", f"Список исключений сохранен")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при сохранении: {str(e)}")
    
    def process_phones(self, phones: List[str]) -> List[str]:
        """Обработка номеров: удаление дубликатов, исключений и сортировка"""
        result = phones.copy()
        
        # Получаем список исключений
        exclusions = self.get_exclusion_list()
        
        # Удаляем номера из списка исключений
        if exclusions:
            result = [phone for phone in result if phone not in exclusions]
        
        # Удаление дубликатов
        if self.remove_duplicates.get():
            result = list(set(result))
        
        # Сортировка
        sort_order = self.sort_order.get()
        if sort_order == "asc":
            result = sorted(result)
        elif sort_order == "desc":
            result = sorted(result, reverse=True)
        # Если "none" - оставляем как есть
        
        return result
    
    def extract_phones(self):
        """Улучшенное извлечение номеров телефонов из текста"""
        text = self.input_text.get("1.0", tk.END)
        
        extraction_mode = self.extraction_mode.get()
        
        if extraction_mode == "russia_only":
            # Режим только для российских номеров
            found_phones = self.extract_russian_phones(text)
        else:
            # Международный режим - извлекаем все номера
            found_phones = self.extract_international_phones(text)
        
        # Сохраняем найденные номера
        self.extracted_phones = sorted(list(found_phones))
        
        # Форматируем номера
        formatted_phones = self.extracted_phones.copy()
        
        # Сохраняем оригинальный список
        self.current_display_phones = formatted_phones
        
        # Применяем обработку (дубликаты, сортировка)
        processed_phones = self.process_phones(formatted_phones)
        
        # Отображаем результат
        self.display_results(processed_phones)
        
        # Обновляем статистику
        original_count = len(formatted_phones)
        processed_count = len(processed_phones)
        
        if original_count != processed_count:
            self.stats_label.config(text=f"Найдено номеров: {original_count} → Отображено: {processed_count}")
        else:
            self.stats_label.config(text=f"Найдено номеров: {processed_count}")
        
        # Обновляем информационную панель
        self.update_info_panel()
    
    def extract_russian_phones(self, text: str) -> Set[str]:
        """Извлечение только российских номеров"""
        # Множество паттернов для поиска российских номеров
        patterns = [
            r'\+7\s*\d{3}\s*\d{3}[-\s]?\d{2}[-\s]?\d{2}',  # +7 978 555-04-22
            r'\+7\d{10}',  # +79785550422
            r'8\s*\d{3}\s*\d{3}[-\s]?\d{2}[-\s]?\d{2}',  # 8 978 555-04-22
            r'8\d{10}',  # 89785550422
            r'\+7\s*\(?\d{3}\)?\s*\d{3}[-\s]?\d{2}[-\s]?\d{2}',  # +7(978)555-04-22
            r'\+7[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{3}[-\s]?\d{2}',  # +7-978-55-500-54
            r'\+7\s*\d{3}\s*\d{2}\s*\d{3}\s*\d{2}',  # +7 978 55 500 98
        ]
        
        found_phones = set()
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # Нормализуем номер
                normalized = self.normalize_phone(match)
                if normalized and self.validate_phone_number(normalized):
                    # Форматируем в +7XXXXXXXXXX
                    if normalized.startswith('7') and len(normalized) == 11:
                        found_phones.add('+' + normalized)
        
        return found_phones
    
    def extract_international_phones(self, text: str) -> Set[str]:
        """Извлечение международных номеров всех стран"""
        found_phones = set()
        
        # Паттерны для международных номеров
        patterns = [
            # Номера с + и различными разделителями
            r'\+\d{1,3}[-\s\(\)]?\d{1,4}[-\s\(\)]?\d{1,4}[-\s]?\d{1,4}[-\s]?\d{1,4}',
            # Номера с + без разделителей
            r'\+\d{8,15}',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # Нормализуем
                normalized = self.normalize_international_phone(match)
                if normalized and self.validate_international_phone(normalized):
                    found_phones.add(normalized)
        
        return found_phones
    
    def normalize_international_phone(self, phone: str) -> str:
        """Нормализация международного номера"""
        # Убираем все кроме цифр и +
        digits = re.sub(r'[^\d+]', '', phone)
        
        # Если нет + в начале, но номер длинный - добавляем
        if not digits.startswith('+') and len(digits) >= 10:
            digits = '+' + digits
        
        return digits if digits.startswith('+') else None
    
    def validate_international_phone(self, phone: str) -> bool:
        """Валидация международного номера"""
        if not phone or not phone.startswith('+'):
            return False
        
        # Убираем +
        digits = phone[1:]
        
        # Проверяем что все цифры
        if not digits.isdigit():
            return False
        
        # Длина номера: от 8 до 15 цифр (международный стандарт E.164)
        if len(digits) < 8 or len(digits) > 15:
            return False
        
        # Исключаем очевидно неправильные паттерны
        # Все одинаковые цифры (например +11111111111)
        if len(set(digits)) == 1:
            return False
        
        # Слишком много повторов одной цифры
        for digit in '0123456789':
            if digits.count(digit) > len(digits) * 0.7:  # Если одна цифра больше 70%
                return False
        
        return True
    
    def normalize_phone(self, phone: str) -> str:
        """Нормализация номера телефона - извлечение только цифр"""
        # Убираем все кроме цифр
        digits = re.sub(r'\D', '', phone)
        
        # Если начинается с 8, заменяем на 7
        if digits.startswith('8') and len(digits) == 11:
            digits = '7' + digits[1:]
        
        # Если начинается с 7 и длина 11 - это правильный номер
        if digits.startswith('7') and len(digits) == 11:
            return digits
        
        return None
    
    def is_valid_phone(self, phone: str) -> bool:
        """Базовая валидация номера"""
        if not phone or len(phone) != 11:
            return False
        
        if not phone.startswith('7'):
            return False
        
        # Проверяем что все символы - цифры
        if not phone.isdigit():
            return False
        
        return True
    
    def validate_phone_number(self, phone: str) -> bool:
        """
        Расширенная валидация номера для исключения ложных срабатываний
        """
        # Проверка базовых критериев
        if not self.is_valid_phone(phone):
            return False
        
        # Код оператора (3 цифры после 7)
        operator_code = phone[1:4]
        
        # Список реальных кодов операторов (основные)
        valid_operator_codes = [
            # Мегафон
            '920', '921', '922', '923', '924', '925', '926', '927', '928', '929',
            # МТС
            '910', '911', '912', '913', '914', '915', '916', '917', '918', '919',
            '980', '981', '982', '983', '984', '985', '986', '987', '988', '989',
            # Билайн
            '900', '901', '902', '903', '904', '905', '906', '908', '909',
            '951', '952', '953', '954', '955', '956', '957', '958', '959',
            # Теле2
            '950', '951', '952', '953',
            # Yota
            '999',
            # Ростелеком
            '930', '931', '932', '933', '934', '936', '937', '938', '939',
            # Крым
            '978',
            # Другие регионы
            '960', '961', '962', '963', '964', '965', '966', '967', '968', '969',
        ]
        
        # Если код не в списке известных, все равно пропускаем (может быть новый оператор)
        # но проверяем на очевидно неправильные паттерны
        
        # Исключаем номера с повторяющимися цифрами (например 77777777777)
        if len(set(phone)) <= 3:
            return False
        
        # Исключаем номера с последовательными цифрами (например 78901234567)
        if self.is_sequential(phone):
            return False
        
        # Исключаем номера, которые выглядят как даты или другие идентификаторы
        # Например: 71234567890 может быть ID, а не номером
        
        return True
    
    def is_sequential(self, phone: str) -> bool:
        """Проверка на последовательные цифры"""
        sequential_count = 0
        for i in range(len(phone) - 1):
            if int(phone[i+1]) == int(phone[i]) + 1 or int(phone[i+1]) == int(phone[i]) - 1:
                sequential_count += 1
            else:
                sequential_count = 0
            
            # Если 6 и более последовательных цифр - подозрительно
            if sequential_count >= 6:
                return True
        
        return False
    
    def format_phone(self, phone: str) -> str:
        """Форматирование номера в +79785550422"""
        if phone.startswith('7'):
            return '+' + phone
        return phone
    
    def apply_mask(self):
        """Применение маски с заменой указанного количества цифр"""
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
            formatted = self.format_phone(phone)  # +79785550422
            
            # Применяем маску
            result = self.apply_advanced_mask(
                formatted, 
                start_count, start_mask_str,
                middle_pos, middle_count, middle_mask_str,
                end_count, end_mask_str
            )
            
            if result:
                masked_phones.append(result)
        
        # Сохраняем оригинальный список
        self.current_display_phones = masked_phones
        
        # Применяем обработку (дубликаты, сортировка)
        processed_phones = self.process_phones(masked_phones)
        
        # Отображаем результат
        self.display_results(processed_phones)
        
        # Обновляем статистику
        original_count = len(masked_phones)
        processed_count = len(processed_phones)
        
        if original_count != processed_count:
            self.stats_label.config(text=f"Создано номеров с маской: {original_count} → Отображено: {processed_count}")
        else:
            self.stats_label.config(text=f"Создано номеров с маской: {processed_count}")
        
        # Обновляем информационную панель
        self.update_info_panel()
    
    def apply_advanced_mask(self, phone: str, start_count: int, start_mask: str,
                           middle_pos: int, middle_count: int, middle_mask: str,
                           end_count: int, end_mask: str) -> str:
        """
        Применение расширенной маски
        phone: +79785550015
        """
        # Убираем + для работы
        if phone.startswith('+'):
            phone_digits = phone[1:]  # 79785550015
            prefix = '+'
        else:
            phone_digits = phone
            prefix = ''
        
        # Преобразуем в список для удобства замены
        result = list(phone_digits)
        
        # Применяем маску для начала
        if start_count > 0 and start_mask:
            # Заменяем первые start_count цифр на start_mask
            result = list(start_mask) + result[start_count:]
        
        # Применяем маску для конца
        if end_count > 0 and end_mask:
            # Заменяем последние end_count цифр на end_mask
            result = result[:-end_count] + list(end_mask)
        
        # Применяем маску для середины
        if middle_count > 0 and middle_mask and middle_pos >= 0:
            # Заменяем middle_count цифр начиная с позиции middle_pos на middle_mask
            if middle_pos < len(result):
                result = result[:middle_pos] + list(middle_mask) + result[middle_pos + middle_count:]
        
        return prefix + ''.join(result)
    
    def display_results(self, phones: List[str]):
        """Отображение результатов в заданном формате"""
        self.output_text.delete("1.0", tk.END)
        
        if not phones:
            self.output_text.insert("1.0", "Номера не найдены")
            return
        
        format_type = self.output_format.get()
        
        if format_type == "column":
            result = "\n".join(phones)
        elif format_type == "comma_no_space":
            result = ",".join(phones)
        elif format_type == "comma_with_space":
            result = ", ".join(phones)
        elif format_type == "semicolon_no_space":
            result = ";".join(phones)
        elif format_type == "semicolon_with_space":
            result = "; ".join(phones)
        elif format_type == "space":
            result = " ".join(phones)
        elif format_type == "tab":
            result = "\t".join(phones)
        else:
            result = "\n".join(phones)
        
        self.output_text.insert("1.0", result)
    
    def clear_all(self):
        """Очистка всех полей"""
        self.input_text.delete("1.0", tk.END)
        self.output_text.delete("1.0", tk.END)
        self.extracted_phones = []
        self.current_display_phones = []
        self.search_results = []
        self.is_searching = False
        self.search_entry.delete(0, tk.END)
        self.search_info_label.config(text="")
        self.stats_label.config(text="Найдено номеров: 0")
        
        # Обновляем информационную панель
        self.update_info_panel()
    
    def on_search_change(self, event):
        """Обработка изменения в поле поиска"""
        # Автоматический поиск при вводе
        if self.current_display_phones:
            self.search_phones()
    
    def search_phones(self):
        """Поиск номеров по заданному критерию"""
        if not self.current_display_phones:
            messagebox.showwarning("Предупреждение", "Сначала извлеките номера!")
            return
        
        search_query = self.search_entry.get().strip()
        
        # Если запрос пустой - показываем все номера
        if not search_query:
            self.reset_search()
            return
        
        # Нормализуем поисковый запрос - убираем все кроме цифр и +
        search_normalized = re.sub(r'[^\d+*]', '', search_query)
        
        # Применяем базовую обработку (дубликаты, исключения, сортировка)
        processed_phones = self.process_phones(self.current_display_phones)
        
        # Выполняем поиск
        search_mode = self.search_mode.get()
        found_phones = []
        
        for phone in processed_phones:
            # Убираем форматирование для сравнения
            phone_digits = re.sub(r'[^\d+]', '', phone)
            
            if search_mode == "contains":
                # Проверка на wildcard паттерн (например: 978555*)
                if '*' in search_normalized:
                    pattern = search_normalized.replace('*', '.*')
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
        
        # Сохраняем результаты поиска
        self.search_results = found_phones
        self.is_searching = True
        
        # ВАЖНО: НЕ изменяем основное окно результатов!
        # Отображаем ТОЛЬКО в окне результатов поиска
        self.search_results_text.delete('1.0', tk.END)
        if found_phones:
            search_display = '\n'.join(found_phones)
            self.search_results_text.insert('1.0', search_display)
        else:
            self.search_results_text.insert('1.0', 'Ничего не найдено')
        
        # Информация о поиске
        total_count = len(processed_phones)
        found_count = len(found_phones)
        
        if found_count > 0:
            self.search_info_label.config(
                text=f"✓ Найдено: {found_count} из {total_count}", 
                foreground="green"
            )
        else:
            self.search_info_label.config(
                text=f"✗ Ничего не найдено (всего номеров: {total_count})", 
                foreground="red"
            )
        
        # Обновляем информационную панель
        self.update_info_panel()
        
        # Обновляем информационную панель
        self.update_info_panel()
    
    def reset_search(self):
        """Сброс поиска и отображение всех номеров"""
        self.search_entry.delete(0, tk.END)
        self.search_results = []
        self.is_searching = False
        self.search_info_label.config(text="")
        self.search_results_text.delete('1.0', tk.END)
        
        if self.current_display_phones:
            self.update_display()
    
    def copy_search_results(self):
        """Копирование результатов поиска в буфер обмена"""
        if not self.search_results:
            messagebox.showwarning("Предупреждение", "Нет результатов поиска для копирования!")
            return
        
        # Получаем текст из поля результатов
        search_text = self.search_results_text.get('1.0', tk.END).strip()
        
        # Копируем в буфер обмена
        self.root.clipboard_clear()
        self.root.clipboard_append(search_text)
        
        messagebox.showinfo("Успех", f"Скопировано {len(self.search_results)} номеров в буфер обмена")
    
    def save_search_results(self):
        """Сохранение результатов поиска в файл"""
        if not self.search_results:
            messagebox.showwarning("Предупреждение", "Нет результатов поиска для сохранения!")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Сохранить результаты поиска",
            defaultextension=".txt",
            filetypes=[
                ("Текстовые файлы", "*.txt"),
                ("CSV файлы", "*.csv"),
                ("Все файлы", "*.*")
            ]
        )
        
        if file_path:
            try:
                search_text = self.search_results_text.get('1.0', tk.END).strip()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(search_text)
                messagebox.showinfo("Успех", f"Результаты поиска сохранены: {len(self.search_results)} номеров")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при сохранении: {str(e)}")
    
    def show_search_in_main(self):
        """Отображение результатов поиска в основном окне результатов"""
        if not self.search_results:
            messagebox.showwarning("Предупреждение", "Нет результатов поиска!")
            return
        
        # Результаты уже отображаются, просто переключаемся на вкладку
        messagebox.showinfo("Информация", 
                          f"Результаты поиска ({len(self.search_results)} номеров) уже отображены на вкладке 'Основные настройки'")
    
    def update_info_panel(self):
        """Обновление информационной панели с подробной статистикой"""
        self.info_panel.config(state='normal')
        self.info_panel.delete('1.0', tk.END)
        
        if not self.current_display_phones:
            info_text = """
╔══════════════════════════════════════════════════════════════╗
║           СТАТИСТИКА ОБРАБОТКИ НОМЕРОВ                       ║
╚══════════════════════════════════════════════════════════════╝

Статус: Ожидание обработки
Действие: Загрузите текст и нажмите "Извлечь номера"

Доступные операции:
• Извлечение номеров из текста
• Применение масок
• Удаление дубликатов
• Сортировка
• Исключение номеров
• Поиск по номерам
"""
        else:
            # Собираем статистику
            total_extracted = len(self.extracted_phones)
            current_display = len(self.current_display_phones)
            
            # Применяем обработку для подсчета
            processed = self.process_phones(self.current_display_phones)
            after_processing = len(processed)
            
            # Получаем исключения
            exclusions = self.get_exclusion_list()
            excluded_count = len(exclusions)
            
            # Подсчет дубликатов
            unique_phones = len(set(self.current_display_phones))
            duplicates_count = current_display - unique_phones
            
            # Подсчет удаленных при обработке
            removed_by_exclusions = current_display - after_processing if excluded_count > 0 else 0
            
            # Статус поиска
            search_status = ""
            if self.is_searching:
                search_query = self.search_entry.get()
                search_mode_text = {
                    "contains": "содержит",
                    "starts": "начинается с",
                    "ends": "заканчивается на",
                    "exact": "точное совпадение"
                }.get(self.search_mode.get(), "")
                search_status = f"\n🔍 Поиск: {search_mode_text} '{search_query}'\n   Найдено: {len(self.search_results)} номеров"
            
            # Подсчет по кодам стран
            country_codes = {'+1': 0, '+2': 0, '+3': 0, '+4': 0, '+5': 0, 
                           '+6': 0, '+7': 0, '+8': 0, '+9': 0, 'другие': 0}
            
            for phone in processed:
                if phone.startswith('+'):
                    code = phone[:2]  # +7, +1, +2 и т.д.
                    if code in country_codes:
                        country_codes[code] += 1
                    else:
                        country_codes['другие'] += 1
                else:
                    country_codes['другие'] += 1
            
            # Формируем строку со статистикой кодов
            codes_stats = []
            for code in ['+1', '+2', '+3', '+4', '+5', '+6', '+7', '+8', '+9']:
                if country_codes[code] > 0:
                    codes_stats.append(f"   ├─ {code}: {country_codes[code]} номеров")
            if country_codes['другие'] > 0:
                codes_stats.append(f"   └─ Другие: {country_codes['другие']} номеров")
            
            codes_display = '\n'.join(codes_stats) if codes_stats else "   └─ Нет данных"
            
            sort_order_text = {
                'asc': '↑ По возрастанию',
                'desc': '↓ По убыванию',
                'none': '– Без сортировки'
            }[self.sort_order.get()]
            
            # Формируем текст
            info_text = f"""
╔══════════════════════════════════════════════════════════════╗
║           СТАТИСТИКА ОБРАБОТКИ НОМЕРОВ                       ║
╚══════════════════════════════════════════════════════════════╝

📊 ОБЩАЯ ИНФОРМАЦИЯ:
   ├─ Всего извлечено:        {total_extracted} номеров
   ├─ Уникальных номеров:     {unique_phones} номеров
   └─ Дубликатов найдено:     {duplicates_count} номеров

🌍 РАСПРЕДЕЛЕНИЕ ПО КОДАМ СТРАН:
{codes_display}

🔧 ОБРАБОТКА:
   ├─ В текущем списке:       {current_display} номеров
   ├─ После обработки:        {after_processing} номеров
   └─ Удалено при обработке:  {current_display - after_processing} номеров

🚫 ИСКЛЮЧЕНИЯ:
   ├─ Номеров в списке:       {excluded_count} номеров
   └─ Удалено исключениями:   {removed_by_exclusions} номеров

📋 НАСТРОЙКИ:
   ├─ Удаление дубликатов:    {'✓ Включено' if self.remove_duplicates.get() else '✗ Выключено'}
   ├─ Сортировка:             {sort_order_text}
   └─ Формат вывода:          {self.get_format_name()}{search_status}

═══════════════════════════════════════════════════════════════
Итого отображено: {after_processing if not self.is_searching else len(self.search_results)} номеров
"""
        
        self.info_panel.insert('1.0', info_text)
        self.info_panel.config(state='disabled')
    
    def get_format_name(self) -> str:
        """Получение читаемого названия формата вывода"""
        format_names = {
            "column": "В столбик",
            "comma_no_space": "Запятая (без пробела)",
            "comma_with_space": "Запятая (с пробелом)",
            "semicolon_no_space": "Точка с запятой (без пробела)",
            "semicolon_with_space": "Точка с запятой (с пробелом)",
            "space": "Пробел",
            "tab": "Табуляция"
        }
        return format_names.get(self.output_format.get(), "Неизвестно")


def main():
    root = TkinterDnD.Tk()
    app = PhoneExtractorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()