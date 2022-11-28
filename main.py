import io
import os
from tkinter import (
    Tk, Toplevel,
    DoubleVar,
    Button, Label, Frame, Canvas, Scale,
    LEFT, RIGHT, CENTER, X, Y, BOTH, TOP, BOTTOM,
)
from tkinter.ttk import (
    Button as Btn, Label as Lbl, Frame as Frm, Scale as Scl, Style
)
from tkinter.colorchooser import askcolor
from tkinter.messagebox import askyesno, showinfo
from tkinter.filedialog import asksaveasfilename
from typing import Literal

from PIL import Image, ImageDraw
from pyautogui import screenshot
from win32gui import GetWindowRect
from os import getenv, path, curdir


class WhiteBoard:
    # Class constants
    title = "Whiteboard"
    dimension = (1050, 570)
    color_swatches = ["black", "brown", "red", "orange", "pink", "yellow", "lightgreen", "darkgreen", "darkblue",
                      "darkcyan", "skyblue", "lightgrey", "grey", "white"]
    default = {
        "X"   : 0,
        "Y"   : 0,
        "BG"  : "white",
        "FG"  : "black",
        "H_BG": "#cce7ff",  # Mouse hover background
        "H_FG": "black",  # Mouse hover foreground
    }
    screenshot_path = getenv("USERPROFILE") + "\\Pictures\\"

    # initializes the WhiteBoard class with the following...
    def __init__(self, title: str | None = None):
        # Overwrites class constants if specified
        self.title = self.title if title is None else title

        # Holds initial variables
        self.is_draw = False  # To display confirmation message on screen clear
        self.is_pencil = True  # To toggle the pencil and the eraser mode on click
        self.reserved = {
            "foreground": "",  # To store the current pencil fg color in eraser mode and used again in pencil mode
            "thickness" : 0.0  # To store the current pencil thickness in eraser mode and used again in pencil mode
        }
        self.reserved_thickness = ""  # To store current pencil thickness

        # Initializes Tkinter window
        self.window = Tk()
        self.window.geometry(f"{self.dimension[0]}x{self.dimension[1]}")
        self.window.minsize(width=self.dimension[0], height=self.dimension[1])
        self.window.title(self.title)

        # Stores tkinter widgets/elements/variables
        self.styles = Style()
        self.background, self.tool_panel_canvas, \
            self.board_panel_canvas, self.control_panel = self.make_panels()
        self.image = Image.new("RGB", (self.board_panel_canvas.winfo_width(),
                                       self.board_panel_canvas.winfo_height()), "white")
        self.draw = ImageDraw.Draw(self.image)
        self.clear_button, self.bucket_button, self.pencil_button = self.make_drawing_tool_buttons()
        self.custom_color_box = self.make_color_palates()
        self.pencil_thickness = DoubleVar()
        self.bg_indicator, self.fg_indicator = self.make_fg_bg_indicator()

        # Runs required functions while initializing
        self.make_thickness_slider()
        self.make_menu()
        self.mouse_bind()

    # Makes frames and panels
    def make_panels(self):
        # App's background frame
        background = Frame(self.window)
        background.pack(fill=BOTH, expand=True)

        # App's tools panel
        tool_panel = Canvas(background, background="white", bd=0)
        tool_panel.place(x=20, width=50, rely=0.07, relheight=0.85)

        # App's drawing panel
        draw_panel = Canvas(background, background="white", cursor="dot")
        draw_panel.place(x=(20 + 50 + 15), relwidth=0.90, rely=0.03, relheight=0.85)

        # App's control panel
        control_panel = Canvas(background, highlightbackground="white", highlightthickness=0, background="white")
        control_panel.place(x=(20 + 50 + 15), relwidth=0.90, rely=0.9, height=40)

        return background, tool_panel, draw_panel, control_panel

    # Makes pre-defined color palates
    def make_color_palates(self):
        for num, color in enumerate(self.color_swatches):
            color_box = Lbl(self.tool_panel_canvas, width=3, background=color, relief="solid", cursor="hand2")
            color_box.pack(side=TOP, pady=(20 if num == 0 else 0, 4))
            color_box.bind('<Button-1>', lambda event=None, val=color: self.set_color(val))

        # Custom color chooser
        custom_color_box = Lbl(self.tool_panel_canvas, text="?", width=3, background="white", relief="solid",
                               cursor="hand2", anchor="center")
        custom_color_box.pack(side=TOP)
        custom_color_box.bind('<Button-1>', lambda event=None: self.set_custom_color())

        # Returns custom_color_box only for changing its background color on choosing custom color
        return custom_color_box

    # Makes board clear button
    def make_drawing_tool_buttons(self):
        clear_btn = Lbl(self.tool_panel_canvas, text="\ue107", foreground="", relief="solid", width=3,
                        anchor="center", font=("Segoe MDL2 Assets", 12), padding=(3, 2))  #\u2718
        clear_btn.pack(side=BOTTOM, pady=(4, 12))

        bucket_btn = Lbl(self.tool_panel_canvas, text="\ue771", foreground="grey", relief="solid", width=3,
                         anchor="center", font=("Segoe MDL2 Assets", 12), padding=(3, 2))
        bucket_btn.pack(side=BOTTOM, pady=(4, 0))

        pencil_btn = Lbl(self.tool_panel_canvas, text="\uef16", foreground="grey", relief="solid", width=3,
                         anchor="center", justify="center", font=("Segoe MDL2 Assets", 12), padding=(3, 2))
        pencil_btn.pack(side=BOTTOM, pady=(4, 0))

        return clear_btn, bucket_btn, pencil_btn

    # Makes foreground and background color indicator
    def make_fg_bg_indicator(self):
        fg_bg_frame = Frame(self.control_panel)
        fg_bg_frame.pack(side=LEFT, padx=(10, 5))
        fg_indicator = Lbl(fg_bg_frame, text="\uf127", anchor="center", foreground=self.default["FG"],
                           background="white", font=("Segoe MDL2 Assets", 10))
        fg_indicator.pack(side=TOP)
        bg_indicator = Lbl(fg_bg_frame, text="\uf126", anchor="center", foreground=self.default["BG"],
                           background="white", font=("Segoe MDL2 Assets", 10))
        bg_indicator.pack(side=TOP)

        return bg_indicator, fg_indicator

    # Makes pencil thickness slider
    def make_thickness_slider(self):
        slider = Scale(self.control_panel, from_=0, to=100, orient="horizontal", relief="flat", sliderrelief="solid",
                       sliderlength=10, bd=0, width=5, font=("Arial", 8), fg="grey", bg="white", highlightthickness=0,
                       command=self.change_thickness, variable=self.pencil_thickness)
        # slider.place(x=110, rely=0.94)  # rely=0.94
        slider.pack(side=LEFT, )
        # slider_label.place(x=220, rely=0.945)

    # Makes basic menu buttons about the app
    def make_menu(self):
        self.styles.configure('Btn.TButton', font=("Segoe MDL2 Assets", 12))

        Btn(self.control_panel, text="\ue946", width=4, style='Btn.TButton',
            command=self.about_the_app).pack(side=RIGHT, padx=(0, 10))
        Btn(self.control_panel, text="\ue115", width=4, style='Btn.TButton').pack(side=RIGHT)
        self.seperator(self.control_panel, side=RIGHT, ht=20, wt=4, bg="white", fg="lightgrey")
        Btn(self.control_panel, text="\ue792", width=4, style='Btn.TButton',
            command=self.save_as).pack(side=RIGHT)
        Btn(self.control_panel, text="\ue105", width=4, style='Btn.TButton',
            command=self.save).pack(side=RIGHT)
        Btn(self.control_panel, text="\uec80", width=4, style='Btn.TButton', command=self.take_screenshot).pack(
            side=RIGHT)
        self.seperator(self.control_panel, side=RIGHT, ht=20, wt=4, bg="white", fg="lightgrey")
        Btn(self.control_panel, text="\ue1a5", width=4, style='Btn.TButton').pack(side=RIGHT)
        self.seperator(self.control_panel, side=RIGHT, ht=20, wt=4, bg="white", fg="lightgrey")
        Btn(self.control_panel, text="\ue160", width=4, style='Btn.TButton').pack(side=RIGHT)

    # Takes screenshot and save them
    # @staticmethod
    def take_screenshot(self):
        from datetime import datetime
        x, y = self.window.winfo_x(), self.window.winfo_y()
        w, h = self.window.winfo_width(), self.window.winfo_height()
        file = f"{self.screenshot_path}{self.title}_shot@{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        shot = screenshot(region=(x + 10, y, w, h + 25))
        shot.save(file)

        self.in_app_notification(f"WhiteFLAT's screenshot is saved to {file}", "done")

    def save(self):
        save_file_name = asksaveasfilename(title="Save WhiteFLAT Canvas to A PostScript File",
                                           confirmoverwrite=True, defaultextension="ps",
                                           initialdir=self.screenshot_path, initialfile="Untitled_WhiteFLAT.ps",
                                           filetypes=[("PostScript File", ".ps"), ("All Files", ".*")])
        if save_file_name:
            self.board_panel_canvas.postscript(file=save_file_name, colormode='color')

    def save_as(self):
        save_as_file_name = asksaveasfilename(title="Save WhiteFLAT Canvas as An Image File",
                                              confirmoverwrite=True, defaultextension="png",
                                              initialdir=self.screenshot_path, initialfile="Untitled_WhiteFLAT.png",
                                              filetypes=[("Portable Network Graphic", ".png"),
                                                         ("JPG", ".jpg"),
                                                         ("Bit Map Pictures", ".bmp")])
        if save_as_file_name:
            self.image.save(save_as_file_name, save_as_file_name[-1:-3])
        # ps = self.board_panel_canvas.postscript(colormode='color')
        # img = Image.open(io.BytesIO(ps.encode('utf-8')))
        # img.save('test.jpg')

    # Adds a vertical lined seperator for a Tkinter toplevel widget with defined height and width
    @staticmethod
    def seperator(parent: Tk | Frame | Canvas,
                  side: [LEFT, RIGHT], ht: int, wt: int, bg: str = "white", fg: str = "grey"):
        """
        Adds a lined (vertical) seperator to a parent Tkinter window, frame, label frame or canvas.
        :param parent: Top level widget of a Tkinter class.
        :type parent: Tk() | Frame() | Canvas()
        :param side: On which side of the parent the seperator will be placed.
        :type side: LEFT, RIGHT or "left", "right"
        :param ht: Height of the seperator.
        :type ht: int
        :param wt: Width of the seperator.
        :type wt: int
        :param bg: Background color of the seperator. Default is "white".
        :type bg: str
        :param fg: Foreground color of the seperator. Default is "lightgrey".
        :type fg: str
        :return: Nothing returns by this function now.
        :rtype: None
        """
        _x = wt / 2 + 1
        _seperator = Canvas(parent, height=ht, width=wt, background=bg, highlightbackground=bg)
        _seperator.pack(side=side)
        _seperator.create_line((_x, 1, _x, ht), fill=fg)

        return None

    # Sets new color on click on colour palate
    def set_color(self, color):
        self.default["FG"] = color
        self.fg_indicator.configure(foreground=self.default["FG"])

    # Sets custom color
    def set_custom_color(self):
        custom_color = askcolor()
        if custom_color[1]:
            self.default["FG"] = str(custom_color[1])
            self.custom_color_box.configure(background=self.default["FG"])
            self.fg_indicator.configure(foreground=self.default["FG"])

    # Sets X, Y on mouse click on drawing board
    def set_xy(self, click):
        self.default["X"], self.default["Y"] = click.x, click.y

    # Draws line on mouse left-click-drag
    def draw_line(self, drag):
        self.board_panel_canvas.create_line(
            (self.default["X"], self.default["Y"], drag.x, drag.y), width=self.pencil_thickness.get(),
            fill=self.default["FG"], capstyle="round", smooth=True)
        self.draw.line([(self.default["X"], self.default["Y"]), (drag.x, drag.y)],
                       width=int(self.pencil_thickness.get()), fill=self.default["FG"], joint="curve")

        self.default["X"], self.default["Y"] = drag.x, drag.y
        self.is_draw = True

    # Draws continuous line right-click
    def draw_continuous_line(self, click):
        self.board_panel_canvas.create_line((self.default['X'], self.default['Y'], click.x, click.y),
                                            fill=self.default["FG"], width=self.pencil_thickness.get())
        self.default["X"], self.default["Y"] = click.x, click.y

    # Clears the drawing canvas on click of clear button
    def clear_drawing_canvas(self):
        self.clear_button.configure(background="red", foreground="white", borderwidth=0)
        if self.is_draw:
            option = askyesno(title="Warning", message="The drawing canvas will be cleared. It's advised you to"
                                                       " click on NO first and save it before clearing the screen."
                                                       "\n\nAre you sure you want to CLEAR the canvas?")
            if option:
                self.board_panel_canvas.delete('all')
                self.is_draw = False

                # Resets canvas background to White too
                self.default["BG"] = "white"
                self.board_panel_canvas.configure(background=self.default["BG"])
                self.fg_indicator.configure(foreground=self.default["FG"])
                self.bg_indicator.configure(foreground=self.default["BG"])

                self.in_app_notification("Drawing canvas is cleared.", "done")

    # Fills the drawing canvas's background color
    def fill_drawing_canvas(self):
        self.board_panel_canvas.configure(background=self.default["FG"])
        self.default["BG"] = self.default["FG"]
        self.is_draw = True
        self.bg_indicator.configure(foreground=self.default["BG"])

        self.in_app_notification("Drawing canvas is filled with the selected color.", "info")

    # Changes the thickness of the pencil
    def change_thickness(self, event):
        # self.thickness_slider_label.configure(text="{: .1f}".format(self.pencil_thickness.get()))
        pass

    # Toggles the pencil and eraser mode on click
    def toggle_pencil_eraser(self):
        if self.is_pencil:
            # Eraser mode
            self.pencil_button.configure(text="\uef17", foreground="black")
            self.reserved["foreground"] = self.default["FG"]  # stores current fg color to use in pencil mode
            self.reserved["thickness"] = self.pencil_thickness.get()  # stores current pencil thickness too
            self.default["FG"] = self.default["BG"]
            self.pencil_thickness.set(5)  # sets eraser thickness to 5 for easy erasing
            self.is_pencil = False

            self.in_app_notification("Drawing canvas is switched to 'Eraser Mode'.", "switch")
        else:
            # Pencil mode
            self.pencil_button.configure(text="\uef16", foreground="grey")
            self.default["FG"] = self.reserved["foreground"]  # sets fg color to that of the stored before
            self.pencil_thickness.set(self.reserved["thickness"])  # sets pencil thickness from stored value too
            self.is_pencil = True

            self.in_app_notification("Drawing canvas is switched to 'Pencil Mode'.", "switch")

    # In-app message notification bar
    def in_app_notification(self, message: str,
                            message_type: Literal["done", "info", "warn", "error", "switch"]):
        # Message heading design
        heading_font = ("Segoe MDL2 Assets", 22, "bold")
        heading_icon = {
            # "message_type": ("\icon_unicode", "icon_color", "heading")
            "done": ("\ue001", "green", "DONE"),
            "info": ("\ue946", "blue", "INFORMATION"),
            "warn": ("\ue814", "yellow", "WARNING"),
            "error": ("\ue25b", "red", "ERROR"),
            "switch": ("\ue148", "violet", "SWITCH")
        }

        # Message bar
        msg_bar = Toplevel(self.window)
        msg_bar.overrideredirect(True)
        msg_bar.attributes('-alpha', 0.7)
        msg_bar.geometry(f"+{self.window.winfo_x() + 30}+{self.window.winfo_y() + 40}")

        bg_frame = Frame(msg_bar, bg="white")
        bg_frame.pack(side="top", fill="both", ipadx=10)
        Label(bg_frame, text=heading_icon[message_type][0], font=heading_font, fg=heading_icon[message_type][1],
              bg="white").grid(row=0, rowspan=2, column=0)
        Label(bg_frame, text=heading_icon[message_type][2], fg=heading_icon[message_type][1],
              bg="white").grid(row=0, column=1, sticky="w")
        Label(bg_frame, text=message, bg="white", fg="black").grid(row=1, column=1)

        msg_bar.after(5000, lambda: msg_bar.destroy())
        msg_bar.mainloop()

    # About the app window
    def about_the_app(self):
        about_window = Toplevel(self.window, background="white")
        about_window.geometry("300x120")
        about_window.wm_attributes('-toolwindow', True)

        main_frame = Frame(about_window, background="white")
        main_frame.pack(fill=BOTH, expand=True)
        Label(main_frame, text=self.title, font=("Times New Roman", 40, "bold"),
              fg="darkcyan", bg="white").pack(fill=BOTH)
        Label(main_frame, text="Made with passion by Passion-Lab", bg="white", fg="grey").pack()

    # Binds mouse and keys event
    def mouse_bind(self):
        # Binds mouse left-click and left-click-and-drag with the drawing board
        self.board_panel_canvas.bind('<Button-1>', self.set_xy)
        self.board_panel_canvas.bind('<Button-3>', self.draw_continuous_line)
        self.board_panel_canvas.bind('<B1-Motion>', self.draw_line)
        # Mouse hover bindings
        self.clear_button.bind('<Enter>', lambda event=None: self.clear_button.configure(
            background=self.default["H_BG"], foreground="red"))
        self.clear_button.bind('<Leave>', lambda event=None: self.clear_button.configure(background="", foreground=""))
        self.bucket_button.bind('<Enter>', lambda event=None: self.bucket_button.configure(
            background=self.default["H_BG"], foreground=self.default["H_FG"]))
        self.bucket_button.bind('<Leave>', lambda event=None: self.bucket_button.configure(
            background="", foreground="grey"))
        self.pencil_button.bind('<Enter>', lambda event=None: self.pencil_button.configure(
            background=self.default["H_BG"], foreground=self.default["H_FG"]))
        self.pencil_button.bind('<Leave>', lambda event=None: self.pencil_button.configure(
            background="", foreground="grey"))
        # Mouse left-click events
        self.clear_button.bind('<Button-1>', lambda event=None: self.clear_drawing_canvas())
        self.bucket_button.bind('<Button-1>', lambda event=None: self.fill_drawing_canvas())
        self.pencil_button.bind('<Button-1>', lambda event=None: self.toggle_pencil_eraser())

    # Makes visible the Tkinter window
    def start(self):
        # Resets drawing canvas's foreground color to white and custom color box to default before starting the app
        self.custom_color_box.configure(background="white")
        self.default["FG"] = "black"

        # Starts the app
        self.window.mainloop()


# Runs main application from this file only
if __name__ == '__main__':
    app = WhiteBoard(title="WhiteFLAT")
    app.start()
