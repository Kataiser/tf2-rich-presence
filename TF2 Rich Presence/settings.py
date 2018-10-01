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
import logger


class GUI(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        self.master = master

        self.log = logger.Log()
        self.log.info("Opening settings menu for TF2 Rich Presence {tf2rpvnum}")

        master.title("TF2 Rich Presence settings")
        master.resizable(0, 0)  # disables resizing
        master.geometry("+710+362")  # positions the window kinda near the center of the screen (or perfectly centered if monitor is 1920x1080)

        # set window icon, doesn't work if launching from Pycharm for some reason
        try:
            master.iconbitmap(default='tf2_logo_blurple_wrench.ico')
        except tk.TclError:
            master.iconbitmap(default=os.path.join('resources', 'tf2_logo_blurple_wrench.ico'))

        self.log_levels = ['Debug', 'Info', 'Error', 'Critical', 'Off']
        self.class_pic_types = ['Icon', 'Emblem', 'Portrait', 'None, use TF2 logo']

        # create every setting variable without values
        self.enable_sentry = tk.BooleanVar()
        self.wait_time = tk.IntVar()
        self.map_invalidation_hours = tk.IntVar()
        self.check_updates = tk.BooleanVar()
        self.request_timeout = tk.IntVar()
        self.scale_wait_time = tk.BooleanVar()
        self.hide_queued_gamemode = tk.BooleanVar()
        self.log_level = tk.StringVar()
        self.console_scan_kb = tk.IntVar()
        self.hide_provider = tk.BooleanVar()
        self.class_pic_type = tk.StringVar()

        try:
            # load settings from settings.json
            self.settings_loaded = access_settings_file()
            self.log.debug(f"Current settings: {self.settings_loaded}")

            self.enable_sentry.set(self.settings_loaded['enable_sentry'])
            self.wait_time.set(self.settings_loaded['wait_time'])
            self.map_invalidation_hours.set(self.settings_loaded['map_invalidation_hours'])
            self.check_updates.set(self.settings_loaded['check_updates'])
            self.request_timeout.set(self.settings_loaded['request_timeout'])
            self.scale_wait_time.set(self.settings_loaded['scale_wait_time'])
            self.hide_queued_gamemode.set(self.settings_loaded['hide_queued_gamemode'])
            self.log_level.set(self.settings_loaded['log_level'])
            self.console_scan_kb.set(self.settings_loaded['console_scan_kb'])
            self.hide_provider.set(self.settings_loaded['hide_provider'])
            self.class_pic_type.set(self.settings_loaded['class_pic_type'])
        except Exception:
            # probably a json decode error
            formatted_exception = traceback.format_exc()
            self.log.error(f"Error in loading settings, defaulting: \n{formatted_exception}")
            messagebox.showerror("Error", f"Couldn't load settings, reverting to defaults.\n\n{formatted_exception}")

            self.restore_defaults()
            self.settings_loaded = get_setting_default(return_all=True)

        check_int_command = self.register(check_int)

        # create settings widgets
        setting1 = ttk.Checkbutton(master, variable=self.enable_sentry, command=self.update_default_button_state, text="{}".format(
            "Report crash logs"))
        setting3_frame = ttk.Frame()
        setting3_text = ttk.Label(setting3_frame, text="{}".format(
            "Base delay, in seconds, between refreshes (will increase after some AFK time): "))
        setting3_option = ttk.Spinbox(setting3_frame, textvariable=self.wait_time, width=6, from_=0, to=1000, validate='all', validatecommand=(check_int_command, '%P', 1000),
                                      command=self.update_default_button_state)
        setting4_frame = ttk.Frame()
        setting4_text = ttk.Label(setting4_frame, text="{}".format(
            "Hours before re-checking custom map gamemode: "))
        setting4_option = ttk.Spinbox(setting4_frame, textvariable=self.map_invalidation_hours, width=6, from_=0, to=1000, validate='all', validatecommand=(check_int_command, '%P', 1000),
                                      command=self.update_default_button_state)
        setting5 = ttk.Checkbutton(master, variable=self.check_updates, command=self.update_default_button_state, text="{}".format(
            "Check for program updates when launching"))
        setting6_frame = ttk.Frame()
        setting6_text = ttk.Label(setting6_frame, text="{}".format(
            "Internet connection (for updater and custom maps) timeout, in seconds: "))
        setting6_option = ttk.Spinbox(setting6_frame, textvariable=self.request_timeout, width=6, from_=0, to=60, validate='all', validatecommand=(check_int_command, '%P', 60),
                                      command=self.update_default_button_state)
        setting7 = ttk.Checkbutton(master, variable=self.scale_wait_time, command=self.update_default_button_state, text="{}".format(
            "Increase refresh delay when AFK"))
        setting8 = ttk.Checkbutton(master, variable=self.hide_queued_gamemode, command=self.update_default_button_state, text="{}".format(
            "Hide game type (Casual, Comp, MvM) queued for"))
        setting9_frame = ttk.Frame()
        setting9_text = ttk.Label(setting9_frame, text="{}".format(
            "Max log level: "))
        setting9_radiobuttons = []
        for log_level_text in self.log_levels:
            setting9_radiobuttons.append(ttk.Radiobutton(setting9_frame, variable=self.log_level, text=log_level_text, value=log_level_text, command=self.update_default_button_state))
        setting10_frame = ttk.Frame()
        setting10_text = ttk.Label(setting10_frame, text="{}".format(
            "Max kilobytes of console.log to scan: "))
        setting10_option = ttk.Spinbox(setting10_frame, textvariable=self.console_scan_kb, width=8, from_=0, to=float('inf'), validate='all',
                                       validatecommand=(check_int_command, '%P', float('inf')), command=self.update_default_button_state)
        setting11 = ttk.Checkbutton(master, variable=self.hide_provider, command=self.update_default_button_state, text="{}".format(
            "Hide community server provider"))
        setting12_frame = ttk.Frame()
        setting12_text = ttk.Label(setting12_frame, text="{}".format(
            "Selected class small image type: "))
        setting12_radiobuttons = []
        for class_pic_type_text in self.class_pic_types:
            setting12_radiobuttons.append(ttk.Radiobutton(setting12_frame, variable=self.class_pic_type, text=class_pic_type_text, value=class_pic_type_text,
                                                          command=self.update_default_button_state))

        # add widgets to the main window
        setting1.grid(row=9, sticky=tk.W, columnspan=2, padx=(20, 20), pady=(4, 0))
        setting3_text.pack(side='left', fill=None, expand=False)
        setting3_option.pack(side='left', fill=None, expand=False)
        setting3_frame.grid(row=0, columnspan=2, sticky=tk.W, padx=(20, 20), pady=(20, 0))
        setting4_text.pack(side='left', fill=None, expand=False)
        setting4_option.pack(side='left', fill=None, expand=False)
        setting4_frame.grid(row=2, columnspan=2, sticky=tk.W, padx=(20, 20), pady=(4, 0))
        setting5.grid(row=7, sticky=tk.W, columnspan=2, padx=(20, 20), pady=(4, 0))
        setting6_text.pack(side='left', fill=None, expand=False)
        setting6_option.pack(side='left', fill=None, expand=False)
        setting6_frame.grid(row=8, columnspan=2, sticky=tk.W, padx=(20, 20), pady=(4, 0))
        setting7.grid(row=1, sticky=tk.W, columnspan=2, padx=(20, 20), pady=(4, 0))
        setting8.grid(row=4, sticky=tk.W, columnspan=2, padx=(20, 20), pady=(4, 0))
        setting9_text.pack(side='left', fill=None, expand=False)
        for setting9_radiobutton in setting9_radiobuttons:
            setting9_radiobutton.pack(side='left', fill=None, expand=False)
        setting9_frame.grid(row=10, columnspan=2, sticky=tk.W, padx=(20, 20), pady=(4, 0))
        setting10_text.pack(side='left', fill=None, expand=False)
        setting10_option.pack(side='left', fill=None, expand=False)
        setting10_frame.grid(row=3, columnspan=2, sticky=tk.W, padx=(20, 20), pady=(4, 0))
        setting11.grid(row=5, sticky=tk.W, columnspan=2, padx=(20, 20), pady=(4, 0))
        setting12_text.pack(side='left', fill=None, expand=False)
        for setting12_radiobutton in setting12_radiobuttons:
            setting12_radiobutton.pack(side='left', fill=None, expand=False)
        setting12_frame.grid(row=6, columnspan=2, sticky=tk.W, padx=(20, 20), pady=(4, 0))

        buttons_frame = ttk.Frame()
        self.restore_button = ttk.Button(buttons_frame, text="Restore defaults", command=self.restore_defaults)
        self.restore_button.grid(row=0, column=0, sticky=tk.E, padx=0, pady=(20, 20))
        cancel_button = ttk.Button(buttons_frame, text="Close without saving", command=self.close_without_saving)
        cancel_button.grid(row=0, column=1, padx=20, pady=(20, 20))
        ok_button = ttk.Button(buttons_frame, text="Save and close", command=self.save_and_close, default=tk.ACTIVE)
        ok_button.grid(row=0, column=2, sticky=tk.W, padx=0, pady=(20, 20))
        buttons_frame.grid(row=100, columnspan=3)

        self.update_default_button_state()
        master.update()
        self.log.debug(f"Window size: {master.winfo_width()}x{master.winfo_height()}")

    # runs every time a setting is changed, updates "restore defaults" button's state
    def update_default_button_state(self):
        if self.get_working_settings() == get_setting_default(return_all=True):  # if settings are default, disable button
            self.restore_button.state(['disabled'])
            self.log.debug("Disabled restore defaults button")
        else:
            self.restore_button.state(['!disabled'])
            self.log.debug("Enabled restore defaults button")

    # return the settings as a dict, as they currently are in the GUI
    def get_working_settings(self) -> dict:
        return {'enable_sentry': self.enable_sentry.get(),
                'wait_time': self.wait_time.get(),
                'map_invalidation_hours': self.map_invalidation_hours.get(),
                'check_updates': self.check_updates.get(),
                'request_timeout': max(self.request_timeout.get(), 1),
                'scale_wait_time': self.scale_wait_time.get(),
                'hide_queued_gamemode': self.hide_queued_gamemode.get(),
                'log_level': self.log_level.get(),
                'console_scan_kb': self.console_scan_kb.get(),
                'hide_provider': self.hide_provider.get(),
                'class_pic_type': self.class_pic_type.get()}

    # set all settings to defaults
    def restore_defaults(self):
        self.enable_sentry.set(get_setting_default('enable_sentry'))
        self.wait_time.set(get_setting_default('wait_time'))
        self.map_invalidation_hours.set(get_setting_default('map_invalidation_hours'))
        self.check_updates.set(get_setting_default('check_updates'))
        self.request_timeout.set(get_setting_default('request_timeout'))
        self.scale_wait_time.set(get_setting_default('scale_wait_time'))
        self.hide_queued_gamemode.set(get_setting_default('hide_queued_gamemode'))
        self.log_level.set(get_setting_default('log_level'))
        self.console_scan_kb.set(get_setting_default('console_scan_kb'))
        self.hide_provider.set(get_setting_default('hide_provider'))
        self.class_pic_type.set(get_setting_default('class_pic_type'))

    # saves settings to file and closes window
    def save_and_close(self):
        # spinboxes can be set to blank, so if the user saves while blank, they try to default or be set to 0
        int_settings = self.wait_time, self.map_invalidation_hours, self.request_timeout, self.console_scan_kb
        for int_setting in int_settings:
            try:
                int_setting.get()
            except tk.TclError:
                int_setting.set(0)

        settings_to_save = self.get_working_settings()

        settings_changed = {k: settings_to_save[k] for k in settings_to_save if k in self.settings_loaded and settings_to_save[k] != self.settings_loaded[k]}  # haha what
        self.log.debug(f"Setting(s) changed: {settings_changed}")
        self.log.info("Saving and closing settings menu")
        access_settings_file(save_dict=settings_to_save)
        self.log.debug(f"Settings have been saved as: {settings_to_save}")

        restart_message = "If TF2 Rich Presence is currently running, it may need to be restarted for changes to take effect."
        settings_changed_num = len(settings_changed)
        if settings_changed_num == 1:
            messagebox.showinfo("Saved", f"1 setting has been changed. {restart_message}")
        elif settings_changed_num > 1:
            messagebox.showinfo("Saved", f"{settings_changed_num} settings have been changed. {restart_message}")

        self.master.destroy()  # closes window

    # closes window without saving
    def close_without_saving(self):
        self.log.info("Closing settings menu without saving")
        self.master.destroy()


# main entry point
def launch():
    root = tk.Tk()
    settings_gui = GUI(root)  # only set to a variable to prevent garbage collection? idk
    root.mainloop()


# access a setting from any file, with a string that is the same as the variable name (cached, so settings changes won't be rechecked right away)
@functools.lru_cache(maxsize=None)
def get(setting: str) -> Any:
    try:
        return access_settings_file()[setting]
    except FileNotFoundError:
        return get_setting_default(setting)
    except Exception:
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
        # saves with defualt settings
        default_settings: dict = get_setting_default(return_all=True)
        with open(settings_path, 'w') as settings_json_create:
            json.dump(default_settings, settings_json_create, indent=4)

        return default_settings


# either gets a settings default, or if return_dict, returns all defaults as a dict
def get_setting_default(setting: str = '', return_all: bool = False) -> Any:
    defaults = {'enable_sentry': True,
                'wait_time': 5,
                'map_invalidation_hours': 24,
                'check_updates': True,
                'request_timeout': 5,
                'scale_wait_time': True,
                'hide_queued_gamemode': False,
                'log_level': 'Debug',
                'console_scan_kb': 1000,
                'hide_provider': False,
                'class_pic_type': 'Icon'}

    if return_all:
        return defaults
    else:
        return defaults[setting]


# checks if a string is an integer between 0 and a supplied maximum (blank is allowed, will get set to default when saving)
def check_int(text_in_entry: str, maximum: int) -> bool:
    if text_in_entry == '':
        return True

    if text_in_entry.isdigit() and 0 <= int(text_in_entry) <= float(maximum):
        return True

    return False


if __name__ == '__main__':
    launch()
