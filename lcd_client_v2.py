#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox
import requests
import threading

PI_URL = "http://172.20.10.3:8000/lcd"   # <--- your Pi IP

class LCDApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Pi 16×2 LCD Sender")
        self.resizable(False, False)
        self.configure(bg="#2b2b2b")
        self.geometry("400x220")

        #STYLE
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TLabel", background="#2b2b2b", foreground="#ffffff", font=("Segoe UI", 11))
        style.configure("TEntry", fieldbackground="#1e1e1e", foreground="#ffffff", insertcolor="#ffffff", font=("Consolas", 12))
        style.configure("TButton", background="#009688", foreground="#ffffff", font=("Segoe UI", 11, "bold"), borderwidth=0)
        style.map("TButton", background=[("active", "#00796b")])

        #WIDGETS
        ttk.Label(self, text="Line 1 (max 16 chars)").pack(anchor="w", padx=20, pady=(20,0))
        self.l1 = ttk.Entry(self, width=18)
        self.l1.pack(fill="x", padx=20)
        self.l1.focus()

        ttk.Label(self, text="Line 2 (max 16 chars)").pack(anchor="w", padx=20, pady=(10,0))
        self.l2 = ttk.Entry(self, width=18)
        self.l2.pack(fill="x", padx=20)

        btn = ttk.Button(self, text="Send to LCD  ➜", command=self.send)
        btn.pack(pady=15)

        #LCD preview box
        self.preview = tk.Text(self, height=2, width=16, font=("Courier", 14), bg="#000", fg="#00ff00", relief="flat", state="disabled")
        self.preview.pack(pady=(0,10))

        #bindings
        self.l1.bind("<Return>", lambda e: self.l2.focus())
        self.l2.bind("<Return>", lambda e: self.send())

        self.update_preview()

    #LOGIC
    def clear_lcd(self):
        """tell Pi to wipe LCD (writes 16 spaces = hardware clear)"""
        try:
            requests.post(PI_URL, json={"line1": " " * 16, "line2": " " * 16}, timeout=2)
        except Exception:
            pass   # ignore network hiccup
    def update_preview(self):
        self.clear_lcd()
        self.preview.config(state="normal")
        self.preview.delete("1.0", "end")
        self.preview.insert("1.0", f"{self.l1.get():<16}\n{self.l2.get():<16}")
        self.preview.config(state="disabled")

    def send(self):
        self.update_preview()
        payload = {"line1": self.l1.get()[:16], "line2": self.l2.get()[:16]}
        threading.Thread(target=self._post, args=(payload,), daemon=True).start()

    def _post(self, payload):
        try:
            r = requests.post(PI_URL, json=payload, timeout=2)
            r.raise_for_status()
            messagebox.showinfo("Success", "LCD updated!", parent=self)
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

#RUN
if __name__ == "__main__":
    LCDApp().mainloop()
    