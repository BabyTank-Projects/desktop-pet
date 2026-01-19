import tkinter as tk
from tkinter import Menu as TkMenu, simpledialog, messagebox, filedialog
from PIL import Image, ImageTk
import requests
from io import BytesIO
import subprocess
import platform
import os
import json
import webbrowser

class DesktopPet:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Desktop Pet")
        
        # Make window transparent and always on top
        self.root.attributes('-transparentcolor', 'black')
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True)
        
        self.root.geometry('150x150+100+100')
        self.root.configure(bg='black')
        
        # Variables for dragging
        self.offset_x = 0
        self.offset_y = 0
        self.dragging = False
        
        # File storage paths
        self.app_data_dir = self.get_app_data_directory()
        self.shortcuts_file = os.path.join(self.app_data_dir, 'desktop_pet_shortcuts.json')
        self.urls_file = os.path.join(self.app_data_dir, 'desktop_pet_urls.json')
        self.settings_file = os.path.join(self.app_data_dir, 'desktop_pet_settings.json')
        self.custom_shortcuts = []
        self.custom_urls = []
        self.stay_on_desktop = tk.BooleanVar(value=False)
        self.custom_image_path = None
        
        # Console window
        self.console_window = None
        self.console_text = None
        self.console_buffer = []
        
        # Load settings
        self.load_settings()
        
        # Load the animated GIF
        self.load_gif()
        
        # Create label
        self.label = tk.Label(self.root, bg='black', bd=0)
        self.label.pack()
        
        # Bind mouse events
        self.label.bind('<Button-1>', self.start_drag)
        self.label.bind('<B1-Motion>', self.drag)
        self.label.bind('<ButtonRelease-1>', self.stop_drag)
        self.label.bind('<Button-3>', self.show_menu)
        
        # Create context menu
        self.create_menu()
        
        # Start animation
        self.current_frame = 0
        self.animate()
        
        self.root.mainloop()
    
    def get_app_data_directory(self):
        """Get the appropriate directory for storing app data"""
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
        """Load the animated GIF or static image"""
        try:
            if self.custom_image_path and os.path.exists(self.custom_image_path):
                img = Image.open(self.custom_image_path)
            else:
                url = "https://oldschool.runescape.wiki/images/thumb/Infernal_cape_detail_animated.gif/100px-Infernal_cape_detail_animated.gif?35cc2"
                response = requests.get(url)
                gif_data = BytesIO(response.content)
                img = Image.open(gif_data)
            
            self.frames = []
            original_width, original_height = img.size
            scale_factor = 0.6
            new_width = int(original_width * scale_factor)
            new_height = int(original_height * scale_factor)
            
            # Check if it's an animated image
            is_animated = False
            try:
                img.seek(1)
                is_animated = True
                img.seek(0)
            except EOFError:
                is_animated = False
            
            if is_animated:
                # Load all frames for animated images
                try:
                    while True:
                        frame = img.copy()
                        frame = frame.convert('RGBA')
                        frame = frame.resize((new_width, new_height), Image.Resampling.LANCZOS)
                        self.frames.append(ImageTk.PhotoImage(frame))
                        img.seek(len(self.frames))
                except EOFError:
                    pass
            else:
                # Load single frame for static images
                frame = img.convert('RGBA')
                frame = frame.resize((new_width, new_height), Image.Resampling.LANCZOS)
                self.frames.append(ImageTk.PhotoImage(frame))
            
            if self.frames:
                self.root.geometry(f'{new_width}x{new_height}+100+100')
                self.current_frame = 0  # Reset frame counter
                
        except Exception as e:
            print(f"Error loading image: {e}")
            self.log_to_console(f"Error loading image: {e}")
            placeholder = Image.new('RGBA', (80, 80), (255, 0, 0, 255))
            self.frames = [ImageTk.PhotoImage(placeholder)]
            self.current_frame = 0
    
    def animate(self):
        """Animate the GIF frames"""
        if self.frames:
            self.label.config(image=self.frames[self.current_frame])
            self.current_frame = (self.current_frame + 1) % len(self.frames)
        self.root.after(100, self.animate)
    
    def start_drag(self, event):
        self.dragging = True
        self.offset_x = event.x
        self.offset_y = event.y
    
    def drag(self, event):
        if self.dragging:
            x = self.root.winfo_x() + event.x - self.offset_x
            y = self.root.winfo_y() + event.y - self.offset_y
            self.root.geometry(f'+{x}+{y}')
    
    def stop_drag(self, event):
        self.dragging = False
    
    def load_settings(self):
        """Load settings from JSON"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    self.stay_on_desktop.set(settings.get('stay_on_desktop', False))
                    self.custom_image_path = settings.get('custom_image_path', None)
                    self.update_window_level()
        except Exception as e:
            print(f"Error loading settings: {e}")
    
    def save_settings(self):
        """Save settings to JSON"""
        try:
            settings = {
                'stay_on_desktop': self.stay_on_desktop.get(),
                'custom_image_path': self.custom_image_path
            }
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def update_window_level(self):
        """Update window level"""
        if self.stay_on_desktop.get():
            self.root.attributes('-topmost', False)
            self.root.lower()
            self.log_to_console("Pet now stays on desktop only")
        else:
            self.root.attributes('-topmost', True)
            self.log_to_console("Pet now stays on top")
    
    def toggle_stay_on_desktop(self):
        """Toggle stay on desktop"""
        self.update_window_level()
        self.save_settings()
    
    def load_custom_shortcuts(self):
        """Load custom shortcuts"""
        try:
            if os.path.exists(self.shortcuts_file):
                with open(self.shortcuts_file, 'r') as f:
                    self.custom_shortcuts = json.load(f)
            else:
                self.custom_shortcuts = []
        except Exception as e:
            print(f"Error loading shortcuts: {e}")
            self.custom_shortcuts = []
    
    def load_custom_urls(self):
        """Load custom URLs"""
        try:
            if os.path.exists(self.urls_file):
                with open(self.urls_file, 'r') as f:
                    self.custom_urls = json.load(f)
            else:
                self.custom_urls = []
        except Exception as e:
            print(f"Error loading URLs: {e}")
            self.custom_urls = []
    
    def save_custom_shortcuts(self):
        """Save custom shortcuts"""
        try:
            with open(self.shortcuts_file, 'w') as f:
                json.dump(self.custom_shortcuts, f, indent=2)
        except Exception as e:
            print(f"Error saving shortcuts: {e}")
    
    def save_custom_urls(self):
        """Save custom URLs"""
        try:
            with open(self.urls_file, 'w') as f:
                json.dump(self.custom_urls, f, indent=2)
        except Exception as e:
            print(f"Error saving URLs: {e}")
    
    def recreate_menu(self):
        """Safely recreate the menu"""
        try:
            if hasattr(self, 'menu'):
                self.menu.delete(0, 'end')
        except:
            pass
        self.create_menu()
    
    def create_menu(self):
        self.menu = TkMenu(
            self.root,
            tearoff=0,
            bg='#3d3d5c',
            fg='#ffffff',
            activebackground='#4d4d6c',
            activeforeground='#ffffff',
            relief='solid',
            bd=1,
            font=('Segoe UI', 10),
            activeborderwidth=0,
            borderwidth=1
        )
        
        # Set border color
        self.menu.configure(borderwidth=1, relief='solid')
        
        # Quick Access section
        self.menu.add_command(
            label="  📝 Notepad",
            command=self.open_notepad,
            compound='left'
        )
        self.menu.add_command(
            label="  🔢 Calculator",
            command=self.open_calculator,
            compound='left'
        )
        self.menu.add_command(
            label="  📂 Downloads",
            command=self.open_downloads,
            compound='left'
        )
        
        self.menu.add_separator()
        
        # Load data
        self.load_custom_shortcuts()
        self.load_custom_urls()
        
        # Custom Apps submenu
        self.apps_submenu = TkMenu(
            self.menu,
            tearoff=0,
            bg='#3d3d5c',
            fg='#ffffff',
            activebackground='#4d4d6c',
            activeforeground='#ffffff',
            relief='solid',
            bd=1,
            font=('Segoe UI', 10)
        )
        
        if self.custom_shortcuts:
            for shortcut in self.custom_shortcuts:
                name = shortcut.get('name', 'Unknown')
                path = shortcut.get('path', '')
                self.apps_submenu.add_command(
                    label=f"  {name}",
                    command=lambda p=path: self.open_custom_path(p)
                )
        else:
            self.apps_submenu.add_command(label="  (No apps added)", state='disabled')
        
        self.apps_submenu.add_separator()
        self.apps_submenu.add_command(label="  ➕ Add App", command=self.add_custom_shortcut)
        self.apps_submenu.add_command(label="  🗑️ Remove App", command=self.delete_custom_shortcut)
        
        self.menu.add_cascade(label="  💻 My Apps", menu=self.apps_submenu)
        
        # Custom URLs submenu
        self.urls_submenu = TkMenu(
            self.menu,
            tearoff=0,
            bg='#3d3d5c',
            fg='#ffffff',
            activebackground='#4d4d6c',
            activeforeground='#ffffff',
            relief='solid',
            bd=1,
            font=('Segoe UI', 10)
        )
        
        if self.custom_urls:
            for url_item in self.custom_urls:
                name = url_item.get('name', 'Unknown')
                url = url_item.get('url', '')
                self.urls_submenu.add_command(
                    label=f"  {name}",
                    command=lambda u=url: self.open_url(u)
                )
        else:
            self.urls_submenu.add_command(label="  (No URLs added)", state='disabled')
        
        self.urls_submenu.add_separator()
        self.urls_submenu.add_command(label="  ➕ Add URL", command=self.add_custom_url)
        self.urls_submenu.add_command(label="  🗑️ Remove URL", command=self.delete_custom_url)
        
        self.menu.add_cascade(label="  🌐 My URLs", menu=self.urls_submenu)
        
        self.menu.add_separator()
        
        # Settings section
        self.menu.add_command(
            label="  🖼️ Change Image",
            command=self.change_pet_image
        )
        self.menu.add_checkbutton(
            label="  📌 Desktop Only",
            variable=self.stay_on_desktop,
            command=self.toggle_stay_on_desktop,
            selectcolor='#4d4d6c',
            indicatoron=True
        )
        
        self.menu.add_separator()
        
        # Tools section
        self.menu.add_command(label="  📂 Settings Folder", command=self.open_settings_folder)
        self.menu.add_command(label="  ❓ Help", command=self.show_help)
        self.menu.add_command(label="  🛠️ Console", command=self.toggle_console)
        self.menu.add_command(label="  💻 Add to Startup", command=self.add_to_startup)
        
        self.menu.add_separator()
        
        # Exit with red highlight
        self.menu.add_command(
            label="  ❌ Close",
            command=self.root.quit,
            foreground='#ff6b6b',
            activeforeground='#ff8888'
        )
    
    def show_menu(self, event):
        """Show context menu"""
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()
    
    def open_settings_folder(self):
        """Open settings folder"""
        system = platform.system()
        try:
            if system == 'Windows':
                os.startfile(self.app_data_dir)
            elif system == 'Darwin':
                subprocess.Popen(['open', self.app_data_dir])
            else:
                subprocess.Popen(['xdg-open', self.app_data_dir])
            self.log_to_console(f"Opened: {self.app_data_dir}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder:\n{e}")
    
    def open_notepad(self):
        """Open Notepad"""
        system = platform.system()
        try:
            if system == 'Windows':
                subprocess.Popen(['notepad.exe'])
            elif system == 'Darwin':
                subprocess.Popen(['open', '-a', 'TextEdit'])
            else:
                subprocess.Popen(['gedit'])
            self.log_to_console("Opened Notepad")
        except Exception as e:
            self.log_to_console(f"Error: {e}")
    
    def open_calculator(self):
        """Open Calculator"""
        system = platform.system()
        try:
            if system == 'Windows':
                subprocess.Popen(['calc.exe'])
            elif system == 'Darwin':
                subprocess.Popen(['open', '-a', 'Calculator'])
            else:
                subprocess.Popen(['gnome-calculator'])
            self.log_to_console("Opened Calculator")
        except Exception as e:
            self.log_to_console(f"Error: {e}")
    
    def open_downloads(self):
        """Open Downloads folder"""
        system = platform.system()
        try:
            downloads_path = os.path.join(os.path.expanduser('~'), 'Downloads')
            if system == 'Windows':
                os.startfile(downloads_path)
            elif system == 'Darwin':
                subprocess.Popen(['open', downloads_path])
            else:
                subprocess.Popen(['xdg-open', downloads_path])
            self.log_to_console("Opened Downloads")
        except Exception as e:
            self.log_to_console(f"Error: {e}")
    
    def add_custom_url(self):
        """Add custom URL"""
        name = simpledialog.askstring("Add URL", "Enter name:")
        if not name:
            return
        
        url = simpledialog.askstring("Enter URL", "Enter full URL (https://...):")
        
        if url:
            if not url.startswith('http://') and not url.startswith('https://'):
                messagebox.showwarning("Invalid", "URL must start with http:// or https://")
                return
            
            self.custom_urls.append({'name': name, 'url': url})
            self.save_custom_urls()
            self.recreate_menu()
            messagebox.showinfo("Success", f"Added: {name}")
            self.log_to_console(f"Added URL: {name}")
    
    def delete_custom_url(self):
        """Delete custom URL"""
        if not self.custom_urls:
            messagebox.showinfo("No URLs", "No URLs to delete")
            return
        
        delete_window = tk.Toplevel(self.root)
        delete_window.title("Delete URL")
        delete_window.geometry("400x450")
        delete_window.configure(bg='#1e1e1e')
        delete_window.attributes('-topmost', True)
        
        tk.Label(
            delete_window,
            text="Delete URL",
            bg='#1e1e1e',
            fg='#ffffff',
            font=('Segoe UI', 16, 'bold')
        ).pack(pady=20)
        
        listbox = tk.Listbox(
            delete_window,
            bg='#2d2d30',
            fg='#f0f0f0',
            font=('Segoe UI', 10),
            selectbackground='#3e3e42',
            selectforeground='#ffffff',
            relief='flat',
            borderwidth=0
        )
        listbox.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        for url_item in self.custom_urls:
            listbox.insert(tk.END, f"  🌐 {url_item['name']}")
        
        def do_delete():
            selection = listbox.curselection()
            if not selection:
                return
            
            index = selection[0]
            deleted = self.custom_urls[index]
            
            if messagebox.askyesno("Confirm", f"Delete '{deleted['name']}'?"):
                self.custom_urls.pop(index)
                self.save_custom_urls()
                self.recreate_menu()
                delete_window.destroy()
                messagebox.showinfo("Deleted", f"Removed {deleted['name']}")
                self.log_to_console(f"Deleted URL: {deleted['name']}")
        
        btn_frame = tk.Frame(delete_window, bg='#1e1e1e')
        btn_frame.pack(pady=(0, 20))
        
        tk.Button(
            btn_frame,
            text="Delete",
            command=do_delete,
            bg='#d32f2f',
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            padx=25,
            pady=8,
            relief='flat',
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame,
            text="Cancel",
            command=delete_window.destroy,
            bg='#424242',
            fg='white',
            font=('Segoe UI', 10),
            padx=25,
            pady=8,
            relief='flat',
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=5)
    
    def open_url(self, url):
        """Open URL"""
        try:
            webbrowser.open(url)
            self.log_to_console(f"Opened: {url}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open URL:\n{e}")
    
    def add_custom_shortcut(self):
        """Add custom shortcut"""
        name = simpledialog.askstring("Add Shortcut", "Enter name:")
        if not name:
            return
        
        choice = messagebox.askquestion(
            "Type",
            "Select FILE?\n\nYes = File\nNo = Folder/Command"
        )
        
        if choice == 'yes':
            path = filedialog.askopenfilename(title="Select file")
        else:
            folder_choice = messagebox.askquestion("Type", "Select FOLDER?\n\nYes = Folder\nNo = Command")
            if folder_choice == 'yes':
                path = filedialog.askdirectory(title="Select folder")
            else:
                path = simpledialog.askstring("Path", "Enter path or command:")
        
        if path:
            self.custom_shortcuts.append({'name': name, 'path': path})
            self.save_custom_shortcuts()
            self.recreate_menu()
            messagebox.showinfo("Success", f"Added: {name}")
            self.log_to_console(f"Added shortcut: {name}")
    
    def delete_custom_shortcut(self):
        """Delete custom shortcut"""
        if not self.custom_shortcuts:
            messagebox.showinfo("No Shortcuts", "No shortcuts to delete")
            return
        
        delete_window = tk.Toplevel(self.root)
        delete_window.title("Delete Shortcut")
        delete_window.geometry("400x450")
        delete_window.configure(bg='#1e1e1e')
        delete_window.attributes('-topmost', True)
        
        tk.Label(
            delete_window,
            text="Delete Shortcut",
            bg='#1e1e1e',
            fg='#ffffff',
            font=('Segoe UI', 16, 'bold')
        ).pack(pady=20)
        
        listbox = tk.Listbox(
            delete_window,
            bg='#2d2d30',
            fg='#f0f0f0',
            font=('Segoe UI', 10),
            selectbackground='#3e3e42',
            selectforeground='#ffffff',
            relief='flat',
            borderwidth=0
        )
        listbox.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        for shortcut in self.custom_shortcuts:
            listbox.insert(tk.END, f"  📎 {shortcut['name']}")
        
        def do_delete():
            selection = listbox.curselection()
            if not selection:
                return
            
            index = selection[0]
            deleted = self.custom_shortcuts[index]
            
            if messagebox.askyesno("Confirm", f"Delete '{deleted['name']}'?"):
                self.custom_shortcuts.pop(index)
                self.save_custom_shortcuts()
                self.recreate_menu()
                delete_window.destroy()
                messagebox.showinfo("Deleted", f"Removed {deleted['name']}")
                self.log_to_console(f"Deleted: {deleted['name']}")
        
        btn_frame = tk.Frame(delete_window, bg='#1e1e1e')
        btn_frame.pack(pady=(0, 20))
        
        tk.Button(
            btn_frame,
            text="Delete",
            command=do_delete,
            bg='#d32f2f',
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            padx=25,
            pady=8,
            relief='flat',
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame,
            text="Cancel",
            command=delete_window.destroy,
            bg='#424242',
            fg='white',
            font=('Segoe UI', 10),
            padx=25,
            pady=8,
            relief='flat',
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=5)
    
    def open_custom_path(self, path):
        """Open custom path"""
        system = platform.system()
        try:
            if os.path.exists(path):
                if system == 'Windows':
                    os.startfile(path)
                elif system == 'Darwin':
                    subprocess.Popen(['open', path])
                else:
                    subprocess.Popen(['xdg-open', path])
                self.log_to_console(f"Opened: {path}")
                return
            
            if system == 'Windows':
                app_lower = path.lower().strip()
                
                if app_lower == 'discord':
                    discord_path = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Discord', 'Update.exe')
                    if os.path.exists(discord_path):
                        subprocess.Popen([discord_path, '--processStart', 'Discord.exe'])
                        self.log_to_console("Launched Discord")
                        return
                
                elif app_lower == 'spotify':
                    spotify_path = os.path.join(os.environ.get('APPDATA', ''), 'Spotify', 'Spotify.exe')
                    if os.path.exists(spotify_path):
                        subprocess.Popen([spotify_path])
                        self.log_to_console("Launched Spotify")
                        return
                
                subprocess.Popen(path, shell=True)
                self.log_to_console(f"Launched: {path}")
            else:
                subprocess.Popen([path])
                self.log_to_console(f"Launched: {path}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Could not open:\n{path}\n\n{e}")
            self.log_to_console(f"Error: {e}")
    
    def change_pet_image(self):
        """Change pet image"""
        path = filedialog.askopenfilename(
            title="Select image/GIF",
            filetypes=[
                ("Images", "*.gif *.png *.jpg *.jpeg"),
                ("All files", "*.*")
            ]
        )
        
        if path:
            try:
                test = Image.open(path)
                test.close()
                
                self.custom_image_path = path
                self.save_settings()
                self.load_gif()
                
                messagebox.showinfo("Success", "Image changed!")
                self.log_to_console(f"Changed image: {path}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not load:\n{e}")
                self.log_to_console(f"Image load error: {e}")
    
    def show_help(self):
        """Show help"""
        help_text = """Desktop Pet - Help

