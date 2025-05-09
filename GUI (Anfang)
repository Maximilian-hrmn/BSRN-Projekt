import tkinter as tk
from tkinter import Tk, Label, Button, StringVar, Entry, messagebox

#Fenster erstellen 
fenster = Tk()
fenster.title("Chatbox")
fenster.configure(bg="white")
fensterBreite = fenster.winfo_screenwidth()
fensterHoehe = fenster.winfo_screenheight()
fenster.geometry(f"{fensterBreite}x{fensterHoehe}+0+0")

#Eingabe und Button Frame erstellen
frameUnten = tk.Frame(fenster, bg="white")
frameUnten.pack(side="bottom", fill="x", padx=10, pady=5)

#Senden Button erstellen
sendenButton =  Button(frameUnten, text="Senden")
sendenButton.grid(row=0, column=1, padx=10, pady=10)

#Eingabefeld erstellen
eingabe = tk.Entry(frameUnten, width=100)  
eingabe.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

fenster.mainloop()