"""
Tournament.py  -  TOURNAMENT INFORMATION & REGISTRATION
=======================================================
Covers Scene 5. Users pick a tournament, see its details
(name, date, category, fee, deadline, slots) and can register
if registration is still open.

  TournamentManager -> logic: tournament list, open/closed check, saving registrations
  TournamentPage    -> the screen
"""

import json
import os
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox

from Users import UserManager      # re-use the email / phone checks

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REG_FILE = os.path.join(BASE_DIR, "data", "registrations.json")


def _days_from_today(n):
    """Helper for the sample data: today + n days as 'YYYY-MM-DD'."""
    return (datetime.now().date() + timedelta(days=n)).isoformat()


# ---------------------------------------------------------------------------
# 1. LOGIC (no GUI)
# ---------------------------------------------------------------------------
class TournamentManager:

    def __init__(self):
        # Sample tournaments. Dates are relative to today so the demo always works.
        # In a real system the administrator would add/edit these.
        self.tournaments = [
            {"id": "T1", "name": "Stapok Open Badminton Championship", "date": _days_from_today(30),
             "category": "Men's / Women's Singles", "fee": 30.00,
             "deadline": _days_from_today(20), "capacity": 32},
            {"id": "T2", "name": "Kuching Doubles Cup", "date": _days_from_today(45),
             "category": "Mixed Doubles", "fee": 50.00,
             "deadline": _days_from_today(35), "capacity": 16},
            {"id": "T3", "name": "Pickleball Fun Day", "date": _days_from_today(10),
             "category": "Open Pickleball", "fee": 20.00,
             "deadline": _days_from_today(-2), "capacity": 20},        # deadline passed = closed
        ]
        self.registrations = self._load()       # list of registration dicts

    # ----- file handling -----
    def _load(self):
        if os.path.exists(REG_FILE):
            with open(REG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def _save(self):
        os.makedirs(os.path.dirname(REG_FILE), exist_ok=True)
        with open(REG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.registrations, f, indent=2)

    # ----- queries -----
    def get(self, tid):
        return next(t for t in self.tournaments if t["id"] == tid)

    def available_slots(self, t):
        """Slots left = capacity - number of registrations for that tournament."""
        used = sum(1 for r in self.registrations if r["tournament_id"] == t["id"])
        return t["capacity"] - used

    def is_open(self, t):
        """Registration is open if deadline has not passed AND slots remain."""
        deadline_ok = datetime.now().date().isoformat() <= t["deadline"]
        return deadline_ok and self.available_slots(t) > 0

    # ----- Scene 5: register -----
    def register(self, t, name, contact, email):
        """
        IF Registration is still open THEN SAVE Registration_Information.
        Returns (success, message).
        """
        if not self.is_open(t):
            return False, "Registration is closed"
        if not (name and contact and email):
            return False, "Please fill in all the information."
        if not UserManager.valid_phone(contact):
            return False, "Contact number is not valid."
        if not UserManager.valid_email(email):
            return False, "Email address is not valid."
        if any(r["tournament_id"] == t["id"] and r["email"].lower() == email.lower()
               for r in self.registrations):
            return False, "This email is already registered for this tournament."

        self.registrations.append({
            "tournament_id": t["id"], "participant_name": name,
            "contact": contact, "email": email,
            "registered_on": datetime.now().isoformat(timespec="seconds"),
        })
        self._save()
        return True, "Registration successful"


# ---------------------------------------------------------------------------
# 2. SCREEN
# ---------------------------------------------------------------------------
class TournamentPage(tk.Frame):
    """Left: list of tournaments.  Right: details + registration form."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=app.BG)
        self.app = app

        ttk.Label(self, text="Tournaments & Events", style="Heading.TLabel",
                  background=app.BG).pack(anchor="w", padx=25, pady=(15, 5))

        body = ttk.Frame(self, style="Page.TFrame")
        body.pack(fill="both", expand=True, padx=25)

        # ---- left: list ----
        self.tree = ttk.Treeview(body, columns=("name", "date"), show="headings",
                                 height=10, selectmode="browse")
        self.tree.heading("name", text="Tournament")
        self.tree.heading("date", text="Date")
        self.tree.column("name", width=250)
        self.tree.column("date", width=90, anchor="center")
        self.tree.pack(side="left", fill="y")
        self.tree.bind("<<TreeviewSelect>>", lambda e: self.show_details())

        # ---- right: details card ----
        right = ttk.Frame(body, style="Card.TFrame", padding=15)
        right.pack(side="left", fill="both", expand=True, padx=(15, 0))
        self.details = ttk.Label(right, text="Select a tournament to see details.",
                                 justify="left")
        self.details.pack(anchor="w")
        self.status = ttk.Label(right, text="", style="Sub.TLabel")
        self.status.pack(anchor="w", pady=(8, 8))

        # Registration form (Participant name, contact, email)
        self.form = ttk.Frame(right, style="Card.TFrame")
        self.name = self._row(self.form, "Participant Name", 0)
        self.contact = self._row(self.form, "Contact Number", 1)
        self.email = self._row(self.form, "Email", 2)
        self.reg_btn = ttk.Button(right, text="Register", style="Primary.TButton",
                                  command=self.register)

        ttk.Button(self, text="Back", style="Secondary.TButton",
                   command=lambda: app.show("home")).pack(pady=10)

    @staticmethod
    def _row(parent, text, row):
        ttk.Label(parent, text=text).grid(row=row, column=0, sticky="e", padx=6, pady=4)
        e = ttk.Entry(parent, width=28)
        e.grid(row=row, column=1, sticky="w", pady=4)
        return e

    def on_show(self):
        self.fill_list()
        self.details.config(text="Select a tournament to see details.")
        self.status.config(text="")
        self.form.pack_forget()
        self.reg_btn.pack_forget()

    def fill_list(self):
        self.tree.delete(*self.tree.get_children())
        for t in self.app.tournaments.tournaments:
            self.tree.insert("", "end", iid=t["id"], values=(t["name"], t["date"]))

    def selected(self):
        sel = self.tree.selection()
        return self.app.tournaments.get(sel[0]) if sel else None

    def show_details(self):
        """PRINT Tournament_Name, Date, Category, Fee, Deadline, Available_Slots."""
        t = self.selected()
        if not t:
            return
        tm = self.app.tournaments
        self.details.config(text=(
            f"Name: {t['name']}\nDate: {t['date']}\nCategory: {t['category']}\n"
            f"Registration Fee: RM {t['fee']:.2f}\nRegistration Deadline: {t['deadline']}\n"
            f"Available Slots: {tm.available_slots(t)} / {t['capacity']}"))
        if tm.is_open(t):
            self.status.config(text="Registration is OPEN")
            # Pre-fill from the logged-in user (or earlier guest details) to save typing
            info = self.app.user or self.app.customer or {}
            for entry, key in ((self.name, "name"), (self.contact, "contact"),
                               (self.email, "email")):
                entry.delete(0, tk.END)
                entry.insert(0, info.get(key, ""))
            self.form.pack(anchor="w")
            self.reg_btn.pack(anchor="w", pady=(10, 0))
        else:
            self.status.config(text="Registration is closed")     # DISPLAY "Registration is closed"
            self.form.pack_forget()
            self.reg_btn.pack_forget()

    def register(self):
        t = self.selected()
        if not t:
            return
        ok, msg = self.app.tournaments.register(
            t, self.name.get().strip(), self.contact.get().strip(), self.email.get().strip())
        if ok:
            messagebox.showinfo("Tournament", f"{msg}!\nSee you at {t['name']} on {t['date']}.\n"
                                              f"Fee payable at the counter: RM {t['fee']:.2f}")
            self.show_details()          # refresh slot count
        else:
            messagebox.showerror("Tournament", msg)
