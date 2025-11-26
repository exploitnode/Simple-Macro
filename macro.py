import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import random
import sys
import platform
from pynput import mouse, keyboard

class AutoClicker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Node-Macro by exploitnode")
        # Increased window size for better layout
        self.root.geometry("800x800")
        self.root.resizable(False, False)

        # ===== Clicker state =====
        self.left_active = False
        self.right_active = False
        self.listening_for_bind = None
        self.left_toggle_state = False
        self.right_toggle_state = False

        # ===== Click rhythm config =====
        self.left_min_cps = tk.DoubleVar(value=15.0)
        self.left_max_cps = tk.DoubleVar(value=20.0)
        self.right_min_cps = tk.DoubleVar(value=12.0)
        self.right_max_cps = tk.DoubleVar(value=14.0)
        self.left_mode = tk.StringVar(value="Hold")
        self.right_mode = tk.StringVar(value="Hold")
        self.left_randomize = tk.BooleanVar(value=True)
        self.right_randomize = tk.BooleanVar(value=True)
        self.left_double_click = tk.BooleanVar(value=False)
        self.left_double_click_chance = tk.DoubleVar(value=7.5)  # %
        self.left_double_click_delay = tk.DoubleVar(value=18.0)  # ms

        # ===== Binds =====
        self.left_bind = tk.StringVar(value="R")
        self.right_bind = tk.StringVar(value="F")
        self.wtap_key = tk.StringVar(value="W")

        # ===== W-Tap (PvP knockback) feature =====
        self.wtap_enabled = tk.BooleanVar(value=True)
        self.wtap_delay = tk.DoubleVar(value=35.0)    # ms
        self.wtap_release = tk.DoubleVar(value=55.0)  # ms

        # ===== Jitter aim =====
        self.jitter_enabled = tk.BooleanVar(value=True)
        self.jitter_range = tk.DoubleVar(value=1.5)   # px
        self.jitter_frequency = tk.DoubleVar(value=0.8) # chance per click (0-1)

        # ===== Extra automation =====
        self.smooth_stop = tk.BooleanVar(value=True)
        self.smooth_stop_time = tk.DoubleVar(value=75.0)  # ms
        self.autostart = tk.BooleanVar(value=False)
        self.always_on_top = tk.BooleanVar(value=False)

        # ===== Theme/Dark mode =====
        # Dark theme is always enabled by default (no toggle in UI)
        self.dark_theme = tk.BooleanVar(value=True)

        # Track system info for "about"
        self.system_platform = platform.system()
        self.python_version = sys.version.split()[0]

        # Set up UI and event listeners
        self.setup_ui()
        self.setup_listeners()
        self.mouse_controller = mouse.Controller()
        self.keyboard_controller = keyboard.Controller()
        if self.autostart.get():
            self.left_active = True

    def setup_ui(self):
        style = ttk.Style()

        # Use a theme that allows widget color overrides more predictably
        try:
            style.theme_use('clam')
        except Exception:
            pass

        # Apply root background to match dark theme
        if self.dark_theme.get():
            self.root.tk_setPalette(background='#181b1f', foreground='#ebebeb')
            self.root.configure(bg='#181b1f')
        else:
            self.root.configure(bg='#f0f0f0')

        # Configure common ttk styles for dark/light mode
        frame_bg = "#24272b" if self.dark_theme.get() else "#f0f0f0"
        labelframe_bg = "#181b1f" if self.dark_theme.get() else "#f0f0f0"
        entry_bg = "#2b2f33" if self.dark_theme.get() else "#ffffff"
        fg_color = "#ebebeb" if self.dark_theme.get() else "#000000"
        secondary_fg = "#a0a0a0" if self.dark_theme.get() else "#888888"

        style.configure("TFrame", background=frame_bg)
        style.configure("TLabel", background=frame_bg, foreground=fg_color)
        style.configure("TLabelframe", background=labelframe_bg)
        style.configure("TLabelframe.Label", background=labelframe_bg, foreground=fg_color)
        style.configure("TLabelFrame", background=labelframe_bg)
        style.configure("TButton", font=("Segoe UI", 10), background=frame_bg, foreground=fg_color)
        style.configure("TCheckbutton", font=("Segoe UI", 10), background=frame_bg, foreground=fg_color)
        style.configure("TEntry", fieldbackground=entry_bg, background=entry_bg, foreground=fg_color)
        style.configure("TCombobox", fieldbackground=entry_bg, background=entry_bg, foreground=fg_color)
        style.configure("TNotebook", background=labelframe_bg)
        style.configure("TNotebook.Tab", background=frame_bg, foreground=fg_color, padding=[8, 4])

        if self.dark_theme.get():
            style.map("TNotebook.Tab",
                      background=[("selected", labelframe_bg)],
                      foreground=[("selected", fg_color)])
        else:
            style.map("TNotebook.Tab",
                      background=[("selected", "#e8e8e8")],
                      foreground=[("selected", "#000000")])

        # Create notebook (tabs) and frames for each tab
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        self.macro_tab = ttk.Frame(self.notebook)
        self.binds_tab = ttk.Frame(self.notebook)
        self.settings_tab = ttk.Frame(self.notebook)
        self.misc_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.macro_tab, text="MACRO")
        self.notebook.add(self.binds_tab, text="BINDS")
        self.notebook.add(self.settings_tab, text="SETTINGS")
        self.notebook.add(self.misc_tab, text="MISC")

        # ==== MACRO (Clicker) Tab ====
        clicker = ttk.LabelFrame(self.macro_tab, text="Clicker", padding=12)
        clicker.pack(pady=6, fill="x")
        ttk.Label(clicker, text="Left Min CPS:").grid(row=0, column=0, padx=(0, 2), sticky="w")
        ttk.Entry(clicker, textvariable=self.left_min_cps, width=7).grid(row=0, column=1)
        ttk.Label(clicker, text="Left Max CPS:").grid(row=0, column=2, padx=(12, 2), sticky="w")
        ttk.Entry(clicker, textvariable=self.left_max_cps, width=7).grid(row=0, column=3)
        ttk.Label(clicker, text="Mode:").grid(row=0, column=4, padx=(12, 2), sticky="w")
        left_mode_cb = ttk.Combobox(clicker, textvariable=self.left_mode,
                                    values=['Hold', 'Toggle'], width=8, state="readonly")
        left_mode_cb.grid(row=0, column=5)
        ttk.Checkbutton(clicker, text="Randomize", variable=self.left_randomize).grid(row=0, column=6, padx=(10, 0))
        self.left_status = ttk.Label(clicker, text="Inactive", foreground="red", font=("Arial", 10, "bold"))
        self.left_status.grid(row=1, column=0, columnspan=7, pady=(4, 1), sticky="w")
        ttk.Checkbutton(clicker, text="Double-Click (butterfly)", variable=self.left_double_click).grid(
            row=2, column=0, padx=(0, 5), pady=(5, 0))
        ttk.Label(clicker, text="Chance (%):").grid(row=2, column=1, sticky="e")
        ttk.Entry(clicker, textvariable=self.left_double_click_chance, width=6).grid(row=2, column=2)
        ttk.Label(clicker, text="Extra Delay (ms):").grid(row=2, column=3, padx=(10, 2))
        ttk.Entry(clicker, textvariable=self.left_double_click_delay, width=6).grid(row=2, column=4)

        ttk.Label(clicker, text="Right Min CPS:").grid(row=3, column=0, padx=(0, 2), pady=(9, 0))
        ttk.Entry(clicker, textvariable=self.right_min_cps, width=7).grid(row=3, column=1, pady=(8, 0))
        ttk.Label(clicker, text="Right Max CPS:").grid(row=3, column=2, padx=(12, 2), pady=(9, 0))
        ttk.Entry(clicker, textvariable=self.right_max_cps, width=7).grid(row=3, column=3, pady=(8, 0))
        ttk.Label(clicker, text="Mode:").grid(row=3, column=4, padx=(12, 2), pady=(9, 0))
        right_mode_cb = ttk.Combobox(clicker, textvariable=self.right_mode,
                                     values=['Hold', 'Toggle'], width=8, state="readonly")
        right_mode_cb.grid(row=3, column=5, pady=(8, 0))
        ttk.Checkbutton(clicker, text="Randomize", variable=self.right_randomize).grid(
            row=3, column=6, padx=(10, 0), pady=(8, 0))
        self.right_status = ttk.Label(clicker, text="Inactive", foreground="red", font=("Arial", 10, "bold"))
        self.right_status.grid(row=4, column=0, columnspan=7, pady=(1, 4), sticky="w")

        # ==== BINDS Tab ====
        binds = ttk.LabelFrame(self.binds_tab, text="Binds", padding=12)
        binds.pack(pady=6, fill="x")
        ttk.Label(binds, text="Left Click Bind:").grid(row=0, column=0, sticky="w")
        self.left_bind_btn = ttk.Button(binds, textvariable=self.left_bind, width=9,
                                        command=lambda: self.start_listening_bind("left"))
        self.left_bind_btn.grid(row=0, column=1, padx=(0, 18))
        ttk.Label(binds, text="Right Click Bind:").grid(row=0, column=2, sticky="w")
        self.right_bind_btn = ttk.Button(binds, textvariable=self.right_bind, width=9,
                                         command=lambda: self.start_listening_bind("right"))
        self.right_bind_btn.grid(row=0, column=3, padx=(0, 22))
        ttk.Label(binds, text="W-Tap Key:").grid(row=0, column=4)
        self.wtap_bind_btn = ttk.Button(binds, textvariable=self.wtap_key, width=9,
                                        command=lambda: self.start_listening_bind("wtap"))
        self.wtap_bind_btn.grid(row=0, column=5)

        # ==== SETTINGS Tab ====
        wtap = ttk.LabelFrame(self.settings_tab, text="W-Tap (PvP Knockback Reset)", padding=10)
        wtap.pack(pady=(0, 5), fill="x")
        ttk.Checkbutton(wtap, text="Enable W-Tap", variable=self.wtap_enabled).grid(row=0, column=0, sticky="w")
        ttk.Label(wtap, text="Delay after click (ms):").grid(row=1, column=0, sticky="w", padx=(0, 4), pady=(8, 0))
        ttk.Entry(wtap, textvariable=self.wtap_delay, width=8).grid(row=1, column=1, padx=(0, 10), pady=(8, 0))
        ttk.Label(wtap, text="W key release (ms):").grid(row=1, column=2, padx=(12, 4), pady=(8, 0))
        ttk.Entry(wtap, textvariable=self.wtap_release, width=8).grid(row=1, column=3, padx=(0, 4), pady=(8, 0))

        jitter = ttk.LabelFrame(self.settings_tab, text="Jitter Aim", padding=10)
        jitter.pack(pady=(0, 5), fill="x")
        ttk.Checkbutton(jitter, text="Enable Jitter", variable=self.jitter_enabled).grid(row=0, column=0, sticky="w")
        ttk.Label(jitter, text="Range (px):").grid(row=1, column=0, padx=(3, 8), sticky="e", pady=(8, 0))
        ttk.Entry(jitter, textvariable=self.jitter_range, width=8).grid(row=1, column=1, pady=(8, 0))
        ttk.Label(jitter, text="Jitter Frequency (0-1):").grid(row=1, column=2, padx=(16, 8), sticky="e", pady=(8, 0))
        ttk.Entry(jitter, textvariable=self.jitter_frequency, width=8).grid(row=1, column=3, pady=(8, 0))

        extra = ttk.LabelFrame(self.settings_tab, text="Extra Automation", padding=9)
        extra.pack(fill="x")
        ttk.Checkbutton(extra, text="Smooth stop (on release)", variable=self.smooth_stop).grid(
            row=0, column=0, sticky="w")
        ttk.Label(extra, text="Stop time (ms):").grid(row=0, column=1, padx=(6, 2))
        ttk.Entry(extra, textvariable=self.smooth_stop_time, width=8).grid(row=0, column=2, padx=(0, 12))
        ttk.Checkbutton(extra, text="Autostart Clicker (at launch)", variable=self.autostart).grid(
            row=0, column=3, sticky="w")
        ttk.Checkbutton(extra, text="Always on Top", variable=self.always_on_top,
                        command=self.set_always_on_top).grid(row=0, column=4, sticky="w")

        # ==== MISC Tab ====
        misc = ttk.LabelFrame(self.misc_tab, text="Miscellaneous & Info", padding=15)
        misc.pack(pady=7, fill="x")

        ttk.Label(misc, text=(
            "• Change binds, modes and settings freely while running.\n"
            "• Compatible with Minecraft, Roblox, FPS and more (Windows tested).\n"
            "• W-Tap & Jitter are human-like and configurable.\n"
            "• Butterfly/Double-click with adjustable chance for PvP.\n"
            "• All timings in ms or CPS, enter any decimal.\n"
            "• Created by exploitnode | Python {}\n"
            "• Platform: {}\n"
            "• Dark theme enabled by default for better comfort."
        ).format(self.python_version, self.system_platform), justify="left").pack(anchor="w", pady=4)

        ttk.Label(misc, text="For best results: experiment with delays for your setup & ping. Use responsibly!",
                  foreground=secondary_fg).pack(anchor="w", pady=(0, 2))

        # ==== STATUS BAR ====
        self.status_bar = ttk.Label(self.root, text="Ready", relief="sunken", anchor="w", foreground="green")
        try:
            self.status_bar.configure(background=labelframe_bg)
        except Exception:
            pass
        self.status_bar.pack(fill="x", pady=(10, 0), side="bottom")

    def setup_listeners(self):
        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        )
        self.keyboard_listener.start()

    def update_status(self, message, color="black"):
        self.status_bar.config(text=message, foreground=color)
        self.root.after(3250, lambda: self.status_bar.config(text="Ready", foreground="green"))

    def set_always_on_top(self):
        self.root.wm_attributes("-topmost", self.always_on_top.get())

    # dark_theme_notice usunięte – brak przełącznika w UI

    def start_listening_bind(self, bind_type):
        if self.listening_for_bind:
            self.stop_listening_bind()
        self.listening_for_bind = bind_type
        if bind_type == "wtap":
            self.wtap_bind_btn.config(text="Press a key...", state="disabled")
        else:
            getattr(self, f"{bind_type}_bind_btn").config(text="Press a key...", state="disabled")
        self.update_status(f"Listening for {bind_type} bind... Press any key", "blue")
        self.keyboard_listener.stop()
        self.bind_listener = keyboard.Listener(on_press=self.on_bind_key_press)
        self.bind_listener.start()

    def stop_listening_bind(self):
        if not self.listening_for_bind:
            return
        bt = self.listening_for_bind
        if bt == "wtap":
            self.wtap_bind_btn.config(text=self.wtap_key.get(), state="normal")
        else:
            getattr(self, f"{bt}_bind_btn").config(
                text=getattr(self, f"{bt}_bind").get(),
                state="normal"
            )
        self.listening_for_bind = None
        if hasattr(self, 'bind_listener'):
            self.bind_listener.stop()
        self.setup_listeners()

    def on_bind_key_press(self, key):
        if not self.listening_for_bind:
            return
        try:
            if hasattr(key, 'char') and key.char:
                new_bind = key.char
            else:
                new_bind = str(key).split('.')[-1]
                if new_bind.lower().startswith('key.'):
                    new_bind = new_bind[4:]
            if self.listening_for_bind in ("left", "right"):
                other = "right" if self.listening_for_bind == "left" else "left"
                other_bind = getattr(self, f"{other}_bind").get().lower()
                if new_bind.lower() == other_bind:
                    messagebox.showwarning("Warning", f"Key {new_bind} is already used for {other} bind!")
                    self.stop_listening_bind()
                    return
                getattr(self, f"{self.listening_for_bind}_bind").set(new_bind.upper())
                msg = f"{self.listening_for_bind.capitalize()} bind changed to: {new_bind.upper()}"
            else:
                self.wtap_key.set(new_bind.upper())
                msg = f"W-Tap bind changed to: {new_bind.upper()}"
            self.update_status(msg, "green")
        except Exception as e:
            print(f"Error while changing bind: {e}")
            self.update_status("Error while changing bind", "red")
        self.stop_listening_bind()

    def on_key_press(self, key):
        if self.listening_for_bind:
            return
        try:
            if hasattr(key, 'char') and key.char:
                current_key = key.char.lower()
            else:
                current_key = str(key).split('.')[-1].lower()
                if current_key.startswith('key.'):
                    current_key = current_key[4:]
            left_bind_key = self.left_bind.get().lower()
            right_bind_key = self.right_bind.get().lower()

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
            if hasattr(key, 'char') and key.char:
                current_key = key.char.lower()
            else:
                current_key = str(key).split('.')[-1].lower()
                if current_key.startswith('key.'):
                    current_key = current_key[4:]
            left_bind_key = self.left_bind.get().lower()
            right_bind_key = self.right_bind.get().lower()

            if current_key == left_bind_key and self.left_mode.get() == "Hold":
                if self.smooth_stop.get():
                    threading.Thread(target=self.smooth_release, args=('left',), daemon=True).start()
                else:
                    self.left_active = False
                    self.left_status.config(text="Inactive", foreground="red")
            elif current_key == right_bind_key and self.right_mode.get() == "Hold":
                if self.smooth_stop.get():
                    threading.Thread(target=self.smooth_release, args=('right',), daemon=True).start()
                else:
                    self.right_active = False
                    self.right_status.config(text="Inactive", foreground="red")
        except Exception as e:
            print(f"Error in on_key_release: {e}")

    def smooth_release(self, button):
        time.sleep(self.smooth_stop_time.get() / 1000.0)
        if button == 'left':
            self.left_active = False
            self.left_status.config(text="Inactive", foreground="red")
        else:
            self.right_active = False
            self.right_status.config(text="Inactive", foreground="red")

    def do_jitter(self):
        if self.jitter_enabled.get() and random.random() < self.jitter_frequency.get():
            r = self.jitter_range.get()
            x_jitter = random.uniform(-r, r)
            y_jitter = random.uniform(-r, r)
            try:
                cx, cy = self.mouse_controller.position
                self.mouse_controller.position = (cx + x_jitter, cy + y_jitter)
                time.sleep(0.006 + random.uniform(0, 0.009))
                self.mouse_controller.position = (cx, cy)
            except Exception as e:
                print(f"Jitter error: {e}")

    def do_wtap(self):
        if not self.wtap_enabled.get():
            return
        delay = max(0.0, self.wtap_delay.get()) / 1000.0
        release = max(10.0, self.wtap_release.get()) / 1000.0
        key_letter = self.wtap_key.get().lower()
        try:
            time.sleep(delay)
            self.keyboard_controller.release(key_letter)
            time.sleep(release)
            self.keyboard_controller.press(key_letter)
        except Exception as e:
            print(f"W-Tap error: {e}")

    def left_clicker(self):
        while self.left_active:
            try:
                if self.left_randomize.get():
                    min_delay = 1.0 / self.left_max_cps.get()
                    max_delay = 1.0 / self.left_min_cps.get()
                else:
                    min_cps = max(self.left_min_cps.get(), 0.1)
                    max_cps = max(self.left_max_cps.get(), min_cps)
                    min_delay = max_delay = 2.0 / (min_cps + max_cps)
                delay = random.uniform(min_delay, max_delay)
                self.do_jitter()
                self.mouse_controller.click(mouse.Button.left)
                if self.left_double_click.get() and random.random() < (self.left_double_click_chance.get() / 100.0):
                    dclick_delay = max(0.002, self.left_double_click_delay.get() / 1000.0)
                    time.sleep(dclick_delay)
                    self.mouse_controller.click(mouse.Button.left)
                if self.wtap_enabled.get():
                    threading.Thread(target=self.do_wtap, daemon=True).start()
                time.sleep(delay)
            except Exception as e:
                print(f"Error in left_clicker: {e}")
                break

    def right_clicker(self):
        while self.right_active:
            try:
                if self.right_randomize.get():
                    min_delay = 1.0 / self.right_max_cps.get()
                    max_delay = 1.0 / self.right_min_cps.get()
                else:
                    min_cps = max(self.right_min_cps.get(), 0.1)
                    max_cps = max(self.right_max_cps.get(), min_cps)
                    min_delay = max_delay = 2.0 / (min_cps + max_cps)
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

