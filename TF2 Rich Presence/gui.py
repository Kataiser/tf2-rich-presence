# Copyright (C) 2021 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE
# cython: language_level=3

import datetime
import functools
import os
import subprocess
import tkinter as tk
import tkinter.ttk as ttk
import traceback
import webbrowser
from tkinter import messagebox
from typing import Dict, List, Optional, Tuple, Union

from PIL import Image, ImageDraw, ImageFilter, ImageTk

import launcher
import localization
import logger
import settings
import settings_gui
import updater
import utils


class GUI(tk.Frame):
    def __init__(self, log: logger.Log):
        self.log: logger.Log = log
        self.log.info("Initializing main GUI")
        self.loc: localization.Localizer = localization.Localizer(self.log)
        self.master: tk.Tk = tk.Tk()
        tk.Frame.__init__(self, self.master)
        self.pack(fill=tk.BOTH, expand=1, padx=0, pady=0)
        self.alive: bool = True

        self.scale: float = settings.get('gui_scale') / 100
        self.size: Tuple[int, int] = (round(500 * self.scale), round(250 * self.scale))
        self.master.geometry(f'{self.size[0]}x{self.size[1] + 20}')  # the +20 is for the menu bar
        self.master.title(self.loc.text("TF2 Rich Presence").format(launcher.VERSION))
        set_window_icon(self.log, self.master, False)
        self.master.resizable(0, 0)  # disables resizing
        self.master.protocol('WM_DELETE_WINDOW', self.close_window)
        self.log.debug("Set up main window")

        # misc stuff that doesn't go anywhere else
        default_bg: ImageTk.PhotoImage = ImageTk.PhotoImage(Image.new('RGB', self.size))
        font_size: int = round(12 * self.scale)
        self.blank_image: ImageTk.PhotoImage = ImageTk.PhotoImage(Image.new('RGBA', (1, 1), color=(0, 0, 0, 0)))
        self.paused_image: ImageTk.PhotoImage = ImageTk.PhotoImage(Image.new('RGBA', self.size, (0, 0, 0, 128)))
        self.vignette: Image = self.load_image('vignette').resize(self.size)
        self.clean_console_log: bool = False
        self.text_state: Tuple[str, ...] = ('',)
        self.bg_state: Tuple[str, int, int] = ('', 0, 0)
        self.fg_state: str = ''
        self.class_state: str = ''
        self.available_update_data: Tuple[str, str, str] = ('', '', '')
        self.update_window_open: bool = False
        self.bottom_text_state: Dict[str, bool] = {'discord': False, 'kataiser': False, 'queued': False, 'holiday': False}
        self.bottom_text_queue_state: str = ""
        self.holiday_text: str = ""
        self.launched_tf2_with_button: bool = False

        menu_bar: tk.Menu = tk.Menu(self.master)
        self.file_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label=self.loc.text("File"), menu=self.file_menu)
        menu_bar.add_cascade(label=self.loc.text("Help"), menu=help_menu)
        self.file_menu.add_command(label=self.loc.text("Change settings"), command=self.menu_open_settings, accelerator="Ctrl+S")
        self.file_menu.add_command(label=self.loc.text("Restore default settings"), command=self.menu_restore_defaults)
        self.file_menu.add_command(label=self.loc.text("Trim/clean console.log"), command=self.menu_clean_console_log, state=tk.DISABLED)
        self.file_menu.add_command(label=self.loc.text("Exit"), command=self.menu_exit, accelerator="Ctrl+Q")
        help_menu.add_command(label=self.loc.text("Open Github page"), command=self.menu_open_github)
        help_menu.add_command(label=self.loc.text("Open readme"), command=self.menu_open_readme)
        help_menu.add_command(label=self.loc.text("Open changelog"), command=self.menu_open_changelog)
        help_menu.add_command(label=self.loc.text("Open license"), command=self.menu_open_license)
        help_menu.add_separator()
        help_menu.add_command(label=self.loc.text("Check for updates"), command=self.menu_check_updates)
        help_menu.add_command(label=self.loc.text("Report bug/issue"), command=self.menu_report_issue)
        help_menu.add_command(label=self.loc.text("About"), command=self.menu_about, accelerator="Ctrl+A")
        self.master.config(menu=menu_bar)
        self.bind_all('<Control-s>', self.menu_open_settings)
        self.bind_all('<Control-q>', self.menu_exit)
        self.bind_all('<Control-a>', self.menu_about)
        self.log.debug("Created menu bar")

        previous_gui_position: List[int] = utils.access_db()['gui_position']
        if previous_gui_position == [0, 0]:
            # center the window on the screen
            window_x: int = round(self.winfo_screenwidth() / 2)
            window_y: int = round(self.winfo_screenheight() / 2) - 40
            pos_window_by_center(self.master, window_x, window_y)
            self.log.debug(f"Window position: {(window_x, window_y)} (centered)")
        else:
            # remember previous position
            window_x, window_y = previous_gui_position
            pos_window_by_center(self.master, window_x - 8, window_y - 41)
            self.log.debug(f"Window position: {(window_x, window_y)} (remembered)")

        # create the main drawing canvas and its elements
        self.canvas: tk.Canvas = tk.Canvas(width=self.size[0], height=self.size[1], borderwidth=0, highlightthickness=0)
        self.bg_image: int = self.canvas.create_image(0, 0, anchor=tk.NW, image=default_bg)
        self.bg_rect: int = self.canvas.create_image(0, 0, anchor=tk.NW)
        self.fg_shadow: int = self.canvas.create_image(65 * self.scale, 45 * self.scale, anchor=tk.NW)
        self.fg_image: int = self.canvas.create_image(85 * self.scale, 65 * self.scale, anchor=tk.NW)
        self.class_image: int = self.canvas.create_image(90 * self.scale, 180 * self.scale, anchor=tk.CENTER)
        self.text_1: int = self.canvas.create_text(358 * self.scale, 110 * self.scale, font=('TkDefaultFont', font_size), fill='white', anchor=tk.CENTER)
        self.text_3_0: int = self.canvas.create_text(220 * self.scale, 105 * self.scale, font=('TkDefaultFont', font_size), fill='white', anchor=tk.W)
        self.text_3_1: int = self.canvas.create_text(220 * self.scale, 125 * self.scale, font=('TkDefaultFont', font_size), fill='white', anchor=tk.W)
        self.text_3_2: int = self.canvas.create_text(220 * self.scale, 145 * self.scale, font=('TkDefaultFont', font_size), fill='gray', anchor=tk.W)
        self.text_4_0: int = self.canvas.create_text(220 * self.scale, 95 * self.scale, font=('TkDefaultFont', font_size), fill='white', anchor=tk.W)
        self.text_4_1: int = self.canvas.create_text(220 * self.scale, 115 * self.scale, font=('TkDefaultFont', font_size), fill='white', anchor=tk.W)
        self.text_4_2: int = self.canvas.create_text(220 * self.scale, 135 * self.scale, font=('TkDefaultFont', font_size), fill='white', anchor=tk.W)
        self.text_4_3: int = self.canvas.create_text(220 * self.scale, 155 * self.scale, font=('TkDefaultFont', font_size), fill='gray', anchor=tk.W)
        self.update_text: int = self.canvas.create_text(467 * self.scale, 20 * self.scale, font=('TkDefaultFont', font_size), fill='light gray', anchor=tk.E)
        self.update_icon: int = self.canvas.create_image(492 * self.scale, 8 * self.scale, anchor=tk.NE)
        self.paused_overlay: int = self.canvas.create_image(0, 0, anchor=tk.NW)
        self.paused_text: int = self.canvas.create_text(5 * self.scale, 5 * self.scale, font=('TkDefaultFont', round(14 * self.scale)), fill='white', anchor=tk.NW)
        self.bottom_text: int = self.canvas.create_text(2 * self.scale, 248 * self.scale, font=('TkDefaultFont', round(10 * self.scale)), fill='light gray', anchor=tk.SW)
        self.canvas.tag_bind(self.update_text, '<Button-1>', self.show_update_menu)
        self.canvas.tag_bind(self.update_icon, '<Button-1>', self.show_update_menu)
        self.canvas.place(x=0, y=0)
        self.log.debug("Created canvas elements")

        self.launch_tf2_button: tk.Button = tk.Button(self.master, text=self.loc.text("Launch TF2"), font=('TkDefaultFont', round(9 * self.scale)), command=self.launch_tf2)

        self.safe_update()
        self.window_dimensions = self.master.winfo_width(), self.master.winfo_height()
        self.log.debug(f"Window size: {self.window_dimensions} (scale {self.scale})")

        # move window to the top (but don't keep it there)
        self.master.lift()
        self.master.attributes('-topmost', True)
        self.master.after_idle(self.master.attributes, '-topmost', False)
        self.log.debug("Finished creating GUI")

    # update the GUI, without errors when closing the main window
    def safe_update(self):
        try:
            self.update()
            # intentionally no update_idletasks here bceause it doesn't seem to be needed
        except tk.TclError as error:
            if "application has been destroyed" in str(error) or "invalid command name" in str(error):
                pass  # GUI has been closed (is there a better way to handle this?)
            else:
                raise

    # set the BG and line states (1 line, for processes not running)
    def set_state_1(self, bg: str, line: str):
        bg_state: Tuple[str, int, int] = (bg, 0, 0)  # None would be cleaner but I want to keep the same tuple configuration

        if bg_state != self.bg_state:
            self.canvas.itemconfigure(self.bg_image, image=self.bg_image_load(bg))
            self.bg_state = bg_state
            self.log.debug(f"Updated GUI BG state: {bg_state}")

        if line != self.text_state:
            self.clear_text(1)
            self.canvas.itemconfigure(self.text_1, text=line)
            self.text_state = (line,)
            self.log.debug(f"Updated GUI text state: \"{line}\"")

    # set the BG and line states (3 lines, for in menus)
    def set_state_3(self, bg: str, lines: Tuple[str, str, str]):
        bg_state = (bg, 85, 164)

        if bg_state != self.bg_state:
            self.canvas.itemconfigure(self.bg_image, image=self.bg_image_load(bg, (bg_state[1], bg_state[2])))
            self.bg_state = bg_state
            self.log.debug(f"Updated GUI BG state: {bg_state}")

        if lines != self.text_state:
            self.clear_text(3)
            self.canvas.itemconfigure(self.text_3_0, text=lines[0])
            self.canvas.itemconfigure(self.text_3_1, text=lines[1])
            self.canvas.itemconfigure(self.text_3_2, text=lines[2])
            self.text_state = lines
            self.log.debug(f"Updated GUI text state: {lines}")

    # set the BG and line states (4 lines, for in game)
    def set_state_4(self, bg: str, lines: Tuple[str, str, str, str]):
        bg_state = (bg, 77, 172)

        if bg_state != self.bg_state:
            self.canvas.itemconfigure(self.bg_image, image=self.bg_image_load(bg, (bg_state[1], bg_state[2])))
            self.bg_state = bg_state
            self.log.debug(f"Updated GUI BG state: {bg_state}")

        if lines != self.text_state:
            self.clear_text(4)
            self.canvas.itemconfigure(self.text_4_0, text=lines[0])
            self.canvas.itemconfigure(self.text_4_1, text=lines[1])
            self.canvas.itemconfigure(self.text_4_2, text=lines[2])
            self.canvas.itemconfigure(self.text_4_3, text=lines[3])
            self.text_state = lines
            self.log.debug(f"Updated GUI text state: {lines}")

    # set the map/gamemode/queued image
    def set_fg_image(self, image: str):
        if image != self.fg_state:
            if image not in ('tf2_logo', 'casual', 'comp', 'mvm_queued', 'fg_modes/unknown'):
                # drop shadow for square images
                self.canvas.itemconfigure(self.fg_shadow, image=self.fg_image_load('fg_shadow', 160))

            self.canvas.itemconfigure(self.fg_image, image=self.fg_image_load(image, 120))
            self.fg_state = image
            self.log.debug(f"Updated GUI FG image to {image}")

    # set the class icon image, over the FG
    def set_class_image(self, tf2_class: str):
        if tf2_class != "unselected":
            class_path: str = f'classes/{tf2_class.lower()}'

            if class_path != self.class_state:
                self.canvas.itemconfigure(self.class_image, image=self.fg_image_load(class_path, 60))
                self.class_state = class_path
                self.log.debug(f"Updated GUI class image to {class_path}")
        else:
            self.clear_class_image()

    # set the smaller text in the bottom left, uses a priority system
    def set_bottom_text(self, state: str, enabled: bool) -> str:
        prev_text: str = ""
        text: str = ""
        states: dict[str, str] = {'discord': self.loc.text("Can't connect to Discord"),
                                  'kataiser': self.loc.text("Hey, it seems that Kataiser, the developer of TF2 Rich Presence, is in your game!\nSay hi to me if you'd like :)"),
                                  'queued': self.bottom_text_queue_state,
                                  'holiday': self.holiday_text}

        for state_key in states:
            if self.bottom_text_state[state_key]:
                prev_text = states[state_key]
                break

        self.bottom_text_state[state] = enabled

        for state_key in states:
            if self.bottom_text_state[state_key]:
                text = states[state_key]
                break

        if text != prev_text:
            self.log.debug(f"Updated GUI bottom text to \"{text}\" (state: {self.bottom_text_state})")
            self.canvas.itemconfigure(self.bottom_text, text=text)

        return text

    # only show the "clean console.log" menu button if the game is running
    def set_clean_console_log_button_state(self, enabled: bool):
        self.file_menu.entryconfigure(2, state=tk.ACTIVE if enabled else tk.DISABLED)

    # only show the "launch TF2" button if Steam is running and the game is not
    def set_launch_tf2_button_state(self, enabled: bool):
        if enabled:
            self.launch_tf2_button['state'] = 'normal'
            self.launch_tf2_button['text'] = self.loc.text("Launch TF2")
            self.launch_tf2_button.place(x=358 * self.scale, y=142 * self.scale, width=round(102 * self.scale), height=round(26 * self.scale), anchor=tk.CENTER)
            self.launched_tf2_with_button = False
        else:
            self.launch_tf2_button.place_forget()

    # clears any text that isn't blank, set dont_clear to avoid clearing text that will be overwritten anyway
    def clear_text(self, dont_clear: int):
        if len(self.text_state) == 1 and dont_clear != 1:
            self.canvas.itemconfigure(self.text_1, text="")
            self.log.debug("Cleared GUI text_1")
        elif len(self.text_state) == 3 and dont_clear != 3:
            self.canvas.itemconfigure(self.text_3_0, text="")
            self.canvas.itemconfigure(self.text_3_1, text="")
            self.canvas.itemconfigure(self.text_3_2, text="")
            self.log.debug("Cleared GUI text_3")
        elif len(self.text_state) == 4 and dont_clear != 4:
            self.canvas.itemconfigure(self.text_4_0, text="")
            self.canvas.itemconfigure(self.text_4_1, text="")
            self.canvas.itemconfigure(self.text_4_2, text="")
            self.canvas.itemconfigure(self.text_4_3, text="")
            self.log.debug("Cleared GUI text_4")

    def clear_fg_image(self):
        if self.fg_state != '':
            self.canvas.itemconfigure(self.fg_image, image=self.blank_image)
            self.canvas.itemconfigure(self.fg_shadow, image=self.blank_image)
            self.fg_state = ''
            self.log.debug("Cleared GUI FG image")

    def clear_class_image(self):
        if self.class_state != '':
            self.canvas.itemconfigure(self.class_image, image=self.blank_image)
            self.class_state = ''
            self.log.debug("Cleared GUI class image")

    # show a pause overlay when a messagebox or something stops the main loop
    def pause(self):
        self.canvas.itemconfigure(self.paused_overlay, image=self.paused_image)
        self.canvas.itemconfigure(self.paused_text, text="PAUSED")
        self.log.debug("Enabled paused overlay")

    def unpause(self):
        self.canvas.itemconfigure(self.paused_overlay, image=self.blank_image)
        self.canvas.itemconfigure(self.paused_text, text="")
        self.log.debug("Disabled paused overlay")

    # show the available update text and icon, no need to disable them once enabled
    def enable_update_notification(self):
        self.canvas.itemconfigure(self.update_text, text=self.loc.text("{0} update available  ").format(self.available_update_data[0]))  # the extra spaces are intentional
        self.canvas.itemconfigure(self.update_icon, image=self.fg_image_load('dl_icon', 25))

    # create and show the available update window
    def show_update_menu(self, *args):
        if not self.update_window_open:
            self.log.debug("Opening available update menu")
            self.update_window_open = True
            newest_version, downloads_url, changelog = self.available_update_data
            window_text = (self.loc.text("This version ({0}) is out of date (newest version is {1}).").format(launcher.VERSION, newest_version), '\n',
                           self.loc.text("{0} changelog:").format(newest_version),
                           changelog,
                           self.loc.text("(If you're more than one version out of date, there may have been more changes and fixes than this.)"), '\n',
                           self.loc.text("Would you like to open the download page?"))

            # this bit is kinda ugly
            update_window: tk.Toplevel = tk.Toplevel()
            update_window.title(self.loc.text("TF2 Rich Presence"))
            set_window_icon(self.log, update_window, False)
            update_window.resizable(0, 0)
            ttk.Label(update_window, text='\n'.join(window_text)).grid(row=0, column=0, padx=40, pady=20)
            button_frame: ttk.Frame = ttk.Frame(update_window)  # why does this need to exist
            yes_button: ttk.Button = ttk.Button(button_frame, text=self.loc.text("Yes"), command=functools.partial(self.update_menu_yes, update_window, downloads_url), default=tk.ACTIVE)
            no_button: ttk.Button = ttk.Button(button_frame, text=self.loc.text("No"), command=functools.partial(self.update_menu_no, update_window))
            yes_button.grid(row=0, column=0, padx=5)
            no_button.grid(row=0, column=1, padx=5, sticky=tk.W)
            button_frame.grid(row=1, column=0, pady=(0, 15))
            update_window.update()
            pos_window_by_center(update_window, *get_window_center(self.master))
            update_window.focus_force()
            update_window.grab_set()
            update_window.protocol('WM_DELETE_WINDOW', functools.partial(self.update_menu_no, update_window))  # closing the window counts as a no

    # if the user says yes to the update window
    def update_menu_yes(self, window: tk.Toplevel, url: str):
        self.log.debug("Opening download page")
        webbrowser.open(url)
        window.destroy()
        self.update_window_open = False

    def update_menu_no(self, window: tk.Toplevel):
        window.destroy()
        self.log.debug("Didn't open download page")
        self.update_window_open = False

    # this is here instead of main because it's hard to reach main.TF2RichPresense from the check for updates menu method, kinda dumb though
    def check_for_updates(self, popup: bool):
        update_data: Optional[Tuple[str, str, str]] = updater.check_for_update(self.log, launcher.VERSION, float(settings.get('request_timeout')))

        if update_data:
            self.available_update_data = update_data
            self.enable_update_notification()

            if popup:
                self.show_update_menu()
        elif popup:
            self.pause()
            messagebox.showinfo(self.loc.text("TF2 Rich Presence"), self.loc.text("No update available, this version ({0}) is the latest version available.").format(launcher.VERSION))
            self.unpause()

    # alerts the user that they don't seem to have -condebug
    def no_condebug_warning(self, tf2_is_running: bool = True):
        warning: List[str] = [self.loc.text("Your TF2 installation doesn't yet seem to be set up properly. To fix:"), '\n',
                              self.loc.text("1. Right click on Team Fortress 2 in your Steam library"),
                              self.loc.text("2. Open properties (very bottom)"),
                              self.loc.text("3. Click \"Set launch options...\""),
                              self.loc.text("4. Add {0}").format("-condebug"),
                              self.loc.text("5. OK and Close")]

        if tf2_is_running:
            warning.append(self.loc.text("6. Restart TF2"))

        self.pause()
        user_retried: bool = messagebox.askretrycancel("TF2 Rich Presence", '\n'.join(warning))

        if user_retried:
            self.unpause()
        else:
            self.close_window()

    # start the game with guaranteed -condebug
    def launch_tf2(self):
        self.log.info("GUI: Launching TF2")
        self.launch_tf2_button['state'] = 'disabled'
        self.launch_tf2_button['text'] = self.loc.text("Launching...")
        self.safe_update()
        self.launched_tf2_with_button = True
        subprocess.run('cmd /c start steam://run/440//-condebug')

    # load a .webp image from gui_images, mode can be RGBA or RGB. image_name shouldn't have the file extension and can have forward slashes
    @functools.cache
    def load_image(self, image_name: str, mode: str = 'RGBA') -> Image:
        images_path: str = 'gui_images' if launcher.DEBUG else os.path.join('resources', 'gui_images')
        image_name_fixed: str = image_name.replace('/', os.path.sep)
        image_path: str = os.path.join(images_path, f'{image_name_fixed}.webp')

        if os.path.isfile(image_path):
            image_loaded: Image = Image.open(image_path)

            if image_loaded.mode != mode:
                image_loaded = image_loaded.convert(mode)

            self.log.debug(f"Loaded GUI image from {image_path} (mode={mode})")
            return image_loaded
        else:
            self.log.error(f"Couldn't find GUI image \"{image_name}\"")
            return Image.new(mode=mode, size=self.size)

    # load and process (scale, blur, vignette, draw rectangle) a background image
    @functools.cache
    def bg_image_load(self, image_name: str, rect_coords: Optional[Tuple[int, int]] = None) -> ImageTk.PhotoImage:
        self.log.debug(f"Loading BG image \"{image_name}\", rect_coords={rect_coords}")
        image: Image = self.load_image(image_name, 'RGB')

        if image.size != self.size:
            image = image.resize(self.size)

        if image_name == 'default':  # don't blur, adjust vignette center
            image.paste(self.vignette, (round(-50 * self.scale), 0), mask=self.vignette)
        else:
            image = image.filter(ImageFilter.GaussianBlur(10 * self.scale))
            image.paste(self.vignette, (0, 0), mask=self.vignette)

        if rect_coords:
            image_draw: ImageDraw.Draw = ImageDraw.Draw(image, 'RGBA')
            image_draw.rectangle((0, rect_coords[0] * self.scale, 500 * self.scale, rect_coords[1] * self.scale), fill=(0, 0, 0, 192))

        self.log.debug("Loading/processing BG image done")
        return ImageTk.PhotoImage(image)

    # assumes square image, also loads TF2 class and anything else if needed
    @functools.cache
    def fg_image_load(self, image_name: str, size: int) -> ImageTk.PhotoImage:
        if 'fg_maps' in image_name or ('fg_modes' in image_name and 'unknown' not in image_name):
            mode = 'RGB'
        else:
            mode = 'RGBA'

        return ImageTk.PhotoImage(self.load_image(image_name, mode).resize((round(size * self.scale), round(size * self.scale))))

    def menu_open_settings(self, *args):
        self.log.info("GUI: Opening settings menu")
        # no need to show pause overlay
        settings_root: tk.Toplevel = tk.Toplevel()
        settings_gui.GUI(settings_root, self.log, position=get_window_center(self.master))
        set_window_icon(self.log, self.master, False)

    def menu_restore_defaults(self, *args):
        self.log.info("GUI: Restoring default settings")
        # TODO: consider sharing code between this and settings GUI restore defaults button
        settings.fix_settings(self.log)
        default_settings: dict = settings.defaults()
        current_settings: dict = settings.access_registry()
        self.pause()

        if current_settings == default_settings:
            self.log.debug("Current settings are default")
            messagebox.showinfo(self.loc.text("Restore defaults"), self.loc.text("Current settings are already default."))
        else:
            changed_settings: dict = {s: current_settings[s] for s in current_settings if current_settings[s] != default_settings[s]}
            self.log.debug(f"Changed settings: {changed_settings}")
            allowed_reset: str = "yes"

            if len(changed_settings) == 1:
                allowed_reset = messagebox.askquestion(self.loc.text("Restore defaults"), self.loc.text("Restore 1 setting to default?"))
            elif len(changed_settings) > 1:
                allowed_reset = messagebox.askquestion(self.loc.text("Restore defaults"), self.loc.text("Restore {0} settings to defaults?").format(len(changed_settings)))

            if allowed_reset == "yes":
                settings.access_registry(save=default_settings)
                self.log.debug("Restored default settings")
            else:
                self.log.debug("Didn't restore default settings")

        self.unpause()

    def menu_clean_console_log(self, *args):
        self.log.info("GUI: Cleaning console.log next loop")
        self.clean_console_log = True  # console_log.py will see this and force a cleanup
        # TODO: do this immediately instead of waiting till next scan

    def menu_exit(self, *args):
        self.log.info("GUI: Exiting")
        self.close_window()

    def menu_open_github(self, *args):
        self.log.info("GUI: Opening Github page")
        webbrowser.open('https://github.com/Kataiser/tf2-rich-presence')

    def menu_open_readme(self, *args):
        self.log.info("GUI: Opening readme")

        try:
            os.startfile('Readme.txt')  # opens in default text editor
        except FileNotFoundError:
            self.log.error("Couldn't open readme, file doesn't exist")

    def menu_open_changelog(self, *args):
        self.log.info("GUI: Opening changelog")

        if os.path.isfile('Changelogs.html'):
            webbrowser.open('Changelogs.html')
        else:
            self.log.error("Couldn't open changelog, file doesn't exist (falling back to Github)")
            webbrowser.open('https://htmlpreview.github.io/?https://github.com/Kataiser/tf2-rich-presence/blob/master/Changelogs.html')

    def menu_open_license(self, *args):
        self.log.info("GUI: Opening license")

        try:
            os.startfile('License.txt')  # opens in default text editor
        except FileNotFoundError:
            self.log.error("Couldn't open license, file doesn't exist (falling back to Github)")
            webbrowser.open('https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE')

    def menu_check_updates(self, *args):
        self.log.info("GUI: checking for updates")
        self.check_for_updates(True)

    def menu_report_issue(self, *args):
        self.log.info("GUI: reporting issue")
        # would be nice if there was a way to auto upload the log file
        webbrowser.open('https://github.com/Kataiser/tf2-rich-presence/issues/new?body=Please%20remember%20to%20add%20your%20most%20recent%20log%20file')

    def menu_about(self, *args, silent: bool = False):
        self.log.info("GUI: opening about window")
        build_info_path: str = os.path.join('resources', 'build_info.txt')
        build_time: str = ""

        if os.path.isfile(build_info_path):
            with open(build_info_path, 'r') as build_info_file:
                build_info_lines: List[str] = build_info_file.readlines()

            for line in build_info_lines:
                if line.startswith("Built at"):
                    build_time: str = line.removeprefix("Built at: ").rstrip('\n')
                    break

        # yeah not gonna localize this
        about: str = f"TF2 Rich Presence {launcher.VERSION}" \
                     f"\nBuilt: {build_time}" \
                     f"\nLicensed under GNU GPLv3, see License.txt" \
                     f"\n\nCredits:" \
                     f"\nKataiser - Lead developer" \
                     f"\nNyanZak and Tobiased - Gamemode SFMs" \
                     f"\nforusu (Mia) - Russian localization improvements" \
                     f"\nhinata_aki - Japanese localization improvements" \
                     f"\nJan200101 - Some cross-platform compatibility" \
                     f"\nYahBoiOven - Testing and feedback" \
                     f"\nThe TF2 Wiki and teamwork.tf - General resources" \
                     f"\nValve - Game graphics" \
                     f"\nAs well as anyone who's ever submitted bug reports"

        self.log.debug(f"Generated about page: {about.splitlines()}")

        if not silent:
            self.pause()
            messagebox.showinfo(self.loc.text("About TF2 Rich Presence"), about)
            self.unpause()

    # cause why not
    def holiday(self):
        now: datetime.datetime = datetime.datetime.now()
        holiday_text: Optional[str] = None

        if now.month == 1 and now.day == 1:
            holiday_text = self.loc.text("Happy New Years!")
        elif now.month == 4 and now.day == 1:
            age: int = now.year - 2018
            ordinal: str = ('th', 'st', 'nd', 'rd', 'th')[min(divmod(age, 10)[1], 4)]  # divmod instead of % because Cython is being mean
            holiday_text = self.loc.text("It's TF2 Rich Presence's {0}{1} birthday today! (Yes, April 1st, seriously)").format(age, ordinal)
        elif now.month == 12 and now.day == 25:
            holiday_text = self.loc.text("Merry Christmas!")

        if holiday_text is not None:
            self.log.info(f"Today is {now.year}/{now.month}/{now.day}, so the holiday text is \"{holiday_text}\"")
            self.set_bottom_text('holiday', True)
            self.holiday_text = holiday_text
        else:
            self.set_bottom_text('holiday', False)
            self.holiday_text = ""

    # runs either when the X button is clicked or whenever needed
    def close_window(self):
        try:
            db: Dict[str, Union[bool, list, str]] = utils.access_db()
            save_pos = get_window_center(self.master)
            db['gui_position'] = list(save_pos)
            utils.access_db(db)
            self.log.info(f"Closing main window and exiting program (saving pos as {save_pos})")
            self.master.destroy()
        except Exception:
            pass  # we really do need the program to close now

        self.alive = False  # this makes main raise SystemExit ASAP


