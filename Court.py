"""
Court.py  -  COURT SELECTION, AVAILABILITY & FEE CALCULATION
============================================================
Covers Scene 2 (Court Selection & Fee Calculation) and the
"update court availability" part of Scene 4.

  CourtManager     -> logic: which courts are free, fee maths, saving bookings
  CourtBookingPage -> the screen (step 1 'Court Booking' in the progress bar)
"""

import json
import os
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data", "bookings.json")

# ---------------------------------------------------------------------------
# Facility settings - change these numbers to match the real facility.
# ---------------------------------------------------------------------------
ACTIVITIES = {
    # activity name : number of courts, price per hour (RM)
    "Badminton":  {"courts": 10, "rate": 25.00},
    "Pickleball": {"courts": 4,  "rate": 30.00},
}
OPEN_HOUR = 8          # facility opens at 08:00
CLOSE_HOUR = 23        # facility closes at 23:00 (last booking must END by then)
DURATIONS = [1, 2, 3]  # only fixed 1/2/3-hour blocks (a limitation in the proposal)
BOOK_AHEAD_DAYS = 14   # users can book up to 14 days in advance


# ---------------------------------------------------------------------------
# 1. LOGIC (no GUI)
# ---------------------------------------------------------------------------
class CourtManager:
    """Keeps the list of bookings and answers 'is this court free?'."""

    def __init__(self):
        self.bookings = self._load()        # list of booking dicts

    # ----- file handling -----
    def _load(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def _save(self):
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.bookings, f, indent=2)

    # ----- fee -----
    @staticmethod
    def calc_fee(activity, duration):
        """Court_Fee = Duration x Hourly_Rate   (from the proposal)."""
        return duration * ACTIVITIES[activity]["rate"]

    # ----- availability -----
    def is_available(self, activity, court_no, date, start_hour, duration):
        """
        A court is free if NO existing booking for the same activity/court/date
        overlaps the requested time range.
        Two ranges [a, a+len) and [b, b+len) overlap when  a < b_end AND b < a_end.
        """
        new_end = start_hour + duration
        for b in self.bookings:
            if (b["activity"] == activity and b["court"] == court_no and b["date"] == date):
                if start_hour < b["start_hour"] + b["duration"] and b["start_hour"] < new_end:
                    return False
        return True

    def available_courts(self, activity, date, start_hour, duration):
        """Return a list of court numbers that are free for the chosen slot."""
        return [n for n in range(1, ACTIVITIES[activity]["courts"] + 1)
                if self.is_available(activity, n, date, start_hour, duration)]

    # ----- Scene 4: save booking -----
    def save_booking(self, booking, customer, method):
        """
        GENERATE Booking_ID, SAVE Booking_Details, UPDATE Court_Availability.
        (Availability updates automatically because is_available() reads self.bookings.)
        Returns the finished booking record, or None if the slot was taken meanwhile.
        """
        # Double-check right before saving, in case someone else booked it
        if not self.is_available(booking["activity"], booking["court"], booking["date"],
                                 booking["start_hour"], booking["duration"]):
            return None

        record = dict(booking)
        record["booking_id"] = f"BK{datetime.now():%Y%m%d}{len(self.bookings) + 1:04d}"
        record["customer"] = customer
        record["payment_method"] = method
        record["payment_status"] = "Successful"
        self.bookings.append(record)
        self._save()
        return record


def fmt_hour(h):
    """9 -> '09:00'  (used for display)."""
    return f"{h:02d}:00"


