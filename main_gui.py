# main_gui.py
import tkinter as tk
from tkinter import scrolledtext
import network_sender  # <--- ИМПОРТИРУЕМ ВТОРОЙ ФАЙЛ
import threading  # Чтобы окно не зависало пока думает Gemini


def start_scan():
    # Очистить поле и написать "Загрузка..."
    output_text.delete(1.0, tk.END)
    output_text.insert(tk.END, "⏳ Сбор данных и анализ... Пожалуйста, подождите...")
    btn_start.config(state=tk.DISABLED)  # Блокируем кнопку

    # Запускаем в отдельном потоке, чтобы GUI не завис
    threading.Thread(target=run_logic).start()


def run_logic():
    # Вызываем главную функцию из network_sender
    result = network_sender.run_process()

    # Обновляем GUI (нужно делать это аккуратно из потока)
    output_text.delete(1.0, tk.END)
    output_text.insert(tk.END, result)
    btn_start.config(state=tk.NORMAL)  # Разблокируем кнопку


# --- Настройка окна ---
root = tk.Tk()
root.title("System Monitor AI")
root.geometry("600x500")

# Кнопка
btn_start = tk.Button(root, text="ЗАПУСТИТЬ ДИАГНОСТИКУ", font=("Arial", 14, "bold"),
                      bg="#4CAF50", fg="white", command=start_scan)
btn_start.pack(pady=20, fill=tk.X, padx=20)

# Поле вывода
output_text = scrolledtext.ScrolledText(root, font=("Consolas", 10), wrap=tk.WORD)
output_text.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

# Запуск
root.mainloop()