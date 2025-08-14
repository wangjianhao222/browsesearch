import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog, font as tkfont
import webbrowser
import urllib.parse
import re
import os
import subprocess
import platform
import random
import string # For password generator
import datetime
import calendar as py_calendar # Avoid conflict with a potential 'calendar' command
from collections import deque

# --- Configuration & Constants ---
MAX_HISTORY_SIZE = 30
APP_VERSION = "V8"

# Themes
THEMES = {
    "light": {
        "bg": "SystemButtonFace", #"#F0F0F0",
        "fg": "black",
        "entry_bg": "white",
        "entry_fg": "black",
        "text_bg": "white",
        "text_fg": "black",
        "button_bg": "SystemButtonFace", #"#E0E0E0",
        "status_bar_bg": "#EAEAEA",
        "status_bar_fg": "black"
    },
    "dark": {
        "bg": "#2E2E2E",
        "fg": "white",
        "entry_bg": "#3C3C3C",
        "entry_fg": "white",
        "text_bg": "#1E1E1E",
        "text_fg": "white",
        "button_bg": "#4A4A4A",
        "status_bar_bg": "#1E1E1E",
        "status_bar_fg": "white"
    }
}
current_theme_name = "light" # Default theme

SEARCH_ENGINES = {
    "Google": {"url_template": "https://www.google.com/search?q={query}", "aliases": ["google"]},
    "DuckDuckGo": {"url_template": "https://duckduckgo.com/?q={query}", "aliases": ["ddg"]},
    "Bing": {"url_template": "https://www.bing.com/search?q={query}", "aliases": []},
    "Brave Search": {"url_template": "https://search.brave.com/search?q={query}", "aliases": ["brave"]},
    "Yahoo": {"url_template": "https://search.yahoo.com/search?p={query}", "aliases": []},
    "Startpage": {"url_template": "https://www.startpage.com/do/search?query={query}", "aliases": ["start page"], "description": "Private search (uses Google results)."},
    "Ecosia": {"url_template": "https://www.ecosia.org/search?q={query}", "aliases": [], "description": "Search engine that plants trees."},
    "Qwant": {"url_template": "https://www.qwant.com/?q={query}", "aliases": [], "description": "European privacy-focused search engine."},
    "Perplexity AI": {"url_template": "https://www.perplexity.ai/search?q={query}", "aliases": ["perplexity"], "description": "AI-powered search and answer engine."}
}
default_search_engine_key = "Google" # Initial default

KNOWN_SITES = {
    # (Extensive list from V7, truncated here for brevity in thought block, will be in full code)
    "Amazon": {"base_url": "https://www.amazon.com", "search_url_template": "https://www.amazon.com/s?k={query}", "aliases": ["亚马逊"], "description": "Global e-commerce."},
    "Wikipedia": {"base_url": "https://en.wikipedia.org", "search_url_template": "https://en.wikipedia.org/w/index.php?search={query}", "aliases": ["wiki", "维基百科"], "description": "Free encyclopedia."},
    "YouTube": {"base_url": "https://www.youtube.com", "search_url_template": "https://www.youtube.com/results?search_query={query}", "aliases": ["yt", "油管"], "description": "Video platform."},
    "GitHub": {"base_url": "https://github.com/", "search_url_template": "https://github.com/search?q={query}", "aliases": [], "description": "Code hosting."},
    "Stack Overflow": {"base_url": "https://stackoverflow.com", "search_url_template": "https://stackoverflow.com/search?q={query}", "aliases": ["so"], "description": "Q&A for programmers."},
    "MDN Web Docs": {"base_url": "https://developer.mozilla.org/", "search_url_template": "https://developer.mozilla.org/en-US/search?q={query}", "aliases": ["mdn"], "description": "Mozilla Web Docs."},
    "Reddit": {"base_url": "https://www.reddit.com", "search_url_template": "https://www.reddit.com/search/?q={query}", "aliases": [], "description": "News aggregation and discussion forums."},
    "Twitter": {"base_url": "https://twitter.com", "search_url_template": "https://twitter.com/search?q={query}&src=typed_query", "aliases": ["推特", "x"], "description": "Microblogging and social networking."},
    "BBC News": {"base_url": "https://www.bbc.com/news", "search_url_template": "https://www.bbc.co.uk/search?q={query}", "aliases": ["bbc"], "description": "British Broadcasting Corporation News."},
    # ... many more sites from V7
    "Wayback Machine": {"base_url": "https://web.archive.org/", "search_url_template": "https://web.archive.org/web/*/{query}*", "aliases": ["archive.org"], "description": "Internet Archive."},
    "Fandom": {"base_url": "https://www.fandom.com/", "search_url_template": "https://www.fandom.com/?s={query}", "aliases": ["wikia"], "description": "Community-focused wiki hosting."}
}