🎮 CONTROLS:
• Left-click + drag to move
• Right-click for menu

📋 FEATURES:
• Quick access to common apps
• Custom app shortcuts
• Custom URL bookmarks
• Change pet image
• Debug console

💡 TIPS:
• Settings save automatically
• Use console to troubleshoot
• Add to startup for auto-launch"""
        
        messagebox.showinfo("Help", help_text)
    
    def log_to_console(self, message):
        """Log to console"""
        self.console_buffer.append(message)
        if self.console_text:
            self.console_text.insert(tk.END, message + "\n")
            self.console_text.see(tk.END)
        print(message)
    
    def toggle_console(self):
        """Toggle console"""
        if self.console_window and self.console_window.winfo_exists():
            self.console_window.destroy()
            self.console_window = None
            self.console_text = None
        else:
            self.show_console()
    
    def show_console(self):
        """Show console window"""
        self.console_window = tk.Toplevel(self.root)
        self.console_window.title("Debug Console")
        self.console_window.geometry("650x400")
        self.console_window.configure(bg='#1e1e1e')
        self.console_window.attributes('-topmost', True)
        
        tk.Label(
            self.console_window,
            text="🛠️ Debug Console",
            bg='#1e1e1e',
            fg='#4CAF50',
            font=('Segoe UI', 14, 'bold')
        ).pack(pady=15)
        
        text_frame = tk.Frame(self.console_window, bg='#0a0a0a')
        text_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.console_text = tk.Text(
            text_frame,
            bg='#0a0a0a',
            fg='#00ff00',
            font=('Consolas', 9),
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set,
            relief='flat',
            padx=10,
            pady=10
        )
        self.console_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.console_text.yview)
        
        for msg in self.console_buffer:
            self.console_text.insert(tk.END, msg + "\n")
        self.console_text.see(tk.END)
        
        btn_frame = tk.Frame(self.console_window, bg='#1e1e1e')
        btn_frame.pack(pady=(0, 15))
        
        tk.Button(
            btn_frame,
            text="Clear",
            command=self.clear_console,
            bg='#424242',
            fg='white',
            font=('Segoe UI', 10),
            padx=20,
            pady=8,
            relief='flat',
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame,
            text="Close",
            command=self.console_window.destroy,
            bg='#4CAF50',
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            padx=25,
            pady=8,
            relief='flat',
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=5)
    
    def clear_console(self):
        """Clear console"""
        if self.console_text:
            self.console_text.delete(1.0, tk.END)
        self.console_buffer.clear()
        self.log_to_console("Console cleared")
    
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
            
            messagebox.showinfo(
                "Success",
                "Desktop Pet added to startup!\n\nIt will start automatically on login.\n\nRemove via Task Manager > Startup if needed."
            )
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
