import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import random
from pynput import mouse, keyboard

class AutoClicker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Advanced AutoClicker")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        # State variables
        self.left_active = False
        self.right_active = False
        self.listening_for_bind = None

        # Toggle state flags
        self.left_toggle_state = False
        self.right_toggle_state = False

        # Configuration variables
        self.left_min_cps = tk.DoubleVar(value=15.0)
        self.left_max_cps = tk.DoubleVar(value=20.0)
        self.right_min_cps = tk.DoubleVar(value=15.0)
        self.right_max_cps = tk.DoubleVar(value=20.0)
        self.left_bind = tk.StringVar(value="R")
        self.right_bind = tk.StringVar(value="F")
        self.left_mode = tk.StringVar(value="Hold")
        self.right_mode = tk.StringVar(value="Hold")
        
        self.setup_ui()
        self.setup_listeners()
        
        self.mouse_controller = mouse.Controller()
        
    def setup_ui(self):
        # Styles
        style = ttk.Style()
        style.configure("TFrame", background="#f0f0f0")
        style.configure("TLabel", background="#f0f0f0")
        style.configure("TLabelframe", background="#f0f0f0")
        style.configure("TLabelframe.Label", background="#f0f0f0")
        
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        # Left mouse button section
        left_frame = ttk.LabelFrame(main_frame, text="Left Mouse Button", padding=15)
        left_frame.pack(pady=10, fill="x")
        
        ttk.Label(left_frame, text="MIN CPS:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        ttk.Entry(left_frame, textvariable=self.left_min_cps, width=8).grid(row=0, column=1, padx=5)
        
        ttk.Label(left_frame, text="MAX CPS:").grid(row=0, column=2, sticky="w", padx=(20, 5))
        ttk.Entry(left_frame, textvariable=self.left_max_cps, width=8).grid(row=0, column=3, padx=5)
        
        ttk.Label(left_frame, text="Bind:").grid(row=1, column=0, sticky="w", pady=(15, 0), padx=(0, 5))
        self.left_bind_btn = ttk.Button(left_frame, textvariable=self.left_bind, width=8,
                                       command=lambda: self.start_listening_bind("left"))
        self.left_bind_btn.grid(row=1, column=1, pady=(15, 0), padx=5)

        ttk.Label(left_frame, text="Mode:").grid(row=1, column=2, sticky="w", pady=(15, 0))
        self.left_mode_option = ttk.Combobox(left_frame, textvariable=self.left_mode, width=7, state="readonly")
        self.left_mode_option['values'] = ['Hold', 'Toggle']
        self.left_mode_option.grid(row=1, column=3, pady=(15, 0), padx=5)
        
        self.left_status = ttk.Label(left_frame, text="Inactive", foreground="red", font=("Arial", 10, "bold"))
        self.left_status.grid(row=2, column=0, columnspan=4, pady=(15, 0), padx=(0, 0))
        
        # Right mouse button section
        right_frame = ttk.LabelFrame(main_frame, text="Right Mouse Button", padding=15)
        right_frame.pack(pady=10, fill="x")
        
        ttk.Label(right_frame, text="MIN CPS:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        ttk.Entry(right_frame, textvariable=self.right_min_cps, width=8).grid(row=0, column=1, padx=5)
        
        ttk.Label(right_frame, text="MAX CPS:").grid(row=0, column=2, sticky="w", padx=(20, 5))
        ttk.Entry(right_frame, textvariable=self.right_max_cps, width=8).grid(row=0, column=3, padx=5)
        
        ttk.Label(right_frame, text="Bind:").grid(row=1, column=0, sticky="w", pady=(15, 0), padx=(0, 5))
        self.right_bind_btn = ttk.Button(right_frame, textvariable=self.right_bind, width=8,
                                        command=lambda: self.start_listening_bind("right"))
        self.right_bind_btn.grid(row=1, column=1, pady=(15, 0), padx=5)

        ttk.Label(right_frame, text="Mode:").grid(row=1, column=2, sticky="w", pady=(15, 0))
        self.right_mode_option = ttk.Combobox(right_frame, textvariable=self.right_mode, width=7, state="readonly")
        self.right_mode_option['values'] = ['Hold', 'Toggle']
        self.right_mode_option.grid(row=1, column=3, pady=(15, 0), padx=5)

        self.right_status = ttk.Label(right_frame, text="Inactive", foreground="red", font=("Arial", 10, "bold"))
        self.right_status.grid(row=2, column=0, columnspan=4, pady=(15, 0), padx=(0, 0))
        
        # Removed instructions/info section
        
        # Status bar
        self.status_bar = ttk.Label(main_frame, text="Ready", relief="sunken", anchor="w", foreground="green")
        self.status_bar.pack(fill="x", pady=(10, 0))
    
    def setup_listeners(self):
        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        )
        self.keyboard_listener.start()
    
    def update_status(self, message, color="black"):
        self.status_bar.config(text=message, foreground=color)
        self.root.after(3000, lambda: self.status_bar.config(text="Ready", foreground="green"))
    
    def start_listening_bind(self, bind_type):
        if self.listening_for_bind:
            self.stop_listening_bind()
        
        self.listening_for_bind = bind_type
        
        # Change button text
        getattr(self, f"{bind_type}_bind_btn").config(text="Press a key...", state="disabled")
        
        self.update_status(f"Listening for {bind_type} bind... Press any key", "blue")
        
        # Temporarily stop key listening for autoclicker
        self.keyboard_listener.stop()
        
        # Start temporary listener for bind change
        self.bind_listener = keyboard.Listener(on_press=self.on_bind_key_press)
        self.bind_listener.start()
    
    def stop_listening_bind(self):
        if self.listening_for_bind:
            bind_type = self.listening_for_bind
            getattr(self, f"{bind_type}_bind_btn").config(
                text=getattr(self, f"{bind_type}_bind").get(), 
                state="normal"
            )
            self.listening_for_bind = None
        
        # Restore normal listener
        if hasattr(self, 'bind_listener'):
            self.bind_listener.stop()
        self.setup_listeners()
    
    def on_bind_key_press(self, key):
        if not self.listening_for_bind:
            return
        
        try:
            # Try to get the key character
            if hasattr(key, 'char') and key.char:
                new_bind = key.char
            else:
                # For special keys
                new_bind = str(key).split('.')[-1]
                if new_bind.startswith('Key.'):
                    new_bind = new_bind[4:]
            
            # Check if key is already used
            other_bind_type = "right" if self.listening_for_bind == "left" else "left"
            other_bind = getattr(self, f"{other_bind_type}_bind").get().lower()
            
            if new_bind.lower() == other_bind:
                messagebox.showwarning("Warning", f"Key {new_bind} is already used for {other_bind_type} bind!")
                self.stop_listening_bind()
                return
            
            # Set new bind
            getattr(self, f"{self.listening_for_bind}_bind").set(new_bind.upper())
            self.update_status(f"{self.listening_for_bind.capitalize()} bind changed to: {new_bind.upper()}", "green")
            
        except Exception as e:
            print(f"Error while changing bind: {e}")
            self.update_status("Error while changing bind", "red")
        
        self.stop_listening_bind()

    def on_key_press(self, key):
        if self.listening_for_bind:
            return

        try:
            current_key = None
            if hasattr(key, 'char') and key.char:
                current_key = key.char.lower()
            else:
                current_key = str(key).split('.')[-1].lower()
                if current_key.startswith('key.'):
                    current_key = current_key[4:]
            
            left_bind_key = self.left_bind.get().lower()
            right_bind_key = self.right_bind.get().lower()

            # Left bind logic
            if current_key == left_bind_key:
                if self.left_mode.get() == "Hold":
                    if not self.left_active:
                        self.left_active = True
                        self.left_status.config(text="Active", foreground="green")
                        threading.Thread(target=self.left_clicker, daemon=True).start()
                elif self.left_mode.get() == "Toggle":
                    if not self.left_toggle_state:
                        self.left_toggle_state = True
                        self.left_active = True
                        self.left_status.config(text="Active (Toggled)", foreground="green")
                        threading.Thread(target=self.left_clicker, daemon=True).start()
                    else:
                        self.left_toggle_state = False
                        self.left_active = False
                        self.left_status.config(text="Inactive", foreground="red")

            # Right bind logic
            elif current_key == right_bind_key:
                if self.right_mode.get() == "Hold":
                    if not self.right_active:
                        self.right_active = True
                        self.right_status.config(text="Active", foreground="green")
                        threading.Thread(target=self.right_clicker, daemon=True).start()
                elif self.right_mode.get() == "Toggle":
                    if not self.right_toggle_state:
                        self.right_toggle_state = True
                        self.right_active = True
                        self.right_status.config(text="Active (Toggled)", foreground="green")
                        threading.Thread(target=self.right_clicker, daemon=True).start()
                    else:
                        self.right_toggle_state = False
                        self.right_active = False
                        self.right_status.config(text="Inactive", foreground="red")
        except Exception as e:
            print(f"Error in on_key_press: {e}")

    def on_key_release(self, key):
        if self.listening_for_bind:
            return

        try:
            current_key = None
            if hasattr(key, 'char') and key.char:
                current_key = key.char.lower()
            else:
                current_key = str(key).split('.')[-1].lower()
                if current_key.startswith('key.'):
                    current_key = current_key[4:]
            
            left_bind_key = self.left_bind.get().lower()
            right_bind_key = self.right_bind.get().lower()
            
            if current_key == left_bind_key and self.left_mode.get() == "Hold":
                self.left_active = False
                self.left_status.config(text="Inactive", foreground="red")
            
            elif current_key == right_bind_key and self.right_mode.get() == "Hold":
                self.right_active = False
                self.right_status.config(text="Inactive", foreground="red")
                
        except Exception as e:
            print(f"Error in on_key_release: {e}")
    
    def left_clicker(self):
        while self.left_active:
            try:
                min_delay = 1.0 / self.left_max_cps.get()
                max_delay = 1.0 / self.left_min_cps.get()
                delay = random.uniform(min_delay, max_delay)
                self.mouse_controller.click(mouse.Button.left)
                time.sleep(delay)
            except Exception as e:
                print(f"Error in left_clicker: {e}")
                break
    
    def right_clicker(self):
        while self.right_active:
            try:
                min_delay = 1.0 / self.right_max_cps.get()
                max_delay = 1.0 / self.right_min_cps.get()
                delay = random.uniform(min_delay, max_delay)
                self.mouse_controller.click(mouse.Button.right)
                time.sleep(delay)
            except Exception as e:
                print(f"Error in right_clicker: {e}")
                break
    
    def run(self):
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("Closing program...")
        finally:
            if hasattr(self, 'keyboard_listener'):
                self.keyboard_listener.stop()
            if hasattr(self, 'bind_listener'):
                self.bind_listener.stop()

if __name__ == "__main__":
    autoclicker = AutoClicker()
    autoclicker.run()