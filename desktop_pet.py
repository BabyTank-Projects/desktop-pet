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
        self.root.overrideredirect(True)  # Remove window decorations
        
        # Set initial position - will resize after loading image
        self.root.geometry('150x150+100+100')
        self.root.configure(bg='black')
        
        # Variables for dragging
        self.offset_x = 0
        self.offset_y = 0
        self.dragging = False
        
        # File to store custom shortcuts and settings
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
        
        # Console buffer
        self.console_buffer = []
        
        # Load settings
        self.load_settings()
        
        # Load the animated GIF
        self.load_gif()
        
        # Create label to display the image
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
            print(f"Created app data directory: {app_data}")
        
        return app_data
    
    def load_gif(self):
        """Load the animated GIF from URL or custom path and resize it"""
        try:
            if self.custom_image_path and os.path.exists(self.custom_image_path):
                gif = Image.open(self.custom_image_path)
            else:
                url = "https://oldschool.runescape.wiki/images/thumb/Infernal_cape_detail_animated.gif/100px-Infernal_cape_detail_animated.gif?35cc2"
                response = requests.get(url)
                gif_data = BytesIO(response.content)
                gif = Image.open(gif_data)
            
            self.frames = []
            original_width, original_height = gif.size
            scale_factor = 0.6
            new_width = int(original_width * scale_factor)
            new_height = int(original_height * scale_factor)
            
            try:
                while True:
                    frame = gif.copy()
                    frame = frame.convert('RGBA')
                    frame = frame.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    self.frames.append(ImageTk.PhotoImage(frame))
                    gif.seek(len(self.frames))
            except EOFError:
                pass
            
            if self.frames:
                self.root.geometry(f'{new_width}x{new_height}+100+100')
                
        except Exception as e:
            print(f"Error loading GIF: {e}")
            placeholder = Image.new('RGBA', (80, 80), (255, 0, 0, 255))
            self.frames = [ImageTk.PhotoImage(placeholder)]
    
    def animate(self):
        """Animate the GIF frames"""
        if self.frames:
            self.label.config(image=self.frames[self.current_frame])
            self.current_frame = (self.current_frame + 1) % len(self.frames)
        self.root.after(100, self.animate)
    
    def start_drag(self, event):
        """Start dragging the window"""
        self.dragging = True
        self.offset_x = event.x
        self.offset_y = event.y
    
    def drag(self, event):
        """Drag the window"""
        if self.dragging:
            x = self.root.winfo_x() + event.x - self.offset_x
            y = self.root.winfo_y() + event.y - self.offset_y
            self.root.geometry(f'+{x}+{y}')
    
    def stop_drag(self, event):
        """Stop dragging"""
        self.dragging = False
    
    def load_settings(self):
        """Load settings from JSON file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    stay_on_desktop = settings.get('stay_on_desktop', False)
                    self.stay_on_desktop.set(stay_on_desktop)
                    self.custom_image_path = settings.get('custom_image_path', None)
                    self.update_window_level()
        except Exception as e:
            print(f"Error loading settings: {e}")
    
    def save_settings(self):
        """Save settings to JSON file"""
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
        """Update whether window stays on top or on desktop only"""
        if self.stay_on_desktop.get():
            self.root.attributes('-topmost', False)
            self.root.lower()
            self.log_to_console("Pet now stays on desktop only")
        else:
            self.root.attributes('-topmost', True)
            self.log_to_console("Pet now stays on top of all windows")
    
    def toggle_stay_on_desktop(self):
        """Toggle the stay on desktop setting"""
        self.update_window_level()
        self.save_settings()
    
    def load_custom_shortcuts(self):
        """Load custom shortcuts from JSON file"""
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
        """Load custom URLs from JSON file"""
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
        """Save custom shortcuts to JSON file"""
        try:
            with open(self.shortcuts_file, 'w') as f:
                json.dump(self.custom_shortcuts, f, indent=2)
        except Exception as e:
            print(f"Error saving shortcuts: {e}")
    
    def save_custom_urls(self):
        """Save custom URLs to JSON file"""
        try:
            with open(self.urls_file, 'w') as f:
                json.dump(self.custom_urls, f, indent=2)
        except Exception as e:
            print(f"Error saving URLs: {e}")
    
    def create_menu(self):
        """Create the context menu with modern styling and organized submenus"""
        self.menu = TkMenu(
            self.root, 
            tearoff=0, 
            bg='#1e1e1e',
            fg='#ffffff',
            activebackground='#0078d4',
            activeforeground='#ffffff',
            relief='flat', 
            bd=0,
            font=('Segoe UI', 10),
            activeborderwidth=0
        )
        
        self.menu.configure(borderwidth=1, relief='solid')
        
        # Quick Access section
        self.menu.add_command(label="  📝 Notepad", command=self.open_notepad)
        self.menu.add_command(label="  🔢 Calculator", command=self.open_calculator)
        self.menu.add_command(label="  📁 Downloads", command=self.open_downloads)
        self.menu.add_separator()
        
        # Load shortcuts and URLs
        self.load_custom_shortcuts()
        self.load_custom_urls()
        
        # Custom Apps Submenu
        self.apps_submenu = TkMenu(
            self.menu,
            tearoff=0,
            bg='#1e1e1e',
            fg='#ffffff',
            activebackground='#0078d4',
            activeforeground='#ffffff',
            relief='flat',
            bd=0,
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
            self.apps_submenu.add_command(label="  (No apps added yet)", state='disabled')
        
        self.apps_submenu.add_separator()
        self.apps_submenu.add_command(label="  ➕ Add New App", command=self.add_custom_shortcut)
        self.apps_submenu.add_command(label="  🗑️ Delete App", command=self.delete_custom_shortcut)
        
        self.menu.add_cascade(label="  🚀 My Apps", menu=self.apps_submenu)
        
        # Custom URLs Submenu
        self.urls_submenu = TkMenu(
            self.menu,
            tearoff=0,
            bg='#1e1e1e',
            fg='#ffffff',
            activebackground='#0078d4',
            activeforeground='#ffffff',
            relief='flat',
            bd=0,
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
            self.urls_submenu.add_command(label="  (No URLs added yet)", state='disabled')
        
        self.urls_submenu.add_separator()
        self.urls_submenu.add_command(label="  ➕ Add New URL", command=self.add_custom_url)
        self.urls_submenu.add_command(label="  🗑️ Delete URL", command=self.delete_custom_url)
        
        self.menu.add_cascade(label="  🌐 My URLs", menu=self.urls_submenu)
        
        self.menu.add_separator()
        
        # Settings section
        self.menu.add_command(label="  🖼️ Change Pet Image/GIF", command=self.change_pet_image)
        self.menu.add_checkbutton(
            label="  📌 Stay on Desktop Only", 
            variable=self.stay_on_desktop,
            command=self.toggle_stay_on_desktop,
            selectcolor='#0078d4',  # Blue background when checked
            activebackground='#0078d4',
            foreground='#ffffff',
            activeforeground='#ffffff'
        )
        
        self.menu.add_separator()
        
        # Tools section
        self.menu.add_command(label="  📂 Open Settings Folder", command=self.open_settings_folder)
        self.menu.add_command(label="  ❓ Help", command=self.show_help)
        self.menu.add_command(label="  🛠 Debug Console", command=self.toggle_console)
        self.menu.add_command(label="  🚀 Add to Startup", command=self.add_to_startup)
        
        self.menu.add_separator()
        self.menu.add_command(label="  ❌ Exit", command=self.root.quit, foreground='#ff4444')
    
    def show_menu(self, event):
        """Show context menu on right-click"""
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
            
            def block_right_click(e):
                return "break"
            
            self.menu.bind("<Button-3>", block_right_click)
            self.menu.bind("<ButtonRelease-3>", block_right_click)
            
        finally:
            self.menu.grab_release()
    
    def open_settings_folder(self):
        """Open the folder where settings are stored"""
        system = platform.system()
        try:
            if system == 'Windows':
                os.startfile(self.app_data_dir)
            elif system == 'Darwin':
                subprocess.Popen(['open', self.app_data_dir])
            else:
                subprocess.Popen(['xdg-open', self.app_data_dir])
            self.log_to_console(f"Opening settings folder: {self.app_data_dir}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open settings folder:\n\n{e}")
            self.log_to_console(f"Error opening settings folder: {e}")
    
    def open_notepad(self):
        """Open Notepad"""
        system = platform.system()
        try:
            if system == 'Windows':
                subprocess.Popen(['notepad.exe'])
            elif system == 'Darwin':
                subprocess.Popen(['open', '-a', 'TextEdit'])
            else:
                try:
                    subprocess.Popen(['gedit'])
                except:
                    subprocess.Popen(['xdg-open', 'text/plain'])
            print("Opening Notepad...")
        except Exception as e:
            print(f"Error opening notepad: {e}")
    
    def open_calculator(self):
        """Open Calculator"""
        system = platform.system()
        try:
            if system == 'Windows':
                subprocess.Popen(['calc.exe'])
            elif system == 'Darwin':
                subprocess.Popen(['open', '-a', 'Calculator'])
            else:
                try:
                    subprocess.Popen(['gnome-calculator'])
                except:
                    subprocess.Popen(['xcalc'])
            print("Opening Calculator...")
        except Exception as e:
            print(f"Error opening calculator: {e}")
    
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
            print(f"Opening Downloads folder: {downloads_path}")
        except Exception as e:
            print(f"Error opening downloads: {e}")
    
    def add_custom_url(self):
        """Add a custom URL"""
        name = simpledialog.askstring("Add URL", "Enter a name for this URL:\n(e.g., 'Google', 'YouTube', 'Gmail')")
        if not name:
            return
        
        url = simpledialog.askstring(
            "Enter URL",
            "Enter the full URL:\n\n"
            "Examples:\n"
            "• https://www.google.com\n"
            "• https://www.youtube.com\n"
            "• https://mail.google.com\n"
            "• https://github.com"
        )
        
        if url:
            if not url.startswith('http://') and not url.startswith('https://'):
                messagebox.showwarning("Invalid URL", "URL must start with http:// or https://")
                return
            
            self.custom_urls.append({
                'name': name,
                'url': url
            })
            self.save_custom_urls()
            
            self.menu.destroy()
            self.create_menu()
            
            messagebox.showinfo("Success", f"Added URL: {name}")
            print(f"Added custom URL: {name} -> {url}")
            self.log_to_console(f"Added URL: {name} -> {url}")
    
    def delete_custom_url(self):
        """Delete a custom URL"""
        if not self.custom_urls:
            messagebox.showinfo("No URLs", "You don't have any custom URLs to delete.")
            return
        
        delete_window = tk.Toplevel(self.root)
        delete_window.title("Delete URL")
        delete_window.geometry("450x500")
        delete_window.configure(bg='#f5f5f5')
        delete_window.attributes('-topmost', True)
        delete_window.resizable(False, False)
        
        main_container = tk.Frame(delete_window, bg='#f5f5f5')
        main_container.pack(fill=tk.BOTH, expand=True)
        
        header_frame = tk.Frame(main_container, bg='#ffffff', height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        header_content = tk.Frame(header_frame, bg='#ffffff')
        header_content.place(relx=0.5, rely=0.5, anchor='center')
        
        title_label = tk.Label(
            header_content,
            text="Delete URL",
            bg='#ffffff',
            fg='#1e1e1e',
            font=('Segoe UI', 20, 'bold')
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            header_content,
            text="Select a URL to remove",
            bg='#ffffff',
            fg='#666666',
            font=('Segoe UI', 10)
        )
        subtitle_label.pack()
        
        content_frame = tk.Frame(main_container, bg='#f5f5f5')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        listbox_frame = tk.Frame(content_frame, bg='#ffffff', highlightthickness=1, 
                                 highlightbackground='#e0e0e0', highlightcolor='#0078d4')
        listbox_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(listbox_frame, bg='#f5f5f5', troughcolor='#ffffff', width=14)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=2, pady=2)
        
        listbox = tk.Listbox(
            listbox_frame,
            bg='#ffffff',
            fg='#1e1e1e',
            font=('Segoe UI', 11),
            selectmode=tk.SINGLE,
            yscrollcommand=scrollbar.set,
            relief=tk.FLAT,
            highlightthickness=0,
            selectbackground='#e3f2fd',
            selectforeground='#0078d4',
            activestyle='none',
            borderwidth=0
        )
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=15, pady=15)
        scrollbar.config(command=listbox.yview)
        
        for url_item in self.custom_urls:
            listbox.insert(tk.END, f"  🌐  {url_item['name']}")
        
        def do_delete():
            selection = listbox.curselection()
            if not selection:
                error_label = tk.Label(
                    content_frame,
                    text="⚠️ Please select a URL first",
                    bg='#fff3cd',
                    fg='#856404',
                    font=('Segoe UI', 9),
                    padx=10,
                    pady=5
                )
                error_label.pack(pady=(5, 0))
                delete_window.after(2000, error_label.destroy)
                return
            
            index = selection[0]
            deleted_url = self.custom_urls[index]
            
            confirm = messagebox.askyesno(
                "Confirm Delete",
                f"Delete '{deleted_url['name']}'?",
                icon='warning'
            )
            
            if confirm:
                self.custom_urls.pop(index)
                self.save_custom_urls()
                
                self.menu.destroy()
                self.create_menu()
                
                delete_window.destroy()
                
                messagebox.showinfo("✓ Deleted", f"Removed {deleted_url['name']}")
                print(f"Deleted custom URL: {deleted_url['name']}")
                self.log_to_console(f"Deleted URL: {deleted_url['name']}")
        
        button_frame = tk.Frame(main_container, bg='#f5f5f5', height=70)
        button_frame.pack(fill=tk.X, padx=30, pady=(0, 20))
        button_frame.pack_propagate(False)
        
        button_container = tk.Frame(button_frame, bg='#f5f5f5')
        button_container.place(relx=0.5, rely=0.5, anchor='center')
        
        delete_btn = tk.Button(
            button_container,
            text="Delete",
            command=do_delete,
            bg='#d32f2f',
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            padx=30,
            pady=10,
            relief=tk.FLAT,
            cursor='hand2',
            activebackground='#c62828',
            activeforeground='white',
            borderwidth=0
        )
        delete_btn.pack(side=tk.LEFT, padx=5)
        
        def on_enter_delete(e):
            delete_btn['bg'] = '#c62828'
        
        def on_leave_delete(e):
            delete_btn['bg'] = '#d32f2f'
        
        delete_btn.bind('<Enter>', on_enter_delete)
        delete_btn.bind('<Leave>', on_leave_delete)
        
        cancel_btn = tk.Button(
            button_container,
            text="Cancel",
            command=delete_window.destroy,
            bg='#e0e0e0',
            fg='#1e1e1e',
            font=('Segoe UI', 10),
            padx=30,
            pady=10,
            relief=tk.FLAT,
            cursor='hand2',
            activebackground='#d0d0d0',
            activeforeground='#1e1e1e',
            borderwidth=0
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        def on_enter_cancel(e):
            cancel_btn['bg'] = '#d0d0d0'
        
        def on_leave_cancel(e):
            cancel_btn['bg'] = '#e0e0e0'
        
        cancel_btn.bind('<Enter>', on_enter_cancel)
        cancel_btn.bind('<Leave>', on_leave_cancel)
        
        delete_window.update_idletasks()
        x = (delete_window.winfo_screenwidth() // 2) - (delete_window.winfo_width() // 2)
        y = (delete_window.winfo_screenheight() // 2) - (delete_window.winfo_height() // 2)
        delete_window.geometry(f"+{x}+{y}")
        
        delete_window.grab_set()
        delete_window.focus_set()
    
    def open_url(self, url):
        """Open a URL in the default browser"""
        try:
            webbrowser.open(url)
            print(f"Opening URL: {url}")
            self.log_to_console(f"Opened URL: {url}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open URL:\n\n{e}")
            print(f"Error opening URL: {e}")
            self.log_to_console(f"Error opening URL: {e}")
    
    def add_custom_shortcut(self):
        """Add a custom shortcut via dialog"""
        name = simpledialog.askstring("Add Shortcut", "Enter a name for this shortcut:")
        if not name:
            return
        
        choice = messagebox.askquestion(
            "Shortcut Type",
            "Do you want to select a FILE?\n\n" +
            "Click 'Yes' for a file\n" +
            "Click 'No' to select a folder or enter a command"
        )
        
        if choice == 'yes':
            path = filedialog.askopenfilename(title="Select a file")
        else:
            folder_choice = messagebox.askquestion(
                "Path Type",
                "Do you want to select a FOLDER?\n\n" +
                "Click 'Yes' to browse for a folder\n" +
                "Click 'No' to manually enter a path/command"
            )
            
            if folder_choice == 'yes':
                path = filedialog.askdirectory(title="Select a folder")
            else:
                path = simpledialog.askstring(
                    "Enter Path",
                    "Enter the full path or command:\n\n" +
                    "Examples:\n" +
                    "• C:\\Program Files\\MyApp\\app.exe\n" +
                    "• discord (for installed apps)\n" +
                    "• spotify (for installed apps)"
                )
        
        if path:
            self.custom_shortcuts.append({
                'name': name,
                'path': path
            })
            self.save_custom_shortcuts()
            
            self.menu.destroy()
            self.create_menu()
            
            messagebox.showinfo("Success", f"Added shortcut: {name}")
            print(f"Added custom shortcut: {name} -> {path}")
            self.log_to_console(f"Added shortcut: {name} -> {path}")
    
    def delete_custom_shortcut(self):
        """Delete a custom shortcut with modern UI"""
        if not self.custom_shortcuts:
            messagebox.showinfo("No Shortcuts", "You don't have any custom shortcuts to delete.")
            return
        
        delete_window = tk.Toplevel(self.root)
        delete_window.title("Delete Shortcut")
        delete_window.geometry("450x500")
        delete_window.configure(bg='#f5f5f5')
        delete_window.attributes('-topmost', True)
        delete_window.resizable(False, False)
        
        main_container = tk.Frame(delete_window, bg='#f5f5f5')
        main_container.pack(fill=tk.BOTH, expand=True)
        
        header_frame = tk.Frame(main_container, bg='#ffffff', height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        header_content = tk.Frame(header_frame, bg='#ffffff')
        header_content.place(relx=0.5, rely=0.5, anchor='center')
        
        title_label = tk.Label(
            header_content,
            text="Delete Shortcut",
            bg='#ffffff',
            fg='#1e1e1e',
            font=('Segoe UI', 20, 'bold')
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            header_content,
            text="Select a shortcut to remove",
            bg='#ffffff',
            fg='#666666',
            font=('Segoe UI', 10)
        )
        subtitle_label.pack()
        
        content_frame = tk.Frame(main_container, bg='#f5f5f5')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        listbox_frame = tk.Frame(content_frame, bg='#ffffff', highlightthickness=1, 
                                 highlightbackground='#e0e0e0', highlightcolor='#0078d4')
        listbox_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(listbox_frame, bg='#f5f5f5', troughcolor='#ffffff', width=14)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=2, pady=2)
        
        listbox = tk.Listbox(
            listbox_frame,
            bg='#ffffff',
            fg='#1e1e1e',
            font=('Segoe UI', 11),
            selectmode=tk.SINGLE,
            yscrollcommand=scrollbar.set,
            relief=tk.FLAT,
            highlightthickness=0,
            selectbackground='#e3f2fd',
            selectforeground='#0078d4',
            activestyle='none',
            borderwidth=0
        )
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=15, pady=15)
        scrollbar.config(command=listbox.yview)
        
        for shortcut in self.custom_shortcuts:
            listbox.insert(tk.END, f"  🔗  {shortcut['name']}")
        
        def do_delete():
            selection = listbox.curselection()
            if not selection:
                error_label = tk.Label(
                    content_frame,
                    text="⚠️ Please select a shortcut first",
                    bg='#fff3cd',
                    fg='#856404',
                    font=('Segoe UI', 9),
                    padx=10,
                    pady=5
                )
                error_label.pack(pady=(5, 0))
                delete_window.after(2000, error_label.destroy)
                return
            
            index = selection[0]
            deleted_shortcut = self.custom_shortcuts[index]
            
            confirm = messagebox.askyesno(
                "Confirm Delete",
                f"Delete '{deleted_shortcut['name']}'?",
                icon='warning'
            )
            
            if confirm:
                self.custom_shortcuts.pop(index)
                self.save_custom_shortcuts()
                
                self.menu.destroy()
                self.create_menu()
                
                delete_window.destroy()
                
                messagebox.showinfo("✓ Deleted", f"Removed {deleted_shortcut['name']}")
                print(f"Deleted custom shortcut: {deleted_shortcut['name']}")
                self.log_to_console(f"Deleted shortcut: {deleted_shortcut['name']}")
        
        button_frame = tk.Frame(main_container, bg='#f5f5f5', height=70)
        button_frame.pack(fill=tk.X, padx=30, pady=(0, 20))
        button_frame.pack_propagate(False)
        
        button_container = tk.Frame(button_frame, bg='#f5f5f5')
        button_container.place(relx=0.5, rely=0.5, anchor='center')
        
        delete_btn = tk.Button(
            button_container,
            text="Delete",
            command=do_delete,
            bg='#d32f2f',
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            padx=30,
            pady=10,
            relief=tk.FLAT,
            cursor='hand2',
            activebackground='#c62828',
            activeforeground='white',
            borderwidth=0
        )
        delete_btn.pack(side=tk.LEFT, padx=5)
        
        def on_enter_delete(e):
            delete_btn['bg'] = '#c62828'
        
        def on_leave_delete(e):
            delete_btn['bg'] = '#d32f2f'
        
        delete_btn.bind('<Enter>', on_enter_delete)
        delete_btn.bind('<Leave>', on_leave_delete)
        
        cancel_btn = tk.Button(
            button_container,
            text="Cancel",
            command=delete_window.destroy,
            bg='#e0e0e0',
            fg='#1e1e1e',
            font=('Segoe UI', 10),
            padx=30,
            pady=10,
            relief=tk.FLAT,
            cursor='hand2',
            activebackground='#d0d0d0',
            activeforeground='#1e1e1e',
            borderwidth=0
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        def on_enter_cancel(e):
            cancel_btn['bg'] = '#d0d0d0'
        
        def on_leave_cancel(e):
            cancel_btn['bg'] = '#e0e0e0'
        
        cancel_btn.bind('<Enter>', on_enter_cancel)
        cancel_btn.bind('<Leave>', on_leave_cancel)
        
        delete_window.update_idletasks()
        x = (delete_window.winfo_screenwidth() // 2) - (delete_window.winfo_width() // 2)
        y = (delete_window.winfo_screenheight() // 2) - (delete_window.winfo_height() // 2)
        delete_window.geometry(f"+{x}+{y}")
        
        delete_window.grab_set()
        delete_window.focus_set()
    
    def open_custom_path(self, path):
        """Open a custom path (file, folder, or command)"""
        system = platform.system()
        try:
            if os.path.exists(path):
                if system == 'Windows':
                    os.startfile(path)
                elif system == 'Darwin':
                    subprocess.Popen(['open', path])
                else:
                    subprocess.Popen(['xdg-open', path])
                print(f"Opening path: {path}")
                self.log_to_console(f"Opened path: {path}")
                return
            
            if system == 'Windows':
                app_lower = path.lower().strip()
                
                if app_lower == 'discord':
                    discord_paths = [
                        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Discord', 'Update.exe'),
                    ]
                    
                    for discord_path in discord_paths:
                        if os.path.exists(discord_path):
                            subprocess.Popen([discord_path, '--processStart', 'Discord.exe'])
                            print(f"Launching Discord via: {discord_path}")
                            self.log_to_console(f"Launched Discord")
                            return
                
                elif app_lower == 'spotify':
                    spotify_path = os.path.join(os.environ.get('APPDATA', ''), 'Spotify', 'Spotify.exe')
                    if os.path.exists(spotify_path):
                        subprocess.Popen([spotify_path])
                        print(f"Launching Spotify via: {spotify_path}")
                        self.log_to_console(f"Launched Spotify")
                        return
                
                try:
                    subprocess.Popen(path, shell=True)
                    print(f"Running command with shell: {path}")
                    self.log_to_console(f"Launched command: {path}")
                    return
                except Exception as e1:
                    print(f"Method 1 (shell) failed: {e1}")
                    try:
                        subprocess.Popen([path])
                        print(f"Running command: {path}")
                        self.log_to_console(f"Launched command: {path}")
                        return
                    except Exception as e2:
                        print(f"Method 2 (direct) failed: {e2}")
                        raise e2
            else:
                subprocess.Popen([path])
                print(f"Running command: {path}")
                self.log_to_console(f"Launched command: {path}")
                
        except Exception as e:
            error_msg = f"Could not open: {path}\n\nError: {e}\n\nTip: For installed apps, try using the full path to the .exe file."
            messagebox.showerror("Error", error_msg)
            print(f"Error opening custom path: {e}")
            self.log_to_console(f"Error opening {path}: {e}")
    
    def change_pet_image(self):
        """Change the pet image/GIF"""
        path = filedialog.askopenfilename(
            title="Select an image or GIF",
            filetypes=[
                ("Image files", "*.gif *.png *.jpg *.jpeg *.bmp"),
                ("GIF files", "*.gif"),
                ("All files", "*.*")
            ]
        )
        
        if path:
            try:
                test_img = Image.open(path)
                test_img.close()
                
                self.custom_image_path = path
                self.save_settings()
                
                self.load_gif()
                
                messagebox.showinfo("Success", "Pet image changed! Restart may be needed for best results.")
                print(f"Changed pet image to: {path}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Could not load image:\n\n{e}")
                print(f"Error loading custom image: {e}")
    
    def show_help(self):
        """Show help dialog"""
        help_text = """Desktop Pet - Help Guide

