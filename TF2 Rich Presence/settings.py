import functools
import json
import os
import sys
import tkinter as tk
import tkinter.ttk as ttk
import traceback
from tkinter import messagebox
from typing import Any, Union

sys.path.append(os.path.abspath(os.path.join('resources', 'python', 'packages')))
sys.path.append(os.path.abspath(os.path.join('resources')))
import logger as log


class GUI(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        self.master = master

        master.title("TF2 Rich Presence settings")
        master.resizable(0, 0)  # disables resizing
        master.geometry("+710+362")  # positions the window kinda near the center of the screen (or perfectly centered if monitor is 1920x1080)

        # set window icon, doesn't work if launching from Pycharm for some reason
        try:
            master.iconbitmap(default='tf2_logo_blurple_wrench.ico')
        except tk.TclError:
            master.iconbitmap(default=os.path.join('resources', 'tf2_logo_blurple_wrench.ico'))

        self.log_levels = ['Debug', 'Info', 'Error', 'Critical', 'Off']

        # create every setting variable without values
        self.enable_sentry = tk.BooleanVar()
        self.wait_time = tk.IntVar()
        self.map_invalidation_hours = tk.IntVar()
        self.check_updates = tk.BooleanVar()
        self.request_timeout = tk.IntVar()
        self.scale_wait_time = tk.BooleanVar()
        self.hide_queued_gamemode = tk.BooleanVar()
        self.log_level = tk.StringVar()
        self.console_scan_lines = tk.IntVar()
        self.hide_provider = tk.BooleanVar()

        try:
            # load settings from settings.json
            self.settings_loaded = access_settings_file()
            log.debug(f"Current settings: {self.settings_loaded}")

            self.enable_sentry.set(self.settings_loaded['enable_sentry'])
            self.wait_time.set(self.settings_loaded['wait_time'])
            self.map_invalidation_hours.set(self.settings_loaded['map_invalidation_hours'])
            self.check_updates.set(self.settings_loaded['check_updates'])
            self.request_timeout.set(self.settings_loaded['request_timeout'])
            self.scale_wait_time.set(self.settings_loaded['scale_wait_time'])
            self.hide_queued_gamemode.set(self.settings_loaded['hide_queued_gamemode'])
            self.log_level.set(self.settings_loaded['log_level'])
            self.console_scan_lines.set(self.settings_loaded['console_scan_lines'])
            self.hide_provider.set(self.settings_loaded['hide_provider'])
        except Exception:
            # probably a json decode error
            formatted_exception = traceback.format_exc()
            log.error(f"Error in loading settings, defaulting: \n{formatted_exception}")
            messagebox.showerror("Error", f"Couldn't load settings, reverting to defaults.\n\n{formatted_exception}")

            # set all settings to defaults
            self.enable_sentry.set(get_setting_default('enable_sentry'))
            self.wait_time.set(get_setting_default('wait_time'))
            self.map_invalidation_hours.set(get_setting_default('map_invalidation_hours'))
            self.check_updates.set(get_setting_default('check_updates'))
            self.request_timeout.set(get_setting_default('request_timeout'))
            self.scale_wait_time.set(get_setting_default('scale_wait_time'))
            self.hide_queued_gamemode.set(get_setting_default('hide_queued_gamemode'))
            self.log_level.set(get_setting_default('log_level'))
            self.console_scan_lines.set(get_setting_default('console_scan_lines'))
            self.hide_provider.set(get_setting_default('hide_provider'))

        check_int_command = self.register(check_int)

        # create settings widgets
        setting1 = ttk.Checkbutton(master, variable=self.enable_sentry, text="{}".format(
            "Report error logs to the developer, via Sentry (https://sentry.io/)"))
        setting3_frame = ttk.Frame()
        setting3_text = ttk.Label(setting3_frame, text="{}".format(
            "Base delay, in seconds, between refreshes (will increase after some AFK time): "))
        setting3_option = ttk.Spinbox(setting3_frame, textvariable=self.wait_time, width=6, from_=0, to=1000, validate='all', validatecommand=(check_int_command, '%P', 1000))
        setting4_frame = ttk.Frame()
        setting4_text = ttk.Label(setting4_frame, text="{}".format(
            "Hours before re-checking custom map gamemode: "))
        setting4_option = ttk.Spinbox(setting4_frame, textvariable=self.map_invalidation_hours, width=6, from_=0, to=1000, validate='all', validatecommand=(check_int_command, '%P', 1000))
        setting5 = ttk.Checkbutton(master, variable=self.check_updates, text="{}".format(
            "Check for program updates when launching"))
        setting6_frame = ttk.Frame()
        setting6_text = ttk.Label(setting6_frame, text="{}".format(
            "Internet connection (for updater and custom maps) timeout, in seconds: "))
        setting6_option = ttk.Spinbox(setting6_frame, textvariable=self.request_timeout, width=6, from_=0, to=60, validate='all', validatecommand=(check_int_command, '%P', 60))
        setting7 = ttk.Checkbutton(master, variable=self.scale_wait_time, text="{}".format(
            "Increase refresh delay when AFK"))
        setting8 = ttk.Checkbutton(master, variable=self.hide_queued_gamemode, text="{}".format(
            "Hide game type (Casual, Comp, MvM) queued for"))
        setting9_frame = ttk.Frame()
        setting9_text = ttk.Label(setting9_frame, text="{}".format(
            "Max log level: "))
        setting9_radiobuttons = []
        for log_level_text in self.log_levels:
            setting9_radiobuttons.append(ttk.Radiobutton(setting9_frame, variable=self.log_level, text=log_level_text, value=log_level_text))
        setting10_frame = ttk.Frame()
        setting10_text = ttk.Label(setting10_frame, text="{}".format(
            "Max lines of console.log to scan: "))
        setting10_option = ttk.Spinbox(setting10_frame, textvariable=self.console_scan_lines, width=8, from_=0, to=float('inf'), validate='all',
                                       validatecommand=(check_int_command, '%P', float('inf')))
        setting11 = ttk.Checkbutton(master, variable=self.hide_provider, text="{}".format(
            "Hide community server provider"))

        # add widgets to the main window
        setting1.grid(row=8, sticky=tk.W, columnspan=2, padx=(15, 15), pady=(2, 0))
        setting3_text.pack(side='left', fill=None, expand=False)
        setting3_option.pack(side='left', fill=None, expand=False)
        setting3_frame.grid(row=0, columnspan=2, sticky=tk.W, padx=(15, 15), pady=(15, 0))
        setting4_text.pack(side='left', fill=None, expand=False)
        setting4_option.pack(side='left', fill=None, expand=False)
        setting4_frame.grid(row=2, columnspan=2, sticky=tk.W, padx=(15, 15), pady=(2, 0))
        setting5.grid(row=6, sticky=tk.W, columnspan=2, padx=(15, 15), pady=(2, 0))
        setting6_text.pack(side='left', fill=None, expand=False)
        setting6_option.pack(side='left', fill=None, expand=False)
        setting6_frame.grid(row=7, columnspan=2, sticky=tk.W, padx=(15, 15), pady=(2, 0))
        setting7.grid(row=1, sticky=tk.W, columnspan=2, padx=(15, 15), pady=(2, 0))
        setting8.grid(row=4, sticky=tk.W, columnspan=2, padx=(15, 15), pady=(2, 0))
        setting9_text.pack(side='left', fill=None, expand=False)
        for setting9_radiobutton in setting9_radiobuttons:
            setting9_radiobutton.pack(side='left', fill=None, expand=False)
        setting9_frame.grid(row=10, columnspan=2, sticky=tk.W, padx=(15, 15), pady=(2, 0))
        setting10_text.pack(side='left', fill=None, expand=False)
        setting10_option.pack(side='left', fill=None, expand=False)
        setting10_frame.grid(row=3, columnspan=2, sticky=tk.W, padx=(15, 15), pady=(2, 0))
        setting11.grid(row=5, sticky=tk.W, columnspan=2, padx=(15, 15), pady=(2, 0))

        cancel_button = ttk.Button(master, text="Close without saving", command=self.close_without_saving)
        cancel_button.grid(row=100, column=0, sticky=tk.E, padx=0, pady=(15, 15))
        ok_button = ttk.Button(master, text="Save and close", command=self.save_and_close, default=tk.ACTIVE)
        ok_button.grid(row=100, column=1, sticky=tk.W, padx=15, pady=(15, 15))

        master.update()
        log.debug(f"Window size: {master.winfo_width()}x{master.winfo_height()}")

    # saves settings to file and closes window
    def save_and_close(self):
        # spinboxes can be set to blank, so if the user saves while blank, they try to default or be set to 0
        int_settings = self.wait_time, self.map_invalidation_hours, self.request_timeout, self.console_scan_lines
        for int_setting in int_settings:
            try:
                int_setting.get()
            except tk.TclError:
                int_setting.set(0)

        settings_to_save = {'enable_sentry': self.enable_sentry.get(),
                            'wait_time': self.wait_time.get(),
                            'map_invalidation_hours': self.map_invalidation_hours.get(),
                            'check_updates': self.check_updates.get(),
                            'request_timeout': max(self.request_timeout.get(), 1),
                            'scale_wait_time': self.scale_wait_time.get(),
                            'hide_queued_gamemode': self.hide_queued_gamemode.get(),
                            'log_level': self.log_level.get(),
                            'console_scan_lines': self.console_scan_lines.get(),
                            'hide_provider': self.hide_provider.get()}

        settings_changed = {k: settings_to_save[k] for k in settings_to_save if k in self.settings_loaded and settings_to_save[k] != self.settings_loaded[k]}  # haha what
        log.debug(f"Setting(s) changed: {settings_changed}")
        log.info("Saving and closing settings menu")
        access_settings_file(save_dict=settings_to_save)
        log.debug(f"Settings have been saved as: {settings_to_save}")

        restart_message = "If TF2 Rich Presence is currently running, it may need to be restarted for changes to take effect."
        settings_changed_num = len(settings_changed)
        if settings_changed_num == 1:
            messagebox.showinfo("Saved", f"1 setting has been changed. {restart_message}")
        elif settings_changed_num > 1:
            messagebox.showinfo("Saved", f"{settings_changed_num} settings have been changed. {restart_message}")

        self.master.destroy()  # closes window

    # closes window without saving
    def close_without_saving(self):
        log.info("Closing settings menu without saving")
        self.master.destroy()


# main entry point
def open_settings_menu():
    log.info("Opening settings menu for TF2 Rich Presence {tf2rpvnum}")

    root = tk.Tk()
    settings_gui = GUI(root)  # only set to a variable to prevent garbage collection? idk
    root.mainloop()


# access a setting from any file, with a string that is the same as the variable name (cached, so settings changes won't be rechecked right away)
@functools.lru_cache(maxsize=None)
def get(setting: str) -> Any:
    try:
        return access_settings_file()[setting]
    except FileNotFoundError:
        log.error(f"Error in getting setting {setting} (settings.json can't be found), defaulting")
        return get_setting_default(setting)
    except Exception as error:
        log.error(f"Error in getting setting {setting} ({error}), defaulting\n{traceback.format_exc()}")
        return get_setting_default(setting)


# either reads the settings file and returns it a a dict, or if a dict is provided, saves it as a json
def access_settings_file(save_dict: Union[dict, None] = None) -> dict:
    if os.path.isdir('resources'):
        settings_path = os.path.join('resources', 'settings.json')
    else:
        settings_path = 'settings.json'

    try:
        if save_dict:
            with open(settings_path, 'w') as settings_json_write:
                json.dump(save_dict, settings_json_write, indent=4)
        else:
            with open(settings_path, 'r') as settings_json_read:
                return json.load(settings_json_read)
    except FileNotFoundError:
        try:
            log.debug("Creating settings.json from defaults")
        except NameError:  # log.log_levels_allowed is not defined, should actually happen every time lol
            pass

        # saves with defualt settings
        default_settings: dict = get_setting_default(return_dict=True)
        with open(settings_path, 'w') as settings_json_create:
            json.dump(default_settings, settings_json_create, indent=4)

        return default_settings


# either gets a settings default, or if return_dict, returns all defaults as a dict
def get_setting_default(setting: str = '', return_dict: bool = False) -> Any:
    defaults = {'enable_sentry': True,
                'wait_time': 5,
                'map_invalidation_hours': 24,
                'check_updates': True,
                'request_timeout': 5,
                'scale_wait_time': True,
                'hide_queued_gamemode': False,
                'log_level': 'Debug',
                'console_scan_lines': 10000,
                'hide_provider': False}

    if return_dict:
        return defaults
    else:
        return defaults[setting]


# checks if a string is an integer between 0 and a supplied maximum (blank is allowed, will get set to default when saving)
def check_int(text_in_entry: str, maximum: int) -> bool:
    if text_in_entry == '':
        log.debug(f"Checking entry: \"{text_in_entry}\" passes (is blank)")
        return True

    if text_in_entry.isdigit() and 0 <= int(text_in_entry) <= float(maximum):
        log.debug(f"Checking entry: \"{text_in_entry}\" passes (is digit and is between 0 and {float(maximum)})")
        return True

    log.debug(f"Checking entry: \"{text_in_entry}\" fails")
    return False


if __name__ == '__main__':
    open_settings_menu()