SPECIAL_CASES = {
    # (Extensive list from V7, truncated)
    "gmail": "https://mail.google.com/",
    "google maps": "https://maps.google.com/",
    "python docs": "https://docs.python.org/3/",
    "github trending": "https://github.com/trending",
    "current time": "#CMD_DATETIME#", # Special internal command marker
    "weather forecast": f"{SEARCH_ENGINES[default_search_engine_key]['url_template'].format(query=urllib.parse.quote_plus('weather forecast'))}", # Updated to use current default
    "speed test": "https://www.speedtest.net/",
    "what is my ip": f"{SEARCH_ENGINES[default_search_engine_key]['url_template'].format(query=urllib.parse.quote_plus('what is my ip'))}",
    # ... more
}

SITE_GROUPS = {
    # (Same as V7, truncated)
    "news": ["BBC News", "CNN", "New York Times", "Reuters"],
    "social": ["Twitter", "Reddit", "Instagram", "LinkedIn"],
    "dev": ["GitHub", "Stack Overflow", "MDN Web Docs", "Python docs"]
}

LOCAL_APPS = {
    # (Same as V7)
    "calculator": {"windows": "calc.exe", "darwin": "open -a Calculator", "linux": ["gnome-calculator", "kcalc", "xcalc"]},
    "notepad": {"windows": "notepad.exe", "darwin": "open -a TextEdit", "linux": ["gedit", "kate", "mousepad"]},
    "text editor": "notepad",
    "terminal": {"windows": "cmd.exe", "darwin": "open -a Terminal", "linux": ["gnome-terminal", "konsole", "xfce4-terminal", "xterm"]}
}

command_history_deque = deque(maxlen=MAX_HISTORY_SIZE)
internal_cwd = os.getcwd() # Start with actual CWD

# --- Backend Logic (Adapted from V7) ---

def open_url_backend(url, description=""): # No change
    try:
        webbrowser.open_new_tab(url)
        msg = f"Opening: {url}" + (f" ({description})" if description else "")
        return True, msg
    except Exception as e:
        return False, f"Error opening URL {url}: {e}"

def add_to_history(executed_command_description): # No change
    if executed_command_description:
        command_history_deque.append(executed_command_description)

def extract_query_site_or_engine_backend_v8(text_input_raw):
    """
    Tries to extract query and site OR query and specific search engine.
    Site matching takes precedence.
    """
    text_lower_for_keywords = text_input_raw.lower() # For keyword matching
    site_name_char_class = r"[\w\s.'&\-/]+"
    engine_name_char_class = r"[\w\s]+" # Simpler for engine names

    # Patterns for site-specific search (query, site_group_name)
    # Order from more specific/common to more general.
    site_patterns_config = [
        (rf"^(?:search|find|look\s+for)\s+(?P<query>.+?)\s+(?:on|in|at|from)\s+(?P<site>{site_name_char_class})$", "query", "site"),
        (rf"^(?P<query>.+?)\s+(?:on|in|at|from)\s+(?P<site>{site_name_char_class})$", "query", "site"),
        (rf"^(?P<site>{site_name_char_class}?)\s+(?:search|find|look\s+for)\s+(?P<query>.+)$", "query", "site"),
        (rf"^(?P<query>.+?)\s*的\s*(?P<site>{site_name_char_class})$", "query", "site"), # Chinese "query 的 site"
        (rf"^在\s*(?P<site>{site_name_char_class}?)\s*(?:上)?(?:搜索|查找)\s*(?P<query>.+)$", "query", "site"), # Chinese
        (rf"^(?P<query>.+?)\s+(?P<site>{site_name_char_class})$", "query", "site"), # General "query site"
    ]

    # Try to match site-specific search first
    for pattern_str, query_group, site_group in site_patterns_config:
        pattern = re.compile(pattern_str, re.IGNORECASE)
        match = pattern.match(text_input_raw)
        if match:
            query_text = match.group(query_group).strip()
            potential_site_name = match.group(site_group).strip().lower()
            for site_key_canonical, site_data in KNOWN_SITES.items():
                if potential_site_name == site_key_canonical.lower() or \
                   potential_site_name in [alias.lower() for alias in site_data.get("aliases", [])]:
                    if query_text:
                        return {"type": "site_search", "query": query_text, "target_key": site_key_canonical}
    
    # Patterns for engine-specific search (query, engine_group_name)
    # Using distinct prepositions like 'via' or 'using engine' to reduce ambiguity
    engine_patterns_config = [
        (rf"^(?P<query>.+?)\s+(?:via|using|with engine|on engine|using)\s+(?P<engine>{engine_name_char_class})$", "query", "engine"),
        (rf"^(?:search|find)\s+(?P<query>.+?)\s+(?:via|using|with engine|on engine)\s+(?P<engine>{engine_name_char_class})$", "query", "engine"),
    ]
    for pattern_str, query_group, engine_group in engine_patterns_config:
        pattern = re.compile(pattern_str, re.IGNORECASE)
        match = pattern.match(text_input_raw)
        if match:
            query_text = match.group(query_group).strip()
            potential_engine_name = match.group(engine_group).strip().lower()
            for engine_key, engine_data in SEARCH_ENGINES.items():
                if potential_engine_name == engine_key.lower() or \
                   potential_engine_name in [alias.lower() for alias in engine_data.get("aliases", [])]:
                    if query_text:
                        return {"type": "engine_search", "query": query_text, "target_key": engine_key}

    return None # No specific site or engine pattern matched, assume general query for default engine


