"""
Main_page.py  -  RUN THIS FILE TO START THE PROGRAM
===================================================
    python Main_page.py

This is the "hub". It:
  1. creates the main window,
  2. creates one manager (logic) object from each module,
  3. creates every page (screen) and stacks them on top of each other,
  4. offers app.show("name") so any page can switch to another page.

Module map
  Users.py      -> accounts + Welcome / Login / SignUp / CustomerProfile pages
  Court.py      -> court availability, fee, CourtBookingPage
  Payment.py    -> payment simulation, e-receipt, PaymentPage / CompletedPage
  Tournament.py -> tournaments + registration page

Booking flow (matches the 4-step bar in the proposal):
  Welcome -> Home -> [1 Court Booking] -> [2 Customer Profile] -> [3 Payment] -> [4 Completed]
"""

import tkinter as tk
from tkinter import ttk

from Users import UserManager, WelcomePage, LoginPage, SignUpPage, CustomerProfilePage
from Court import CourtManager, CourtBookingPage
from Payment import PaymentPage, CompletedPage
from Tournament import TournamentManager, TournamentPage


class StepBar(tk.Frame):
    """The 1-2-3-4 progress bar (Court Booking > Customer Profile > Payment > Completed)."""
    STEPS = ["Court Booking", "Customer Profile", "Payment", "Completed"]

    def __init__(self, parent, app):
        super().__init__(parent, bg=app.BG)
        self.app = app
        self.circles, self.labels = [], []
        for i, text in enumerate(self.STEPS):
            col = tk.Frame(self, bg=app.BG)
            col.pack(side="left", expand=True, padx=25, pady=8)
            circle = tk.Label(col, text=str(i + 1), width=3, font=("Segoe UI", 11, "bold"),
                              bg="#cccccc", fg="white")
            circle.pack()
            label = tk.Label(col, text=text, font=("Segoe UI", 9), bg=app.BG, fg=app.MUTED)
            label.pack()
            self.circles.append(circle)
            self.labels.append(label)

    def set_step(self, step):
        """Highlight steps 1..step in colour; the rest stay grey."""
        for i, (c, l) in enumerate(zip(self.circles, self.labels), start=1):
            done = i <= step
            c.config(bg=self.app.PRIMARY if done else "#cccccc")
            l.config(fg="black" if done else self.app.MUTED,
                     font=("Segoe UI", 9, "bold" if done else "normal"))


class HomePage(tk.Frame):
    """Menu shown after Login / Guest: choose Book a Court or Tournaments."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=app.BG)
        self.app = app
        self.greeting = tk.Label(self, text="", font=("Segoe UI", 18, "bold"),
                                 bg=app.BG, fg=app.PRIMARY)
        self.greeting.pack(pady=(70, 25))

        ttk.Button(self, text="Book a Court", width=28, style="Primary.TButton",
                   command=lambda: app.show("court")).pack(pady=6)
        ttk.Button(self, text="Tournaments & Registration", width=28,
                   style="Secondary.TButton",
                   command=lambda: app.show("tournament")).pack(pady=6)
        ttk.Button(self, text="Log Out", width=28, style="Link.TButton",
                   command=lambda: app.show("welcome")).pack(pady=(25, 0))

    def on_show(self):
        user = self.app.user
        self.greeting.config(text=f"Hello, {user['name']}!" if user else "Hello, Guest!")


class App(tk.Tk):
    """The main window. Also stores data that pages need to share."""

    # --- colour palette (change here to re-theme everything) ---
    BG = "#f4f7f6"
    CARD = "#ffffff"
    PRIMARY = "#0f7b5f"
    PRIMARY_DARK = "#0a5c47"
    MUTED = "#6b7a75"

    def __init__(self):
        super().__init__()
        self.title("Book Right Now - Dewan Badminton Stapok")
        self.geometry("820x640")
        self.minsize(760, 600)
        self.configure(bg=self.BG)
        self.setup_styles()

        # ----- shared "managers" (each one lives in its own module) -----
        self.users = UserManager()
        self.courts = CourtManager()
        self.tournaments = TournamentManager()

        # ----- shared data passed between pages -----
        self.user = None          # logged-in account (None = guest)
        self.customer = None      # name/contact/email used for the booking
        self.booking = None       # court/date/time chosen on the booking page
        self.last_record = None    # the completed booking (for the receipt)

        # ----- top banner -----
        banner = tk.Frame(self, bg=self.PRIMARY)
        banner.pack(fill="x")
        tk.Label(banner, text="BOOK RIGHT NOW", font=("Segoe UI", 15, "bold"),
                 bg=self.PRIMARY, fg="white").pack(side="left", padx=20, pady=10)

        # ----- progress bar (hidden except during the booking flow) -----
        self.stepbar = StepBar(self, self)

        # ----- container: all pages are stacked in the same cell -----
        container = tk.Frame(self, bg=self.BG)
        container.pack(fill="both", expand=True)
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        self.pages = {}
        page_classes = {
            "welcome": WelcomePage, "login": LoginPage, "signup": SignUpPage,
            "home": HomePage, "court": CourtBookingPage, "profile": CustomerProfilePage,
            "payment": PaymentPage, "completed": CompletedPage, "tournament": TournamentPage,
        }
        for name, cls in page_classes.items():
            page = cls(container, self)
            page.grid(row=0, column=0, sticky="nsew")
            self.pages[name] = page

        self.show("welcome")

    def set_user(self, account):
        """Remember who is logged in (None = guest) and reset any half-done booking."""
        self.user = account
        self.customer = None
        self.booking = None

    def show(self, name):
        """Bring page `name` to the front. Shows the step bar only for booking pages."""
        if name in ("court", "profile", "payment", "completed"):
            self.stepbar.pack(fill="x", before=self.pages[name].master)
        else:
            self.stepbar.pack_forget()
        page = self.pages[name]
        page.tkraise()                       # move this frame on top of the others
        if hasattr(page, "on_show"):
            page.on_show()                   # let the page refresh itself

    def setup_styles(self):
        """Define the look of ttk widgets (buttons, labels, cards)."""
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("TLabel", background=self.CARD, font=("Segoe UI", 10))
        s.configure("Heading.TLabel", font=("Segoe UI", 14, "bold"), foreground=self.PRIMARY)
        s.configure("Sub.TLabel", font=("Segoe UI", 10, "bold"))
        s.configure("Muted.TLabel", foreground=self.MUTED)
        s.configure("Card.TFrame", background=self.CARD, relief="solid", borderwidth=1)
        s.configure("Page.TFrame", background=self.BG)
        s.configure("TRadiobutton", background=self.CARD, font=("Segoe UI", 10))
        s.configure("Treeview", rowheight=26, font=("Segoe UI", 10))
        s.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        s.configure("Primary.TButton", background=self.PRIMARY, foreground="white",
                    font=("Segoe UI", 11, "bold"), padding=8, borderwidth=0)
        s.map("Primary.TButton", background=[("active", self.PRIMARY_DARK)])
        s.configure("Secondary.TButton", background="#dfe9e5", foreground="black",
                    font=("Segoe UI", 11), padding=8, borderwidth=0)
        s.map("Secondary.TButton", background=[("active", "#c9d9d3")])
        s.configure("Link.TButton", background=self.BG, foreground=self.MUTED,
                    font=("Segoe UI", 10, "underline"), borderwidth=0)


if __name__ == "__main__":
    App().mainloop()       # start the program and wait for the user's clicks