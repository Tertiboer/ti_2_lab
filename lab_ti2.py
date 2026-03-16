import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import random

class LFSR:
    def __init__(self, polynomial_mask, initial_state):
        """
        Инициализация LFSR
        polynomial_mask: битовая маска примитивного многочлена
        initial_state: начальное состояние регистра
        """
        self.mask = polynomial_mask
        self.state = initial_state & ((1 << 24) - 1)  # 24-битный регистр
        self.original_state = self.state
        self.states_history = []
        self.key_bits = []
        self.step_count = 0  # Счетчик тактов
        
    def next_bit(self):
        """
        Генерация следующего бита ключа
        """
        # Сохраняем текущее состояние
        self.states_history.append(format(self.state, '024b'))
        
        # Получаем старший бит (выходной бит)
        output_bit = (self.state >> 23) & 1
        self.key_bits.append(output_bit)
        
        # Вычисляем бит обратной связи (XOR всех битов по маске)
        feedback = 0
        for i in range(24):
            if (self.mask >> i) & 1:
                feedback ^= (self.state >> i) & 1
        
        # Сдвигаем регистр и вставляем бит обратной связи
        self.state = ((self.state << 1) | feedback) & ((1 << 24) - 1)
        self.step_count += 1
        
        return output_bit
    
    def generate_key_stream(self, length):
        """
        Генерация ключевого потока заданной длины
        """
        self.states_history = []
        self.key_bits = []
        self.step_count = 0
        for _ in range(length):
            self.next_bit()
        return self.key_bits
    
    def get_states_history(self):
        """Возвращает историю состояний"""
        return self.states_history
    
    def get_key_bits(self):
        """Возвращает сгенерированные ключевые биты"""
        return self.key_bits
    
    def get_step_count(self):
        """Возвращает количество тактов"""
        return self.step_count
    
    def reset(self):
        """Сброс регистра в начальное состояние"""
        self.state = self.original_state
        self.states_history = []
        self.key_bits = []
        self.step_count = 0


class LFSRCipherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LFSR Потоковое шифрование - Вариант 2 (степень 24)")
        self.root.geometry("1100x950")
        
        # Примитивный многочлен для степени 24: x^24 + x^4 + x^3 + x + 1
        # Биты: 24, 4, 3, 1, 0
        self.polynomial_mask = (1 << 24) | (1 << 4) | (1 << 3) | (1 << 1) | 1
        
        self.input_file_path = ""
        self.encrypt_file_path = ""
        self.decrypt_file_path = ""
        self.plain_data = None
        self.cipher_data = None
        self.key_bits = None
        self.lfsr = None
        
        self.setup_ui()
        
    def setup_ui(self):
        # Основной фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Информация о варианте и многочлене
        info_frame = ttk.LabelFrame(main_frame, text="Информация о варианте", padding="10")
        info_frame.grid(row=0, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(info_frame, text="ВАРИАНТ 2", font=('Arial', 12, 'bold')).grid(row=0, column=0, sticky=tk.W)
        ttk.Label(info_frame, text="Примитивный многочлен: x^24 + x^4 + x^3 + x + 1", 
                 font=('Arial', 10)).grid(row=1, column=0, sticky=tk.W)
        ttk.Label(info_frame, text="Длина регистра: 24 бита | Период: 2^24 - 1 ≈ 16.7 млн бит", 
                 font=('Arial', 10)).grid(row=2, column=0, sticky=tk.W)
        ttk.Label(info_frame, text="Ячейки обратной связи: 24, 4, 3, 1, 0", 
                 font=('Arial', 10)).grid(row=3, column=0, sticky=tk.W)
        
        # Ввод начального состояния
        state_frame = ttk.LabelFrame(main_frame, text="Начальное состояние регистра (24 бита)", padding="10")
        state_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(state_frame, text="Введите 24 бита (только 0 и 1):").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.state_var = tk.StringVar()
        self.state_var.trace('w', self.validate_state_input)
        state_entry = ttk.Entry(state_frame, textvariable=self.state_var, width=30, font=('Courier', 12))
        state_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Счетчик введенных бит
        self.bits_counter = ttk.Label(state_frame, text="0 / 24", font=('Arial', 10))
        self.bits_counter.grid(row=1, column=1, padx=10)
        
        # Подсказка
        ttk.Label(state_frame, text="Пример: 1100 1010 1011 1000 0101 1100", 
                 font=('Courier', 9), foreground='gray').grid(row=2, column=0, sticky=tk.W)
        
        # Кнопки управления состоянием
        btn_frame = ttk.Frame(state_frame)
        btn_frame.grid(row=3, column=0, pady=10)
        
        ttk.Button(btn_frame, text="Случайное", command=self.generate_random_state).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Очистить", command=self.clear_state).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="Пример", command=self.show_example).grid(row=0, column=2, padx=5)
        
        # Кнопки тестовых состояний
        test_frame = ttk.LabelFrame(main_frame, text="Тестовые состояния", padding="10")
        test_frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(test_frame, text="🧪 Все нули", command=lambda: self.state_var.set("0" * 24)).grid(row=0, column=0, padx=5)
        ttk.Button(test_frame, text="🧪 Все единицы", command=lambda: self.state_var.set("1" * 24)).grid(row=0, column=1, padx=5)
        ttk.Button(test_frame, text="🧪 Чередование 1010", command=lambda: self.state_var.set("1010" * 6)).grid(row=0, column=2, padx=5)
        ttk.Button(test_frame, text="🧪 Чередование 0101", command=lambda: self.state_var.set("0101" * 6)).grid(row=0, column=3, padx=5)
        ttk.Button(test_frame, text="🧪 Пары 1100", command=lambda: self.state_var.set("1100" * 6)).grid(row=1, column=0, padx=5)
        ttk.Button(test_frame, text="🧪 Тройки 111000", command=lambda: self.state_var.set("111000" * 4)).grid(row=1, column=1, padx=5)
        ttk.Button(test_frame, text="🧪 Единица в начале", command=lambda: self.state_var.set("1" + "0" * 23)).grid(row=1, column=2, padx=5)
        ttk.Button(test_frame, text="🧪 Единица в конце", command=lambda: self.state_var.set("0" * 23 + "1")).grid(row=1, column=3, padx=5)
        
        # Файловые операции
        file_frame = ttk.LabelFrame(main_frame, text="Файловые операции", padding="10")
        file_frame.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        
        # Выбор файла для шифрования
        ttk.Button(file_frame, text="📂 Выбрать файл для ШИФРОВАНИЯ", 
                  command=self.select_file_for_encrypt).grid(row=0, column=0, padx=5, pady=5)
        
        self.encrypt_file_label = ttk.Label(file_frame, text="Не выбран", foreground='blue')
        self.encrypt_file_label.grid(row=0, column=1, padx=5, pady=5)
        
        # Выбор файла для дешифрования
        ttk.Button(file_frame, text="📂 Выбрать файл для ДЕШИФРОВАНИЯ", 
                  command=self.select_file_for_decrypt).grid(row=1, column=0, padx=5, pady=5)
        
        self.decrypt_file_label = ttk.Label(file_frame, text="Не выбран", foreground='blue')
        self.decrypt_file_label.grid(row=1, column=1, padx=5, pady=5)
        
        # Кнопки действий
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=4, column=0, columnspan=4, pady=10)
        
        self.encrypt_btn = ttk.Button(action_frame, text="ЗАШИФРОВАТЬ", 
                                      command=self.encrypt_file, state='disabled', width=20)
        self.encrypt_btn.grid(row=0, column=0, padx=20)
        
        self.decrypt_btn = ttk.Button(action_frame, text="РАСШИФРОВАТЬ", 
                                      command=self.decrypt_file, state='disabled', width=20)
        self.decrypt_btn.grid(row=0, column=1, padx=20)
        
        # Кнопки просмотра файлов
        view_frame = ttk.LabelFrame(main_frame, text="Просмотр файлов", padding="10")
        view_frame.grid(row=5, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(view_frame, text="📄 Просмотреть исходный файл", 
                  command=self.view_original_file).grid(row=0, column=0, padx=5)
        ttk.Button(view_frame, text="📄 Просмотреть зашифрованный файл", 
                  command=self.view_encrypted_file).grid(row=0, column=1, padx=5)
        ttk.Button(view_frame, text="📄 Просмотреть расшифрованный файл", 
                  command=self.view_decrypted_file).grid(row=0, column=2, padx=5)
        
        # Область для вывода
        output_frame = ttk.LabelFrame(main_frame, text="Результаты работы", padding="10")
        output_frame.grid(row=6, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Текстовое поле с прокруткой
        text_frame = ttk.Frame(output_frame)
        text_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.output_text = tk.Text(text_frame, height=25, width=110, wrap=tk.WORD, font=('Courier', 10))
        scrollbar_y = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.output_text.yview)
        scrollbar_x = ttk.Scrollbar(text_frame, orient=tk.HORIZONTAL, command=self.output_text.xview)
        self.output_text.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar_y.grid(row=0, column=1, sticky=(tk.N, tk.S))
        scrollbar_x.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Статус бар
        self.status_var = tk.StringVar()
        self.status_var.set("Готов к работе. Введите начальное состояние (24 бита) и выберите файл.")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=7, column=0, columnspan=4, sticky=(tk.W, tk.E))
        
        # Настройка весов
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(3, weight=1)
        main_frame.rowconfigure(6, weight=1)
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
    
    def validate_state_input(self, *args):
        value = self.state_var.get()
        filtered = ''.join(c for c in value if c in '01')
        if len(filtered) > 24:
            filtered = filtered[:24]
        if filtered != value:
            self.state_var.set(filtered)
        
        # Обновляем счетчик
        self.bits_counter.config(text=f"{len(filtered)} / 24")
        
        # Обновляем состояние кнопок
        state_ok = (len(filtered) == 24)
        
        if state_ok and self.encrypt_file_path and self.encrypt_file_path != "Не выбран":
            self.encrypt_btn.config(state='normal')
        else:
            self.encrypt_btn.config(state='disabled')
            
        if state_ok and self.decrypt_file_path and self.decrypt_file_path != "Не выбран":
            self.decrypt_btn.config(state='normal')
        else:
            self.decrypt_btn.config(state='disabled')
    
    def generate_random_state(self):
        state = ''.join(str(random.randint(0, 1)) for _ in range(24))
        self.state_var.set(state)
        self.status_var.set("Сгенерировано случайное начальное состояние")
    
    def clear_state(self):
        self.state_var.set("")
        self.status_var.set("Введите начальное состояние (24 бита)")
    
    def show_example(self):
        example = "110010101011100001011100"
        self.state_var.set(example)
        messagebox.showinfo("Пример", f"Установлено начальное состояние:\n{example}\n\n(24 бита: 6 групп по 4 бита)")
    
    def select_file_for_encrypt(self):
        filename = filedialog.askopenfilename(title="Выберите файл для шифрования")
        if filename:
            self.encrypt_file_path = filename
            self.encrypt_file_label.config(text=os.path.basename(filename))
            if len(self.state_var.get()) == 24:
                self.encrypt_btn.config(state='normal')
            self.status_var.set(f"Выбран файл для шифрования: {os.path.basename(filename)}")
    
    def select_file_for_decrypt(self):
        filename = filedialog.askopenfilename(title="Выберите файл для дешифрования")
        if filename:
            self.decrypt_file_path = filename
            self.decrypt_file_label.config(text=os.path.basename(filename))
            if len(self.state_var.get()) == 24:
                self.decrypt_btn.config(state='normal')
            self.status_var.set(f"Выбран файл для дешифрования: {os.path.basename(filename)}")
    
    def get_initial_state(self):
        state_str = self.state_var.get()
        if len(state_str) != 24:
            messagebox.showerror("Ошибка", f"Введите 24 бита для начального состояния (сейчас {len(state_str)})")
            return None
        
        state = 0
        for i, bit in enumerate(state_str):
            if bit == '1':
                state |= (1 << (23 - i))
        return state
    
    def encrypt_file(self):
        if not self.encrypt_file_path:
            messagebox.showerror("Ошибка", "Выберите файл для шифрования")
            return
        
        initial_state = self.get_initial_state()
        if initial_state is None:
            return
        
        try:
            # Читаем файл
            with open(self.encrypt_file_path, 'rb') as f:
                self.plain_data = f.read()
            
            # Создаем LFSR
            self.lfsr = LFSR(self.polynomial_mask, initial_state)
            self.key_bits = self.lfsr.generate_key_stream(len(self.plain_data) * 8)
            
            # Шифруем
            self.cipher_data = bytearray()
            key_bytes = []
            
            for i in range(0, len(self.key_bits), 8):
                if i + 8 <= len(self.key_bits):
                    key_byte = 0
                    for j in range(8):
                        key_byte = (key_byte << 1) | self.key_bits[i + j]
                    key_bytes.append(key_byte)
            
            for i, byte in enumerate(self.plain_data):
                if i < len(key_bytes):
                    self.cipher_data.append(byte ^ key_bytes[i])
            
            # СПРАШИВАЕМ КУДА СОХРАНИТЬ ЗАШИФРОВАННЫЙ ФАЙЛ
            base_name = os.path.basename(self.encrypt_file_path)
            suggested_name = base_name + "_encrypted"
            
            output_path = filedialog.asksaveasfilename(
                title="Сохранить зашифрованный файл как",
                initialfile=suggested_name,
                defaultextension=".*"
            )
            
            if not output_path:  # Если пользователь нажал Отмена
                messagebox.showinfo("Отмена", "Шифрование отменено")
                return
            
            # Сохраняем файл
            with open(output_path, 'wb') as f:
                f.write(self.cipher_data)
            
            # Показываем результаты
            self.display_results(operation="ШИФРОВАНИЕ")
            
            messagebox.showinfo("Успех", f"Файл зашифрован!\n\nСохранен как:\n{output_path}")
            self.status_var.set(f"Файл зашифрован: {os.path.basename(output_path)}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при шифровании: {str(e)}")
    
    def decrypt_file(self):
        if not self.decrypt_file_path:
            messagebox.showerror("Ошибка", "Выберите файл для дешифрования")
            return
        
        initial_state = self.get_initial_state()
        if initial_state is None:
            return
        
        try:
            # Читаем зашифрованный файл
            with open(self.decrypt_file_path, 'rb') as f:
                self.cipher_data = f.read()
            
            # Создаем LFSR
            self.lfsr = LFSR(self.polynomial_mask, initial_state)
            self.key_bits = self.lfsr.generate_key_stream(len(self.cipher_data) * 8)
            
            # Дешифруем
            decrypted = bytearray()
            key_bytes = []
            
            for i in range(0, len(self.key_bits), 8):
                if i + 8 <= len(self.key_bits):
                    key_byte = 0
                    for j in range(8):
                        key_byte = (key_byte << 1) | self.key_bits[i + j]
                    key_bytes.append(key_byte)
            
            for i, byte in enumerate(self.cipher_data):
                if i < len(key_bytes):
                    decrypted.append(byte ^ key_bytes[i])
            
            self.plain_data = decrypted
            
            # СПРАШИВАЕМ КУДА СОХРАНИТЬ РАСШИФРОВАННЫЙ ФАЙЛ
            base_name = os.path.basename(self.decrypt_file_path)
            # Если файл заканчивается на _encrypted, предлагаем убрать это
            if base_name.endswith('_encrypted'):
                suggested_name = base_name[:-10] + os.path.splitext(base_name[:-10])[1]
            else:
                suggested_name = base_name + "_decrypted"
            
            output_path = filedialog.asksaveasfilename(
                title="Сохранить расшифрованный файл как",
                initialfile=suggested_name,
                defaultextension=".*"
            )
            
            if not output_path:  # Если пользователь нажал Отмена
                messagebox.showinfo("Отмена", "Дешифрование отменено")
                return
            
            # Сохраняем файл
            with open(output_path, 'wb') as f:
                f.write(decrypted)
            
            # Показываем результаты
            self.display_results(operation="ДЕШИФРОВАНИЕ")
            
            messagebox.showinfo("Успех", f"Файл расшифрован!\n\nСохранен как:\n{output_path}")
            self.status_var.set(f"Файл расшифрован: {os.path.basename(output_path)}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при дешифровании: {str(e)}")
    
    def view_original_file(self):
        if hasattr(self, 'plain_data') and self.plain_data:
            self.show_file_content(self.plain_data, "Исходный файл")
        elif self.encrypt_file_path and os.path.exists(self.encrypt_file_path):
            with open(self.encrypt_file_path, 'rb') as f:
                data = f.read()
            self.show_file_content(data, f"Исходный файл: {os.path.basename(self.encrypt_file_path)}")
        else:
            messagebox.showerror("Ошибка", "Нет исходного файла для просмотра")
    
    def view_encrypted_file(self):
        if hasattr(self, 'cipher_data') and self.cipher_data:
            self.show_file_content(self.cipher_data, "Зашифрованный файл")
        else:
            messagebox.showerror("Ошибка", "Нет зашифрованного файла для просмотра")
    
    def view_decrypted_file(self):
        if hasattr(self, 'plain_data') and self.plain_data:
            self.show_file_content(self.plain_data, "Расшифрованный файл")
        else:
            messagebox.showerror("Ошибка", "Нет расшифрованного файла для просмотра")
    
    def show_file_content(self, data, title):
        """Показывает содержимое файла в новом окне"""
        view_window = tk.Toplevel(self.root)
        view_window.title(title)
        view_window.geometry("900x700")
        
        # Фрейм с текстом
        frame = ttk.Frame(view_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Информация о файле
        info_frame = ttk.Frame(frame)
        info_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(info_frame, text=f"Размер: {len(data)} байт", font=('Arial', 10)).pack(side=tk.LEFT, padx=10)
        
        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        # Создаем вкладки для разных представлений
        notebook = ttk.Notebook(frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Вкладка HEX
        hex_frame = ttk.Frame(notebook)
        notebook.add(hex_frame, text="HEX")
        
        hex_text = tk.Text(hex_frame, wrap=tk.NONE, font=('Courier', 10))
        hex_scroll_y = ttk.Scrollbar(hex_frame, orient=tk.VERTICAL, command=hex_text.yview)
        hex_scroll_x = ttk.Scrollbar(hex_frame, orient=tk.HORIZONTAL, command=hex_text.xview)
        hex_text.configure(yscrollcommand=hex_scroll_y.set, xscrollcommand=hex_scroll_x.set)
        
        hex_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        hex_scroll_y.grid(row=0, column=1, sticky=(tk.N, tk.S))
        hex_scroll_x.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        hex_frame.columnconfigure(0, weight=1)
        hex_frame.rowconfigure(0, weight=1)
        
        # Вкладка BINARY
        bin_frame = ttk.Frame(notebook)
        notebook.add(bin_frame, text="BINARY")
        
        bin_text = tk.Text(bin_frame, wrap=tk.NONE, font=('Courier', 10))
        bin_scroll_y = ttk.Scrollbar(bin_frame, orient=tk.VERTICAL, command=bin_text.yview)
        bin_scroll_x = ttk.Scrollbar(bin_frame, orient=tk.HORIZONTAL, command=bin_text.xview)
        bin_text.configure(yscrollcommand=bin_scroll_y.set, xscrollcommand=bin_scroll_x.set)
        
        bin_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        bin_scroll_y.grid(row=0, column=1, sticky=(tk.N, tk.S))
        bin_scroll_x.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        bin_frame.columnconfigure(0, weight=1)
        bin_frame.rowconfigure(0, weight=1)
        
        # Вкладка TEXT (если это текст)
        text_frame_tab = ttk.Frame(notebook)
        notebook.add(text_frame_tab, text="TEXT")
        
        text_text = tk.Text(text_frame_tab, wrap=tk.WORD, font=('Arial', 10))
        text_scroll = ttk.Scrollbar(text_frame_tab, orient=tk.VERTICAL, command=text_text.yview)
        text_text.configure(yscrollcommand=text_scroll.set)
        
        text_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        text_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        text_frame_tab.columnconfigure(0, weight=1)
        text_frame_tab.rowconfigure(0, weight=1)
        
        # HEX представление
        hex_lines = []
        for i in range(0, min(len(data), 5000), 16):
            chunk = data[i:i+16]
            hex_str = ' '.join(f'{b:02x}' for b in chunk)
            ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
            hex_lines.append(f'{i:04x}: {hex_str:<48} {ascii_str}')
        
        hex_text.insert(tk.END, '\n'.join(hex_lines))
        if len(data) > 5000:
            hex_text.insert(tk.END, f"\n\n... и еще {len(data) - 5000} байт")
        
        # BINARY представление (по 8 байт в строке)
        bin_lines = []
        for i in range(0, min(len(data), 500), 8):
            chunk = data[i:i+8]
            bin_str = ' '.join(f'{b:08b}' for b in chunk)
            hex_vals = ' '.join(f'{b:02x}' for b in chunk)
            bin_lines.append(f'{i:04x}: {bin_str} | {hex_vals}')
        
        bin_text.insert(tk.END, '\n'.join(bin_lines))
        if len(data) > 500:
            bin_text.insert(tk.END, f"\n\n... и еще {len(data) - 500} байт")
        
        # TEXT представление
        try:
            text_data = data.decode('utf-8')
            text_text.insert(tk.END, text_data[:10000])
            if len(text_data) > 10000:
                text_text.insert(tk.END, f"\n\n... [показаны первые 10000 символов из {len(text_data)}]")
        except:
            text_text.insert(tk.END, "Файл не является текстовым в кодировке UTF-8")
            text_text.insert(tk.END, "\n\nПервые 100 байт в HEX:\n")
            for i in range(min(100, len(data))):
                if i % 16 == 0:
                    text_text.insert(tk.END, f"\n{i:04x}: ")
                text_text.insert(tk.END, f"{data[i]:02x} ")
    
    def display_results(self, operation="ШИФРОВАНИЕ"):
        self.output_text.delete(1.0, tk.END)
        
        # Заголовок с вариантом
        self.output_text.insert(tk.END, "=" * 100 + "\n")
        self.output_text.insert(tk.END, f"ВАРИАНТ 2 - {operation}\n")
        self.output_text.insert(tk.END, f"Многочлен: x^24 + x^4 + x^3 + x + 1\n")
        self.output_text.insert(tk.END, "=" * 100 + "\n\n")
        
        # 1. Начальное состояние
        self.output_text.insert(tk.END, "1. НАЧАЛЬНОЕ СОСТОЯНИЕ РЕГИСТРА:\n")
        self.output_text.insert(tk.END, "-" * 50 + "\n")
        state = self.state_var.get()
        state_formatted = ' '.join([state[i:i+4] for i in range(0, 24, 4)])
        self.output_text.insert(tk.END, f"Введенное состояние: {state_formatted}\n")
        self.output_text.insert(tk.END, f"Всего бит: {len(state)}\n\n")
        
        # 2. Первые 60 тактов LFSR
        self.output_text.insert(tk.END, "2. ПЕРВЫЕ 60 ТАКТОВ РАБОТЫ LFSR:\n")
        self.output_text.insert(tk.END, "-" * 100 + "\n")
        self.output_text.insert(tk.END, "Такт | Состояние регистра (b24...b1)           | Вых.бит\n")
        self.output_text.insert(tk.END, "-" * 100 + "\n")
        
        states = self.lfsr.get_states_history()
        for i in range(min(60, len(states))):
            state = states[i]
            state_formatted = ' '.join([state[j:j+4] for j in range(0, 24, 4)])
            output_bit = state[0]
            
            # Добавляем разделитель после каждых 10 тактов
            if i > 0 and i % 10 == 0:
                self.output_text.insert(tk.END, "-" * 100 + "\n")
            
            self.output_text.insert(tk.END, f"{i+1:3d}  | {state_formatted} |     {output_bit}\n")
        
        self.output_text.insert(tk.END, f"\nВсего тактов сгенерировано: {self.lfsr.get_step_count()}\n\n")
        
        # 3. Ключевой поток (первая и последняя части)
        self.output_text.insert(tk.END, "3. СГЕНЕРИРОВАННЫЙ КЛЮЧ:\n")
        self.output_text.insert(tk.END, "-" * 50 + "\n")
        
        # Первые 60 бит
        self.output_text.insert(tk.END, "ПЕРВЫЕ 60 БИТ КЛЮЧА:\n")
        key_str_start = ''.join(str(bit) for bit in self.key_bits[:60])
        key_formatted_start = ' '.join([key_str_start[i:i+8] for i in range(0, 60, 8)])
        self.output_text.insert(tk.END, f"{key_formatted_start}\n")
        
        # Статистика первых 60 бит
        ones_start = self.key_bits[:60].count(1)
        zeros_start = 60 - ones_start
        self.output_text.insert(tk.END, f"Статистика (первые 60 бит): 1 - {ones_start}, 0 - {zeros_start}\n\n")
        
        # Последние 60 бит (если ключ длиннее 60 бит)
        if len(self.key_bits) > 60:
            self.output_text.insert(tk.END, "ПОСЛЕДНИЕ 60 БИТ КЛЮЧА:\n")
            key_str_end = ''.join(str(bit) for bit in self.key_bits[-60:])
            key_formatted_end = ' '.join([key_str_end[i:i+8] for i in range(0, 60, 8)])
            self.output_text.insert(tk.END, f"{key_formatted_end}\n")
            
            # Статистика последних 60 бит
            ones_end = self.key_bits[-60:].count(1)
            zeros_end = 60 - ones_end
            self.output_text.insert(tk.END, f"Статистика (последние 60 бит): 1 - {ones_end}, 0 - {zeros_end}\n")
        
        self.output_text.insert(tk.END, f"\nВсего сгенерировано бит ключа: {len(self.key_bits)}\n\n")
        
        # 4. Информация о файлах
        self.output_text.insert(tk.END, "4. ИНФОРМАЦИЯ О ФАЙЛАХ:\n")
        self.output_text.insert(tk.END, "-" * 50 + "\n")
        
        if operation == "ШИФРОВАНИЕ":
            self.output_text.insert(tk.END, f"Исходный файл: {os.path.basename(self.encrypt_file_path)}\n")
            self.output_text.insert(tk.END, f"Размер: {len(self.plain_data)} байт ({len(self.plain_data)*8} бит)\n")
            self.output_text.insert(tk.END, f"Зашифрованный файл: сохранен пользователем\n")
        else:
            self.output_text.insert(tk.END, f"Зашифрованный файл: {os.path.basename(self.decrypt_file_path)}\n")
            self.output_text.insert(tk.END, f"Размер: {len(self.cipher_data)} байт\n")
            self.output_text.insert(tk.END, f"Расшифрованный файл: сохранен пользователем\n")
        
        self.output_text.insert(tk.END, "\n")
        
        # 5. Данные в двоичном виде (первые 50 байт)
        self.output_text.insert(tk.END, "5. ПЕРВЫЕ 50 БАЙТ В ДВОИЧНОМ ВИДЕ:\n")
        self.output_text.insert(tk.END, "-" * 80 + "\n")
        
        if operation == "ШИФРОВАНИЕ":
            self.output_text.insert(tk.END, "ИСХОДНЫЙ ФАЙЛ:\n")
            for i in range(min(50, len(self.plain_data))):
                if i % 10 == 0 and i > 0:
                    self.output_text.insert(tk.END, "\n")
                self.output_text.insert(tk.END, f"{format(self.plain_data[i], '08b')} ")
            
            self.output_text.insert(tk.END, "\n\nЗАШИФРОВАННЫЙ ФАЙЛ:\n")
            for i in range(min(50, len(self.cipher_data))):
                if i % 10 == 0 and i > 0:
                    self.output_text.insert(tk.END, "\n")
                self.output_text.insert(tk.END, f"{format(self.cipher_data[i], '08b')} ")
        else:
            self.output_text.insert(tk.END, "ЗАШИФРОВАННЫЙ ФАЙЛ:\n")
            for i in range(min(50, len(self.cipher_data))):
                if i % 10 == 0 and i > 0:
                    self.output_text.insert(tk.END, "\n")
                self.output_text.insert(tk.END, f"{format(self.cipher_data[i], '08b')} ")
            
            self.output_text.insert(tk.END, "\n\nРАСШИФРОВАННЫЙ ФАЙЛ:\n")
            for i in range(min(50, len(self.plain_data))):
                if i % 10 == 0 and i > 0:
                    self.output_text.insert(tk.END, "\n")
                self.output_text.insert(tk.END, f"{format(self.plain_data[i], '08b')} ")
        
        self.output_text.insert(tk.END, "\n\n" + "=" * 100 + "\n")
        self.output_text.insert(tk.END, f"ВАРИАНТ 2 - {operation} ЗАВЕРШЕНО УСПЕШНО\n")
        self.output_text.insert(tk.END, "=" * 100 + "\n")


def main():
    root = tk.Tk()
    app = LFSRCipherApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
