"""
Users.py  -  USER ACCOUNTS + USER SCREENS
=========================================
Covers Scene 1 (Main Page: Sign Up / Login / Guest) and the
"Customer Profile" step (step 2) of the booking progress bar.

The file has two kinds of code:
  1. UserManager   -> the "brain": saves/loads accounts, checks passwords.
                      (no GUI code inside, so it is easy to test)
  2. *Page classes -> the "screens": each one is a tkinter Frame that
                      Main_page.py can show or hide.

Every page class follows the same simple rules so Main_page.py can treat
them all alike:
  - __init__(self, parent, app)  : build the widgets. `app` is the main
                                    window, used to switch pages and to share data.
  - on_show(self)                : called each time the page is displayed
                                    (good for clearing/refreshing fields).
"""

import hashlib      # to hash (scramble) passwords so they are not stored as plain text
import json         # to save accounts in a text file
import os
import re           # regular expressions, used to check email / phone format
import secrets      # to make a random "salt" for each password
import tkinter as tk
from tkinter import ttk, messagebox

# Accounts are stored in  <this folder>/data/users.json
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data", "users.json")


# ---------------------------------------------------------------------------
# 1. LOGIC (no GUI)
# ---------------------------------------------------------------------------
class UserManager:
    """Handles sign up, login and input validation."""

    def __init__(self):
        self.users = self._load()       # dict: username -> account info

    # ----- file handling -----
    def _load(self):
        """Read accounts from the JSON file (empty dict if file not found)."""
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save(self):
        """Write all accounts back to the JSON file."""
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.users, f, indent=2)

    # ----- password hashing -----
    @staticmethod
    def _hash(password, salt):
        """Return a SHA-256 hash of salt+password. We never store the real password."""
        return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()

    # ----- validation helpers (also used by other modules) -----
    @staticmethod
    def valid_email(email):
        """True if text looks like name@domain.com"""
        return re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) is not None

    @staticmethod
    def valid_phone(phone):
        """True if the phone has 9-11 digits (Malaysian style, e.g. 012-345 6789)."""
        digits = re.sub(r"[\s\-+]", "", phone)       # remove spaces, dashes, plus
        return digits.isdigit() and 9 <= len(digits) <= 12

    # ----- Scene 1: Sign Up -----
    def sign_up(self, name, contact, email, username, password):
        """
        Pseudocode from proposal:
          IF Username already exists -> error ELSE SAVE User_Account
        Returns (success: bool, message: str)
        """
        if not all([name, contact, email, username, password]):
            return False, "Please fill in all the fields."
        if not self.valid_phone(contact):
            return False, "Contact number is not valid."
        if not self.valid_email(email):
            return False, "Email address is not valid."
        if len(password) < 6:
            return False, "Password must be at least 6 characters."
        if username.lower() in self.users:
            return False, "Username already exists. Please choose another username."

        salt = secrets.token_hex(8)                  # random text mixed into the hash
        self.users[username.lower()] = {
            "name": name, "contact": contact, "email": email,
            "username": username, "salt": salt,
            "password_hash": self._hash(password, salt),
        }
        self._save()
        return True, "Sign up successful. Please login to continue."

    # ----- Scene 1: Login -----
    def login(self, username, password):
        """
        Returns the account dict if username + password are correct, else None.
        """
        account = self.users.get(username.lower())
        if account and account["password_hash"] == self._hash(password, account["salt"]):
            return account
        return None


# ---------------------------------------------------------------------------
# Small helper used by several pages: a label + entry box pair
# ---------------------------------------------------------------------------
def labelled_entry(parent, text, row, show=None, width=32):
    """Create 'Label: [ entry ]' on a grid row and return the Entry widget."""
    ttk.Label(parent, text=text).grid(row=row, column=0, sticky="e", padx=8, pady=6)
    entry = ttk.Entry(parent, width=width, show=show)
    entry.grid(row=row, column=1, sticky="w", padx=8, pady=6)
    return entry


# ---------------------------------------------------------------------------
# 2. SCREENS
# ---------------------------------------------------------------------------
class WelcomePage(tk.Frame):
    """Scene 1: 'Welcome to Dewan Badminton Stapok Booking System'."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=app.BG)
        self.app = app

        tk.Label(self, text="Welcome to", font=("Segoe UI", 14), bg=app.BG,
                 fg=app.MUTED).pack(pady=(70, 0))
        tk.Label(self, text="Dewan Badminton Stapok\nBooking System",
                 font=("Segoe UI", 26, "bold"), bg=app.BG, fg=app.PRIMARY).pack(pady=(0, 10))
        tk.Label(self, text="Book badminton & pickleball courts and join tournaments",
                 font=("Segoe UI", 11), bg=app.BG, fg=app.MUTED).pack(pady=(0, 35))

        # The three choices from the proposal: Sign Up / Login / Guest
        ttk.Button(self, text="Login", width=28, style="Primary.TButton",
                   command=lambda: app.show("login")).pack(pady=6)
        ttk.Button(self, text="Sign Up", width=28, style="Secondary.TButton",
                   command=lambda: app.show("signup")).pack(pady=6)
        ttk.Button(self, text="Continue as Guest", width=28, style="Secondary.TButton",
                   command=self.guest).pack(pady=6)

    def guest(self):
        """PRINT 'Continue as Guest.' -> no account, go straight to the home menu."""
        self.app.set_user(None)              # None means "guest"
        self.app.show("home")


class LoginPage(tk.Frame):
    """Scene 1: Login form."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=app.BG)
        self.app = app

        tk.Label(self, text="Login", font=("Segoe UI", 22, "bold"),
                 bg=app.BG, fg=app.PRIMARY).pack(pady=(50, 15))

        form = ttk.Frame(self, style="Card.TFrame", padding=20)
        form.pack()
        self.username = labelled_entry(form, "Username", 0)
        self.password = labelled_entry(form, "Password", 1, show="*")
        self.password.bind("<Return>", lambda e: self.submit())   # Enter key = Login

        ttk.Button(self, text="Login", style="Primary.TButton",
                   command=self.submit).pack(pady=(18, 5))
        ttk.Button(self, text="Back", style="Link.TButton",
                   command=lambda: app.show("welcome")).pack()

    def on_show(self):
        self.username.delete(0, tk.END)
        self.password.delete(0, tk.END)
        self.username.focus()

    def submit(self):
        account = self.app.users.login(self.username.get().strip(), self.password.get())
        if account:                                    # PRINT "Login successful."
            self.app.set_user(account)
            messagebox.showinfo("Login", f"Login successful. Welcome, {account['name']}!")
            self.app.show("home")
        else:                                          # PRINT "Invalid username or password."
            messagebox.showerror("Login", "Invalid username or password. Please try again.")


