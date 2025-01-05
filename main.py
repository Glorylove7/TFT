from time import sleep

import cv2
import numpy as np
import mss
import time
import win32api
import win32con
import tkinter as tk
import json
import threading
import os
from tkinter import font
import sys
from concurrent.futures import ThreadPoolExecutor
import keyboard
import pyautogui
from multiprocessing import Process



def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        # 获取打包时的临时目录路径
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class ScreenCapture:
    def __init__(self):
        self.root1 = tk.Tk()
        self.start_x = None
        self.start_y = None
        self.rect_id = None
        self.roi = None

        # 创建全屏透明窗口
        self.root1.attributes("-fullscreen", True)
        self.root1.attributes("-alpha", 0.3)  # 设置窗口透明度
        self.root1.configure(bg="gray")       # 背景色
        self.canvas = tk.Canvas(self.root1, cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=tk.TRUE)

        # 绑定鼠标事件
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

    def on_mouse_down(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="red", width=2
        )

    def on_mouse_drag(self, event):
        self.canvas.coords(self.rect_id, self.start_x, self.start_y, event.x, event.y)

    def on_mouse_up(self, event):
        end_x, end_y = event.x, event.y
        self.roi = {
            "top": min(self.start_y, end_y),
            "left": min(self.start_x, end_x),
            "width": abs(self.start_x - end_x),
            "height": abs(self.start_y - end_y)
        }
        self.root1.destroy()

    def run(self):
        self.root1.mainloop()
        return self.roi

def create_capture_gui():
    global captured
    global roi
    window=tk.Tk()
    window.iconbitmap(resource_path('image/avatar.ico'))
    window.title("请截图")
    window.geometry("200x100")
    window.attributes('-topmost', 1)
    def capture_screenshot():
        def run_capture():
            global captured
            global roi
            capture = ScreenCapture()
            roi = capture.run()
            captured = True
            window.after(100,window.destroy)
        threading.Thread(target=run_capture).start()
    capture_button = tk.Button(window, text="截屏选择牌库", command=capture_screenshot)
    capture_button.pack(pady=20)
    window.mainloop()





# 加载所有英雄模板
def load_all_heroes():
    with open(TEMPLATES_FILE, "r",encoding='utf-8') as file:
        templates = json.load(file)
    all_heroes = {}
    for stage, heroes in templates.items():
        all_heroes[stage]=heroes
    return all_heroes

# 英雄模板路径
TEMPLATES = {}
templates_changed = threading.Event()  # 用于检测模板改变的事件

def capture_screen(region):
    with mss.mss() as sct:
        screenshot = sct.grab(region)
        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_BGRA2RGB)
        # return cv2.cvtColor(np.array(screenshot), cv2.COLOR_BGRA2GRAY)

def match_hero(template_path, screenshot, threshold=0.6):
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    if template is None:
        raise ValueError(f"无法加载模板图片：{template_path}")
    # 模板匹配
    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    if max_val > threshold:
        h, w,_ = template.shape
        matched_image = screenshot[max_loc[1]:max_loc[1] + h, max_loc[0]:max_loc[0] + w]
        return max_loc, matched_image
    else:
        return None, None



def is_greyscale_image(image, threshold=0.8, tolerance=20):
    if image.ndim == 3:
        image=image.astype(np.int16)
        diff_rg = np.abs(image[:, :, 0] - image[:, :, 1])
        diff_gb = np.abs(image[:, :, 1] - image[:, :, 2])
        diff_rb = np.abs(image[:, :, 0] - image[:, :, 2])
        grey_pixels = (diff_rg <= tolerance) & (diff_gb <= tolerance) & (diff_rb <= tolerance)
    else:
        grey_pixels = np.ones(image.shape[:2], dtype=bool)
    grey_pixel_ratio = np.sum(grey_pixels) / grey_pixels.size
    return grey_pixel_ratio >= threshold

def click(x, y):
    win32api.SetCursorPos((x, y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
    time.sleep(0.01)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
    time.sleep(0.01)

# 更新全局 TEMPLATES
def update_templates(selected_heroes, all_heroes):
    global TEMPLATES
    all_heroes_copy={}
    for category,heroes in all_heroes.items():
        for hero,j in heroes.items():
            all_heroes_copy[hero]=j
    TEMPLATES = {hero: all_heroes_copy[hero] for hero in selected_heroes}
    templates_changed.set()


def create_hero_selection_gui():
    def toggle_false():
        global pause
        pause=False

    def toggle_true():
        global pause
        pause=True

    keyboard.add_hotkey('f1',toggle_false)
    keyboard.add_hotkey('f2',toggle_true)
    all_heroes = load_all_heroes()
    selected_heroes = []

    def on_select(hero, var):
        if var.get():
            selected_heroes.append(hero)
        else:
            selected_heroes.remove(hero)
        update_templates(selected_heroes, all_heroes)
    def on_mouse_wheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    root = tk.Tk()
    root.iconbitmap(resource_path('image/avatar.ico'))
    root.title("选择英雄")
    root.geometry("400x600")
    root.attributes('-topmost', 1)
    default_font = font.nametofont("TkDefaultFont")
    default_font.configure(family="SimHei", size=12)
    frame = tk.Frame(root)
    frame.pack(fill="both", expand=True)
    canvas = tk.Canvas(frame)
    scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollable_frame = tk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    for stage, heroes in all_heroes.items():
        stage_label = tk.Label(scrollable_frame, text=stage, font=("SimHei", 14, "bold"))
        stage_label.pack(anchor="w", padx=10, pady=5)
        for hero in heroes:
            var = tk.BooleanVar()
            checkbox = tk.Checkbutton(
                scrollable_frame,
                text=hero,
                variable=var,
                command=lambda h=hero, v=var: on_select(h, v)
            )
            checkbox.pack(anchor="w", padx=20)
    frame.bind_all("<MouseWheel>", on_mouse_wheel)
    def on_close():
        global running
        running=False
        root.quit()
        root.destroy()
        sys.exit()
    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

def match_all_heroes(templates, screenshot):
    results = {}
    with ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(match_hero, resource_path(template_path), screenshot): hero
            for hero, template_path in templates.items()
        }
        for future in futures:
            hero = futures[future]
            match, matched_image = future.result()
            if match:
                results[hero] = (match, matched_image)
    return results

# 主循环
def main_loop():
    # global pause
    global ROI
    while running:
        if pause:
            time.sleep(0.1)
            continue
        screenshot = capture_screen(ROI)
        results = match_all_heroes(TEMPLATES, screenshot)
        for hero, (match, matched_image) in results.items():
            if match:
                if is_greyscale_image(matched_image):
                    break
                x, y = match[0] + ROI["left"]+100, match[1] + ROI["top"]+100
                click(x, y)
                time.sleep(0.1)
                break

running=True
# 启动 GUI 和主循环的线程
if __name__ == "__main__":
    roi=None
    captured=False
    create_capture_gui()
    if roi:
        ROI = {"top":roi["top"],"left":roi["left"],"width":roi["width"],"height":roi["height"]}
    pause=True

    if captured:
        TEMPLATES_FILE = resource_path("templates.json")
        detection_thread = threading.Thread(target=main_loop, daemon=True)
        detection_thread.start()
        create_hero_selection_gui()