🎮 BASIC CONTROLS:
• LEFT CLICK + DRAG: Move the pet anywhere
• RIGHT CLICK: Open menu

📋 MENU ORGANIZATION:
• Quick Access: Notepad, Calculator, Downloads
• 🚀 My Apps: Your custom application shortcuts
• 🌐 My URLs: Your custom website bookmarks
• Settings & Tools: Image, startup, console, etc.

🔗 ADDING CUSTOM APPS:
1. Right-click → My Apps → Add New App
2. Enter a name
3. Choose file, folder, or enter command

🌐 ADDING CUSTOM URLS:
1. Right-click → My URLs → Add New URL
2. Enter a name (e.g., "Google", "YouTube")
3. Enter full URL (e.g., https://www.google.com)

💡 TIPS:
• URLs automatically open in your default browser
• Use dropdown menus to keep things organized
• Settings are saved automatically
• Use Debug Console to troubleshoot
• Add to Startup to launch on boot"""
        
        messagebox.showinfo("Desktop Pet - Help", help_text)
    
    def log_to_console(self, message):
        """Log message to console buffer and console window if open"""
        self.console_buffer.append(message)
        if self.console_text:
            self.console_text.insert(tk.END, message + "\n")
            self.console_text.see(tk.END)
        print(message)
    
    def toggle_console(self):
        """Toggle debug console window"""
        if self.console_window and self.console_window.winfo_exists():
            self.console_window.destroy()
            self.console_window = None
            self.console_text = None
        else:
            self.show_console()
    
    def show_console(self):
        """Show debug console window"""
        self.console_window = tk.Toplevel(self.root)
        self.console_window.title("Desktop Pet - Debug Console")
        self.console_window.geometry("700x400")
        self.console_window.configure(bg='#1a1a1a')
        self.console_window.attributes('-topmost', True)
        self.console_window.attributes('-alpha', 0.95)
        
        main_container = tk.Frame(self.console_window, bg='#1a1a1a')
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        title_frame = tk.Frame(main_container, bg='#00aa00', height=50)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame,
            text="🛠 Debug Console",
            bg='#00aa00',
            fg='white',
            font=('Segoe UI', 14, 'bold')
        )
        title_label.place(relx=0.5, rely=0.5, anchor='center')
        
        text_frame = tk.Frame(main_container, bg='#2a2a2a', highlightthickness=1, 
                             highlightbackground='#444444')
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        scrollbar = tk.Scrollbar(text_frame, bg='#3a3a3a', troughcolor='#2a2a2a', width=12)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.console_text = tk.Text(
            text_frame,
            bg='#0a0a0a',
            fg='#00ff00',
            font=('Consolas', 9),
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set,
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        self.console_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.console_text.yview)
        
        for message in self.console_buffer:
            self.console_text.insert(tk.END, message + "\n")
        self.console_text.see(tk.END)
        
        button_frame = tk.Frame(main_container, bg='#1a1a1a')
        button_frame.pack()
        
        clear_btn = tk.Button(
            button_frame,
            text="Clear Console",
            command=self.clear_console,
            bg='#555555',
            fg='white',
            font=('Segoe UI', 10),
            padx=20,
            pady=8,
            relief=tk.FLAT,
            cursor='hand2'
        )
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        close_btn = tk.Button(
            button_frame,
            text="Close",
            command=self.console_window.destroy,
            bg='#00aa00',
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            padx=30,
            pady=8,
            relief=tk.FLAT,
            cursor='hand2'
        )
        close_btn.pack(side=tk.LEFT, padx=5)
    
    def clear_console(self):
        """Clear console text"""
        if self.console_text:
            self.console_text.delete(1.0, tk.END)
        self.console_buffer.clear()
    
    def add_to_startup(self):
        """Add the desktop pet to Windows startup"""
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
                "Desktop Pet added to startup!\n\n"
                "It will now start automatically when you log in.\n\n"
                "To remove it later, go to Task Manager > Startup tab."
            )
            self.log_to_console("Added to Windows startup")
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not add to startup:\n\n{e}")
            self.log_to_console(f"Error adding to startup: {e}")

if __name__ == "__main__":
    print("Starting Desktop Pet...")
    print("LEFT CLICK and DRAG to move")
    print("RIGHT CLICK to open menu")
    print("-" * 40)
    
    pet = DesktopPet()
    
    pet.log_to_console("Desktop Pet started successfully")
    pet.log_to_console(f"Settings directory: {pet.app_data_dir}")
    pet.log_to_console(f"Loaded {len(pet.custom_shortcuts)} custom shortcuts")
    pet.log_to_console(f"Loaded {len(pet.custom_urls)} custom URLs")