# ---------------------------------------------------------------------------
# 2. SCREEN
# ---------------------------------------------------------------------------
class CourtBookingPage(tk.Frame):
    """
    Left side : date / activity / start time / duration + list of free courts.
    Right side: summary (court, date, total).  'Next' goes to Customer Profile.
    The list of free courts refreshes automatically whenever an input changes
    (this is the 'real-time availability' strength in the proposal).
    """

    def __init__(self, parent, app):
        super().__init__(parent, bg=app.BG)
        self.app = app

        card = ttk.Frame(self, style="Card.TFrame", padding=18)
        card.pack(fill="both", expand=True, padx=25, pady=15)
        ttk.Label(card, text="Court Booking", style="Heading.TLabel").grid(
            row=0, column=0, columnspan=4, sticky="w", pady=(0, 10))

        # ---- input widgets ----
        # Date: a dropdown of the next 14 days (avoids needing extra calendar libraries)
        ttk.Label(card, text="Booking Date *").grid(row=1, column=0, sticky="w")
        today = datetime.now().date()
        self.dates = [(today + timedelta(days=i)).isoformat() for i in range(BOOK_AHEAD_DAYS)]
        self.date_var = tk.StringVar(value=self.dates[0])
        ttk.Combobox(card, textvariable=self.date_var, values=self.dates,
                     state="readonly", width=18).grid(row=2, column=0, sticky="w", padx=(0, 20))

        ttk.Label(card, text="Activity *").grid(row=1, column=1, sticky="w")
        self.activity_var = tk.StringVar(value="Badminton")
        ttk.Combobox(card, textvariable=self.activity_var, values=list(ACTIVITIES),
                     state="readonly", width=18).grid(row=2, column=1, sticky="w", padx=(0, 20))

        ttk.Label(card, text="Start Time *").grid(row=3, column=0, sticky="w", pady=(10, 0))
        self.time_var = tk.StringVar(value="18:00")
        times = [fmt_hour(h) for h in range(OPEN_HOUR, CLOSE_HOUR)]
        ttk.Combobox(card, textvariable=self.time_var, values=times,
                     state="readonly", width=18).grid(row=4, column=0, sticky="w")

        ttk.Label(card, text="Duration (Hour) *").grid(row=3, column=1, sticky="w", pady=(10, 0))
        self.duration_var = tk.IntVar(value=2)
        dur_frame = ttk.Frame(card, style="Card.TFrame")
        dur_frame.grid(row=4, column=1, sticky="w")
        for d in DURATIONS:
            ttk.Radiobutton(dur_frame, text=f"{d} Hour{'s' if d > 1 else ''}",
                            variable=self.duration_var, value=d).pack(side="left", padx=(0, 8))

        # Whenever any input changes, refresh the court list (trace_add = "watch this variable")
        for var in (self.date_var, self.activity_var, self.time_var, self.duration_var):
            var.trace_add("write", lambda *a: self.refresh())

        # ---- list of available courts ----
        ttk.Label(card, text="Available Courts (click one to select)",
                  style="Sub.TLabel").grid(row=5, column=0, columnspan=2, sticky="w", pady=(18, 4))
        cols = ("court", "time", "duration", "price")
        self.tree = ttk.Treeview(card, columns=cols, show="headings", height=8,
                                 selectmode="browse")
        for c, title, w in (("court", "Court", 130), ("time", "Time", 120),
                            ("duration", "Duration", 70), ("price", "Price", 80)):
            self.tree.heading(c, text=title)
            self.tree.column(c, width=w, anchor="center")
        self.tree.grid(row=6, column=0, columnspan=2, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", lambda e: self.update_summary())

        # ---- summary box (right side) ----
        summ = ttk.Frame(card, style="Card.TFrame")
        summ.grid(row=5, column=2, rowspan=2, sticky="nsew", padx=(25, 0))
        ttk.Label(summ, text="Summary", style="Sub.TLabel").pack(anchor="w", pady=(0, 6))
        self.summary_lbl = ttk.Label(summ, text="No court selected.", justify="left")
        self.summary_lbl.pack(anchor="w")
        self.total_lbl = ttk.Label(summ, text="Total: RM 0.00", style="Heading.TLabel")
        self.total_lbl.pack(anchor="w", pady=(15, 0))

        self.msg = ttk.Label(card, text="", style="Muted.TLabel")
        self.msg.grid(row=7, column=0, columnspan=3, sticky="w", pady=(8, 0))

        card.columnconfigure(2, weight=1)
        card.rowconfigure(6, weight=1)

        # ---- buttons ----
        btns = ttk.Frame(self, style="Page.TFrame")
        btns.pack(pady=(0, 10))
        ttk.Button(btns, text="Back", style="Secondary.TButton",
                   command=lambda: app.show("home")).pack(side="left", padx=6)
        ttk.Button(btns, text="Next", style="Primary.TButton",
                   command=self.next).pack(side="left", padx=6)

    # ----- helpers -----
    def start_hour(self):
        """'18:00' -> 18"""
        return int(self.time_var.get().split(":")[0])

    def on_show(self):
        self.app.stepbar.set_step(1)
        self.refresh()

    def refresh(self):
        """Re-calculate which courts are free and fill the table."""
        self.tree.delete(*self.tree.get_children())
        self.msg.config(text="")
        self.update_summary()

        activity, date = self.activity_var.get(), self.date_var.get()
        start, dur = self.start_hour(), self.duration_var.get()

        # Rule 1: booking must finish before closing time
        if start + dur > CLOSE_HOUR:
            self.msg.config(text=f"Booking must end by {fmt_hour(CLOSE_HOUR)}. "
                                 "Choose an earlier start time or shorter duration.")
            return
        # Rule 2: cannot book a time that has already passed today
        if date == datetime.now().date().isoformat() and start <= datetime.now().hour:
            self.msg.config(text="That start time has already passed today.")
            return

        free = self.app.courts.available_courts(activity, date, start, dur)
        fee = CourtManager.calc_fee(activity, dur)
        for n in free:
            self.tree.insert("", "end", iid=str(n), values=(
                f"{activity} Court {n}", f"{fmt_hour(start)} - {fmt_hour(start + dur)}",
                f"{dur} Hour", f"RM {fee:.2f}"))
        if not free:
            # PRINT "Court is unavailable. Please select another time slot."
            self.msg.config(text="Court is unavailable. Please select another time slot.")

    def update_summary(self):
        """Show the chosen court + total price on the right."""
        sel = self.tree.selection()
        if not sel:
            self.summary_lbl.config(text="No court selected.")
            self.total_lbl.config(text="Total: RM 0.00")
            return
        start, dur = self.start_hour(), self.duration_var.get()
        fee = CourtManager.calc_fee(self.activity_var.get(), dur)
        self.summary_lbl.config(text=(
            f"{self.activity_var.get()} Court {sel[0]}\n{self.date_var.get()}\n"
            f"{fmt_hour(start)} - {fmt_hour(start + dur)}"))
        self.total_lbl.config(text=f"Total: RM {fee:.2f}")

    def next(self):
        """Save the choice into app.booking and move to the Customer Profile step."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Court Booking", "Please select an available court.")
            return
        start, dur = self.start_hour(), self.duration_var.get()
        activity = self.activity_var.get()
        self.app.booking = {
            "activity": activity, "court": int(sel[0]), "date": self.date_var.get(),
            "start_hour": start, "duration": dur,
            "fee": CourtManager.calc_fee(activity, dur),
        }
        self.app.show("profile")
