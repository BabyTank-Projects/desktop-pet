import tkinter as tk
from tkinter import Menu as TkMenu, simpledialog, messagebox, filedialog
from PIL import Image, ImageTk
import requests
from io import BytesIO
import subprocess
import platform
import os
import json

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
        # Get the directory where the script is located
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.shortcuts_file = os.path.join(self.script_dir, 'desktop_pet_shortcuts.json')
        self.settings_file = os.path.join(self.script_dir, 'desktop_pet_settings.json')
        self.custom_shortcuts = []
        self.stay_on_desktop = tk.BooleanVar(value=False)
        self.custom_image_path = None
        
        # Console window
        self.console_window = None
        self.console_text = None
        
        # Redirect print statements to our console
        self.console_buffer = []
        
        # Load settings
        self.load_settings()
        
        # Load the animated GIF
        self.load_gif()
        
        # Create label to display the image
        self.label = tk.Label(self.root, bg='black', bd=0)
        self.label.pack()
        
        # Bind mouse events - LEFT CLICK to drag, RIGHT CLICK for menu
        self.label.bind('<Button-1>', self.start_drag)
        self.label.bind('<B1-Motion>', self.drag)
        self.label.bind('<ButtonRelease-1>', self.stop_drag)
        self.label.bind('<Button-3>', self.show_menu)  # Right-click for menu
        
        # Create context menu
        self.create_menu()
        
        # Start animation
        self.current_frame = 0
        self.animate()
        
        self.root.mainloop()
    
    def load_gif(self):
        """Load the animated GIF from URL or custom path and resize it"""
        try:
            # Check if custom image is set
            if self.custom_image_path and os.path.exists(self.custom_image_path):
                # Load from local file
                gif = Image.open(self.custom_image_path)
            else:
                # Load default from URL
                url = "https://oldschool.runescape.wiki/images/thumb/Infernal_cape_detail_animated.gif/100px-Infernal_cape_detail_animated.gif?35cc2"
                response = requests.get(url)
                gif_data = BytesIO(response.content)
                gif = Image.open(gif_data)
            
            # Load all frames
            self.frames = []
            
            # Get original size and calculate new size (make it smaller)
            original_width, original_height = gif.size
            
            # Scale down to 60% of original size to show full image
            scale_factor = 0.6
            new_width = int(original_width * scale_factor)
            new_height = int(original_height * scale_factor)
            
            try:
                while True:
                    frame = gif.copy()
                    frame = frame.convert('RGBA')
                    # Resize frame with high quality
                    frame = frame.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    self.frames.append(ImageTk.PhotoImage(frame))
                    gif.seek(len(self.frames))
            except EOFError:
                pass  # End of frames
            
            # Adjust window size to fit the resized image
            if self.frames:
                self.root.geometry(f'{new_width}x{new_height}+100+100')
                
        except Exception as e:
            print(f"Error loading GIF: {e}")
            # Create a placeholder if loading fails
            placeholder = Image.new('RGBA', (80, 80), (255, 0, 0, 255))
            self.frames = [ImageTk.PhotoImage(placeholder)]
    
    def animate(self):
        """Animate the GIF frames"""
        if self.frames:
            self.label.config(image=self.frames[self.current_frame])
            self.current_frame = (self.current_frame + 1) % len(self.frames)
        self.root.after(100, self.animate)  # Update every 100ms
    
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
            # Remove always on top
            self.root.attributes('-topmost', False)
            # Send to bottom (desktop level)
            self.root.lower()
            self.log_to_console("Pet now stays on desktop only")
        else:
            # Set always on top
            self.root.attributes('-topmost', True)
            self.log_to_console("Pet now stays on top of all windows")
    
    def toggle_stay_on_desktop(self):
        """Toggle the stay on desktop setting"""
        self.update_window_level()
        self.save_settings()
    
    def load_custom_shortcuts(self):
        """Load custom shortcuts from JSON file and add to menu"""
        try:
            if os.path.exists(self.shortcuts_file):
                with open(self.shortcuts_file, 'r') as f:
                    self.custom_shortcuts = json.load(f)
            else:
                self.custom_shortcuts = []
        except Exception as e:
            print(f"Error loading shortcuts: {e}")
            self.custom_shortcuts = []
    
    def add_shortcuts_to_menu(self):
        """Add loaded shortcuts to the menu"""
        if self.custom_shortcuts:
            for shortcut in self.custom_shortcuts:
                name = shortcut.get('name', 'Unknown')
                path = shortcut.get('path', '')
                # Use default argument to capture current path value
                self.menu.add_command(
                    label=f"  🔗 {name}", 
                    command=lambda p=path: self.open_custom_path(p)
                )
                print(f"Added shortcut to menu: {name}")
    
    def save_custom_shortcuts(self):
        """Save custom shortcuts to JSON file"""
        try:
            with open(self.shortcuts_file, 'w') as f:
                json.dump(self.custom_shortcuts, f, indent=2)
        except Exception as e:
            print(f"Error saving shortcuts: {e}")
    
    def create_menu(self):
        """Create the context menu"""
        self.menu = TkMenu(
            self.root, 
            tearoff=0, 
            bg='#2a2a2a', 
            fg='#e0e0e0', 
            activebackground='#ff6600', 
            activeforeground='white',
            relief='flat', 
            bd=0,
            font=('Segoe UI', 10),
            activeborderwidth=0
        )
        
        self.menu.add_command(label="  📝 Notepad", command=self.open_notepad)
        self.menu.add_command(label="  🔢 Calculator", command=self.open_calculator)
        self.menu.add_command(label="  📁 Downloads", command=self.open_downloads)
        self.menu.add_separator()
        
        # Load and display custom shortcuts
        self.load_custom_shortcuts()
        self.add_shortcuts_to_menu()
        
        if self.custom_shortcuts:
            self.menu.add_separator()
        
        self.menu.add_command(label="  ➕ Add Custom Shortcut", command=self.add_custom_shortcut)
        self.menu.add_command(label="  🗑️ Delete Custom Shortcut", command=self.delete_custom_shortcut)
        self.menu.add_command(label="  🖼️ Change Pet Image/GIF", command=self.change_pet_image)
        self.menu.add_separator()
        
        # Add checkbox for stay on desktop
        self.menu.add_checkbutton(
            label="  📌 Stay on Desktop Only", 
            variable=self.stay_on_desktop,
            command=self.toggle_stay_on_desktop
        )
        
        self.menu.add_separator()
        self.menu.add_command(label="  ❓ Help", command=self.show_help)
        self.menu.add_command(label="  🐛 Debug Console", command=self.toggle_console)
        self.menu.add_command(label="  🚀 Add to Startup", command=self.add_to_startup)
        self.menu.add_command(label="  ❌ Exit", command=self.root.quit)
    
    def show_menu(self, event):
        """Show context menu on right-click"""
        try:
            # Show menu at cursor position
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()
    
    def open_notepad(self):
        """Open Notepad"""
        system = platform.system()
        try:
            if system == 'Windows':
                subprocess.Popen(['notepad.exe'])
            elif system == 'Darwin':  # macOS
                subprocess.Popen(['open', '-a', 'TextEdit'])
            else:  # Linux
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
            elif system == 'Darwin':  # macOS
                subprocess.Popen(['open', '-a', 'Calculator'])
            else:  # Linux
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
            elif system == 'Darwin':  # macOS
                subprocess.Popen(['open', downloads_path])
            else:  # Linux
                subprocess.Popen(['xdg-open', downloads_path])
            print(f"Opening Downloads folder: {downloads_path}")
        except Exception as e:
            print(f"Error opening downloads: {e}")
    
    def add_custom_shortcut(self):
        """Add a custom shortcut via dialog"""
        # Ask for name
        name = simpledialog.askstring("Add Shortcut", "Enter a name for this shortcut:")
        if not name:
            return
        
        # Ask what type of shortcut
        choice = messagebox.askquestion(
            "Shortcut Type",
            "Do you want to select a FILE?\n\n" +
            "Click 'Yes' for a file\n" +
            "Click 'No' to select a folder or enter a command/URL"
        )
        
        if choice == 'yes':
            # File picker
            path = filedialog.askopenfilename(title="Select a file")
        else:
            # Folder picker or manual entry
            folder_choice = messagebox.askquestion(
                "Path Type",
                "Do you want to select a FOLDER?\n\n" +
                "Click 'Yes' to browse for a folder\n" +
                "Click 'No' to manually enter a path/URL/command"
            )
            
            if folder_choice == 'yes':
                path = filedialog.askdirectory(title="Select a folder")
            else:
                path = simpledialog.askstring(
                    "Enter Path",
                    "Enter the full path, URL, or command:\n\n" +
                    "Examples:\n" +
                    "• C:\\Program Files\\MyApp\\app.exe\n" +
                    "• https://www.google.com\n" +
                    "• spotify (for installed apps)"
                )
        
        if path:
            # Add to shortcuts
            self.custom_shortcuts.append({
                'name': name,
                'path': path
            })
            self.save_custom_shortcuts()
            
            # Recreate menu to show new shortcut
            self.menu.destroy()
            self.create_menu()
            
            messagebox.showinfo("Success", f"Added shortcut: {name}")
            print(f"Added custom shortcut: {name} -> {path}")
    
    def delete_custom_shortcut(self):
        """Delete a custom shortcut"""
        if not self.custom_shortcuts:
            messagebox.showinfo("No Shortcuts", "You don't have any custom shortcuts to delete.")
            return
        
        # Create a modern dialog to select which shortcut to delete
        delete_window = tk.Toplevel(self.root)
        delete_window.title("Delete Custom Shortcut")
        delete_window.geometry("500x400")
        delete_window.configure(bg='#1a1a1a')
        delete_window.attributes('-topmost', True)
        delete_window.attributes('-alpha', 0.95)
        delete_window.resizable(True, True)
        
        # Main container with padding
        main_container = tk.Frame(delete_window, bg='#1a1a1a')
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title with colored background
        title_frame = tk.Frame(main_container, bg='#ff4444', height=50)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame,
            text="Select a shortcut to delete:",
            bg='#ff4444',
            fg='white',
            font=('Segoe UI', 14, 'bold')
        )
        title_label.place(relx=0.5, rely=0.5, anchor='center')
        
        # Listbox container with border
        listbox_container = tk.Frame(main_container, bg='#444444', highlightthickness=1, 
                                     highlightbackground='#555555')
        listbox_container.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        listbox_frame = tk.Frame(listbox_container, bg='#2a2a2a')
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        scrollbar = tk.Scrollbar(listbox_frame, bg='#3a3a3a', troughcolor='#2a2a2a', width=12)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(
            listbox_frame,
            bg='#2a2a2a',
            fg='#e0e0e0',
            font=('Segoe UI', 11),
            selectmode=tk.SINGLE,
            yscrollcommand=scrollbar.set,
            relief=tk.FLAT,
            highlightthickness=0,
            selectbackground='#ff6600',
            selectforeground='white',
            activestyle='none'
        )
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.config(command=listbox.yview)
        
        # Add shortcuts to listbox (names only)
        for shortcut in self.custom_shortcuts:
            listbox.insert(tk.END, f"  {shortcut['name']}")
        
        # Delete button
        def do_delete():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a shortcut to delete.")
                return
            
            index = selection[0]
            deleted_shortcut = self.custom_shortcuts[index]
            
            # Confirm deletion
            confirm = messagebox.askyesno(
                "Confirm Delete",
                f"Are you sure you want to delete:\n\n{deleted_shortcut['name']}?"
            )
            
            if confirm:
                self.custom_shortcuts.pop(index)
                self.save_custom_shortcuts()
                
                # Recreate menu
                self.menu.destroy()
                self.create_menu()
                
                delete_window.destroy()
                messagebox.showinfo("Deleted", f"Deleted shortcut: {deleted_shortcut['name']}")
                print(f"Deleted custom shortcut: {deleted_shortcut['name']}")
        
        button_frame = tk.Frame(main_container, bg='#1a1a1a')
        button_frame.pack()
        
        delete_btn = tk.Button(
            button_frame,
            text="Delete Selected",
            command=do_delete,
            bg='#ff4444',
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            padx=25,
            pady=8,
            relief=tk.FLAT,
            cursor='hand2',
            activebackground='#ff6666',
            activeforeground='white'
        )
        delete_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = tk.Button(
            button_frame,
            text="Cancel",
            command=delete_window.destroy,
            bg='#555555',
            fg='white',
            font=('Segoe UI', 10),
            padx=25,
            pady=8,
            relief=tk.FLAT,
            cursor='hand2',
            activebackground='#777777',
            activeforeground='white'
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        # Keep window open until manually closed
        delete_window.grab_set()
        delete_window.focus_set()
    
    def open_custom_path(self, path):
        """Open a custom path (file, folder, URL, or command)"""
        system = platform.system()
        try:
            # Check if it's a URL
            if path.startswith('http://') or path.startswith('https://'):
                import webbrowser
                webbrowser.open(path)
                print(f"Opening URL: {path}")
            # Check if it's a file or folder
            elif os.path.exists(path):
                if system == 'Windows':
                    os.startfile(path)
                elif system == 'Darwin':
                    subprocess.Popen(['open', path])
                else:
                    subprocess.Popen(['xdg-open', path])
                print(f"Opening path: {path}")
            # Try as a command
            else:
                subprocess.Popen([path])
                print(f"Running command: {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open: {path}\n\nError: {e}")
            print(f"Error opening custom path: {e}")
    
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
            # Test if image can be loaded
            try:
                test_img = Image.open(path)
                test_img.close()
                
                # Save the custom image path
                self.custom_image_path = path
                self.save_settings()
                
                # Reload the image
                self.load_gif()
                
                messagebox.showinfo("Success", "Pet image changed! Restart may be needed for best results.")
                print(f"Changed pet image to: {path}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Could not load image:\n\n{e}")
                print(f"Error loading custom image: {e}")
    
    def show_help(self):
        """Show help dialog"""
        help_window = tk.Toplevel(self.root)
        help_window.title("Desktop Pet - Help")
        help_window.geometry("600x650")
        help_window.configure(bg='#1a1a1a')
        help_window.attributes('-topmost', True)
        help_window.attributes('-alpha', 0.95)  # Slight transparency
        help_window.resizable(True, True)
        
        # Create main container with padding
        main_container = tk.Frame(help_window, bg='#1a1a1a')
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title with gradient effect background
        title_frame = tk.Frame(main_container, bg='#ff6600', height=60)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame,
            text="Desktop Pet - Help Guide",
            bg='#ff6600',
            fg='white',
            font=('Segoe UI', 18, 'bold')
        )
        title_label.place(relx=0.5, rely=0.5, anchor='center')
        
        # Create canvas with scrollbar for content
        canvas_frame = tk.Frame(main_container, bg='#2a2a2a', highlightthickness=1, highlightbackground='#444444')
        canvas_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        canvas = tk.Canvas(canvas_frame, bg='#2a2a2a', highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview, 
                                bg='#3a3a3a', troughcolor='#2a2a2a', width=12)
        scrollable_frame = tk.Frame(canvas, bg='#2a2a2a')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=540)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Enable mouse wheel scrolling anywhere on the window
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        # Bind mouse wheel to all widgets
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        help_window.bind("<MouseWheel>", on_mousewheel)
        scrollable_frame.bind("<MouseWheel>", on_mousewheel)
        
        # Unbind when window closes to prevent interference
        def on_close():
            canvas.unbind_all("<MouseWheel>")
            help_window.destroy()
        
        help_window.protocol("WM_DELETE_WINDOW", on_close)
        
        # Help content with better formatting
        help_sections = [
            ("🎮 BASIC CONTROLS", [
                "• LEFT CLICK + DRAG: Move the pet anywhere on your screen",
                "• RIGHT CLICK: Open the menu with all options"
            ]),
            ("📝 MENU FUNCTIONS", [
                "Notepad: Opens Windows Notepad for quick notes",
                "Calculator: Opens the system calculator",
                "Downloads: Opens your Downloads folder",
                "",
                "➕ Add Custom Shortcut: Add your own apps, folders, or websites",
                "🗑️ Delete Custom Shortcut: Remove shortcuts you no longer need",
                "🖼️ Change Pet Image/GIF: Replace the pet with your own image",
                "",
                "📌 Stay on Desktop Only: When checked, pet stays behind windows",
                "❓ Help: Shows this help guide",
                "❌ Exit: Close the desktop pet"
            ]),
            ("🔗 ADDING CUSTOM SHORTCUTS", [
                "1. Right-click the pet and select 'Add Custom Shortcut'",
                "2. Enter a name (e.g., 'Chrome', 'My Project')",
                "3. Choose the type:",
                "   • FILE: Select an .exe or any file",
                "   • FOLDER: Select a folder to open",
                "   • MANUAL: Enter a URL or command",
                "",
                "Examples:",
                "   • File: C:\\Program Files\\MyApp\\app.exe",
                "   • URL: https://www.google.com",
                "   • Command: spotify, discord, chrome"
            ]),
            ("⚠️ CLEANING UP YOUR DESKTOP", [
                "If you want to remove icons from your desktop:",
                "",
                "DO NOT just delete the .exe files! They need to exist for",
                "shortcuts to work.",
                "",
                "CORRECT WAY:",
                "1. Create a folder: C:\\MyApps or C:\\Programs",
                "2. MOVE (don't delete) your .exe files there",
                "3. Delete old shortcuts from the pet menu",
                "4. Add NEW shortcuts pointing to the new location",
                "",
                "OR - If it's an installed program:",
                "• The .exe is usually in C:\\Program Files\\AppName\\",
                "• Delete the desktop shortcut",
                "• Add a shortcut to the installed program location"
            ]),
            ("💡 TIPS", [
                "• The pet remembers your position and settings",
                "• Shortcuts are saved even after closing the app",
                "• Use 'Stay on Desktop Only' to keep it in the background",
                "• You can use any GIF or image as your pet!",
                "• Custom shortcuts support URLs, files, folders, and commands"
            ]),
            ("📂 FILES CREATED", [
                "The pet creates these files in its folder:",
                "• desktop_pet_shortcuts.json (your shortcuts)",
                "• desktop_pet_settings.json (your preferences)"
            ]),
            ("🎨 CUSTOMIZATION", [
                "Want a different pet? Click 'Change Pet Image/GIF' and",
                "select any image or animated GIF from your computer!"
            ])
        ]
        
        # Create styled sections
        for section_title, section_content in help_sections:
            # Section header
            header_frame = tk.Frame(scrollable_frame, bg='#ff6600', height=2)
            header_frame.pack(fill=tk.X, padx=20, pady=(15, 5))
            
            section_label = tk.Label(
                scrollable_frame,
                text=section_title,
                bg='#2a2a2a',
                fg='#ff6600',
                font=('Segoe UI', 11, 'bold'),
                anchor='w'
            )
            section_label.pack(fill=tk.X, padx=20, pady=(5, 8))
            
            # Section content
            for line in section_content:
                content_label = tk.Label(
                    scrollable_frame,
                    text=line,
                    bg='#2a2a2a',
                    fg='#e0e0e0',
                    font=('Segoe UI', 9),
                    anchor='w',
                    justify=tk.LEFT,
                    wraplength=500
                )
                content_label.pack(fill=tk.X, padx=25, pady=1)
        
        # Add some bottom padding
        tk.Frame(scrollable_frame, bg='#2a2a2a', height=20).pack()
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Modern close button
        close_btn = tk.Button(
            main_container,
            text="Close",
            command=on_close,
            bg='#ff6600',
            fg='white',
            font=('Segoe UI', 11, 'bold'),
            padx=40,
            pady=10,
            relief=tk.FLAT,
            cursor='hand2',
            activebackground='#ff8833',
            activeforeground='white'
        )
        close_btn.pack(pady=(0, 5))
        
        # Keep window open until manually closed
        help_window.grab_set()
        help_window.focus_set()
    
    def log_to_console(self, message):
        """Log message to console buffer and console window if open"""
        self.console_buffer.append(message)
        if self.console_text:
            self.console_text.insert(tk.END, message + "\n")
            self.console_text.see(tk.END)
        print(message)  # Also print to regular console
    
    def toggle_console(self):
        """Toggle debug console window"""
        if self.console_window and self.console_window.winfo_exists():
            # Close console
            self.console_window.destroy()
            self.console_window = None
            self.console_text = None
        else:
            # Open console
            self.show_console()
    
    def show_console(self):
        """Show debug console window"""
        self.console_window = tk.Toplevel(self.root)
        self.console_window.title("Desktop Pet - Debug Console")
        self.console_window.geometry("700x400")
        self.console_window.configure(bg='#1a1a1a')
        self.console_window.attributes('-topmost', True)
        self.console_window.attributes('-alpha', 0.95)
        
        # Main container
        main_container = tk.Frame(self.console_window, bg='#1a1a1a')
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_frame = tk.Frame(main_container, bg='#00aa00', height=50)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame,
            text="🐛 Debug Console",
            bg='#00aa00',
            fg='white',
            font=('Segoe UI', 14, 'bold')
        )
        title_label.place(relx=0.5, rely=0.5, anchor='center')
        
        # Text area with scrollbar
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
        
        # Load existing console buffer
        for message in self.console_buffer:
            self.console_text.insert(tk.END, message + "\n")
        self.console_text.see(tk.END)
        
        # Button frame
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
            
            # Get the path to the script
            script_path = os.path.abspath(__file__)
            
            # For .py files, we need to run with pythonw.exe (no console)
            python_path = sys.executable.replace('python.exe', 'pythonw.exe')
            
            # Create the command
            if script_path.endswith('.py'):
                command = f'"{python_path}" "{script_path}"'
            else:
                command = f'"{script_path}"'
            
            # Registry path for startup
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            
            # Open the registry key
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            
            # Set the value
            winreg.SetValueEx(key, "DesktopPet", 0, winreg.REG_SZ, command)
            
            # Close the key
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
    
    # Install required packages:
    # pip install pillow requests
    
    pet = DesktopPet()
    
    # Log startup message
    pet.log_to_console("Desktop Pet started successfully")
    pet.log_to_console(f"Script directory: {pet.script_dir}")
    pet.log_to_console(f"Loaded {len(pet.custom_shortcuts)} custom shortcuts")
    

    pet.root.mainloop()
