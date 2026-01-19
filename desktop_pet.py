"""
Enhanced Desktop Pet with AI Chat and Web Search - PART 1
Features:
- Web search integration for current information
- Intuitive chat interface with suggestions
- Smart response generation
- All original features preserved

INSTRUCTIONS:
1. Copy this entire PART 1 file and save as desktop_pet.py
2. Then copy PART 2 below and paste it at the bottom of desktop_pet.py
"""

import os
import sys

# Fix SSL certificates for PyInstaller builds
if getattr(sys, 'frozen', False):
    try:
        import certifi
        os.environ['SSL_CERT_FILE'] = certifi.where()
        os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
    except:
        # Fallback: disable SSL verification (not ideal but works)
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import tkinter as tk
from tkinter import Menu as TkMenu, simpledialog, messagebox, filedialog
from PIL import Image, ImageTk
import requests
from io import BytesIO
import subprocess
import platform
import json
import webbrowser
import datetime
import random
import threading
import urllib.parse
import re

class DesktopPet:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Desktop Pet")
        self.root.attributes('-transparentcolor', 'black')
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True)
        self.root.geometry('150x150+100+100')
        self.root.configure(bg='black')
        
        self.offset_x = 0
        self.offset_y = 0
        self.dragging = False
        
        self.app_data_dir = self.get_app_data_directory()
        self.shortcuts_file = os.path.join(self.app_data_dir, 'desktop_pet_shortcuts.json')
        self.urls_file = os.path.join(self.app_data_dir, 'desktop_pet_urls.json')
        self.settings_file = os.path.join(self.app_data_dir, 'desktop_pet_settings.json')
        self.custom_shortcuts = []
        self.custom_urls = []
        self.stay_on_desktop = tk.BooleanVar(value=False)
        self.custom_image_path = None
        
        self.console_window = None
        self.console_text = None
        self.console_buffer = []
        
        self.chat_window = None
        self.chat_display = None
        self.chat_input = None
        self.chat_history = []
        
        self.load_settings()
        self.load_gif()
        
        self.label = tk.Label(self.root, bg='black', bd=0)
        self.label.pack()
        
        self.label.bind('<Button-1>', self.start_drag)
        self.label.bind('<B1-Motion>', self.drag)
        self.label.bind('<ButtonRelease-1>', self.stop_drag)
        self.label.bind('<Button-3>', self.show_menu)
        
        self.create_menu()
        self.current_frame = 0
        self.animate()
        self.root.mainloop()
    
    def get_app_data_directory(self):
        system = platform.system()
        if system == 'Windows':
            app_data = os.path.join(os.environ.get('APPDATA', ''), 'DesktopPet')
        elif system == 'Darwin':
            app_data = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'DesktopPet')
        else:
            app_data = os.path.join(os.path.expanduser('~'), '.local', 'share', 'DesktopPet')
        
        if not os.path.exists(app_data):
            os.makedirs(app_data)
        return app_data
    
    def load_gif(self):
        try:
            if self.custom_image_path and os.path.exists(self.custom_image_path):
                img = Image.open(self.custom_image_path)
            else:
                url = "https://media.tenor.com/Ot-v5CHE2TUAAAAM/yoojung-gif-kim-yoo-jung.gif"
                # Disable SSL verification if running as EXE
                verify_ssl = not getattr(sys, 'frozen', False)
                response = requests.get(url, timeout=5, verify=verify_ssl)
                img = Image.open(BytesIO(response.content))
            
            self.frames = []
            w, h = img.size
            nw, nh = int(w * 0.6), int(h * 0.6)
            
            try:
                img.seek(1)
                is_animated = True
                img.seek(0)
            except EOFError:
                is_animated = False
            
            if is_animated:
                try:
                    while True:
                        frame = img.copy().convert('RGBA').resize((nw, nh), Image.Resampling.LANCZOS)
                        self.frames.append(ImageTk.PhotoImage(frame))
                        img.seek(len(self.frames))
                except EOFError:
                    pass
            else:
                frame = img.convert('RGBA').resize((nw, nh), Image.Resampling.LANCZOS)
                self.frames.append(ImageTk.PhotoImage(frame))
            
            if self.frames:
                self.root.geometry(f'{nw}x{nh}+100+100')
                self.current_frame = 0
        except Exception as e:
            self.log_to_console(f"Error loading image: {e}")
            self.frames = [ImageTk.PhotoImage(Image.new('RGBA', (80, 80), (255, 0, 0, 255)))]
    
    def animate(self):
        if self.frames:
            self.label.config(image=self.frames[self.current_frame])
            self.current_frame = (self.current_frame + 1) % len(self.frames)
        self.root.after(100, self.animate)
    
    def start_drag(self, e):
        self.dragging = True
        self.offset_x, self.offset_y = e.x, e.y
    
    def drag(self, e):
        if self.dragging:
            self.root.geometry(f'+{self.root.winfo_x() + e.x - self.offset_x}+{self.root.winfo_y() + e.y - self.offset_y}')
    
    def stop_drag(self, e):
        self.dragging = False
    
    def load_settings(self):
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    s = json.load(f)
                    self.stay_on_desktop.set(s.get('stay_on_desktop', False))
                    self.custom_image_path = s.get('custom_image_path')
                    self.update_window_level()
        except:
            pass
    
    def save_settings(self):
        try:
            with open(self.settings_file, 'w') as f:
                json.dump({'stay_on_desktop': self.stay_on_desktop.get(), 
                          'custom_image_path': self.custom_image_path}, f, indent=2)
        except:
            pass
    
    def update_window_level(self):
        self.root.attributes('-topmost', not self.stay_on_desktop.get())
        if self.stay_on_desktop.get():
            self.root.lower()
    
    def toggle_stay_on_desktop(self):
        self.update_window_level()
        self.save_settings()
    
    def load_custom_shortcuts(self):
        try:
            if os.path.exists(self.shortcuts_file):
                with open(self.shortcuts_file, 'r') as f:
                    self.custom_shortcuts = json.load(f)
            else:
                self.custom_shortcuts = []
        except:
            self.custom_shortcuts = []
    
    def load_custom_urls(self):
        try:
            if os.path.exists(self.urls_file):
                with open(self.urls_file, 'r') as f:
                    self.custom_urls = json.load(f)
            else:
                self.custom_urls = []
        except:
            self.custom_urls = []
    
    def save_custom_shortcuts(self):
        try:
            with open(self.shortcuts_file, 'w') as f:
                json.dump(self.custom_shortcuts, f, indent=2)
        except:
            pass
    
    def save_custom_urls(self):
        try:
            with open(self.urls_file, 'w') as f:
                json.dump(self.custom_urls, f, indent=2)
        except:
            pass
    
    def recreate_menu(self):
        try:
            if hasattr(self, 'menu'):
                self.menu.delete(0, 'end')
        except:
            pass
        self.create_menu()
    
    def create_menu(self):
        self.menu = TkMenu(self.root, tearoff=0, bg='#3d3d5c', fg='#ffffff',
                          activebackground='#4d4d6c', activeforeground='#ffffff',
                          relief='solid', bd=1, font=('Segoe UI', 10))
        
        self.menu.add_command(label="  📝 Notepad", command=self.open_notepad)
        self.menu.add_command(label="  🔢 Calculator", command=self.open_calculator)
        self.menu.add_command(label="  📂 Downloads", command=self.open_downloads)
        self.menu.add_separator()
        
        self.load_custom_shortcuts()
        self.load_custom_urls()
        
        self.apps_submenu = TkMenu(self.menu, tearoff=0, bg='#3d3d5c', fg='#ffffff',
                                   activebackground='#4d4d6c', activeforeground='#ffffff',
                                   relief='solid', bd=1, font=('Segoe UI', 10))
        if self.custom_shortcuts:
            for s in self.custom_shortcuts:
                self.apps_submenu.add_command(label=f"  {s.get('name', 'Unknown')}", 
                                              command=lambda p=s.get('path', ''): self.open_custom_path(p))
        else:
            self.apps_submenu.add_command(label="  (No apps)", state='disabled')
        self.apps_submenu.add_separator()
        self.apps_submenu.add_command(label="  ➕ Add", command=self.add_custom_shortcut)
        self.apps_submenu.add_command(label="  🗑️ Remove", command=self.delete_custom_shortcut)
        self.menu.add_cascade(label="  💻 My Apps", menu=self.apps_submenu)
        
        self.urls_submenu = TkMenu(self.menu, tearoff=0, bg='#3d3d5c', fg='#ffffff',
                                   activebackground='#4d4d6c', activeforeground='#ffffff',
                                   relief='solid', bd=1, font=('Segoe UI', 10))
        if self.custom_urls:
            for u in self.custom_urls:
                self.urls_submenu.add_command(label=f"  {u.get('name', 'Unknown')}", 
                                             command=lambda url=u.get('url', ''): self.open_url(url))
        else:
            self.urls_submenu.add_command(label="  (No URLs)", state='disabled')
        self.urls_submenu.add_separator()
        self.urls_submenu.add_command(label="  ➕ Add", command=self.add_custom_url)
        self.urls_submenu.add_command(label="  🗑️ Remove", command=self.delete_custom_url)
        self.menu.add_cascade(label="  🌐 My URLs", menu=self.urls_submenu)
        
        self.menu.add_separator()
        self.menu.add_command(label="  🖼️ Change Image", command=self.change_pet_image)
        self.menu.add_checkbutton(label="  📌 Desktop Only", variable=self.stay_on_desktop,
                                 command=self.toggle_stay_on_desktop, selectcolor='#4d4d6c')
        self.menu.add_separator()
        self.menu.add_command(label="  📂 Settings Folder", command=self.open_settings_folder)
        self.menu.add_command(label="  💬 Chat with Pet", command=self.toggle_chat)
        self.menu.add_command(label="  ❓ Help", command=self.show_help)
        self.menu.add_command(label="  🛠️ Console", command=self.toggle_console)
        self.menu.add_command(label="  💻 Add to Startup", command=self.add_to_startup)
        self.menu.add_separator()
        self.menu.add_command(label="  ❌ Close", command=self.root.quit,
                             foreground='#ff6b6b', activeforeground='#ff8888')
    
    def show_menu(self, e):
        try:
            self.menu.tk_popup(e.x_root, e.y_root)
        finally:
            self.menu.grab_release()
    
    def open_settings_folder(self):
        system = platform.system()
        try:
            if system == 'Windows':
                os.startfile(self.app_data_dir)
            elif system == 'Darwin':
                subprocess.Popen(['open', self.app_data_dir])
            else:
                subprocess.Popen(['xdg-open', self.app_data_dir])
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def open_notepad(self):
        system = platform.system()
        try:
            if system == 'Windows':
                subprocess.Popen(['notepad.exe'])
            elif system == 'Darwin':
                subprocess.Popen(['open', '-a', 'TextEdit'])
            else:
                subprocess.Popen(['gedit'])
        except:
            pass
    
    def open_calculator(self):
        system = platform.system()
        try:
            if system == 'Windows':
                subprocess.Popen(['calc.exe'])
            elif system == 'Darwin':
                subprocess.Popen(['open', '-a', 'Calculator'])
            else:
                subprocess.Popen(['gnome-calculator'])
        except:
            pass
    
    def open_downloads(self):
        system = platform.system()
        try:
            path = os.path.join(os.path.expanduser('~'), 'Downloads')
            if system == 'Windows':
                os.startfile(path)
            elif system == 'Darwin':
                subprocess.Popen(['open', path])
            else:
                subprocess.Popen(['xdg-open', path])
        except:
            pass
    
    def add_custom_url(self):
        name = simpledialog.askstring("Add URL", "Enter name:")
        if not name:
            return
        url = simpledialog.askstring("Enter URL", "Enter full URL (https://...):")
        if url and url.startswith(('http://', 'https://')):
            self.custom_urls.append({'name': name, 'url': url})
            self.save_custom_urls()
            self.recreate_menu()
            messagebox.showinfo("Success", f"Added: {name}")
    
    def delete_custom_url(self):
        if not self.custom_urls:
            messagebox.showinfo("No URLs", "No URLs to delete")
            return
        
        win = tk.Toplevel(self.root)
        win.title("Delete URL")
        win.geometry("400x450")
        win.configure(bg='#1e1e1e')
        win.attributes('-topmost', True)
        
        tk.Label(win, text="Delete URL", bg='#1e1e1e', fg='#fff',
                font=('Segoe UI', 16, 'bold')).pack(pady=20)
        
        lb = tk.Listbox(win, bg='#2d2d30', fg='#f0f0f0', font=('Segoe UI', 10),
                       selectbackground='#3e3e42', selectforeground='#fff', relief='flat')
        lb.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        for u in self.custom_urls:
            lb.insert(tk.END, f"  🌐 {u['name']}")
        
        def do_del():
            sel = lb.curselection()
            if sel and messagebox.askyesno("Confirm", f"Delete '{self.custom_urls[sel[0]]['name']}'?"):
                self.custom_urls.pop(sel[0])
                self.save_custom_urls()
                self.recreate_menu()
                win.destroy()
        
        frm = tk.Frame(win, bg='#1e1e1e')
        frm.pack(pady=(0, 20))
        tk.Button(frm, text="Delete", command=do_del, bg='#d32f2f', fg='white',
                 font=('Segoe UI', 10, 'bold'), padx=25, pady=8, relief='flat').pack(side=tk.LEFT, padx=5)
        tk.Button(frm, text="Cancel", command=win.destroy, bg='#424242', fg='white',
                 font=('Segoe UI', 10), padx=25, pady=8, relief='flat').pack(side=tk.LEFT, padx=5)
    
    def open_url(self, url):
        try:
            webbrowser.open(url)
        except:
            pass
    
    def add_custom_shortcut(self):
        name = simpledialog.askstring("Add Shortcut", "Enter name:")
        if not name:
            return
        
        choice = messagebox.askquestion("Type", "Select FILE?\n\nYes = File\nNo = Folder/Command")
        if choice == 'yes':
            path = filedialog.askopenfilename()
        else:
            fc = messagebox.askquestion("Type", "FOLDER?\n\nYes = Folder\nNo = Command")
            path = filedialog.askdirectory() if fc == 'yes' else simpledialog.askstring("Path", "Enter command:")
        
        if path:
            self.custom_shortcuts.append({'name': name, 'path': path})
            self.save_custom_shortcuts()
            self.recreate_menu()
            messagebox.showinfo("Success", f"Added: {name}")
    
    def delete_custom_shortcut(self):
        if not self.custom_shortcuts:
            messagebox.showinfo("No Shortcuts", "No shortcuts")
            return
        
        win = tk.Toplevel(self.root)
        win.title("Delete Shortcut")
        win.geometry("400x450")
        win.configure(bg='#1e1e1e')
        win.attributes('-topmost', True)
        
        tk.Label(win, text="Delete Shortcut", bg='#1e1e1e', fg='#fff',
                font=('Segoe UI', 16, 'bold')).pack(pady=20)
        
        lb = tk.Listbox(win, bg='#2d2d30', fg='#f0f0f0', font=('Segoe UI', 10),
                       selectbackground='#3e3e42', selectforeground='#fff', relief='flat')
        lb.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        for s in self.custom_shortcuts:
            lb.insert(tk.END, f"  📎 {s['name']}")
        
        def do_del():
            sel = lb.curselection()
            if sel and messagebox.askyesno("Confirm", f"Delete '{self.custom_shortcuts[sel[0]]['name']}'?"):
                self.custom_shortcuts.pop(sel[0])
                self.save_custom_shortcuts()
                self.recreate_menu()
                win.destroy()
        
        frm = tk.Frame(win, bg='#1e1e1e')
        frm.pack(pady=(0, 20))
        tk.Button(frm, text="Delete", command=do_del, bg='#d32f2f', fg='white',
                 font=('Segoe UI', 10, 'bold'), padx=25, pady=8, relief='flat').pack(side=tk.LEFT, padx=5)
        tk.Button(frm, text="Cancel", command=win.destroy, bg='#424242', fg='white',
                 font=('Segoe UI', 10), padx=25, pady=8, relief='flat').pack(side=tk.LEFT, padx=5)
    
    def open_custom_path(self, path):
        system = platform.system()
        try:
            if os.path.exists(path):
                if system == 'Windows':
                    os.startfile(path)
                elif system == 'Darwin':
                    subprocess.Popen(['open', path])
                else:
                    subprocess.Popen(['xdg-open', path])
            else:
                subprocess.Popen(path if system != 'Windows' else path, shell=True)
        except:
            pass
    
    def change_pet_image(self):
        path = filedialog.askopenfilename(title="Select image/GIF",
                                         filetypes=[("Images", "*.gif *.png *.jpg *.jpeg")])
        if path:
            try:
                Image.open(path).close()
                self.custom_image_path = path
                self.save_settings()
                self.load_gif()
                messagebox.showinfo("Success", "Image changed!")
            except:
                messagebox.showerror("Error", "Could not load image")
    
    def show_help(self):
        messagebox.showinfo("Help", """Desktop Pet - Help

🎮 CONTROLS:
• Left-click + drag to move
• Right-click for menu

💬 CHAT FEATURES:
• Ask any question
• Web search automatically
• Current events & news
• Time, jokes, tips & more

💡 EXAMPLES:
"what's the weather in NYC?"
"latest news on AI"
"tell me a joke"
"what time is it?"

Settings save automatically!""")

