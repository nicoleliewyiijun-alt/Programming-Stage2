"""
Payment.py  -  PAYMENT, E-RECEIPT AND BOOKING-COMPLETED SCREENS
===============================================================
Covers Scene 3 (Payment) and Scene 4 (Booking Completed).

IMPORTANT: this is a SIMULATION. No real money moves. A real system would
call the FPX / Sarawak Pay gateway where PaymentManager.process() is.

  PaymentManager -> logic: process payment (simulated), build the e-receipt
  PaymentPage    -> step 3 'Payment' screen
  CompletedPage  -> step 4 'Completed' screen (confirmation + e-receipt)
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from Court import fmt_hour

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RECEIPT_DIR = os.path.join(BASE_DIR, "receipts")

# Payment methods shown in the screenshots of the proposal
PAYMENT_METHODS = ["FPX", "Sarawak Pay"]
FPX_BANKS = ["Maybank2u", "CIMB Clicks", "Public Bank", "RHB Now", "Bank Islam", "Hong Leong"]


# ---------------------------------------------------------------------------
# 1. LOGIC (no GUI)
# ---------------------------------------------------------------------------
class PaymentManager:

    @staticmethod
    def is_valid_method(method):
        """IF Payment_Method is valid THEN ..."""
        return method in PAYMENT_METHODS

    @staticmethod
    def process(method, amount):
        """
        PROCESS Payment. Returns True when payment is successful.
        Simulation: any valid method with an amount > 0 succeeds.
        """
        return PaymentManager.is_valid_method(method) and amount > 0

    @staticmethod
    def build_receipt(record):
        """
        Build the e-receipt text. The proposal says it must contain:
        user's name, booking date, time slot, court number and total payment.
        """
        b, c = record, record["customer"]
        end = b["start_hour"] + b["duration"]
        lines = [
            "=" * 44,
            "   DEWAN BADMINTON STAPOK  -  E-RECEIPT",
            "=" * 44,
            f"Booking ID   : {b['booking_id']}",
            f"Name         : {c['name']}",
            f"Contact      : {c['contact']}",
            f"Email        : {c['email']}",
            "-" * 44,
            f"Court        : {b['activity']} Court {b['court']}",
            f"Booking Date : {b['date']}",
            f"Time Slot    : {fmt_hour(b['start_hour'])} - {fmt_hour(end)}",
            f"Duration     : {b['duration']} hour(s)",
            "-" * 44,
            f"Payment      : {b['payment_method']} ({b['payment_status']})",
            f"TOTAL PAID   : RM {b['fee']:.2f}",
            "=" * 44,
            f"Issued on {datetime.now():%Y-%m-%d %H:%M}",
        ]
        return "\n".join(lines)

    @staticmethod
    def save_receipt(record, text):
        """Write the receipt to receipts/<Booking_ID>.txt and return the path."""
        os.makedirs(RECEIPT_DIR, exist_ok=True)
        path = os.path.join(RECEIPT_DIR, f"{record['booking_id']}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path


# ---------------------------------------------------------------------------
# 2. SCREENS
# ---------------------------------------------------------------------------
class PaymentPage(tk.Frame):
    """Scene 3: show the booking summary + total, let the user choose FPX / Sarawak Pay."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=app.BG)
        self.app = app

        card = ttk.Frame(self, style="Card.TFrame", padding=20)
        card.pack(pady=20, padx=30, fill="x")
        ttk.Label(card, text="Payment", style="Heading.TLabel").pack(anchor="w")

        # Summary table (Space Booked | Booking Date | Payment Amount)
        self.tree = ttk.Treeview(card, columns=("space", "date", "amount"),
                                 show="headings", height=2)
        for c, t, w in (("space", "Space Booked", 180), ("date", "Booking Date", 200),
                        ("amount", "Payment Amount", 130)):
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor="center")
        self.tree.pack(fill="x", pady=10)
        self.total_lbl = ttk.Label(card, text="", style="Heading.TLabel")
        self.total_lbl.pack(anchor="e")

        # Payment method choice (radio buttons) - PROMPT user to select Payment_Method
        ttk.Label(card, text="Payment Method", style="Sub.TLabel").pack(anchor="w", pady=(12, 4))
        self.method_var = tk.StringVar(value="")
        for m in PAYMENT_METHODS:
            ttk.Radiobutton(card, text=m, value=m, variable=self.method_var,
                            command=self.method_changed).pack(anchor="w")

        # Bank dropdown: only visible when FPX is chosen
        self.bank_var = tk.StringVar(value=FPX_BANKS[0])
        self.bank_box = ttk.Combobox(card, textvariable=self.bank_var, values=FPX_BANKS,
                                     state="readonly", width=24)

        btns = ttk.Frame(self, style="Page.TFrame")
        btns.pack()
        ttk.Button(btns, text="Back", style="Secondary.TButton",
                   command=lambda: app.show("profile")).pack(side="left", padx=6)
        ttk.Button(btns, text="Pay Now", style="Primary.TButton",
                   command=self.pay).pack(side="left", padx=6)

    def on_show(self):
        self.app.stepbar.set_step(3)
        b = self.app.booking
        self.method_var.set("")
        self.bank_box.pack_forget()
        # Refill the summary table
        self.tree.delete(*self.tree.get_children())
        self.tree.insert("", "end", values=(
            f"{b['activity']} Court {b['court']}",
            f"{b['date']}  {fmt_hour(b['start_hour'])}-{fmt_hour(b['start_hour'] + b['duration'])}",
            f"RM {b['fee']:.2f}"))
        self.total_lbl.config(text=f"Total Amount: RM {b['fee']:.2f}")

    def method_changed(self):
        """Show the bank list only for FPX."""
        if self.method_var.get() == "FPX":
            self.bank_box.pack(anchor="w", pady=(4, 0))
        else:
            self.bank_box.pack_forget()

    def pay(self):
        method = self.method_var.get()
        if not PaymentManager.is_valid_method(method):
            messagebox.showerror("Payment", "Invalid payment method. Please choose one.")
            return

        # Simulated payment gateway window
        bank = f" via {self.bank_var.get()}" if method == "FPX" else ""
        ok = messagebox.askyesno(
            f"{method} (simulated)",
            f"Pay RM {self.app.booking['fee']:.2f} using {method}{bank}?\n\n"
            "Click YES to simulate a successful payment,\n"
            "or NO to simulate a failed/cancelled payment.")
        if not ok or not PaymentManager.process(method, self.app.booking["fee"]):
            messagebox.showerror("Payment", "Payment failed. Please try again.")   # DISPLAY "Payment failed"
            return

        # Payment successful -> Scene 4: save booking
        record = self.app.courts.save_booking(self.app.booking, self.app.customer, method)
        if record is None:
            messagebox.showerror("Booking", "Sorry, this slot was just taken. "
                                            "Please select another court.")
            self.app.show("court")
            return
        self.app.last_record = record
        self.app.show("completed")


