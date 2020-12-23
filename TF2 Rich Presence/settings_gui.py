# Copyright (C) 2019 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE
# cython: language_level=3

import atexit
import gc
import os
import subprocess
import tkinter as tk
import tkinter.ttk as ttk
import traceback
import webbrowser
from tkinter import messagebox
from typing import Union

import launcher
import localization
import logger
import settings
import utils


class GUI(tk.Frame):
    def __init__(self, master, log=None, reload_settings=None):
        if log:
            self.log = log
        else:
            self.log = logger.Log()
            self.log.to_stderr = True

        self.log.info(f"Opening settings menu for TF2 Rich Presence {launcher.VERSION}")
        self.gui_language = self.languages[self.languages.index(reload_settings[10].get())] if reload_settings else None
        self.loc = localization.Localizer(self.log, self.gui_language if self.gui_language else settings.get('language'))

        tk.Frame.__init__(self, master)
        self.master = master
        self.instructions_image = self.font_window = None
        check_int_command = self.register(check_int)
        atexit.register(self.window_close_log)

        master.title(self.loc.text("TF2 Rich Presence ({0}) settings").format(launcher.VERSION))
        master.resizable(0, 0)  # disables resizing
        utils.set_window_icon(self.log, master, True)
        if not reload_settings:
            self.window_x: Union[int, None] = None
            self.window_y: Union[int, None] = None

        self.log_levels = ('Debug', 'Info', 'Error', 'Critical', 'Off')
        self.sentry_levels = ('All errors', 'Crashes', 'Never')
        self.class_pic_types = ('Icon', 'Emblem', 'Portrait', 'None, use TF2 logo')
        self.languages = ('English', 'German', 'French', 'Spanish', 'Portuguese', 'Italian', 'Dutch', 'Polish', 'Russian', 'Korean', 'Chinese', 'Japanese')
        self.second_lines = ('Player count', 'Time on map', 'Class', 'Kills')

        self.log_levels_display = [self.loc.text(item) for item in self.log_levels]
        self.sentry_levels_display = [self.loc.text(item) for item in self.sentry_levels]
        self.class_pic_types_display = [self.loc.text(item) for item in self.class_pic_types]
        self.second_lines_display = [self.loc.text(item) for item in self.second_lines]
        self.languages_display = ('English', 'Deutsch', 'Français', 'Español', 'Português Brasileiro', 'Italiano', 'Nederlands', 'Polski', 'русский язык', '한국어', '汉语', '日本語')

        if reload_settings:
            # the GUI was reloaded with a new language, so persist the currently selected (but not saved) settings
            self.sentry_level, self.wait_time, self.wait_time_slow, self.map_invalidation_hours, self.check_updates, self.request_timeout, self.hide_queued_gamemode, self.log_level, \
            self.console_scan_kb, self.class_pic_type, self.language, self.second_line, self.trim_console_log, self.server_rate_limit = reload_settings
        else:
            # create every setting variable without values
            self.sentry_level = tk.StringVar()
            self.wait_time = tk.IntVar()
            self.wait_time_slow = tk.IntVar()
            self.map_invalidation_hours = tk.IntVar()
            self.check_updates = tk.BooleanVar()
            self.request_timeout = tk.IntVar()
            self.hide_queued_gamemode = tk.BooleanVar()
            self.log_level = tk.StringVar()
            self.console_scan_kb = tk.IntVar()
            self.class_pic_type = tk.StringVar()
            self.language = tk.StringVar()
            self.second_line = tk.StringVar()
            self.trim_console_log = tk.BooleanVar()
            self.server_rate_limit = tk.IntVar()

            try:
                # load settings from registry
                settings.fix_settings(self.log)
                self.settings_loaded = settings.access_registry()
                self.log.debug(f"Current settings: {self.settings_loaded}")
                self.log.debug(f"Are default: {self.settings_loaded == settings.defaults()}")

                self.sentry_level.set(self.settings_loaded['sentry_level'])
                self.wait_time.set(self.settings_loaded['wait_time'])
                self.wait_time_slow.set(self.settings_loaded['wait_time_slow'])
                self.map_invalidation_hours.set(self.settings_loaded['map_invalidation_hours'])
                self.check_updates.set(self.settings_loaded['check_updates'])
                self.request_timeout.set(self.settings_loaded['request_timeout'])
                self.hide_queued_gamemode.set(self.settings_loaded['hide_queued_gamemode'])
                self.log_level.set(self.settings_loaded['log_level'])
                self.console_scan_kb.set(self.settings_loaded['console_scan_kb'])
                self.class_pic_type.set(self.settings_loaded['class_pic_type'])
                self.language.set(self.gui_language if self.gui_language else self.settings_loaded['language'])
                self.second_line.set(self.settings_loaded['second_line'])
                self.trim_console_log.set(self.settings_loaded['trim_console_log'])
                self.server_rate_limit.set(self.settings_loaded['server_rate_limit'])
            except Exception:
                # probably a json decode error
                formatted_exception = traceback.format_exc()
                self.log.error(f"Error in loading settings, defaulting: \n{formatted_exception}")
                messagebox.showerror(self.loc.text("Error"), self.loc.text("Couldn't load settings, reverting to defaults.{0}").format(f'\n\n{formatted_exception}'))

                self.restore_defaults()
                self.settings_loaded = settings.defaults()

        # make dropdown options account for localization
        self.log_level.set(self.log_levels_display[self.log_levels.index(self.log_level.get())])
        self.sentry_level.set(self.sentry_levels_display[self.sentry_levels.index(self.sentry_level.get())])
        self.class_pic_type.set(self.class_pic_types_display[self.class_pic_types.index(self.class_pic_type.get())])
        self.language.set(self.languages_display[self.languages.index(self.language.get())])
        self.second_line.set(self.second_lines_display[self.second_lines.index(self.second_line.get())])
        actual_language = self.language.get()
        actual_second_line = self.second_line.get()

        # create label frames
        self.lf_main = ttk.Labelframe(master, text=self.loc.text("Main"))
        self.lf_advanced = ttk.Labelframe(master, text=self.loc.text("Advanced"))

        # create settings widgets
        setting1_frame = ttk.Frame(self.lf_advanced)
        setting1_text = ttk.Label(setting1_frame, text="{}".format(
            self.loc.text("Log reporting frequency: ")))
        setting1_radiobuttons = []
        for sentry_level_text in self.sentry_levels_display:
            setting1_radiobuttons.append(ttk.Radiobutton(setting1_frame, variable=self.sentry_level, text=sentry_level_text, value=sentry_level_text, command=self.update_default_button_state))
        setting3_frame = ttk.Frame(self.lf_main)
        setting3_text = ttk.Label(setting3_frame, text="{}".format(
            self.loc.text("Delay between refreshes, in seconds: ")))
        setting3_option = ttk.Spinbox(setting3_frame, textvariable=self.wait_time, width=6, from_=0, to=float('inf'), validate='all', validatecommand=(check_int_command, '%P'),
                                      command=self.update_default_button_state)
        setting4_frame = ttk.Frame(self.lf_advanced)
        setting4_text = ttk.Label(setting4_frame, text="{}".format(
            self.loc.text("Hours before re-checking custom map gamemode: ")))
        setting4_option = ttk.Spinbox(setting4_frame, textvariable=self.map_invalidation_hours, width=6, from_=0, to=float('inf'), validate='all', validatecommand=(check_int_command, '%P'),
                                      command=self.update_default_button_state)
        setting5 = ttk.Checkbutton(self.lf_main, variable=self.check_updates, command=self.update_default_button_state, text="{}".format(
            self.loc.text("Check for program updates when launching")))
        setting6_frame = ttk.Frame(self.lf_advanced)
        setting6_text = ttk.Label(setting6_frame, text="{}".format(
            self.loc.text("Internet connection timeout (for updater and some custom maps), in seconds: ")))
        setting6_option = ttk.Spinbox(setting6_frame, textvariable=self.request_timeout, width=6, from_=0, to=float('inf'), validate='all', validatecommand=(check_int_command, '%P'),
                                      command=self.update_default_button_state)
        setting8 = ttk.Checkbutton(self.lf_main, variable=self.hide_queued_gamemode, command=self.update_default_button_state, text="{}".format(
            self.loc.text("Hide game type (Casual, Comp, MvM) queued for")))
        setting9_frame = ttk.Frame(self.lf_advanced)
        setting9_text = ttk.Label(setting9_frame, text="{}".format(
            self.loc.text("Max log level: ")))
        setting9_radiobuttons = []
        for log_level_text in self.log_levels_display:
            setting9_radiobuttons.append(ttk.Radiobutton(setting9_frame, variable=self.log_level, text=log_level_text, value=log_level_text, command=self.update_default_button_state))
        setting10_frame = ttk.Frame(self.lf_advanced)
        setting10_text = ttk.Label(setting10_frame, text="{}".format(
            self.loc.text("Max kilobytes of console.log to scan: ")))
        setting10_option = ttk.Spinbox(setting10_frame, textvariable=self.console_scan_kb, width=8, from_=0, to=float('inf'), validate='all',
                                       validatecommand=(check_int_command, '%P'), command=self.update_default_button_state)
        setting12_frame = ttk.Frame(self.lf_main)
        setting12_text = ttk.Label(setting12_frame, text="{}".format(
            self.loc.text("Selected class small image type: ")))
        setting12_radiobuttons = []
        for class_pic_type_text in self.class_pic_types_display:
            setting12_radiobuttons.append(ttk.Radiobutton(setting12_frame, variable=self.class_pic_type, text=class_pic_type_text, value=class_pic_type_text,
                                                          command=self.update_default_button_state))
        setting13_frame = ttk.Frame(self.lf_main)
        setting13_text = ttk.Label(setting13_frame, text="{}".format(
            self.loc.text("Language: ")))
        setting13_options = ttk.OptionMenu(setting13_frame, self.language, self.languages[0], *self.languages_display, command=self.update_language)
        setting14_frame = ttk.Frame(self.lf_main)
        setting14_text = ttk.Label(setting14_frame, text="{}".format(
            self.loc.text("Second line: ")))
        setting14_options = ttk.OptionMenu(setting14_frame, self.second_line, self.second_lines[0], *self.second_lines_display, command=self.update_default_button_state)
        setting15 = ttk.Checkbutton(self.lf_advanced, variable=self.trim_console_log, command=self.update_default_button_state, text="{}".format(
            self.loc.text("Occasionally limit console.log's size and remove empty lines")))
        setting16_frame = ttk.Frame(self.lf_main)
        setting16_text = ttk.Label(setting16_frame, text="{}".format(
            self.loc.text("Delay between refreshes when TF2 and Discord aren't running: ")))  # and Steam but whatever
        setting16_option = ttk.Spinbox(setting16_frame, textvariable=self.wait_time_slow, width=6, from_=0, to=float('inf'), validate='all', validatecommand=(check_int_command, '%P'),
                                       command=self.update_default_button_state)
        setting17_frame = ttk.Frame(self.lf_advanced)
        setting17_text = ttk.Label(setting17_frame, text="{}".format(
            self.loc.text("Server querying rate limit: ")))
        setting17_option = ttk.Spinbox(setting17_frame, textvariable=self.server_rate_limit, width=6, from_=0, to=float('inf'), validate='all', validatecommand=(check_int_command, '%P'),
                                       command=self.update_default_button_state)

        # more localization compensation
        self.language.set(actual_language)
        self.second_line.set(actual_second_line)

        # download page button, but only if a new version is available
        db = utils.access_db()
        show_update_button = db['available_version']['exists']
        if show_update_button:
            new_version_name = db['available_version']['tag']
            self.new_version_url = db['available_version']['url']

            self.update_button_text = tk.StringVar(value=self.loc.text(" Open {0} download page in default browser ").format(new_version_name))
            self.update_button = ttk.Button(self.lf_main, textvariable=self.update_button_text, command=self.open_update_page)

        # prepare widgets to be added
        setting1_text.pack(side='left', fill=None, expand=False)
        for setting1_radiobutton in setting1_radiobuttons:
            setting1_radiobutton.pack(side='left', fill=None, expand=False)
        setting3_text.pack(side='left', fill=None, expand=False)
        setting3_option.pack(side='left', fill=None, expand=False)
        setting4_text.pack(side='left', fill=None, expand=False)
        setting4_option.pack(side='left', fill=None, expand=False)
        setting6_text.pack(side='left', fill=None, expand=False)
        setting6_option.pack(side='left', fill=None, expand=False)
        setting9_text.pack(side='left', fill=None, expand=False)
        for setting9_radiobutton in setting9_radiobuttons:
            setting9_radiobutton.pack(side='left', fill=None, expand=False)
        setting10_text.pack(side='left', fill=None, expand=False)
        setting10_option.pack(side='left', fill=None, expand=False)
        setting12_text.pack(side='left', fill=None, expand=False)
        for setting12_radiobutton in setting12_radiobuttons:
            setting12_radiobutton.pack(side='left', fill=None, expand=False)
        setting13_text.pack(side='left', fill=None, expand=False)
        setting13_options.pack(side='left', fill=None, expand=False)
        setting14_text.pack(side='left', fill=None, expand=False)
        setting14_options.pack(side='left', fill=None, expand=False)
        setting16_text.pack(side='left', fill=None, expand=False)
        setting16_option.pack(side='left', fill=None, expand=False)
        setting17_text.pack(side='left', fill=None, expand=False)
        setting17_option.pack(side='left', fill=None, expand=False)

        # add widgets to the labelframes and main window
        setting13_frame.grid(row=0, columnspan=2, sticky=tk.W, padx=(20, 40), pady=(9, 0))
        setting3_frame.grid(row=1, columnspan=2, sticky=tk.W, padx=(20, 40), pady=(3, 0))
        setting16_frame.grid(row=2, columnspan=2, sticky=tk.W, padx=(20, 40), pady=(3, 0))
        setting14_frame.grid(row=3, columnspan=2, sticky=tk.W, padx=(20, 40), pady=(3, 0))
        setting10_frame.grid(row=4, columnspan=2, sticky=tk.W, padx=(20, 40), pady=(11, 0))
        setting8.grid(row=5, sticky=tk.W, columnspan=2, padx=(20, 40), pady=(4, 0))
        setting15.grid(row=6, sticky=tk.W, columnspan=2, padx=(20, 40), pady=(4, 0))
        setting12_frame.grid(row=7, columnspan=2, sticky=tk.W, padx=(20, 40), pady=(4, 0))
        setting5.grid(row=8, sticky=tk.W, columnspan=2, padx=(20, 40), pady=(4, 10))
        if show_update_button:
            self.update_button.grid(row=9, sticky=tk.W, padx=(20, 40), pady=(0, 12))
        setting4_frame.grid(row=10, columnspan=2, sticky=tk.W, padx=(20, 40), pady=(4, 0))
        setting6_frame.grid(row=11, columnspan=2, sticky=tk.W, padx=(20, 40), pady=(4, 0))
        setting17_frame.grid(row=12, columnspan=2, sticky=tk.W, padx=(20, 40), pady=(3, 0))
        setting1_frame.grid(row=13, columnspan=2, sticky=tk.W, padx=(20, 40), pady=(4, 0))
        setting9_frame.grid(row=14, columnspan=2, sticky=tk.W, padx=(20, 40), pady=(4, 10))

        self.lf_main.grid(row=0, padx=30, pady=15, sticky=tk.W + tk.E)
        self.lf_advanced.grid(row=1, padx=30, pady=0, sticky=tk.W + tk.E)

        self.buttons_frame = ttk.Frame()
        self.restore_button = ttk.Button(self.buttons_frame, text=self.loc.text("Restore defaults"), command=self.restore_defaults)
        self.restore_button.grid(row=0, column=1, padx=(10, 0), pady=(20, 20))
        cancel_button = ttk.Button(self.buttons_frame, text=self.loc.text("Close without saving"), command=self.close_without_saving)
        cancel_button.grid(row=0, column=2, padx=10, pady=(20, 20))
        self.ok_button = ttk.Button(self.buttons_frame, text=self.loc.text("Save and close"), command=self.save_and_close, default=tk.ACTIVE)
        self.ok_button.grid(row=0, column=3, sticky=tk.W, padx=0, pady=(20, 20))
        self.buttons_frame.grid(row=100, columnspan=3)

        if not self.window_x and not self.window_y:
            target_h, target_y = (600, 500)
            self.window_x = round((self.winfo_screenwidth() / 2) - (target_h / 2))
            self.window_y = round((self.winfo_screenheight() / 2) - (target_y / 2)) - 40
        master.geometry(f'+{self.window_x}+{self.window_y}')
        self.log.debug(f"Window position: {(self.window_x, self.window_y)}")

        self.update_default_button_state()
        master.update()
        self.window_dimensions = master.winfo_width(), master.winfo_height()
        self.log.debug(f"Window size: {self.window_dimensions}")

        # move window to the top (but don't keep it there)
        master.lift()
        master.attributes('-topmost', True)
        master.after_idle(master.attributes, '-topmost', False)

        if not gc.isenabled():
            gc.enable()
            gc.collect()
            self.log.debug("Enabled GC and collected")

    def __repr__(self):
        return f"settings.GUI {self.window_dimensions}"

    # runs every time a setting is changed, updates "restore defaults" button's state
    def update_default_button_state(self, *args):
        if self.get_working_settings() == settings.defaults():  # if settings are default, disable button
            self.restore_button.state(['disabled'])
            self.log.debug("Disabled restore defaults button")
        else:
            self.restore_button.state(['!disabled'])
            self.log.debug("Enabled restore defaults button")

    # runs every time the language setting is changed
    def update_language(self, language_selected: str):
        language_selected_normal = self.languages[self.languages_display.index(language_selected)]

        if language_selected_normal != self.gui_language:
            self.log.debug(f"Reloading settings menu with language {language_selected_normal}")
            self.lf_main.destroy()
            self.lf_advanced.destroy()
            self.buttons_frame.destroy()

            # normalize some settings to english so that the reload will be converted back
            self.log_level.set(self.log_levels[self.log_levels_display.index(self.log_level.get())])
            self.sentry_level.set(self.sentry_levels[self.sentry_levels_display.index(self.sentry_level.get())])
            self.class_pic_type.set(self.class_pic_types[self.class_pic_types_display.index(self.class_pic_type.get())])
            self.language.set(self.languages[self.languages_display.index(self.language.get())])
            self.second_line.set(self.second_lines[self.second_lines_display.index(self.second_line.get())])

            selected_settings = (self.sentry_level, self.wait_time, self.wait_time_slow, self.map_invalidation_hours, self.check_updates, self.request_timeout, self.hide_queued_gamemode,
                                 self.log_level, self.console_scan_kb, self.class_pic_type, self.language, self.second_line, self.trim_console_log, self.server_rate_limit)
            self.window_x = self.master.winfo_rootx() - 8
            self.window_y = self.master.winfo_rooty() - 31
            self.__init__(self.master, self.log, reload_settings=selected_settings)
            self.show_font_message(language_selected)

    # (possibly) show a window with instructions for changing the command prompt font
    def show_font_message(self, language: str = None):
        if language in self.languages_display[-3:]:  # Korean, Chinese, and Japanese
            self.master.update()
            font_message_1 = self.loc.text("The Windows command prompt's default font doesn't support {0} characters. Here's how to fix it:").format(language)
            font_message_2 = self.loc.text("Choose your preference between MS Gothic, NSimSun, and SimSun-ExtB.")

            font_instructions_path = os.path.join('resources', 'font_instructions.gif') if os.path.isdir('resources') else 'font_instructions.gif'
            self.font_window = tk.Toplevel(self.master)
            self.font_window.geometry(f'+{self.master.winfo_x()}+{self.master.winfo_y()}')
            self.font_window.title(self.loc.text("Font instructions"))
            self.font_window.resizable(0, 0)

            ttk.Label(self.font_window, text=font_message_1).grid(row=0, padx=(20, 40), pady=(15, 10), sticky=tk.W)
            instructions_canvas = tk.Canvas(self.font_window, width=382, height=325)
            self.instructions_image = tk.PhotoImage(file=font_instructions_path)
            instructions_canvas.create_image(0, 0, anchor=tk.NW, image=self.instructions_image)
            instructions_canvas.grid(row=1, padx=30, sticky=tk.W)
            ttk.Label(self.font_window, text=font_message_2).grid(row=2, padx=20, pady=5, sticky=tk.W)
            ttk.Button(self.font_window, text=self.loc.text("Close"), command=self.font_window.destroy, default=tk.ACTIVE).grid(row=3, padx=20, pady=(0, 20), sticky=tk.E)

            self.font_window.update()
            target_x = self.master.winfo_x() + round((self.master.winfo_width() - self.font_window.winfo_width()) / 2)
            target_y = self.master.winfo_y() + round((self.master.winfo_height() - self.font_window.winfo_height()) / 2)
            self.font_window.geometry(f'+{target_x}+{target_y}')
            self.font_window.lift()
            self.font_window.focus_force()

            font_window_info = {'x': target_x, 'y': target_y, 'w': self.font_window.winfo_height(), 'h': self.font_window.winfo_width()}
            self.log.debug(f"Created font message window: {font_window_info}")
            # can't easily add a close window log, not worth all the hoops you'd need to jump through

    # return the settings as a dict, as they currently are in the GUI
    def get_working_settings(self) -> dict:
        return {'sentry_level': self.sentry_levels[self.sentry_levels_display.index(self.sentry_level.get())],
                'wait_time': self.wait_time.get(),
                'wait_time_slow': self.wait_time_slow.get(),
                'map_invalidation_hours': self.map_invalidation_hours.get(),
                'check_updates': self.check_updates.get(),
                'request_timeout': max(self.request_timeout.get(), 1),
                'hide_queued_gamemode': self.hide_queued_gamemode.get(),
                'log_level': self.log_levels[self.log_levels_display.index(self.log_level.get())],
                'console_scan_kb': self.console_scan_kb.get(),
                'class_pic_type': self.class_pic_types[self.class_pic_types_display.index(self.class_pic_type.get())],
                'language': self.languages[self.languages_display.index(self.language.get())],
                'second_line': self.second_lines[self.second_lines_display.index(self.second_line.get())],
                'trim_console_log': self.trim_console_log.get(),
                'server_rate_limit': self.server_rate_limit.get()}

    # set all settings to defaults
    def restore_defaults(self):
        settings_to_save = self.get_working_settings()
        settings_changed = {k: settings_to_save[k] for k in settings_to_save if k in self.settings_loaded and settings_to_save[k] != self.settings_loaded[k]}  # haha what

        settings_changed_num = len(settings_changed)
        allowed_reset = "yes"
        if settings_changed_num == 1:
            allowed_reset = messagebox.askquestion(self.loc.text("Restore defaults"), self.loc.text("Restore 1 changed setting to default?"))
        elif settings_changed_num > 1:
            allowed_reset = messagebox.askquestion(self.loc.text("Restore defaults"), self.loc.text("Restore {0} changed settings to defaults?").format(settings_changed_num))

        if allowed_reset == "yes":
            need_to_reload = self.language.get() != 'English'

            self.sentry_level.set(settings.get_setting_default('sentry_level'))
            self.wait_time.set(settings.get_setting_default('wait_time'))
            self.wait_time_slow.set(settings.get_setting_default('wait_time_slow'))
            self.map_invalidation_hours.set(settings.get_setting_default('map_invalidation_hours'))
            self.check_updates.set(settings.get_setting_default('check_updates'))
            self.request_timeout.set(settings.get_setting_default('request_timeout'))
            self.hide_queued_gamemode.set(settings.get_setting_default('hide_queued_gamemode'))
            self.log_level.set(settings.get_setting_default('log_level'))
            self.console_scan_kb.set(settings.get_setting_default('console_scan_kb'))
            self.class_pic_type.set(settings.get_setting_default('class_pic_type'))
            self.language.set(settings.get_setting_default('language'))
            self.second_line.set(settings.get_setting_default('second_line'))
            self.trim_console_log.set(settings.get_setting_default('trim_console_log'))
            self.server_rate_limit.set(settings.get_setting_default('server_rate_limit'))

            # make options account for localization (same as in __init__)
            self.log_level.set(self.log_levels_display[self.log_levels.index(self.log_level.get())])
            self.sentry_level.set(self.sentry_levels_display[self.sentry_levels.index(self.sentry_level.get())])
            self.class_pic_type.set(self.class_pic_types_display[self.class_pic_types.index(self.class_pic_type.get())])
            self.language.set(self.languages_display[self.languages.index(self.language.get())])
            self.second_line.set(self.second_lines_display[self.second_lines.index(self.second_line.get())])

            self.log.debug("Restored defaults")

            try:
                self.restore_button.state(['disabled'])
            except (NameError, AttributeError):
                self.log.error("Restore button doesn't exist yet")

            if need_to_reload:
                self.update_language('English')

    # saves settings to file and closes window
    def save_and_close(self):
        # spinboxes can be set to blank, so if the user saves while blank, they try to default or be set to 0
        int_settings = (self.wait_time, self.wait_time_slow, self.map_invalidation_hours, self.request_timeout, self.console_scan_kb, self.server_rate_limit)

        for int_setting in int_settings:
            try:
                int_setting.get()
            except tk.TclError:
                int_setting.set(0)

        settings_to_save = self.get_working_settings()
        settings_changed = settings.compare_settings(self.settings_loaded, settings_to_save)
        self.log.debug(f"Setting(s) changed: {settings_changed}")
        self.log.info("Saving and closing settings menu")
        settings.access_registry(save=settings_to_save)
        self.log.info(f"Settings have been saved as: {settings_to_save}")

        restart_message = ""
        if len(settings_changed) >= 1:
            processes = str(subprocess.check_output('tasklist /fi "STATUS eq running"', creationflags=0x08000000))  # the creation flag disables a cmd window flash
            if 'Launch Rich Presence' in processes or 'Launch TF2 with Rich' in processes:
                restart_message = self.loc.text("TF2 Rich Presence is currently running, so it needs to be restarted for changes to take effect.")

        if len(settings_changed) == 1:
            messagebox.showinfo(self.loc.text("Save and close"), self.loc.text("1 setting has been changed. {0}").format(restart_message))
        elif len(settings_changed) > 1:
            messagebox.showinfo(self.loc.text("Save and close"), self.loc.text("{0} settings have been changed. {1}").format(len(settings_changed), restart_message))

        self.master.destroy()  # closes window

    # closes window without saving
    def close_without_saving(self):
        settings_to_save = self.get_working_settings()
        settings_changed = settings.compare_settings(self.settings_loaded, settings_to_save)
        self.log.debug(f"Setting(s) changed (but not yet saved): {settings_changed}")

        close_question = self.loc.text("Close without saving?")
        settings_changed_num = len(settings_changed)
        allowed_close = "yes"
        if settings_changed_num == 1:
            allowed_close = messagebox.askquestion(self.loc.text("Close without saving"), self.loc.text("1 setting has been changed. {0}").format(close_question))
        elif settings_changed_num > 1:
            allowed_close = messagebox.askquestion(self.loc.text("Close without saving"), self.loc.text("{0} settings have been changed. {1}").format(settings_changed_num, close_question))

        if allowed_close == "yes":
            self.log.info("Closing settings menu without saving")
            self.master.destroy()

    # open the release page in the default browser
    def open_update_page(self):
        webbrowser.open(self.new_version_url)

    # called by atexit
    def window_close_log(self):
        self.log.info("Closing settings window")


# main entry point
def launch():
    gc.disable()
    root = tk.Tk()
    settings_gui = GUI(root)
    settings_gui.mainloop()


# checks if a string is an integer between 0 and a supplied maximum (blank is allowed, will get set to default when saving)
def check_int(text_in_entry: str) -> bool:
    if text_in_entry == '':
        return True

    if text_in_entry.isdigit() and int(text_in_entry) >= 0:
        return True

    return False


if __name__ == '__main__':
    launch()