class SignUpPage(tk.Frame):
    """Scene 1: Sign Up form (Name, Contact, Email, Username, Password)."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=app.BG)
        self.app = app

        tk.Label(self, text="Create an Account", font=("Segoe UI", 22, "bold"),
                 bg=app.BG, fg=app.PRIMARY).pack(pady=(30, 10))

        form = ttk.Frame(self, style="Card.TFrame", padding=20)
        form.pack()
        self.name = labelled_entry(form, "Full Name", 0)
        self.contact = labelled_entry(form, "Contact Number", 1)
        self.email = labelled_entry(form, "Email", 2)
        self.username = labelled_entry(form, "Username", 3)
        self.password = labelled_entry(form, "Password", 4, show="*")

        ttk.Button(self, text="Sign Up", style="Primary.TButton",
                   command=self.submit).pack(pady=(15, 5))
        ttk.Button(self, text="Back", style="Link.TButton",
                   command=lambda: app.show("welcome")).pack()

    def on_show(self):
        for e in (self.name, self.contact, self.email, self.username, self.password):
            e.delete(0, tk.END)
        self.name.focus()

    def submit(self):
        ok, msg = self.app.users.sign_up(
            self.name.get().strip(), self.contact.get().strip(), self.email.get().strip(),
            self.username.get().strip(), self.password.get())
        if ok:
            messagebox.showinfo("Sign Up", msg)
            self.app.show("login")              # after sign up, user must login
        else:
            messagebox.showerror("Sign Up", msg)


class CustomerProfilePage(tk.Frame):
    """
    Step 2 of the booking bar: 'Customer Profile'.
    - Logged-in users: their details are pre-filled.
    - Guests: they type First/Last name, contact number and email.
    The result is saved in app.customer and used for payment + e-receipt.
    """

    def __init__(self, parent, app):
        super().__init__(parent, bg=app.BG)
        self.app = app

        card = ttk.Frame(self, style="Card.TFrame", padding=20)
        card.pack(pady=25)
        ttk.Label(card, text="Customer Profile", style="Heading.TLabel").grid(
            row=0, column=0, columnspan=2, pady=(0, 10))
        self.status = ttk.Label(card, text="", style="Muted.TLabel")
        self.status.grid(row=1, column=0, columnspan=2, pady=(0, 8))

        self.name = labelled_entry(card, "Full Name *", 2)
        self.contact = labelled_entry(card, "Contact Number *", 3)
        self.email = labelled_entry(card, "Email *", 4)

        btns = ttk.Frame(self, style="Page.TFrame")
        btns.pack()
        ttk.Button(btns, text="Back", style="Secondary.TButton",
                   command=lambda: app.show("court")).pack(side="left", padx=6)
        ttk.Button(btns, text="Submit", style="Primary.TButton",
                   command=self.submit).pack(side="left", padx=6)

    def on_show(self):
        self.app.stepbar.set_step(2)
        user = self.app.user
        # Clear first, then pre-fill if the user is logged in
        for e in (self.name, self.contact, self.email):
            e.delete(0, tk.END)
        if user:
            self.status.config(text=f"Logged in as {user['username']}")
            self.name.insert(0, user["name"])
            self.contact.insert(0, user["contact"])
            self.email.insert(0, user["email"])
        else:
            self.status.config(text="Checking out as guest")
            # If a guest already filled this once, keep what they typed
            c = self.app.customer
            if c:
                self.name.insert(0, c["name"])
                self.contact.insert(0, c["contact"])
                self.email.insert(0, c["email"])

    def submit(self):
        name, contact, email = (self.name.get().strip(), self.contact.get().strip(),
                                self.email.get().strip())
        if not (name and contact and email):
            messagebox.showerror("Customer Profile", "Please fill in all the information.")
            return
        if not UserManager.valid_phone(contact):
            messagebox.showerror("Customer Profile", "Contact number is not valid.")
            return
        if not UserManager.valid_email(email):
            messagebox.showerror("Customer Profile", "Email address is not valid.")
            return
        self.app.customer = {"name": name, "contact": contact, "email": email}
        self.app.show("payment")