class CompletedPage(tk.Frame):
    """Scene 4: 'Success! You have successfully booked space' + e-receipt."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=app.BG)
        self.app = app

        card = ttk.Frame(self, style="Card.TFrame", padding=20)
        card.pack(pady=20, padx=30)
        tk.Label(card, text="Success!", font=("Segoe UI", 24, "bold"),
                 bg=app.CARD, fg=app.PRIMARY).pack()
        ttk.Label(card, text="You have successfully booked the court.\n"
                             "Payment Status: Successful").pack(pady=(0, 10))
        # Read-only text box that shows the e-receipt
        self.receipt = tk.Text(card, width=48, height=17, font=("Courier New", 10),
                               bg="#fafafa", relief="solid", bd=1)
        self.receipt.pack()
        self.path_lbl = ttk.Label(card, text="", style="Muted.TLabel")
        self.path_lbl.pack(pady=(6, 0))

        ttk.Button(self, text="Back to Home", style="Primary.TButton",
                   command=self.finish).pack(pady=5)

    def on_show(self):
        self.app.stepbar.set_step(4)
        record = self.app.last_record
        text = PaymentManager.build_receipt(record)
        path = PaymentManager.save_receipt(record, text)    # "sends" the e-receipt (saves to file)
        self.receipt.config(state="normal")
        self.receipt.delete("1.0", tk.END)
        self.receipt.insert("1.0", text)
        self.receipt.config(state="disabled")
        self.path_lbl.config(text=f"E-receipt saved: receipts/{os.path.basename(path)}\n"
                                  f"(a copy would be emailed to {record['customer']['email']})")

    def finish(self):
        """Clear the finished booking and return to the home menu."""
        self.app.booking = None
        self.app.show("home")
