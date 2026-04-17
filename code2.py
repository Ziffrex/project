import tkinter as tk
from tkinter import messagebox, colorchooser
import random
import string
import time
import os
import sys
import json
from datetime import datetime

# ---------- ПУТИ И ФАЙЛЫ ----------
if getattr(sys, 'frozen', False):
    base_path = os.path.dirname(sys.executable)
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

stats_file = os.path.join(base_path, "typing_records.txt")
settings_file = os.path.join(base_path, "ui_settings.json")
texts_ru_file = os.path.join(base_path, "texts_ru.txt")
texts_en_file = os.path.join(base_path, "texts_en.txt")

# ---------- КОНСТАНТЫ ----------
AVAILABLE_FONTS = ["Arial", "Courier New", "Consolas", "Times New Roman", "Verdana", "Comic Sans MS"]
letters_en = string.ascii_lowercase + " "
letters_ru = "йцукенгшщзхъфывапролджэячсмитьбю "

# ---------- ТЕМЫ И НАСТРОЙКИ ----------
def default_theme():
    return {
        "bg": "#121212",
        "text": "#ffffff",
        "accent": "#4CAF50",
        "button": "#1f1f1f",
        "entry": "#1a1a1a",
        "font_family": "Arial"
    }

def load_theme():
    if os.path.exists(settings_file):
        with open(settings_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return default_theme()

def save_theme():
    with open(settings_file, "w", encoding="utf-8") as f:
        json.dump(theme, f)

def apply_theme():
    root.configure(bg=theme["bg"])
    font_family = theme.get("font_family", "Arial")
    
    for frame in [menu_frame, trainer_frame, stats_frame, settings_frame]:
        frame.configure(bg=theme["bg"])

    for lbl in all_labels:
        try:
            import tkinter.font as tkfont
            size = tkfont.Font(font=lbl['font']).cget('size')
        except: size = 16
        lbl.configure(bg=theme["bg"], fg=theme["text"], font=(font_family, int(size)))

    for btn in all_buttons:
        try:
            size = tkfont.Font(font=btn['font']).cget('size')
        except: size = 14
        btn.configure(bg=theme["button"], fg=theme["text"], activebackground=theme["accent"], relief="flat", bd=0, font=(font_family, int(size)))

    text_display.configure(bg=theme["entry"], fg=theme["text"], font=(font_family, 22))
    entry.configure(bg=theme["entry"], fg=theme["text"], insertbackground=theme["text"], font=(font_family, 26))

# ---------- ЛОГИКА СТАТИСТИКИ ----------
def load_stats():
    global records
    if os.path.exists(stats_file):
        with open(stats_file, "r", encoding="utf-8") as f:
            records = [line.strip() for line in f.readlines() if line.strip()]

def save_stats():
    with open(stats_file, "w", encoding="utf-8") as f:
        for r in records: f.write(r + "\n")

def add_record(wpm, err_count):
    global records
    now = datetime.now().strftime("%d.%m %H:%M")
    new_entry = f"{int(wpm)} WPM | Ош: {err_count} ({now})"
    current_results = []
    for r in records:
        try:
            wpm_val = int(r.split()[0])
            current_results.append((wpm_val, r))
        except: continue
    current_results.append((int(wpm), new_entry))
    current_results.sort(key=lambda x: x[0], reverse=True)
    records = [x[1] for x in current_results[:5]]
    save_stats()

# ---------- ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ----------
theme = load_theme()
current_letters = letters_ru
current_mode = "random" # "random" или "text"
target = ""
start_time = None
errors = 0
records = []
all_labels = []
all_buttons = []

# ---------- ОСНОВНАЯ ЛОГИКА ТРЕНАЖЕРА ----------
def set_language(lang):
    global current_letters
    if lang == "ru":
        current_letters = letters_ru
        language_label.config(text="Язык: Русский")
    else:
        current_letters = letters_en
        language_label.config(text="Язык: English")

def set_mode(mode):
    global current_mode
    current_mode = mode
    mode_label.config(text=f"Режим: {'Случайные' if mode == 'random' else 'Осознанный текст'}")

def generate_text():
    global target, start_time, errors

    if current_mode == "random":
        raw_chars = []
        while len(raw_chars) < 60:
            ch = random.choice(current_letters)
            if ch == " " and raw_chars and raw_chars[-1] == " ": continue
            raw_chars.append(ch)
        raw = ''.join(raw_chars)
        groups = [raw[i:i+5] for i in range(0, len(raw), 5)]
        target = " ".join(groups)
    else:
        active_file = texts_ru_file if current_letters == letters_ru else texts_en_file
        lang_tag = "RU" if current_letters == letters_ru else "EN"
        
        if os.path.exists(active_file):
            with open(active_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                # Разделяем по ПУСТЫМ СТРОКАМ
                blocks = [b.strip() for b in content.split('\n\n') if b.strip()]
            if blocks:
                # Заменяем внутренние переносы на пробелы для красивого wrap
                target = random.choice(blocks).replace('\n', ' ')
            else:
                target = f"Файл {lang_tag} пуст! Разделите тексты пустой строкой."
        else:
            target = f"Файл texts_{lang_tag.lower()}.txt не найден!"

    text_display.config(state="normal")
    text_display.delete("1.0", tk.END)
    text_display.insert("1.0", target)
    text_display.config(state="disabled")
    entry.delete(0, tk.END)
    timer_label.config(text="Время: 0.00 сек")
    wpm_label.config(text="WPM: 0")
    errors_label.config(text="Ошибки: 0")
    start_time = None

def start_timer():
    global start_time
    if start_time is None:
        start_time = time.time()
        update_timer()

def update_timer():
    if start_time:
        elapsed = time.time() - start_time
        timer_label.config(text=f"Время: {elapsed:.2f} сек")
        typed = entry.get()
        if elapsed > 0:
            wpm = (len(typed) / 5) / (elapsed / 60)
            wpm_label.config(text=f"WPM: {int(wpm)}")
        root.after(50, update_timer)

def check_text(event=None):
    global errors, start_time
    typed = entry.get()
    
    if len(typed) > len(target):
        entry.delete(len(target), tk.END)
        typed = typed[:len(target)]

    text_display.config(state="normal")
    text_display.tag_remove("correct", "1.0", tk.END)
    text_display.tag_remove("wrong", "1.0", tk.END)

    errors = 0
    for i in range(len(typed)):
        if typed[i] == target[i]:
            text_display.tag_add("correct", f"1.{i}", f"1.{i+1}")
        else:
            text_display.tag_add("wrong", f"1.{i}", f"1.{i+1}")
            errors += 1
    errors_label.config(text=f"Ошибки: {errors}")
    text_display.config(state="disabled")

    if len(typed) == len(target) and len(target) > 0:
        final_time = time.time() - start_time
        final_wpm = (len(target) / 5) / (final_time / 60)
        start_time = None
        add_record(final_wpm, errors)
        messagebox.showinfo("Готово", f"Скорость: {int(final_wpm)} WPM\nОшибок: {errors}")
        go_to_menu()

def block_keys(event):
    if event.keysym == "BackSpace": return "break"

# ---------- UI ФУНКЦИИ ----------
def open_settings():
    menu_frame.pack_forget(); settings_frame.pack(fill="both", expand=True)

def back_to_menu():
    settings_frame.pack_forget(); menu_frame.pack(fill="both", expand=True)

def go_to_menu():
    global start_time
    start_time = None
    trainer_frame.pack_forget(); menu_frame.pack(fill="both", expand=True)
    update_menu_stats()

def choose_color(key):
    color = colorchooser.askcolor()[1]
    if color: theme[key] = color; apply_theme(); save_theme()

def set_font(font_name):
    theme["font_family"] = font_name; apply_theme(); save_theme()

def reset_theme():
    global theme; theme = default_theme(); apply_theme(); save_theme()

def update_menu_stats():
    stats_text = "ТОП РЕКОРДОВ (WPM):\n"
    if not records: stats_text += "нет результатов"
    else:
        for i, res in enumerate(records, 1): stats_text += f"{i}. {res}\n"
    stats_label.config(text=stats_text)

# ---------- СОЗДАНИЕ ОКОН ----------
root = tk.Tk()
root.title("Тренажёр слепой печати")
root.geometry("1280x720")

menu_frame = tk.Frame(root)
trainer_frame = tk.Frame(root)
settings_frame = tk.Frame(root)
menu_frame.pack(fill="both", expand=True)

def make_label(parent, text, size=16, pady=10):
    lbl = tk.Label(parent, text=text, font=("Arial", size))
    lbl.pack(pady=pady)
    all_labels.append(lbl)
    return lbl

def make_button(parent, text, cmd, size=14, pady=5):
    btn = tk.Button(parent, text=text, font=("Arial", size), command=cmd)
    btn.pack(pady=pady)
    all_buttons.append(btn)
    return btn

# --- МЕНЮ ---
make_label(menu_frame, "Тренажёр слепой печати", 36)
language_label = make_label(menu_frame, "Язык: Русский", 18)
mode_label = make_label(menu_frame, "Режим: Случайные", 18)

lang_frame = tk.Frame(menu_frame, bg="#121212") # временный цвет, поправится apply_theme
lang_frame.pack()
make_button(menu_frame, "Русский", lambda: set_language("ru"))
make_button(menu_frame, "English", lambda: set_language("en"))

make_label(menu_frame, "--- ВЫБОР РЕЖИМА ---", 14)
make_button(menu_frame, "Случайные символы", lambda: set_mode("random"))
make_button(menu_frame, "Текст из файла", lambda: set_mode("text"))

make_button(menu_frame, "Начать тренировку", lambda: [menu_frame.pack_forget(), trainer_frame.pack(fill="both", expand=True), generate_text()], 18, 20)
make_button(menu_frame, "Настройки", open_settings)

stats_label = tk.Label(menu_frame, font=("Arial", 16), justify="left")
stats_label.pack(pady=20)
all_labels.append(stats_label)

# --- НАСТРОЙКИ ---
make_label(settings_frame, "Цвета и шрифты", 32)
make_button(settings_frame, "Фон", lambda: choose_color("bg"))
make_button(settings_frame, "Текст", lambda: choose_color("text"))
make_button(settings_frame, "Кнопки", lambda: choose_color("button"))
make_button(settings_frame, "Поля", lambda: choose_color("entry"))
make_label(settings_frame, "Шрифты", 18)
for f in AVAILABLE_FONTS:
    make_button(settings_frame, f, lambda fn=f: set_font(fn))
make_button(settings_frame, "Сброс", reset_theme, 14, 20)
make_button(settings_frame, "Назад", back_to_menu)

# --- ТРЕНАЖЕР ---
# Настройка переноса текста и высоты
text_display = tk.Text(
    trainer_frame, 
    height=5, 
    width=60, 
    wrap="word", 
    padx=20, 
    pady=20, 
    bd=0, 
    highlightthickness=1
)
text_display.pack(pady=30)
text_display.tag_config("correct", foreground="#00ff88")
text_display.tag_config("wrong", foreground="#ff4444")

entry = tk.Entry(trainer_frame, width=60, bd=0, highlightthickness=1)
entry.pack(pady=10)
entry.bind("<KeyPress>", block_keys)
entry.bind("<KeyPress>", lambda e: start_timer(), add="+")
entry.bind("<KeyRelease>", check_text)

stats_frame = tk.Frame(trainer_frame)
stats_frame.pack(pady=20)
timer_label = make_label(stats_frame, "Время: 0.00 сек", 18)
wpm_label = make_label(stats_frame, "WPM: 0", 18)
errors_label = make_label(stats_frame, "Ошибки: 0", 18)

make_button(trainer_frame, "В меню", go_to_menu)

# ---------- ЗАПУСК ----------
load_stats()
update_menu_stats()
apply_theme()
root.mainloop()