# hopefully only sets the current window, not any future ones
def set_window_icon(log: logger.Log, window: Union[tk.Tk, tk.Toplevel], wrench: bool):
    filename: str = 'tf2_logo_blurple_wrench.ico' if wrench else 'tf2_logo_blurple.ico'
    path: str = filename if launcher.DEBUG else os.path.join('resources', filename)

    try:
        window.iconbitmap(path)
    except tk.TclError:
        log.error(traceback.format_exc())


# calculate the center of a window
def get_window_center(window: Union[tk.Tk, tk.Toplevel]) -> Tuple[int, int]:
    x: int = round(window.winfo_rootx() + (window.winfo_width() / 2))
    y: int = round(window.winfo_rooty() + (window.winfo_height() / 2))
    return x, y


# position a window such that its center is x and y
def pos_window_by_center(window: Union[tk.Tk, tk.Toplevel], x: int, y: int):
    root_x: int = round(x - (window.winfo_width() / 2))
    root_y: int = round(y - (window.winfo_height() / 2))
    window.geometry(f'+{root_x}+{root_y}')


def main():
    main_gui = GUI(logger.Log())
    main_gui.set_clean_console_log_button_state(True)  # cause main would normally enable it once in game
    test_state(main_gui, int(input("0-4: ")))
    main_gui.mainloop()