# ===== PART 2 CONTINUES BELOW - COPY EVERYTHING FROM HERE DOWN =====
    
    def log_to_console(self, msg):
        self.console_buffer.append(msg)
        if self.console_text:
            self.console_text.insert(tk.END, msg + "\n")
            self.console_text.see(tk.END)
        print(msg)
    
    def toggle_console(self):
        if self.console_window and self.console_window.winfo_exists():
            self.console_window.destroy()
            self.console_window = self.console_text = None
        else:
            self.show_console()
    
    def show_console(self):
        self.console_window = tk.Toplevel(self.root)
        self.console_window.title("Debug Console")
        self.console_window.geometry("650x400")
        self.console_window.configure(bg='#1e1e1e')
        self.console_window.attributes('-topmost', True)
        
        tk.Label(self.console_window, text="🛠️ Debug Console", bg='#1e1e1e',
                fg='#4CAF50', font=('Segoe UI', 14, 'bold')).pack(pady=15)
        
        frm = tk.Frame(self.console_window, bg='#0a0a0a')
        frm.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        sb = tk.Scrollbar(frm)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.console_text = tk.Text(frm, bg='#0a0a0a', fg='#00ff00', font=('Consolas', 9),
                                   wrap=tk.WORD, yscrollcommand=sb.set, relief='flat', padx=10, pady=10)
        self.console_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.config(command=self.console_text.yview)
        
        for msg in self.console_buffer:
            self.console_text.insert(tk.END, msg + "\n")
        
        bf = tk.Frame(self.console_window, bg='#1e1e1e')
        bf.pack(pady=(0, 15))
        tk.Button(bf, text="Clear", command=lambda: (self.console_text.delete(1.0, tk.END), self.console_buffer.clear()),
                 bg='#424242', fg='white', font=('Segoe UI', 10), padx=20, pady=8, relief='flat').pack(side=tk.LEFT, padx=5)
        tk.Button(bf, text="Close", command=self.console_window.destroy, bg='#4CAF50', fg='white',
                 font=('Segoe UI', 10, 'bold'), padx=25, pady=8, relief='flat').pack(side=tk.LEFT, padx=5)
    
    def toggle_chat(self):
        if self.chat_window and self.chat_window.winfo_exists():
            self.chat_window.destroy()
            self.chat_window = self.chat_display = self.chat_input = None
        else:
            self.show_chat()
    
    def show_chat(self):
        self.chat_window = tk.Toplevel(self.root)
        self.chat_window.title("AI Pet Assistant")
        self.chat_window.geometry("580x780")
        self.chat_window.minsize(520, 700)
        self.chat_window.configure(bg='#2b2d31')
        self.chat_window.attributes('-topmost', True)
        
        hdr = tk.Frame(self.chat_window, bg='#1e1f22', height=80)
        hdr.pack(fill=tk.X, side=tk.TOP)
        hdr.pack_propagate(False)
        
        tk.Label(hdr, text="🤖 AI Pet Assistant", bg='#1e1f22', fg='#fff',
                font=('Segoe UI', 18, 'bold')).pack(pady=(12, 4))
        tk.Label(hdr, text="Ask me anything! I search the web for current information.", bg='#1e1f22',
                fg='#949ba4', font=('Segoe UI', 10)).pack()
        
        btm = tk.Frame(self.chat_window, bg='#2b2d31', height=140)
        btm.pack(fill=tk.X, side=tk.BOTTOM)
        btm.pack_propagate(False)
        
        tk.Label(btm, text="💡 Try: 'latest AI news' • 'weather in NYC' • 'tell me a joke'",
                bg='#2b2d31', fg='#949ba4', font=('Segoe UI', 9)).pack(side=tk.BOTTOM, pady=10)
        
        inp_frm = tk.Frame(btm, bg='#2b2d31')
        inp_frm.pack(fill=tk.BOTH, expand=True, padx=18, pady=(12, 5))
        
        self.chat_input = tk.Entry(inp_frm, bg='#383a40', fg='#dbdee1', font=('Segoe UI', 11),
                                   relief='solid', insertbackground='#dbdee1', borderwidth=1,
                                   highlightthickness=2, highlightbackground='#5865f2', highlightcolor='#5865f2')
        self.chat_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, ipady=15, padx=(0, 12))
        self.chat_input.bind('<Return>', lambda e: self.send_chat_message())
        self.chat_input.bind('<Escape>', lambda e: self.chat_window.destroy())
        self.chat_input.focus_set()
        
        tk.Button(inp_frm, text="Send", command=self.send_chat_message,
                 bg='#5865f2', fg='white', font=('Segoe UI', 11, 'bold'),
                 padx=32, pady=16, relief='flat', cursor='hand2').pack(side=tk.RIGHT)
        
        chat_frm = tk.Frame(self.chat_window, bg='#313338')
        chat_frm.pack(fill=tk.BOTH, expand=True, padx=18, pady=16)
        
        sb = tk.Scrollbar(chat_frm)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.chat_display = tk.Text(chat_frm, bg='#313338', fg='#dbdee1', font=('Segoe UI', 10),
                                   wrap=tk.WORD, yscrollcommand=sb.set, relief='flat', padx=16, pady=16,
                                   spacing1=6, spacing3=6, state=tk.DISABLED, cursor='arrow')
        self.chat_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.config(command=self.chat_display.yview)
        
        self.chat_display.tag_config('user', foreground='#00a8fc', font=('Segoe UI', 11, 'bold'))
        self.chat_display.tag_config('pet', foreground='#23a55a', font=('Segoe UI', 11, 'bold'))
        self.chat_display.tag_config('system', foreground='#949ba4', font=('Segoe UI', 9, 'italic'))
        self.chat_display.tag_config('searching', foreground='#faa61a', font=('Segoe UI', 9, 'italic'))
        self.chat_display.tag_config('content', foreground='#dbdee1', font=('Segoe UI', 10), spacing1=2, spacing3=2)
        self.chat_display.tag_config('link', foreground='#00a8fc', font=('Segoe UI', 9), underline=True)
        self.chat_display.tag_config('divider', foreground='#4a4d52')
        
        self.add_chat_message('system', "👋 Hi! I'm your AI assistant. I can answer questions and search the web for you. What would you like to know?")
        self.chat_window.after(100, lambda: self.chat_input.focus_force())
    
    def add_chat_message(self, sender, message):
        if not self.chat_display:
            return
        
        self.chat_display.config(state=tk.NORMAL)
        
        if sender == 'user':
            self.chat_display.insert(tk.END, "You: ", 'user')
            self.chat_display.insert(tk.END, message + "\n\n")
        elif sender == 'pet':
            self.chat_display.insert(tk.END, "🤖 Pet: ", 'pet')
            
            # Format the message with better styling
            self.format_pet_message(message)
            
            self.chat_display.insert(tk.END, "\n")
            # Add a subtle divider
            self.chat_display.insert(tk.END, "─" * 60 + "\n\n", 'divider')
        elif sender == 'searching':
            self.chat_display.insert(tk.END, message + "\n", 'searching')
        else:
            self.chat_display.insert(tk.END, "→ ", 'system')
            self.chat_display.insert(tk.END, message + "\n\n", 'system')
        
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
    
    def format_pet_message(self, message):
        """Format pet messages with better styling and ALL clickable links"""
        import time
        
        # Split into lines
        lines = message.split('\n')
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Empty line
            if not line_stripped:
                self.chat_display.insert(tk.END, "\n")
                continue
            
            # Check if this line is a source link
            if line_stripped.startswith('🔗 Source:'):
                # Extract URL (everything after "🔗 Source: ")
                url = line_stripped.replace('🔗 Source:', '').strip()
                
                if url:
                    # Insert the label part
                    self.chat_display.insert(tk.END, "   🔗 Source: ", 'content')
                    
                    # Insert the clickable URL part
                    link_start = self.chat_display.index(tk.INSERT)
                    self.chat_display.insert(tk.END, url)
                    link_end = self.chat_display.index(tk.INSERT)
                    
                    # Create unique tag for this specific link
                    tag_name = f"clickable_link_{i}_{int(time.time() * 1000000)}"
                    
                    # Apply the tag to just this URL
                    self.chat_display.tag_add(tag_name, link_start, link_end)
                    
                    # Configure tag styling
                    self.chat_display.tag_config(tag_name, foreground='#00a8fc', underline=True)
                    
                    # Bind click event - CRITICAL: must use u=url to capture variable
                    self.chat_display.tag_bind(tag_name, '<Button-1>', 
                        lambda event, u=url: self.open_url_from_click(u))
                    
                    # Bind hover effects
                    self.chat_display.tag_bind(tag_name, '<Enter>', 
                        lambda event: self.chat_display.config(cursor='hand2'))
                    self.chat_display.tag_bind(tag_name, '<Leave>', 
                        lambda event: self.chat_display.config(cursor='arrow'))
                    
                    self.chat_display.insert(tk.END, "\n")
                    continue
            
            # Check if it's a section header with emoji
            if any(line_stripped.startswith(emoji) for emoji in ['📚', '💡', '🎬', '🎭', '🎪', '🎨', '🎯', '👤', '📅', '📍', '🤔', '✅', '🌤️', '📰', '📝']):
                self.chat_display.insert(tk.END, line_stripped + "\n", 'pet')
            else:
                # Regular content
                self.chat_display.insert(tk.END, line_stripped + "\n", 'content')
    
    def open_url_from_click(self, url):
        """Open URL when clicked"""
        try:
            url = url.strip()
            # Add https:// if not present
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            webbrowser.open(url)
            self.log_to_console(f"Opened URL: {url}")
        except Exception as e:
            self.log_to_console(f"Error opening URL: {e}")
            messagebox.showerror("Error", f"Could not open URL:\n{url}\n\nError: {e}")
    
    def send_chat_message(self):
        msg = self.chat_input.get().strip()
        if not msg:
            return
        
        self.add_chat_message('user', msg)
        self.chat_input.delete(0, tk.END)
        self.chat_history.append({'user': msg})
        
        thread = threading.Thread(target=self.process_message, args=(msg,), daemon=True)
        thread.start()
    
    def process_message(self, msg):
        msg_lower = msg.lower()
        
        # Simple commands that don't need web search (must be EXACT matches or very specific)
        if msg_lower in ['joke', 'tell me a joke', 'tell a joke', 'make me laugh']:
            response = self.generate_pet_response(msg_lower)
        elif msg_lower in ['time', 'what time is it', 'whats the time', "what's the time", 'what time']:
            response = self.generate_pet_response(msg_lower)
        elif msg_lower in ['date', 'what date is it', 'whats the date', "what's the date", 'what is the date', 'todays date', "today's date", 'what date', 'what is todays date', 'what is today', 'todays date']:
            response = self.generate_pet_response(msg_lower)
        elif msg_lower in ['help', 'what can you do', 'commands']:
            response = self.generate_pet_response(msg_lower)
        elif msg_lower in ['tip', 'give me a tip', 'productivity tip', 'advice']:
            response = self.generate_pet_response(msg_lower)
        elif msg_lower in ['fact', 'tell me a fact', 'fun fact', 'random fact']:
            response = self.generate_pet_response(msg_lower)
        elif any(msg_lower == greeting for greeting in ['hello', 'hi', 'hey', 'hi there', 'hey there', 'greetings']):
            response = self.generate_pet_response(msg_lower)
        elif msg_lower in ['thanks', 'thank you', 'thx']:
            response = self.generate_pet_response(msg_lower)
        elif msg_lower in ['how are you', 'how do you feel', 'how are you doing']:
            response = self.generate_pet_response(msg_lower)
        elif msg_lower in ['who are you', 'what are you']:
            response = self.generate_pet_response(msg_lower)
        elif msg_lower in ['bye', 'goodbye', 'see you', 'see ya', 'later']:
            response = self.generate_pet_response(msg_lower)
        else:
            # Everything else gets web search
            self.root.after(0, lambda: self.add_chat_message('searching', "🔍 Searching the web..."))
            response = self.web_search_answer(msg)
        
        self.root.after(0, lambda: self.add_chat_message('pet', response))
    
    def web_search_answer(self, query):
        """Search the web and provide intelligent interpretation"""
        try:
            # Try Google first (best results)
            result = self.search_google(query)
            if result:
                return self.interpret_search_result(query, result)
            
            # Fallback to DuckDuckGo
            result = self.search_duckduckgo(query)
            if result:
                return self.interpret_search_result(query, result)
            
            # Final fallback to Wikipedia
            result = self.search_wikipedia(query)
            if result:
                return self.interpret_search_result(query, result)
            
            return "I couldn't find specific information on that. Try rephrasing your question!"
            
        except Exception as e:
            self.log_to_console(f"Search error: {e}")
            return "I'm having trouble searching right now. Please check your internet connection and try again!"
    
    def interpret_search_result(self, query, raw_result):
        """Interpret search results to give direct, conversational answers"""
        query_lower = query.lower()
        
        # Split result into content and sources
        lines = raw_result.split('\n')
        content_lines = []
        source_lines = []
        
        for line in lines:
            if line.strip().startswith('🔗 Source:'):
                source_lines.append(line.strip())
            else:
                content_lines.append(line)
        
        content = '\n'.join(content_lines).strip()
        
        # Detect question type and format answer accordingly
        
        # WHO questions - extract names/people
        if any(word in query_lower for word in ['who is', 'who are', 'who was', 'who were', 'main cast', 'cast members', 'actors', 'starring', 'names of', 'name of']):
            if 'cast' in query_lower or 'actor' in query_lower or 'starring' in query_lower or 'names' in query_lower:
                # For cast questions, present content directly without over-processing
                response = f"🎬 {self.summarize_content(content, 400)}"
            else:
                response = f"👤 {self.summarize_content(content, 300)}"
        
        # WHAT questions - extract definitions/explanations
        elif any(word in query_lower for word in ['what is', 'what are', 'what was', 'what does']):
            response = f"💡 {self.summarize_content(content, 300)}"
        
        # HOW questions - extract steps/methods
        elif query_lower.startswith('how to') or query_lower.startswith('how do'):
            response = f"📝 {self.summarize_content(content, 350)}"
        
        # WHEN questions - extract dates/times
        elif any(word in query_lower for word in ['when is', 'when was', 'when did', 'when does']):
            response = f"📅 {self.summarize_content(content, 250)}"
        
        # WHERE questions - extract locations
        elif any(word in query_lower for word in ['where is', 'where are', 'where can']):
            response = f"📍 {self.summarize_content(content, 250)}"
        
        # WHY questions - extract reasons
        elif query_lower.startswith('why'):
            response = f"🤔 {self.summarize_content(content, 300)}"
        
        # REQUIREMENTS questions
        elif 'requirement' in query_lower or 'need' in query_lower:
            response = f"✅ {self.summarize_content(content, 350)}"
        
        # WEATHER queries
        elif 'weather' in query_lower:
            response = f"🌤️ {self.summarize_content(content, 200)}"
        
        # NEWS queries
        elif 'news' in query_lower or 'latest' in query_lower:
            response = f"📰 {self.summarize_content(content, 300)}"
        
        # Default: Smart summarization
        else:
            response = self.summarize_content(content, 250)
        
        # Add sources at the end
        if source_lines:
            response += "\n\n" + "\n".join(source_lines)
        
        return response
    
    def summarize_content(self, content, max_chars=250):
        """Intelligently summarize content to specified length"""
        # Remove extra whitespace
        content = ' '.join(content.split())
        
        # If content is already short enough, return as-is
        if len(content) <= max_chars:
            return content
        
        # Try to cut at sentence boundary
        sentences = content.split('. ')
        summary = ""
        
        for sentence in sentences:
            test_length = len(summary) + len(sentence) + 2  # +2 for ". "
            if test_length <= max_chars:
                summary += sentence + ". "
            else:
                break
        
        # If we got at least one sentence, return it
        if summary and len(summary) > 50:
            return summary.strip()
        
        # Otherwise, cut at word boundary near the limit
        truncated = content[:max_chars]
        last_space = truncated.rfind(' ')
        if last_space > 0:
            return truncated[:last_space] + "..."
        
        return truncated + "..."
    
    def clean_html_text(self, text):
        """Clean HTML entities and tags from text"""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Replace common HTML entities
        text = text.replace('&quot;', '"')
        text = text.replace('&#x27;', "'")
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&#39;', "'")
        text = text.replace('&nbsp;', ' ')
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def search_google(self, query):
        """Search using Google - gets COMPLETE answers with ALL links"""
        try:
            clean_query = urllib.parse.quote_plus(query)
            search_url = f"https://www.google.com/search?q={clean_query}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            response = requests.get(search_url, headers=headers, timeout=10)
            html = response.text
            
            # Multiple patterns for complete content
            snippet_patterns = [
                r'<div class="[^"]*VwiC3b[^"]*"[^>]*>(.*?)</div>',
                r'<span class="[^"]*aCOpRe[^"]*"[^>]*>(.*?)</span>',
                r'<div[^>]*data-attrid="[^"]*"[^>]*>(.*?)</div>',
            ]
            
            all_snippets = []
            for pattern in snippet_patterns:
                all_snippets.extend(re.findall(pattern, html, re.DOTALL))
            
            # Extract ALL URLs (not just the first one)
            url_pattern = r'<a href="/url\?q=(https?://[^&]+)'
            found_urls = re.findall(url_pattern, html)
            
            # Get the longest/best snippet - NO TRUNCATION
            best_result = None
            best_length = 0
            
            for snippet in all_snippets[:15]:
                clean_text = self.clean_html_text(snippet)
                if clean_text and len(clean_text) > best_length and len(clean_text) > 50:
                    best_result = clean_text
                    best_length = len(clean_text)
            
            if best_result:
                # Format with content and ALL source URLs
                result_parts = [best_result]
                
                # Add up to 3 unique source URLs
                seen_domains = set()
                added_urls = 0
                
                for url in found_urls:
                    if added_urls >= 3:
                        break
                    
                    clean_url = urllib.parse.unquote(url)
                    
                    # Extract domain to avoid duplicates
                    domain_match = re.search(r'https?://([^/]+)', clean_url)
                    if domain_match:
                        domain = domain_match.group(1)
                        if domain not in seen_domains:
                            seen_domains.add(domain)
                            result_parts.append(f"🔗 Source: {clean_url}")
                            added_urls += 1
                
                return "\n".join(result_parts)
            
            return None
            
        except Exception as e:
            self.log_to_console(f"Google search error: {e}")
            return None
    
    def search_duckduckgo(self, query):
        """Search using DuckDuckGo - gets COMPLETE answers with ALL links"""
        try:
            clean_query = urllib.parse.quote_plus(query)
            search_url = f"https://html.duckduckgo.com/html/?q={clean_query}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(search_url, headers=headers, timeout=10)
            html = response.text
            
            # Extract snippets
            snippet_patterns = [
                r'class="result__snippet"[^>]*>(.*?)</a>',
                r'class="result__body"[^>]*>(.*?)</div>',
            ]
            
            all_snippets = []
            for pattern in snippet_patterns:
                all_snippets.extend(re.findall(pattern, html, re.DOTALL))
            
            # Extract ALL URLs
            url_matches = re.findall(r'class="result__url"[^>]*>(.*?)</a>', html, re.DOTALL)
            
            # Get longest snippet - NO TRUNCATION
            best_result = None
            best_length = 0
            
            for snippet in all_snippets[:10]:
                clean_text = self.clean_html_text(snippet)
                if clean_text and len(clean_text) > best_length and len(clean_text) > 50:
                    best_result = clean_text
                    best_length = len(clean_text)
            
            if best_result:
                result_parts = [best_result]
                
                # Add up to 3 source URLs
                for i, url_html in enumerate(url_matches[:3]):
                    clean_url = self.clean_html_text(url_html)
                    if clean_url:
                        # Make sure it's a proper URL
                        if not clean_url.startswith(('http://', 'https://')):
                            clean_url = 'https://' + clean_url
                        result_parts.append(f"🔗 Source: {clean_url}")
                
                return "\n".join(result_parts)
            
            return None
            
        except Exception as e:
            self.log_to_console(f"DuckDuckGo search error: {e}")
            return None
    
    def search_wikipedia(self, query):
        """Fallback Wikipedia search - with FULL content"""
        try:
            clean_query = urllib.parse.quote_plus(query)
            wiki_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={clean_query}&format=json&utf8=1"
            
            response = requests.get(wiki_url, timeout=10)
            data = response.json()
            
            if data.get('query', {}).get('search'):
                result = data['query']['search'][0]
                title = result['title']
                page_id = result['pageid']
                
                # Get FULL extract
                extract_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro&explaintext&pageids={page_id}&format=json"
                extract_response = requests.get(extract_url, timeout=10)
                extract_data = extract_response.json()
                
                page_data = extract_data.get('query', {}).get('pages', {}).get(str(page_id), {})
                full_text = page_data.get('extract', '')
                
                if full_text:
                    page_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
                    
                    return f"📚 {title}\n\n{full_text}\n🔗 Source: {page_url}"
            
            return "I couldn't find specific information on that. Try rephrasing your question!"
            
        except Exception as e:
            self.log_to_console(f"Wikipedia error: {e}")
            return "Sorry, I'm having trouble accessing search services right now."
    
    def generate_pet_response(self, message):
        """Generate response for built-in commands"""
        
        if 'help' in message or 'what can you do' in message:
            return ("I can help you with:\n"
                   "• Search the web for ANY question\n"
                   "• Tell you the time/date\n"
                   "• Tell jokes and fun facts\n"
                   "• Give productivity tips\n"
                   "• Answer questions\n"
                   "• Just chat!\n\n"
                   "Just ask me anything naturally!")
        
        if 'time' in message or 'what time' in message:
            current_time = datetime.datetime.now().strftime("%I:%M %p")
            return f"It's currently {current_time}! ⏰"
        
        if 'date' in message or 'what day' in message or ('today' in message and 'news' not in message):
            current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
            return f"Today is {current_date}! 📅"
        
        if 'joke' in message or 'funny' in message or 'make me laugh' in message:
            jokes = [
                "Why do programmers prefer dark mode? Because light attracts bugs! 🐛",
                "Why did the desktop pet cross the road? To get to the other taskbar! 🐾",
                "What's a computer's favorite snack? Microchips! 💾",
                "Why was the computer cold? It left its Windows open! 🪟",
                "How do you comfort a JavaScript bug? You console it! 😄",
                "Why do Java developers wear glasses? Because they can't C#! 👓",
                "What did the router say to the doctor? It hurts when IP! 🤕"
            ]
            return random.choice(jokes)
        
        if 'tip' in message or 'productivity' in message or 'advice' in message:
            tips = [
                "Take regular breaks! Try the Pomodoro technique: 25 minutes of work, 5 minutes of rest. 🍅",
                "Stay hydrated! Your brain works better when you drink enough water. 💧",
                "Organize your tasks by priority. Do the most important things first! 📝",
                "A clean workspace leads to a clear mind. Take a minute to tidy up! 🧹",
                "Don't forget to stretch! Your body will thank you. 🧘",
                "Use keyboard shortcuts to save time and boost productivity! ⌨️",
                "Set specific goals for the day. Checking them off feels great! ✅"
            ]
            return random.choice(tips)
        
        if 'fact' in message or 'tell me something' in message:
            facts = [
                "The first computer mouse was made of wood! 🖱️",
                "The average person blinks 15-20 times per minute, but only 7 times while using a computer! 👀",
                "The QWERTY keyboard was designed to slow down typing to prevent typewriter jams! ⌨️",
                "Email existed before the World Wide Web! 📧",
                "The first 1GB hard drive weighed over 500 pounds! 💾",
                "There are more possible games of chess than atoms in the observable universe! ♟️",
                "The first computer bug was an actual bug - a moth trapped in a computer! 🦋"
            ]
            return random.choice(facts)
        
        if 'thank' in message:
            return "You're very welcome! Happy to help! 😊"
        
        if 'how are you' in message or 'how do you feel' in message:
            return "I'm doing great! Thanks for asking. Ready to assist you anytime! 🐾"
        
        if 'who are you' in message or 'what are you' in message:
            return "I'm your Desktop Pet AI Assistant! I'm here to keep you company, help you stay productive, and answer your questions. I can search the web for you! 🤖"
        
        if 'bye' in message or 'goodbye' in message:
            return "Goodbye! I'll be here whenever you need me. Take care! 👋"
        
        if 'love' in message or '❤' in message or 'like you' in message:
            return "Aww, I appreciate you too! You're awesome! ❤️"
        
        if any(word in message for word in ['hello', 'hi', 'hey', 'greetings']):
            greetings = [
                "Hello! How can I help you today? 😊",
                "Hey there! What's up? 🐾",
                "Hi! Nice to see you! What can I do for you? 👋",
                "Greetings! Ready to assist! ✨"
            ]
            return random.choice(greetings)
        
        return "I'm here to help! Ask me anything and I'll search the web for answers. 🔍"
    
    def add_to_startup(self):
        """Add to startup"""
        try:
            import winreg
            import sys
            
            script_path = os.path.abspath(__file__)
            python_path = sys.executable.replace('python.exe', 'pythonw.exe')
            
            if script_path.endswith('.py'):
                command = f'"{python_path}" "{script_path}"'
            else:
                command = f'"{script_path}"'
            
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "DesktopPet", 0, winreg.REG_SZ, command)
            winreg.CloseKey(key)
            
            messagebox.showinfo("Success", "Desktop Pet added to startup!\n\nIt will start automatically on login.")
            self.log_to_console("Added to Windows startup")
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not add to startup:\n\n{e}")
            self.log_to_console(f"Startup error: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("Desktop Pet - Starting...")
    print("=" * 50)
    print("LEFT CLICK + DRAG: Move the pet")
    print("RIGHT CLICK: Open menu")
    print("=" * 50)
    
    pet = DesktopPet()
    
    pet.log_to_console("Desktop Pet started successfully")
    pet.log_to_console(f"Settings directory: {pet.app_data_dir}")
    pet.log_to_console(f"Loaded {len(pet.custom_shortcuts)} shortcuts")
    pet.log_to_console(f"Loaded {len(pet.custom_urls)} URLs")


