# Copyright (C) 2018-2022 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE
# cython: language_level=3

import tkinter as tk
import tkinter.ttk as ttk
import traceback
from tkinter import messagebox
from typing import Any, Dict, List, Optional, Tuple, Union

import gui
import launcher
import localization
import logger
import settings


class GUI(tk.Frame):
    def __init__(self, master: tk.Toplevel, log: logger.Log, position: Optional[tuple] = None, reload_settings: Optional[tuple] = None):
        self.log: logger.Log = log
        self.log.info(f"Opening settings menu for TF2 Rich Presence {launcher.VERSION}")
        self.gui_language: Optional[str] = localization.langs[localization.langs.index(reload_settings[8].get())] if reload_settings else None
        self.loc: localization.Localizer = localization.Localizer(self.log, self.gui_language if self.gui_language else settings.get('language'))

        self.log_levels: Tuple[str, ...] = ('Debug', 'Info', 'Error', 'Critical', 'Off')
        self.sentry_levels: Tuple[str, ...] = ('All errors', 'Crashes', 'Never')
        self.rpc_lines: Tuple[str, ...] = ('Server name', 'Player count', 'Time on map', 'Kills', 'Class', 'Map')

        self.log_levels_display: List[str] = [self.loc.text(item) for item in self.log_levels]
        self.sentry_levels_display: List[str] = [self.loc.text(item) for item in self.sentry_levels]
        self.rpc_lines_display: List[str] = [self.loc.text(item) for item in self.rpc_lines]

        if reload_settings:
            # the GUI was reloaded with a new language, so persist the currently selected (but not saved) settings
            self.sentry_level, self.wait_time, self.wait_time_slow, self.check_updates, self.request_timeout, self.hide_queued_gamemode, self.log_level, self.console_scan_kb, \
            self.language, self.top_line, self.bottom_line, self.trim_console_log, self.server_rate_limit, self.gui_scale, self.drawing_gamemodes, self.preserve_window_pos = reload_settings
        else:
            # create every setting variable without values
            self.sentry_level: tk.StringVar = tk.StringVar()
            self.wait_time: tk.IntVar = tk.IntVar()
            self.wait_time_slow: tk.IntVar = tk.IntVar()
            self.check_updates: tk.BooleanVar = tk.BooleanVar()
            self.request_timeout: tk.IntVar = tk.IntVar()
            self.hide_queued_gamemode: tk.BooleanVar = tk.BooleanVar()
            self.log_level: tk.StringVar = tk.StringVar()
            self.console_scan_kb: tk.IntVar = tk.IntVar()
            self.language: tk.StringVar = tk.StringVar()
            self.top_line: tk.StringVar = tk.StringVar()
            self.bottom_line: tk.StringVar = tk.StringVar()
            self.trim_console_log: tk.BooleanVar = tk.BooleanVar()
            self.server_rate_limit: tk.IntVar = tk.IntVar()
            self.gui_scale: tk.IntVar = tk.IntVar()
            self.drawing_gamemodes: tk.BooleanVar = tk.BooleanVar()
            self.preserve_window_pos: tk.BooleanVar = tk.BooleanVar()

            try:
                # load settings from registry
                settings.fix_settings(self.log)
                self.settings_loaded: dict = settings.access_registry()
                self.log.debug(f"Current settings: {self.settings_loaded}")
                self.log.debug(f"Are default: {self.settings_loaded == settings.defaults()}")

                self.sentry_level.set(self.settings_loaded['sentry_level'])
                self.wait_time.set(self.settings_loaded['wait_time'])
                self.wait_time_slow.set(self.settings_loaded['wait_time_slow'])
                self.check_updates.set(self.settings_loaded['check_updates'])
                self.request_timeout.set(self.settings_loaded['request_timeout'])
                self.hide_queued_gamemode.set(self.settings_loaded['hide_queued_gamemode'])
                self.log_level.set(self.settings_loaded['log_level'])
                self.console_scan_kb.set(self.settings_loaded['console_scan_kb'])
                self.language.set(self.gui_language if self.gui_language else self.settings_loaded['language'])
                self.top_line.set(self.settings_loaded['top_line'])
                self.bottom_line.set(self.settings_loaded['bottom_line'])
                self.trim_console_log.set(self.settings_loaded['trim_console_log'])
                self.server_rate_limit.set(self.settings_loaded['server_rate_limit'])
                self.gui_scale.set(self.settings_loaded['gui_scale'])
                self.drawing_gamemodes.set(self.settings_loaded['drawing_gamemodes'])
                self.preserve_window_pos.set(self.settings_loaded['preserve_window_pos'])
            except Exception:
                # probably a json decode error
                formatted_exception: str = traceback.format_exc()
                self.log.error(f"Error in loading settings, defaulting: \n{formatted_exception}")
                messagebox.showerror(self.loc.text("Error"), self.loc.text("Couldn't load settings, reverting to defaults.{0}").format(f'\n\n{formatted_exception}'))

                self.restore_defaults()
                self.settings_loaded: dict = settings.defaults()

        # account for localization
        self.localization_compensate()
        actual_language: str = self.language.get()
        actual_top_line: str = self.top_line.get()
        actual_bottom_line: str = self.bottom_line.get()

        # actually create the settings window fairly late to reduce time with a tiny window visible
        self.master: Union[tk.Toplevel, tk.Tk] = master
        tk.Frame.__init__(self, self.master)
        if position:
            gui.pos_window_by_center(self.master, *position)
        check_int_command: str = self.register(check_int)
        self.master.protocol('WM_DELETE_WINDOW', self.close_window)
        self.master.title(self.loc.text("TF2 Rich Presence ({0}) settings").format(launcher.VERSION))
        self.master.resizable(False, False)  # disables resizing
        gui.set_window_icon(self.log, self.master, True)
        if not reload_settings:
            self.window_x: Optional[int] = None
            self.window_y: Optional[int] = None

        # create label frames
        self.lf_main: ttk.Labelframe = ttk.Labelframe(self.master, text=self.loc.text("Main"))
        self.lf_advanced: ttk.Labelframe = ttk.Labelframe(self.master, text=self.loc.text("Advanced"))

        # create settings widgets
        setting1_frame = ttk.Frame(self.lf_advanced)
        setting1_text = ttk.Label(setting1_frame, text="{}".format(
            self.loc.text("Log reporting frequency: ")))
        setting1_radiobuttons = []
        for sentry_level_text in self.sentry_levels_display:
            setting1_radiobuttons.append(ttk.Radiobutton(setting1_frame, variable=self.sentry_level, text=sentry_level_text, value=sentry_level_text, command=self.setting_changed))
        setting3_frame = ttk.Frame(self.lf_main)
        setting3_text = ttk.Label(setting3_frame, text="{}".format(
            self.loc.text("Delay between refreshes, in seconds: ")))
        setting3_option = ttk.Spinbox(setting3_frame, textvariable=self.wait_time, width=6, from_=0, to=float('inf'), validate='all', validatecommand=(check_int_command, '%P'),
                                      command=self.setting_changed)
        setting5 = ttk.Checkbutton(self.lf_main, variable=self.check_updates, command=self.setting_changed, text="{}".format(
            self.loc.text("Check for program updates when launching")))
        setting6_frame = ttk.Frame(self.lf_advanced)
        setting6_text = ttk.Label(setting6_frame, text="{}".format(
            self.loc.text("Internet connection timeout (for updater and server querying): ")))
        setting6_option = ttk.Spinbox(setting6_frame, textvariable=self.request_timeout, width=6, from_=0, to=float('inf'), validate='all', validatecommand=(check_int_command, '%P'),
                                      command=self.setting_changed)
        setting8 = ttk.Checkbutton(self.lf_main, variable=self.hide_queued_gamemode, command=self.setting_changed, text="{}".format(
            self.loc.text("Hide game type (Casual, Comp, MvM) queued for")))
        setting9_frame = ttk.Frame(self.lf_advanced)
        setting9_text = ttk.Label(setting9_frame, text="{}".format(
            self.loc.text("Max log level: ")))
        setting9_radiobuttons = []
        for log_level_text in self.log_levels_display:
            setting9_radiobuttons.append(ttk.Radiobutton(setting9_frame, variable=self.log_level, text=log_level_text, value=log_level_text, command=self.setting_changed))
        setting10_frame = ttk.Frame(self.lf_advanced)
        setting10_text = ttk.Label(setting10_frame, text="{}".format(
            self.loc.text("Max kilobytes of console.log to scan: ")))
        setting10_option = ttk.Spinbox(setting10_frame, textvariable=self.console_scan_kb, width=8, from_=0, to=float('inf'), validate='all', validatecommand=(check_int_command, '%P'),
                                       command=self.setting_changed)
        setting13_frame = ttk.Frame(self.lf_main)
        setting13_text = ttk.Label(setting13_frame, text="{}".format(
            self.loc.text("Language: ")))
        setting13_options = ttk.OptionMenu(setting13_frame, self.language, localization.langs[0], *localization.langs_localized, command=self.update_language)
        setting14_frame = ttk.Frame(self.lf_main)
        setting14_text = ttk.Label(setting14_frame, text="{}".format(
            self.loc.text("Bottom line: ")))
        setting14_radiobuttons = []
        for rpc_line_text in self.rpc_lines_display:
            setting14_radiobuttons.append(ttk.Radiobutton(setting14_frame, variable=self.bottom_line, text=rpc_line_text, value=rpc_line_text, command=self.setting_changed))
        setting15 = ttk.Checkbutton(self.lf_advanced, variable=self.trim_console_log, command=self.setting_changed, text="{}".format(
            self.loc.text("Occasionally limit console.log's size and remove empty lines and common errors")))
        setting16_frame = ttk.Frame(self.lf_main)
        setting16_text = ttk.Label(setting16_frame, text="{}".format(
            self.loc.text("Delay between refreshes when TF2 and Discord aren't running: ")))  # and Steam but whatever
        setting16_option = ttk.Spinbox(setting16_frame, textvariable=self.wait_time_slow, width=6, from_=0, to=float('inf'), validate='all', validatecommand=(check_int_command, '%P'),
                                       command=self.setting_changed)
        setting17_frame = ttk.Frame(self.lf_advanced)
        setting17_text = ttk.Label(setting17_frame, text="{}".format(
            self.loc.text("Server querying rate limit: ")))
        setting17_option = ttk.Spinbox(setting17_frame, textvariable=self.server_rate_limit, width=6, from_=0, to=float('inf'), validate='all', validatecommand=(check_int_command, '%P'),
                                       command=self.setting_changed)
        setting18_frame = ttk.Frame(self.lf_main)
        setting18_text = ttk.Label(setting18_frame, text="{}".format(
            self.loc.text("GUI scale: ")))
        setting18_option = tk.Scale(setting18_frame, variable=self.gui_scale, from_=50, to=200, resolution=5, length=150, orient=tk.HORIZONTAL, command=self.setting_changed)
        setting19_frame = ttk.Frame(self.lf_main)
        setting19_text = ttk.Label(setting19_frame, text="{}".format(
            self.loc.text("Top line: ")))
        setting19_radiobuttons = []
        for rpc_line_text in self.rpc_lines_display:
            setting19_radiobuttons.append(ttk.Radiobutton(setting19_frame, variable=self.top_line, text=rpc_line_text, value=rpc_line_text, command=self.setting_changed))
        setting20 = ttk.Checkbutton(self.lf_main, variable=self.drawing_gamemodes, command=self.setting_changed, text="{}".format(
            self.loc.text("Use classic gamemode images in the GUI")))
        setting21 = ttk.Checkbutton(self.lf_main, variable=self.preserve_window_pos, command=self.setting_changed, text="{}".format(
            self.loc.text("Remember previous window position")))

        # more localization compensation
        self.language.set(actual_language)
        self.top_line.set(actual_top_line)
        self.bottom_line.set(actual_bottom_line)

        # prepare widgets to be added
        setting1_text.pack(side='left', fill='none', expand=False)
        for setting1_radiobutton in setting1_radiobuttons:
            setting1_radiobutton.pack(side='left', fill='none', expand=False, padx=(0, 5))
        setting3_text.pack(side='left', fill='none', expand=False)
        setting3_option.pack(side='left', fill='none', expand=False)
        setting6_text.pack(side='left', fill='none', expand=False)
        setting6_option.pack(side='left', fill='none', expand=False)
        setting9_text.pack(side='left', fill='none', expand=False)
        for setting9_radiobutton in setting9_radiobuttons:
            setting9_radiobutton.pack(side='left', fill='none', expand=False, padx=(0, 5))
        setting10_text.pack(side='left', fill='none', expand=False)
        setting10_option.pack(side='left', fill='none', expand=False)
        setting13_text.pack(side='left', fill='none', expand=False)
        setting13_options.pack(side='left', fill='none', expand=False)
        setting14_text.pack(side='left', fill='none', expand=False)
        for setting14_radiobutton in setting14_radiobuttons:
            setting14_radiobutton.pack(side='left', fill='none', expand=False, padx=(0, 5))
        setting16_text.pack(side='left', fill='none', expand=False)
        setting16_option.pack(side='left', fill='none', expand=False)
        setting17_text.pack(side='left', fill='none', expand=False)
        setting17_option.pack(side='left', fill='none', expand=False)
        setting18_text.pack(side='left', fill='none', expand=False)
        setting18_option.pack(side='left', padx=5)
        setting19_text.pack(side='left', fill='none', expand=False)
        for setting19_radiobutton in setting19_radiobuttons:
            setting19_radiobutton.pack(side='left', fill='none', expand=False, padx=(0, 5))

        # add widgets to the labelframes and main window
        setting13_frame.grid(row=0, columnspan=2, sticky=tk.W, padx=(20, 40), pady=(9, 0))
        setting3_frame.grid(row=1, columnspan=2, sticky=tk.W, padx=(20, 40), pady=(3, 0))
        setting16_frame.grid(row=2, columnspan=2, sticky=tk.W, padx=(20, 40), pady=(3, 0))
        setting19_frame.grid(row=3, columnspan=2, sticky=tk.W, padx=(20, 40), pady=(3, 0))
        setting14_frame.grid(row=4, columnspan=2, sticky=tk.W, padx=(20, 40), pady=(3, 0))
        setting18_frame.grid(row=5, columnspan=2, sticky=tk.W, padx=(20, 40), pady=(0, 0))
        setting10_frame.grid(row=6, columnspan=2, sticky=tk.W, padx=(20, 40), pady=(11, 0))
        setting20.grid(row=7, sticky=tk.W, columnspan=2, padx=(20, 40), pady=(4, 0))
        setting8.grid(row=8, sticky=tk.W, columnspan=2, padx=(20, 40), pady=(4, 0))
        setting21.grid(row=9, sticky=tk.W, columnspan=2, padx=(20, 40), pady=(4, 0))
        setting15.grid(row=10, sticky=tk.W, columnspan=2, padx=(20, 40), pady=(4, 0))
        setting5.grid(row=11, sticky=tk.W, columnspan=2, padx=(20, 40), pady=(4, 10))
        setting6_frame.grid(row=12, columnspan=2, sticky=tk.W, padx=(20, 40), pady=(4, 0))
        setting17_frame.grid(row=13, columnspan=2, sticky=tk.W, padx=(20, 40), pady=(3, 0))
        setting1_frame.grid(row=14, columnspan=2, sticky=tk.W, padx=(20, 40), pady=(4, 0))
        setting9_frame.grid(row=15, columnspan=2, sticky=tk.W, padx=(20, 40), pady=(4, 10))

        self.lf_main.grid(row=0, padx=30, pady=15, sticky=tk.W + tk.E)
        self.lf_advanced.grid(row=1, padx=30, pady=0, sticky=tk.W + tk.E)

        self.buttons_frame = ttk.Frame(self.master)
        self.restore_button = ttk.Button(self.buttons_frame, text=self.loc.text("Restore defaults"), command=self.restore_defaults)
        self.restore_button.grid(row=0, column=1, padx=(10, 0), pady=(20, 20))
        cancel_button = ttk.Button(self.buttons_frame, text=self.loc.text("Close without saving"), command=self.close_without_saving)
        cancel_button.grid(row=0, column=2, padx=10, pady=(20, 20))
        self.ok_button = ttk.Button(self.buttons_frame, text=self.loc.text("Save and close"), command=self.save_and_close, default=tk.ACTIVE)
        self.ok_button.grid(row=0, column=3, sticky=tk.W, padx=0, pady=(20, 20))
        self.buttons_frame.grid(row=100, columnspan=3)

        self.defaults_button_enabled: bool = True
        self.setting_changed()
        self.master.update()
        self.window_dimensions = self.master.winfo_width(), self.master.winfo_height()
        self.log.debug(f"Window size: {self.window_dimensions}")
        self.master.focus_force()
        self.master.grab_set()
        if position:
            gui.pos_window_by_center(self.master, *position)

    def __repr__(self) -> str:
        return f"settings.GUI {self.window_dimensions}"

    # runs every time a setting is changed
    def setting_changed(self, changed: Optional[Any] = None):
        if changed is None:  # jank but improves performance
            self.fix_blank_spinboxes()

        # updates "restore defaults" button's state
        if self.get_working_settings() == settings.defaults() and self.defaults_button_enabled:
            self.restore_button.state(['disabled'])
            self.defaults_button_enabled = False
            self.log.debug("Disabled restore defaults button")
        elif not self.defaults_button_enabled:
            self.restore_button.state(['!disabled'])
            self.defaults_button_enabled = True
            self.log.debug("Enabled restore defaults button")

    # runs every time the language setting is changed
    def update_language(self, language_selected: str):
        language_selected_normal: str = localization.langs[localization.langs_localized.index(language_selected)]

        if language_selected_normal != self.gui_language:
            self.log.debug(f"Reloading settings menu with language {language_selected_normal}")
            self.lf_main.destroy()
            self.lf_advanced.destroy()
            self.buttons_frame.destroy()

            # normalize some settings to english so that the reload will be converted back
            self.log_level.set(self.log_levels[self.log_levels_display.index(self.log_level.get())])
            self.sentry_level.set(self.sentry_levels[self.sentry_levels_display.index(self.sentry_level.get())])
            self.language.set(localization.langs[localization.langs_localized.index(self.language.get())])
            self.top_line.set(self.rpc_lines[self.rpc_lines_display.index(self.top_line.get())])
            self.bottom_line.set(self.rpc_lines[self.rpc_lines_display.index(self.bottom_line.get())])

            selected_settings: tuple = (self.sentry_level, self.wait_time, self.wait_time_slow, self.check_updates, self.request_timeout, self.hide_queued_gamemode, self.log_level,
                                        self.console_scan_kb, self.language, self.top_line, self.bottom_line, self.trim_console_log, self.server_rate_limit, self.gui_scale,
                                        self.drawing_gamemodes, self.preserve_window_pos)
            self.window_x = self.master.winfo_rootx() - 8
            self.window_y = self.master.winfo_rooty() - 31
            self.__init__(self.master, self.log, reload_settings=selected_settings)

    # return the settings as a dict, as they currently are in the GUI
    def get_working_settings(self) -> Dict[str, str]:
        return {'sentry_level': self.sentry_levels[self.sentry_levels_display.index(self.sentry_level.get())],
                'wait_time': self.wait_time.get(),
                'wait_time_slow': self.wait_time_slow.get(),
                'check_updates': self.check_updates.get(),
                'request_timeout': max(self.request_timeout.get(), 1),
                'hide_queued_gamemode': self.hide_queued_gamemode.get(),
                'log_level': self.log_levels[self.log_levels_display.index(self.log_level.get())],
                'console_scan_kb': self.console_scan_kb.get(),
                'language': localization.langs[localization.langs_localized.index(self.language.get())],
                'top_line': self.rpc_lines[self.rpc_lines_display.index(self.top_line.get())],
                'bottom_line': self.rpc_lines[self.rpc_lines_display.index(self.bottom_line.get())],
                'trim_console_log': self.trim_console_log.get(),
                'server_rate_limit': self.server_rate_limit.get(),
                'gui_scale': self.gui_scale.get(),
                'drawing_gamemodes': self.drawing_gamemodes.get(),
                'preserve_window_pos': self.preserve_window_pos.get()}

    # set all settings to defaults
    def restore_defaults(self):
        settings_to_save: Dict[str, str] = self.get_working_settings()
        settings_changed: dict = {k: settings_to_save[k] for k in settings_to_save if k in self.settings_loaded and settings_to_save[k] != self.settings_loaded[k]}  # haha what

        settings_changed_num: int = len(settings_changed)
        allowed_reset: str = "yes"
        if settings_changed_num == 1:
            allowed_reset = messagebox.askquestion(self.loc.text("Restore defaults"), self.loc.text("Restore 1 changed setting to default?"))
        elif settings_changed_num > 1:
            allowed_reset = messagebox.askquestion(self.loc.text("Restore defaults"), self.loc.text("Restore {0} changed settings to defaults?").format(settings_changed_num))

        if allowed_reset == "yes":
            need_to_reload: bool = self.language.get() != 'English'

            self.sentry_level.set(settings.get_setting_default('sentry_level'))
            self.wait_time.set(settings.get_setting_default('wait_time'))
            self.wait_time_slow.set(settings.get_setting_default('wait_time_slow'))
            self.check_updates.set(settings.get_setting_default('check_updates'))
            self.request_timeout.set(settings.get_setting_default('request_timeout'))
            self.hide_queued_gamemode.set(settings.get_setting_default('hide_queued_gamemode'))
            self.log_level.set(settings.get_setting_default('log_level'))
            self.console_scan_kb.set(settings.get_setting_default('console_scan_kb'))
            self.language.set(settings.get_setting_default('language'))
            self.top_line.set(settings.get_setting_default('top_line'))
            self.bottom_line.set(settings.get_setting_default('bottom_line'))
            self.trim_console_log.set(settings.get_setting_default('trim_console_log'))
            self.server_rate_limit.set(settings.get_setting_default('server_rate_limit'))
            self.gui_scale.set(settings.get_setting_default('gui_scale'))
            self.drawing_gamemodes.set(settings.get_setting_default('drawing_gamemodes'))

            self.localization_compensate()
            self.log.debug("Restored defaults")

            try:
                self.restore_button.state(['disabled'])
            except (NameError, AttributeError):
                self.log.error("Restore button doesn't exist yet")

            if need_to_reload:
                self.update_language('English')

    # saves settings to file and closes window
    def save_and_close(self, force: bool = False):
        # TODO: update GUI scale immediately if possible (and anything else if needed)
        self.fix_blank_spinboxes()
        settings_to_save: Dict[str, str] = self.get_working_settings()
        settings_changed = settings.compare_settings(self.settings_loaded, settings_to_save)
        self.log.debug(f"Setting(s) changed: {settings_changed}")
        self.log.info("Saving and closing settings menu")
        settings.access_registry(save=settings_to_save)
        self.log.info(f"Settings have been saved as: {settings_to_save}")

        if not force:
            if 'gui_scale' in settings_changed:
                messagebox.showinfo(self.loc.text("TF2 Rich Presence"), self.loc.text("Changing GUI scale requires a restart to take effect."))
            if 'language' in settings_changed:
                messagebox.showinfo(self.loc.text("TF2 Rich Presence"), self.loc.text("Changing language requires a restart to take effect."))

        self.master.destroy()  # closes window

    # closes window without saving
    def close_without_saving(self):
        self.log.info("Closing settings menu without saving")
        self.master.destroy()

    # a spinbox can be set to blank, so set it to defualt in that case
    def fix_blank_spinboxes(self):
        int_settings: tuple = (self.wait_time, self.wait_time_slow, self.request_timeout, self.console_scan_kb, self.server_rate_limit)
        int_settings_str: Tuple[str, ...] = ('wait_time', 'wait_time_slow', 'request_timeout', 'console_scan_kb', 'server_rate_limit')

        for int_setting in int_settings:
            try:
                int_setting.get()
            except tk.TclError:
                int_setting_str: str = int_settings_str[int_settings.index(int_setting)]
                default_value: int = settings.get_setting_default(int_setting_str)
                self.log.debug(f"Set {int_setting_str} from blank to default ({default_value})")
                int_setting.set(default_value)

    # make dropdown options account for localization (very ugly)
    def localization_compensate(self):
        self.log_level.set(self.log_levels_display[self.log_levels.index(self.log_level.get())])
        self.sentry_level.set(self.sentry_levels_display[self.sentry_levels.index(self.sentry_level.get())])
        self.language.set(localization.langs_localized[localization.langs.index(self.language.get())])
        self.bottom_line.set(self.rpc_lines_display[self.rpc_lines.index(self.bottom_line.get())])
        self.top_line.set(self.rpc_lines_display[self.rpc_lines.index(self.top_line.get())])

    def close_window(self):
        self.log.info("Closing settings window")
        self.master.destroy()


# main entry point
def launch():
    settings_gui = GUI(tk.Toplevel(), logger.Log())
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