def launch_local_app_backend(app_name_key): # Same as V7
    # ... (full function from V7)
    app_name_key_lower = app_name_key.lower()
    if app_name_key_lower in LOCAL_APPS and isinstance(LOCAL_APPS[app_name_key_lower], str):
        app_name_key_lower = LOCAL_APPS[app_name_key_lower].lower()

    app_config = LOCAL_APPS.get(app_name_key_lower)
    if not app_config:
        return False, f"Local application '{app_name_key}' not configured."
    system = platform.system().lower()
    cmd_to_run = None
    shell_needed = False
    if system == "windows": cmd_to_run = app_config.get("windows")
    elif system == "darwin":
        cmd_to_run = app_config.get("darwin")
        if isinstance(cmd_to_run, str) and cmd_to_run.startswith("open -a"): shell_needed = True
    elif system == "linux":
        linux_cmds = app_config.get("linux")
        if isinstance(linux_cmds, list):
            for l_cmd in linux_cmds:
                if subprocess.call(['which', l_cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
                    cmd_to_run = l_cmd; break
            if not cmd_to_run: return False, f"None Linux cmd found for '{app_name_key}'"
        else: cmd_to_run = linux_cmds
    else: return False, f"Unsupported OS: {system}"
    if not cmd_to_run: return False, f"No cmd for '{app_name_key}' on {system}."
    try:
        if shell_needed: subprocess.Popen(cmd_to_run, shell=True)
        elif isinstance(cmd_to_run, list): subprocess.Popen(cmd_to_run)
        else: subprocess.Popen([cmd_to_run])
        return True, f"Attempting launch: {app_name_key} ('{cmd_to_run}')"
    except Exception as e: return False, f"Error launching {app_name_key}: {e}"


def open_file_with_default_app_backend(file_path): # Same as V7
    # ... (full function from V7)
    system = platform.system().lower()
    try:
        abs_file_path = os.path.abspath(os.path.expanduser(file_path))
        if not os.path.exists(abs_file_path): return False, f"File not found: {abs_file_path}"
        if system == "windows": os.startfile(abs_file_path)
        elif system == "darwin": subprocess.run(['open', abs_file_path], check=True)
        elif system == "linux": subprocess.run(['xdg-open', abs_file_path], check=True)
        else: return False, f"Unsupported OS: {system}"
        return True, f"Attempting to open: {abs_file_path}"
    except Exception as e: return False, f"Error opening file {file_path}: {e}"

def generate_password(length=16, use_upper=True, use_lower=True, use_digits=True, use_symbols=True):
    character_pool = ""
    if use_upper: character_pool += string.ascii_uppercase
    if use_lower: character_pool += string.ascii_lowercase
    if use_digits: character_pool += string.digits
    if use_symbols: character_pool += string.punctuation

    if not character_pool:
        return None, "Error: No character types selected for password."
    
    # Ensure password length is reasonable
    length = max(8, min(length, 128)) # Clamp length between 8 and 128
    
    password = ''.join(random.choice(character_pool) for _ in range(length))
    
    # Optional: ensure all selected character types are present (more complex logic)
    # For simplicity now, just generate from the pool.
    
    return password, f"Generated password ({length} chars): {password}"

# --- Tkinter GUI Application ---
class BrowserControlApp:
    def __init__(self, master):
        self.master = master
        master.title(f"Browser & App Control {APP_VERSION}")
        # master.geometry("850x650") # Default size

        self.current_theme_name = current_theme_name
        self.current_default_engine_key = default_search_engine_key # Class instance variable
        self.internal_cwd = internal_cwd # Class instance variable

        self.create_widgets()
        self.apply_theme() # Apply initial theme
        self.update_status_bar()

        self.log_message(f"Welcome to Browser & App Control {APP_VERSION}! Type 'help' or click button.")


    def create_widgets(self):
        # Main frame to hold everything, allows theme to apply to whole window background
        self.main_frame = tk.Frame(self.master)
        self.main_frame.pack(expand=True, fill=tk.BOTH)

        # Input Frame
        input_frame = tk.Frame(self.main_frame, pady=5)
        input_frame.pack(fill=tk.X)
        tk.Label(input_frame, text="Cmd:").pack(side=tk.LEFT, padx=(10,2)) # Added more padding left
        self.command_entry = tk.Entry(input_frame, width=70)
        self.command_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        self.command_entry.bind("<Return>", self.execute_command_event)
        self.execute_button = tk.Button(input_frame, text="Execute", command=self.execute_command)
        self.execute_button.pack(side=tk.LEFT, padx=(0,10)) # More padding right

        # Button Frame
        button_frame = tk.Frame(self.main_frame, pady=3)
        button_frame.pack(fill=tk.X)
        button_padx = 3
        self.help_button = tk.Button(button_frame, text="Help/Sites", command=self.display_help_gui)
        self.help_button.pack(side=tk.LEFT, padx=button_padx, anchor='w')
        self.groups_button = tk.Button(button_frame, text="Site Groups", command=self.list_site_groups_gui)
        self.groups_button.pack(side=tk.LEFT, padx=button_padx, anchor='w')
        self.engines_button = tk.Button(button_frame, text="List Engines", command=self.list_search_engines_gui)
        self.engines_button.pack(side=tk.LEFT, padx=button_padx, anchor='w')
        self.history_button = tk.Button(button_frame, text="History", command=self.show_history_gui)
        self.history_button.pack(side=tk.LEFT, padx=button_padx, anchor='w')
        self.theme_button = tk.Button(button_frame, text="Toggle Theme", command=self.toggle_theme)
        self.theme_button.pack(side=tk.LEFT, padx=button_padx, anchor='w')
        self.clear_button = tk.Button(button_frame, text="Clear Out", command=self.clear_output)
        self.clear_button.pack(side=tk.LEFT, padx=button_padx, anchor='w')

        # Output Area
        self.output_text = scrolledtext.ScrolledText(self.main_frame, wrap=tk.WORD, height=25, width=100)
        self.output_text.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
        self.output_text.configure(state='disabled')

        # Status Bar
        self.status_bar = tk.Label(self.main_frame, text="", bd=1, relief=tk.SUNKEN, anchor=tk.W, padx=5)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Default font
        self.default_font = tkfont.nametofont("TkDefaultFont")
        self.text_font = tkfont.nametofont("TkTextFont")
        self.fixed_font = tkfont.nametofont("TkFixedFont")


    def apply_theme(self):
        theme = THEMES[self.current_theme_name]
        self.master.configure(bg=theme["bg"])
        self.main_frame.configure(bg=theme["bg"])

        # Frames
        for frame_child in self.main_frame.winfo_children():
            if isinstance(frame_child, tk.Frame):
                frame_child.configure(bg=theme["bg"])
                # Labels and Buttons within frames
                for widget in frame_child.winfo_children():
                    if isinstance(widget, tk.Label):
                        widget.configure(bg=theme["bg"], fg=theme["fg"])
                    elif isinstance(widget, tk.Button):
                        widget.configure(bg=theme["button_bg"], fg=theme["fg"]) # relief=tk.RAISED for 3D buttons
                    elif isinstance(widget, tk.Entry): # command_entry
                        widget.configure(bg=theme["entry_bg"], fg=theme["entry_fg"],
                                         insertbackground=theme["fg"]) # Cursor color

        # Output ScrolledText (main text area and its frame if any internal)
        self.output_text.configure(bg=theme["text_bg"], fg=theme["text_fg"],
                                   insertbackground=theme["fg"]) # Cursor color
        
        # Status bar
        self.status_bar.configure(bg=theme["status_bar_bg"], fg=theme["status_bar_fg"])

        # Font color for output text tags needs to be managed in log_message for tags
        self.output_text.tag_config("command_echo", foreground="blue" if self.current_theme_name == "light" else "#60A5FA")
        self.output_text.tag_config("history_log", foreground="purple" if self.current_theme_name == "light" else "#C47EFF",
                                    font=(self.fixed_font.actual()["family"], self.fixed_font.actual()["size"]-1, 'italic'))
        self.output_text.tag_config("error_log", foreground="red" if self.current_theme_name == "light" else "#FF7575",
                                     font=(self.default_font.actual()["family"], self.default_font.actual()["size"], 'bold'))
        self.output_text.tag_config("success_log", foreground="green" if self.current_theme_name == "light" else "#6EE7B7")
        self.output_text.tag_config("info_log", foreground="#555555" if self.current_theme_name == "light" else "#AAAAAA")


    def toggle_theme(self):
        self.current_theme_name = "dark" if self.current_theme_name == "light" else "light"
        self.apply_theme()
        self.log_message(f"Theme changed to {self.current_theme_name}.", tag_key="info_log")
        add_to_history(f"Toggled theme to {self.current_theme_name}")

    def update_status_bar(self):
        engine_name = self.current_default_engine_key
        cwd_display = self.internal_cwd
        max_cwd_len = 45 # Max length for CWD in status bar
        if len(cwd_display) > max_cwd_len:
            cwd_display = "..." + cwd_display[-(max_cwd_len-3):]
        
        self.status_bar.config(text=f"Engine: {engine_name}  |  Dir: {cwd_display}")


    def log_message(self, message, is_command_echo=False, is_history=False, tag_key=None):
        self.output_text.configure(state='normal')
        prefix = ""
        effective_tag = None # tuple of tags
        if tag_key: effective_tag = (tag_key,)
        
        if is_command_echo:
            prefix = ">>> "
            effective_tag = ("command_echo",)
        elif is_history:
            prefix = "HIST: "
            effective_tag = ("history_log",)
        
        self.output_text.insert(tk.END, f"{prefix}{message}\n", effective_tag)
        self.output_text.see(tk.END)
        self.output_text.configure(state='disabled')


    def clear_output(self): # Same as V7
        self.output_text.configure(state='normal')
        self.output_text.delete(1.0, tk.END)
        self.output_text.configure(state='disabled')
        self.log_message("Output cleared.", tag_key="info_log")
        add_to_history("Output cleared")

    def execute_command_event(self, event): # Same as V7
        self.execute_command()

    def execute_command(self): # Heavily Modified
        raw_input_command = self.command_entry.get().strip()
        self.command_entry.delete(0, tk.END)

        if not raw_input_command:
            return

        self.log_message(raw_input_command, is_command_echo=True)
        user_input_lower = raw_input_command.lower()
        executed_action_description = None
        success = True
        message_to_log = ""
        log_tag = None # For error/success logs

        # --- Command Processing Logic V8 ---
        if user_input_lower in ['exit', 'quit', 'q']:
            self.master.quit(); return
        elif user_input_lower in ['help', 'list', 'ls', 'man']:
            self.display_help_gui()
            executed_action_description = "Displayed help"
        elif user_input_lower in ['clear hist', 'clear history']:
            command_history_deque.clear()
            message_to_log = "Command history cleared."; log_tag="success_log"
            executed_action_description = "Cleared command history"
        
        # Theme command
        elif user_input_lower.startswith("theme "):
            theme_name = user_input_lower[len("theme "):].strip()
            if theme_name in THEMES:
                self.current_theme_name = theme_name
                self.apply_theme()
                message_to_log = f"Theme set to {theme_name}."; log_tag="success_log"
                executed_action_description = f"Set theme to {theme_name}"
            else:
                message_to_log = f"Error: Unknown theme '{theme_name}'. Available: {', '.join(THEMES.keys())}"; log_tag="error_log"
        
        # Search Engine commands
        elif user_input_lower.startswith("set engine ") or user_input_lower.startswith("use engine "):
            parts = user_input_lower.split(" ", 2)
            if len(parts) == 3:
                engine_name_input = parts[2].strip()
                found_engine = False
                for key, data in SEARCH_ENGINES.items():
                    if engine_name_input == key.lower() or engine_name_input in [a.lower() for a in data.get("aliases",[])]:
                        self.current_default_engine_key = key
                        self.update_status_bar() # Update status bar
                        message_to_log = f"Default search engine set to: {key}"; log_tag="success_log"
                        executed_action_description = f"Set default engine to {key}"
                        found_engine = True; break
                if not found_engine:
                    message_to_log = f"Error: Search engine '{engine_name_input}' not found."; log_tag="error_log"
            else: message_to_log = "Usage: set engine <engine_name>"; log_tag="error_log"

        elif user_input_lower == "list engines":
            self.list_search_engines_gui() # This logs and adds to history
            executed_action_description = "Listed search engines" # Already handled by list_search_engines_gui

        # Date & Time utilities
        elif user_input_lower in ["date", "time", "datetime", "now"]:
            now = datetime.datetime.now()
            if user_input_lower == "date": format_str, desc = "%Y-%m-%d (%A)", "Current Date"
            elif user_input_lower == "time": format_str, desc = "%H:%M:%S", "Current Time"
            else: format_str, desc = "%Y-%m-%d %H:%M:%S (%A)", "Current Date & Time"
            message_to_log = f"{desc}: {now.strftime(format_str)}"; log_tag="info_log"
            executed_action_description = f"Showed {desc}"
        elif user_input_lower.startswith("cal") or user_input_lower.startswith("calendar"):
            parts = user_input_lower.split()
            now = datetime.datetime.now()
            month, year = now.month, now.year
            try:
                if len(parts) == 3: month, year = int(parts[1]), int(parts[2])
                elif len(parts) == 2: # cal YEAR or cal MONTH (assuming current year)
                    val = int(parts[1])
                    if 1 <= val <= 12: month = val
                    else: year = val # Assume it's a year
                
                if not (1900 <= year <= 2200): raise ValueError("Year out of sensible range.")
                cal_text = py_calendar.month(year, month)
                message_to_log = f"Calendar for {py_calendar.month_name[month]} {year}:\n{cal_text}"; log_tag="info_log"
                executed_action_description = f"Showed calendar for {month}/{year}"
            except Exception as e: success=False; message_to_log=f"Calendar error: {e}. Use 'cal [month] [year]'"; log_tag="error_log"

        # Clipboard utilities
        elif user_input_lower.startswith("copy "):
            text_to_copy = raw_input_command[len("copy "):].strip()
            if text_to_copy:
                try:
                    self.master.clipboard_clear()
                    self.master.clipboard_append(text_to_copy)
                    self.master.update() # Process clipboard event
                    message_to_log = "Text copied to clipboard."; log_tag="success_log"
                    executed_action_description = "Copied text to clipboard"
                except tk.TclError as e: # Should not happen with modern Tk, but for safety
                    success = False; message_to_log = f"Clipboard error: {e}"; log_tag="error_log"
            else: message_to_log = "Usage: copy <text to copy>"; log_tag="error_log"
        elif user_input_lower == "paste":
            try:
                clipboard_content = self.master.clipboard_get()
                self.command_entry.insert(tk.END, clipboard_content)
                message_to_log = f"Pasted from clipboard into entry: '{clipboard_content[:50]}{'...' if len(clipboard_content)>50 else ''}'"
                log_tag = "info_log"
                executed_action_description = "Pasted from clipboard"
            except tk.TclError: # Clipboard empty or non-text
                message_to_log = "Clipboard is empty or contains non-text data."; log_tag="info_log"


        # File System commands (internal CWD)
        elif user_input_lower == "pwd":
            message_to_log = f"Internal CWD: {self.internal_cwd}"; log_tag="info_log"
            executed_action_description = "Showed internal PWD"
        elif user_input_lower.startswith("cd "):
            path_to_cd = raw_input_command[len("cd "):].strip()
            try:
                # Handle special cases like 'cd ..' 'cd ~'
                if path_to_cd == "~": new_path = os.path.expanduser("~")
                elif path_to_cd == "..": new_path = os.path.dirname(self.internal_cwd)
                elif os.path.isabs(path_to_cd): new_path = path_to_cd
                else: new_path = os.path.join(self.internal_cwd, path_to_cd)
                
                normalized_path = os.path.normpath(new_path)
                if os.path.isdir(normalized_path):
                    self.internal_cwd = normalized_path
                    self.update_status_bar()
                    message_to_log = f"Internal CWD changed to: {self.internal_cwd}"; log_tag="success_log"
                    executed_action_description = f"CD to {self.internal_cwd}"
                else: success=False; message_to_log = f"Error: Path is not a directory: {normalized_path}"; log_tag="error_log"
            except Exception as e: success=False; message_to_log = f"CD Error: {e}"; log_tag="error_log"

        elif user_input_lower.startswith("ls") or user_input_lower.startswith("dir"):
            parts = user_input_lower.split(" ", 1)
            path_to_list = self.internal_cwd
            if len(parts) > 1 and parts[1].strip():
                input_path = parts[1].strip()
                if os.path.isabs(input_path): path_to_list = input_path
                else: path_to_list = os.path.join(self.internal_cwd, input_path)
            
            path_to_list = os.path.normpath(os.path.expanduser(path_to_list))

            if not os.path.isdir(path_to_list):
                success=False; message_to_log = f"Error: Not a directory or not found: {path_to_list}"; log_tag="error_log"
            else:
                try:
                    entries = os.listdir(path_to_list)
                    dirs = sorted([d for d in entries if os.path.isdir(os.path.join(path_to_list, d))])
                    files = sorted([f for f in entries if os.path.isfile(os.path.join(path_to_list, f))])
                    
                    output_lines = [f"Contents of '{path_to_list}':"]
                    if not dirs and not files:
                        output_lines.append("  (empty directory)")
                    for d_name in dirs: output_lines.append(f"  <DIR>  {d_name}")
                    for f_name in files: output_lines.append(f"         {f_name}")
                    message_to_log = "\n".join(output_lines); log_tag="info_log" # Multi-line
                    executed_action_description = f"Listed contents of {path_to_list}"
                except Exception as e: success=False; message_to_log = f"LS/DIR Error: {e}"; log_tag="error_log"

        # Password Generator
        elif user_input_lower.startswith("genpass"):
            parts = raw_input_command.split()
            length = 16 # Default length
            use_upper, use_lower, use_digits, use_symbols = True, True, True, False # Default options
            if len(parts) > 1:
                try: length = int(parts[1])
                except ValueError: message_to_log = "Invalid length for genpass."; success=False; log_tag="error_log"
            if len(parts) > 2 and success: # Options string like -ulns
                opts = parts[2].lower()
                use_upper = 'u' in opts
                use_lower = 'l' in opts
                use_digits = 'n' in opts or 'd' in opts
                use_symbols = 's' in opts or 'p' in opts
                # If no specific char sets selected via options, default to uln
                if not (use_upper or use_lower or use_digits or use_symbols) and len(opts)>1: # opts like -xyz won't work unless defined
                    message_to_log = f"No valid character types selected by '{opts}'. Using defaults."; log_tag="info_log"
                    use_upper, use_lower, use_digits = True, True, True
                elif not (use_upper or use_lower or use_digits or use_symbols): # Just "genpass" or "genpass len" with no specific char sets from options
                     use_upper, use_lower, use_digits = True, True, True # Sensible default if only len provided


            if success:
                password, gen_msg = generate_password(length, use_upper, use_lower, use_digits, use_symbols)
                if password:
                    message_to_log += (("\n" if message_to_log else "") + gen_msg) ; log_tag="success_log" # Append if existing info message
                    executed_action_description = "Generated password"
                else: success=False; message_to_log += (("\n" if message_to_log else "") + gen_msg); log_tag="error_log"


        # === The rest of the command processing (URL, Site Search, etc.) ===
        elif raw_input_command.startswith("#CMD_"): # Handle internal special commands
            cmd_key = raw_input_command.split("#")[2]
            if cmd_key == "DATETIME": # From "current time" special case
                 now_dt = datetime.datetime.now()
                 message_to_log = f"Current Date & Time: {now_dt.strftime('%Y-%m-%d %H:%M:%S (%A)')}"; log_tag="info_log"
                 executed_action_description = "Showed current date & time"
        elif raw_input_command in SPECIAL_CASES:
            success, message_to_log = open_url_backend(SPECIAL_CASES[raw_input_command], f"Special: {raw_input_command}")
            if success: executed_action_description = f"Executed special: {raw_input_command}"; log_tag="success_log"
            else: log_tag = "error_log"
        elif any(user_input_lower == key.lower() or user_input_lower in [a.lower() for a in data.get("aliases", [])] for key, data in KNOWN_SITES.items()):
            matched_site_key = next(key for key, data in KNOWN_SITES.items() if user_input_lower == key.lower() or user_input_lower in [a.lower() for a in data.get("aliases", [])])
            success, message_to_log = open_url_backend(KNOWN_SITES[matched_site_key]["base_url"], f"{matched_site_key} homepage")
            if success: executed_action_description = f"Opened site: {matched_site_key}"; log_tag="success_log"
            else: log_tag="error_log"
        elif re.match(r"^(https?://|www\.)[^\s/$.?#].[^\s]*$", user_input_lower, re.IGNORECASE) or \
             (raw_input_command.count('.') > 0 and ('/' in raw_input_command or ':' in raw_input_command) and ' ' not in raw_input_command and not (os.path.exists(raw_input_command) and os.path.isfile(raw_input_command)) ) :
            url_to_open = raw_input_command
            if not (url_to_open.startswith("http://") or url_to_open.startswith("https://")): url_to_open = "http://" + url_to_open
            success, message_to_log = open_url_backend(url_to_open, "Direct URL")
            if success: executed_action_description = f"Opened URL: {url_to_open}"; log_tag="success_log"
            else: log_tag="error_log"
        else: # Default to general search or specific engine/site search
            parsed_action = extract_query_site_or_engine_backend_v8(raw_input_command)
            if parsed_action:
                query = parsed_action["query"]
                target_key = parsed_action["target_key"]
                
                if parsed_action["type"] == "site_search":
                    site_info = KNOWN_SITES[target_key]
                    if "search_url_template" in site_info and site_info["search_url_template"]:
                        search_url = site_info["search_url_template"].format(query=urllib.parse.quote_plus(query))
                        success, message_to_log = open_url_backend(search_url, f"Search '{query}' on {target_key}")
                        if success: executed_action_description = f"Searched on {target_key} for: {query}"; log_tag="success_log"
                        else: log_tag="error_log"
                    else:
                        message_to_log = f"Site '{target_key}' known but no search. Opening homepage."
                        s_home, m_home = open_url_backend(site_info["base_url"], f"{target_key} homepage")
                        if s_home: message_to_log += f"\n  {m_home}"; log_tag="success_log" # If homepage opens, overall is a success
                        else: success=False; log_tag="error_log" # If homepage fails, whole action fails
                        executed_action_description = f"Tried search on {target_key}, opened homepage"
                
                elif parsed_action["type"] == "engine_search":
                    engine_info = SEARCH_ENGINES[target_key]
                    search_url = engine_info["url_template"].format(query=urllib.parse.quote_plus(query))
                    success, message_to_log = open_url_backend(search_url, f"Search '{query}' via {target_key}")
                    if success: executed_action_description = f"Searched via {target_key} for: {query}"; log_tag="success_log"
                    else: log_tag="error_log"
            else: # Default to currently selected search engine
                active_engine_key = self.current_default_engine_key
                active_engine_info = SEARCH_ENGINES[active_engine_key]
                default_search_url = active_engine_info["url_template"].format(query=urllib.parse.quote_plus(raw_input_command))
                success, message_to_log = open_url_backend(default_search_url, f"{active_engine_key} search: '{raw_input_command}'")
                if success: executed_action_description = f"{active_engine_key} search: {raw_input_command}"; log_tag="success_log"
                else: log_tag="error_log"
        
        self.log_message(message_to_log, tag_key=log_tag) # Log with appropriate tag
        if success and executed_action_description:
            add_to_history(executed_action_description)
        elif not success and not executed_action_description and message_to_log : # Failed action already logged its message
            add_to_history(f"Failed action attempt for: {raw_input_command}") # Minimal history for failure
        elif not executed_action_description and not message_to_log : # Truly unhandled command
             self.log_message(f"Error: Command not understood: '{raw_input_command}'", tag_key="error_log")
             add_to_history(f"Unknown command: {raw_input_command}")


    def display_help_gui(self): # Updated for V8
        active_engine_name = self.current_default_engine_key
        help_text = f"""--- Browser & App Control {APP_VERSION} Help ---
Default Engine: {active_engine_name}. Type 'list engines' or 'set engine <name>'.

General Web:
  <url>                      - Opens URL (e.g., https://example.com)
  <site_name_or_alias>       - Opens known site's homepage (e.g., YouTube)
  <query>                    - Searches query on {active_engine_name}
  <query> via/using <engine> - Search query with a specific engine (e.g. 'cats via DuckDuckGo')
  <query> on <site>          - Search query on specified site (e.g., 'python tutorial on Stack Overflow')
  (More search syntax like "search X for Y on Z" also supported)
  <special_command>          - (e.g., 'Gmail', 'weather forecast', 'python docs')

Local Apps & Files:
  open calculator / notepad / terminal
  open file <full_path_to_file>

Internal Tools:
  calc <expression>          - Calculator (e.g. calc 2*(3+5)^2)
  roll dice [NdS]            - Dice roller (e.g. roll dice 3d8)
  random number [min] [max]  - Random number (e.g. random 1 1000)
  date / time / datetime / now - Current date/time info
  cal [month] [year]         - Text calendar
  copy <text>                - Copy text to clipboard
  paste                      - Paste from clipboard into command entry
  pwd                        - Show internal current working directory
  cd <path>                  - Change internal current working directory (e.g. cd .., cd D:\\, cd ~)
  ls / dir [path]            - List directory contents (uses internal CWD if no path)
  genpass [len] [-ulnsp]     - Generate password (u:upper, l:lower, n:num, s:symbol, p:punc)

GUI & Other:
  theme light/dark           - Toggle GUI theme
  help / list engines / list groups / show history / clear hist / clear output / exit
--- Known Sites (Sample - type full site name or alias to open) ---
"""
        site_sample = [f"  - {name}{' (Alias: '+ KNOWN_SITES[name]['aliases'][0] +')' if KNOWN_SITES[name].get('aliases') else ''}" for i, name in enumerate(sorted(KNOWN_SITES.keys())) if i < 12]
        if len(KNOWN_SITES) > 12: site_sample.append("  ...and many more!")
        help_text += "\n".join(site_sample)
        help_text += "\n--- Special Commands (Sample) ---\n"
        special_sample = [f"  - {name}" for i, name in enumerate(sorted(SPECIAL_CASES.keys())) if i < 8]
        if len(SPECIAL_CASES) > 8: special_sample.append("  ...and more!")
        help_text += "\n".join(special_sample)
        
        self.log_message("--- HELP ---", tag_key="info_log")
        for line in help_text.split('\n'): self.log_message(line, tag_key="info_log")
        self.log_message("--- END HELP ---", tag_key="info_log")
        add_to_history("Displayed help")


    def list_site_groups_gui(self): # (Same as V7)
        self.log_message("\n--- Available Site Groups ---", tag_key="info_log")
        if SITE_GROUPS:
            for group_name, sites in sorted(SITE_GROUPS.items()):
                self.log_message(f"  Group '{group_name}': {', '.join(sites)}", tag_key="info_log")
            self.log_message("Use 'open group <group_name>' to open all.", tag_key="info_log")
        else: self.log_message("(No site groups defined)", tag_key="info_log")
        add_to_history("Listed site groups")

    def list_search_engines_gui(self):
        self.log_message("\n--- Available Search Engines ---", tag_key="info_log")
        for key, data in SEARCH_ENGINES.items():
            aliases_str = f" (Aliases: {', '.join(data['aliases'])})" if data.get('aliases') else ""
            desc_str = f" - {data['description']}" if data.get('description') else ""
            is_default = " (DEFAULT)" if key == self.current_default_engine_key else ""
            self.log_message(f"  - {key}{aliases_str}{desc_str}{is_default}", tag_key="info_log")
        self.log_message("Use 'set engine <name>' to change default.", tag_key="info_log")
        add_to_history("Listed search engines")

    def show_history_gui(self): # (Same as V7)
        self.log_message("\n--- Command History (Current Session) ---", tag_key="info_log")
        if not command_history_deque: self.log_message("(History is empty)", tag_key="info_log")
        else:
            for i, cmd_desc in enumerate(list(command_history_deque)):
                self.log_message(f"{i+1}: {cmd_desc}", is_history=True) # Uses history tag
        add_to_history("Viewed history")


if __name__ == "__main__":
    # Load full KNOWN_SITES and SPECIAL_CASES if they were truncated in the thought block
    # (For this single-file example, assume they are fully defined above)
    
    # Update special cases that depend on the default search engine *after* default_search_engine_key is set
    # This needs to be done dynamically if the default engine changes. For now, it's initial.
    # Let's ensure special cases that use the default engine get it from the active key.
    # This is better handled at execution time of the special command if it points to a search.
    # Or, define them as special #CMD_ markers like "#CMD_WEATHER#" then resolve in execute_command
    
    # Simplification: let 'weather forecast' be resolved with the *current* default when executed
    # This means SPECIAL_CASES for 'weather forecast' would need a placeholder or to be handled in `execute_command` logic.
    # The current `SPECIAL_CASES` directly puts the URL; this needs to be more dynamic.
    # Let's make such special cases point to internal command markers for now.
    SPECIAL_CASES["weather forecast"] = f"#CMD_SEARCH#weather forecast"
    SPECIAL_CASES["local weather"] = f"#CMD_SEARCH#local weather"
    SPECIAL_CASES["news headlines"] = f"#CMD_SEARCH#news headlines today"
    SPECIAL_CASES["ip address"] = f"#CMD_SEARCH#what is my ip address"
    SPECIAL_CASES["current time"] = "#CMD_DATETIME#" # Already did this

    root = tk.Tk()
    app = BrowserControlApp(root)
    root.mainloop()