def test_state(test_gui: GUI, state: int):
    if state == 0:
        test_gui.set_state_1('default', "Team Fortress 2 isn't running")
        test_gui.clear_fg_image()
        test_gui.clear_class_image()
        test_gui.set_launch_tf2_button_state(True)
    elif state == 1:
        test_gui.set_state_3('main_menu', ("In menus", "Not queued", "01:21 elapsed"))
        test_gui.set_fg_image('tf2_logo')
        test_gui.clear_class_image()
    elif state == 2:
        test_gui.set_state_3('main_menu', ("In menus", "Queued for Casual", "01:21 elapsed"))
        test_gui.set_fg_image('casual')
        test_gui.clear_class_image()
    elif state == 3:
        test_gui.set_state_4('bg_modes/payload', ("Map: Swiftwater", "Players: 19/24", "Time on map: 2:39", "06:21 elapsed"))
        test_gui.set_fg_image('fg_maps/pl_swiftwater_final1')
        test_gui.set_class_image('sniper')
    elif state == 4:
        test_gui.set_state_4('bg_modes/control-point', ("Map: cp_catwalk_a5c (hosting)", "Players: ?/?", "Time on map: 2:39", "06:21 elapsed"))
        test_gui.set_fg_image('fg_modes/control-point')
        test_gui.set_class_image('pyro')


if __name__ == "__main__":
    main()
