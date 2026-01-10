#!/usr/bin/env python3
"""
GESTIONALE FTTH LOCALE COMPLETO - Versione Desktop Windows
Applicazione standalone completa per gestione lavori FTTH con tutte le funzionalità web
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext, simpledialog
import sqlite3
import os
import json
from datetime import datetime
import pdfplumber
import re
from typing import List, Dict
import threading
import webbrowser

class WorkData:
    def __init__(self):
        self.numero_wr = None
        self.operatore = None
        self.indirizzo = None
        self.nome_cliente = None
        self.tipo_lavoro = None
        self.stato = None
        self.data_apertura = None
        self.note = None
        self.requires_ont = False
        self.requires_modem = False
        self.ont_delivered = False
        self.modem_delivered = False
        self.extra_fields = {}

class Technician:
    def __init__(self):
        self.id = None
        self.nome = None
        self.cognome = None
        self.telefono = None
        self.telegram_id = None

class FTTHCompleteDesktopApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestionale FTTH Completo Locale v2.0")
        self.root.geometry("1400x900")
        self.root.configure(bg='#f0f0f0')

        # Database path
        self.db_path = os.path.join(os.path.dirname(__file__), "gestionale_ftth.db")

        # Inizializza database
        self.init_database()

        # Crea interfaccia principale con tabs
        self.create_main_interface()

        # Carica dati iniziali
        self.load_initial_data()

    def init_database(self):
        """Inizializza il database completo con tutte le tabelle"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Tabella works completa
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS works (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_wr TEXT UNIQUE,
                operatore TEXT,
                indirizzo TEXT,
                tipo_lavoro TEXT,
                nome_cliente TEXT,
                stato TEXT DEFAULT 'aperto',
                data_apertura TEXT,
                data_chiusura TEXT,
                tecnico_assegnato_id INTEGER,
                tecnico_chiusura_id INTEGER,
                note TEXT,
                requires_ont BOOLEAN DEFAULT FALSE,
                requires_modem BOOLEAN DEFAULT FALSE,
                ont_delivered BOOLEAN DEFAULT FALSE,
                modem_delivered BOOLEAN DEFAULT FALSE,
                extra_fields TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabella technicians
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS technicians (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT,
                cognome TEXT,
                telefono TEXT,
                telegram_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabella teams
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def create_main_interface(self):
        """Crea l'interfaccia principale con notebook (tabs)"""
        # Main container
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Titolo
        title_frame = tk.Frame(main_frame, bg='#f0f0f0')
        title_frame.pack(fill=tk.X, pady=(0, 10))

        title_label = tk.Label(title_frame, text="🛠️ GESTIONALE FTTH LOCALE COMPLETO",
                              font=('Arial', 18, 'bold'), bg='#f0f0f0', fg='#2E8B57')
        title_label.pack()

        subtitle_label = tk.Label(title_frame, text="Sistema completo gestione lavori fibra ottica - Tutto locale, zero internet",
                                 font=('Arial', 10), bg='#f0f0f0', fg='#666')
        subtitle_label.pack()

        # Toolbar
        toolbar_frame = tk.Frame(main_frame, bg='#f0f0f0')
        toolbar_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Button(toolbar_frame, text="📁 Carica PDF WR", command=self.load_pdf,
                 font=('Arial', 10, 'bold'), bg='#4CAF50', fg='white',
                 padx=15, pady=8).pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(toolbar_frame, text="📊 Dashboard", command=self.show_dashboard,
                 font=('Arial', 10), bg='#2196F3', fg='white',
                 padx=15, pady=8).pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(toolbar_frame, text="🗑️ Svuota DB", command=self.clear_database,
                 font=('Arial', 10), bg='#f44336', fg='white',
                 padx=15, pady=8).pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(toolbar_frame, text="ℹ️ Info", command=self.show_info,
                 font=('Arial', 10), bg='#9C27B0', fg='white',
                 padx=15, pady=8).pack(side=tk.RIGHT)

        # Notebook (tabs)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Dashboard
        self.dashboard_frame = tk.Frame(self.notebook, bg='#f0f0f0')
        self.notebook.add(self.dashboard_frame, text="📊 Dashboard")

        # Tab 2: Lavori
        self.works_frame = tk.Frame(self.notebook, bg='#f0f0f0')
        self.notebook.add(self.works_frame, text="📋 Lavori")

        # Tab 3: Nuovo Lavoro
        self.new_work_frame = tk.Frame(self.notebook, bg='#f0f0f0')
        self.notebook.add(self.new_work_frame, text="➕ Nuovo Lavoro")

        # Tab 4: Tecnici
        self.technicians_frame = tk.Frame(self.notebook, bg='#f0f0f0')
        self.notebook.add(self.technicians_frame, text="👷 Tecnici")

        # Inizializza tabs
        self.create_dashboard_tab()
        self.create_works_tab()
        self.create_new_work_tab()
        self.create_technicians_tab()

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Pronto - Database: gestionale_ftth.db")
        status_bar = tk.Label(main_frame, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))

    def create_dashboard_tab(self):
        """Crea il tab Dashboard con statistiche"""
        # Stats container
        stats_frame = tk.Frame(self.dashboard_frame, bg='#f0f0f0')
        stats_frame.pack(fill=tk.X, pady=10)

        # Statistiche principali
        self.stats_labels = {}
        stats_data = [
            ("📋 Totale Lavori", "total_works"),
            ("🟢 Aperti", "aperto"),
            ("🟡 In Corso", "in_corso"),
            ("🔵 Sospesi", "sospeso"),
            ("✅ Chiusi", "chiuso"),
            ("🔧 ONT Richiesti", "ont_required"),
            ("📡 Modem Richiesti", "modem_required")
        ]

        for i, (label, key) in enumerate(stats_data):
            frame = tk.Frame(stats_frame, bg='white', relief=tk.RAISED, bd=2)
            frame.grid(row=i//4, column=i%4, padx=5, pady=5, sticky='nsew')

            self.stats_labels[key] = tk.Label(frame, text="0", font=('Arial', 16, 'bold'),
                                            fg='#2E8B57', bg='white')
            self.stats_labels[key].pack(pady=(10, 5))

            tk.Label(frame, text=label, font=('Arial', 9), bg='white').pack(pady=(0, 10))

        # Grafico stati
        chart_frame = tk.Frame(self.dashboard_frame, bg='white', relief=tk.RAISED, bd=2)
        chart_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        tk.Label(chart_frame, text="📈 Distribuzione Stati Lavori", font=('Arial', 12, 'bold'),
                bg='white').pack(pady=10)

        # Placeholder per grafico (potremmo aggiungere matplotlib dopo)
        self.chart_canvas = tk.Canvas(chart_frame, bg='white', height=200)
        self.chart_canvas.pack(fill=tk.X, padx=20, pady=(0, 20))

        # Lavori recenti
        recent_frame = tk.Frame(self.dashboard_frame, bg='white', relief=tk.RAISED, bd=2)
        recent_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        tk.Label(recent_frame, text="🕐 Lavori Recenti", font=('Arial', 12, 'bold'),
                bg='white').pack(pady=10)

        # Lista lavori recenti
        self.recent_listbox = tk.Listbox(recent_frame, height=8, font=('Arial', 9))
        scrollbar = tk.Scrollbar(recent_frame, orient=tk.VERTICAL, command=self.recent_listbox.yview)
        self.recent_listbox.config(yscrollcommand=scrollbar.set)

        self.recent_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=(0, 10))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=(0, 10))

    def create_works_tab(self):
        """Crea il tab Lavori con tabella e ricerca"""
        # Frame controlli
        controls_frame = tk.Frame(self.works_frame, bg='#f0f0f0')
        controls_frame.pack(fill=tk.X, pady=(0, 10))

        # Ricerca
        tk.Label(controls_frame, text="🔍 Cerca:", font=('Arial', 10), bg='#f0f0f0').pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(controls_frame, textvariable=self.search_var, font=('Arial', 10), width=30)
        search_entry.pack(side=tk.LEFT, padx=(5, 10))
        search_entry.bind('<KeyRelease>', self.on_search_change)

        # Filtro stato
        tk.Label(controls_frame, text="📊 Stato:", font=('Arial', 10), bg='#f0f0f0').pack(side=tk.LEFT)
        self.status_filter = tk.StringVar(value="Tutti")
        status_combo = ttk.Combobox(controls_frame, textvariable=self.status_filter,
                                   values=["Tutti", "aperto", "in_corso", "sospeso", "chiuso"],
                                   state="readonly", width=10)
        status_combo.pack(side=tk.LEFT, padx=(5, 10))
        status_combo.bind('<<ComboboxSelected>>', self.on_filter_change)

        # Pulsanti azione
        tk.Button(controls_frame, text="🔄 Aggiorna", command=self.load_works,
                 font=('Arial', 9)).pack(side=tk.RIGHT, padx=(0, 10))

        tk.Button(controls_frame, text="✏️ Modifica", command=self.edit_selected_work,
                 font=('Arial', 9)).pack(side=tk.RIGHT, padx=(0, 10))

        tk.Button(controls_frame, text="🗑️ Elimina", command=self.delete_selected_work,
                 font=('Arial', 9)).pack(side=tk.RIGHT, padx=(0, 10))

        # Tabella lavori
        table_frame = tk.Frame(self.works_frame, bg='white', relief=tk.SUNKEN, bd=1)
        table_frame.pack(fill=tk.BOTH, expand=True)

        # Scrollbar per la tabella
        tree_scroll_y = tk.Scrollbar(table_frame)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        tree_scroll_x = tk.Scrollbar(table_frame, orient=tk.HORIZONTAL)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        # Tabella Treeview
        columns = ('ID', 'WR', 'Cliente', 'Indirizzo', 'Tipo', 'Stato', 'Tecnico', 'Data', 'ONT', 'Modem')
        self.works_tree = ttk.Treeview(table_frame, columns=columns, show='headings', yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)

        # Configura colonne
        self.works_tree.heading('ID', text='ID')
        self.works_tree.heading('WR', text='N° WR')
        self.works_tree.heading('Cliente', text='Cliente')
        self.works_tree.heading('Indirizzo', text='Indirizzo')
        self.works_tree.heading('Tipo', text='Tipo Lavoro')
        self.works_tree.heading('Stato', text='Stato')
        self.works_tree.heading('Tecnico', text='Tecnico')
        self.works_tree.heading('Data', text='Data Apertura')
        self.works_tree.heading('ONT', text='ONT')
        self.works_tree.heading('Modem', text='Modem')

        self.works_tree.column('ID', width=50, minwidth=50)
        self.works_tree.column('WR', width=100, minwidth=100)
        self.works_tree.column('Cliente', width=150, minwidth=150)
        self.works_tree.column('Indirizzo', width=200, minwidth=200)
        self.works_tree.column('Tipo', width=120, minwidth=120)
        self.works_tree.column('Stato', width=80, minwidth=80)
        self.works_tree.column('Tecnico', width=100, minwidth=100)
        self.works_tree.column('Data', width=100, minwidth=100)
        self.works_tree.column('ONT', width=60, minwidth=60)
        self.works_tree.column('Modem', width=60, minwidth=60)

        self.works_tree.pack(fill=tk.BOTH, expand=True)

        tree_scroll_y.config(command=self.works_tree.yview)
        tree_scroll_x.config(command=self.works_tree.xview)

        # Bind doppio click per dettagli
        self.works_tree.bind('<Double-1>', self.show_work_details)

    def create_new_work_tab(self):
        """Crea il tab Nuovo Lavoro con form completo"""
        # Scrollable frame
        canvas = tk.Canvas(self.new_work_frame, bg='#f0f0f0')
        scrollbar = tk.Scrollbar(self.new_work_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#f0f0f0')

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Form container
        form_frame = tk.Frame(scrollable_frame, bg='white', relief=tk.RAISED, bd=2)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        tk.Label(form_frame, text="➕ NUOVO LAVORO FTTH", font=('Arial', 14, 'bold'),
                bg='white', fg='#2E8B57').pack(pady=(20, 30))

        # Crea form fields
        self.form_vars = {}

        # Sezione Dati Principali
        self.create_form_section(form_frame, "📋 DATI PRINCIPALI", [
            ("numero_wr", "Numero WR *", "entry", "Es: 15699897"),
            ("nome_cliente", "Cliente", "entry", "Nome cliente"),
            ("indirizzo", "Indirizzo", "entry", "Via, numero, città"),
            ("tipo_lavoro", "Tipo Lavoro", "combo", ["Attivazione FTTH", "Guasto", "Manutenzione", "Sostituzione"]),
            ("stato", "Stato", "combo", ["aperto", "in_corso", "sospeso", "chiuso"]),
            ("operatore", "Operatore", "entry", "Operatore assegnato"),
        ])

        # Sezione Date
        self.create_form_section(form_frame, "📅 DATE", [
            ("data_apertura", "Data Apertura", "entry", "YYYY-MM-DD HH:MM"),
        ])

        # Sezione Equipaggiamento
        self.create_form_section(form_frame, "🔧 EQUIPAGGIAMENTO", [
            ("requires_ont", "Richiede ONT", "check", False),
            ("requires_modem", "Richiede Modem", "check", False),
            ("ont_delivered", "ONT Consegnato", "check", False),
            ("modem_delivered", "Modem Consegnato", "check", False),
        ])

        # Sezione Note
        self.create_form_section(form_frame, "📝 NOTE", [
            ("note", "Note", "text", "Note aggiuntive..."),
        ])

        # Pulsanti
        buttons_frame = tk.Frame(form_frame, bg='white')
        buttons_frame.pack(fill=tk.X, padx=20, pady=20)

        tk.Button(buttons_frame, text="💾 Salva Lavoro", command=self.save_new_work,
                 font=('Arial', 11, 'bold'), bg='#4CAF50', fg='white',
                 padx=30, pady=10).pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(buttons_frame, text="🧹 Pulisci Form", command=self.clear_form,
                 font=('Arial', 11), bg='#FF9800', fg='white',
                 padx=30, pady=10).pack(side=tk.LEFT)

        tk.Button(buttons_frame, text="📄 Carica da PDF", command=self.load_pdf,
                 font=('Arial', 11), bg='#2196F3', fg='white',
                 padx=30, pady=10).pack(side=tk.RIGHT)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def create_form_section(self, parent, title, fields):
        """Crea una sezione del form"""
        section_frame = tk.Frame(parent, bg='white')
        section_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        tk.Label(section_frame, text=title, font=('Arial', 11, 'bold'),
                bg='white', fg='#666').pack(anchor=tk.W, pady=(0, 10))

        for field_name, label, field_type, default in fields:
            field_frame = tk.Frame(section_frame, bg='white')
            field_frame.pack(fill=tk.X, pady=(0, 8))

            tk.Label(field_frame, text=label, font=('Arial', 9, 'bold'),
                    bg='white', width=15, anchor=tk.W).pack(side=tk.LEFT)

            if field_type == "entry":
                var = tk.StringVar(value=default if isinstance(default, str) and not default.startswith("Es:") else "")
                self.form_vars[field_name] = var
                entry = tk.Entry(field_frame, textvariable=var, font=('Arial', 9), width=40)
                entry.pack(side=tk.LEFT, padx=(10, 0))
                if default.startswith("Es:"):
                    entry.insert(0, default[4:])  # Remove "Es: "
                    entry.config(fg='gray')
                    entry.bind('<FocusIn>', lambda e, entry=entry: self.on_entry_focus_in(e, entry))
                    entry.bind('<FocusOut>', lambda e, entry=entry, placeholder=default[4:]: self.on_entry_focus_out(e, entry, placeholder))

            elif field_type == "combo":
                var = tk.StringVar(value=default[0] if default else "")
                self.form_vars[field_name] = var
                combo = ttk.Combobox(field_frame, textvariable=var, values=default, state="readonly", width=37)
                combo.pack(side=tk.LEFT, padx=(10, 0))

            elif field_type == "check":
                var = tk.BooleanVar(value=default)
                self.form_vars[field_name] = var
                tk.Checkbutton(field_frame, variable=var, bg='white').pack(side=tk.LEFT, padx=(10, 0))

            elif field_type == "text":
                text_frame = tk.Frame(field_frame, bg='white')
                text_frame.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)
                text_widget = tk.Text(text_frame, height=3, width=50, font=('Arial', 9))
                text_widget.pack(fill=tk.X)
                if default:
                    text_widget.insert(tk.END, default)
                self.form_vars[field_name] = text_widget

    def create_technicians_tab(self):
        """Crea il tab Tecnici"""
        # Controlli
        controls_frame = tk.Frame(self.technicians_frame, bg='#f0f0f0')
        controls_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Button(controls_frame, text="➕ Nuovo Tecnico", command=self.add_technician,
                 font=('Arial', 10, 'bold'), bg='#4CAF50', fg='white',
                 padx=15, pady=8).pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(controls_frame, text="🔄 Aggiorna", command=self.load_technicians,
                 font=('Arial', 10)).pack(side=tk.LEFT)

        # Lista tecnici
        list_frame = tk.Frame(self.technicians_frame, bg='white', relief=tk.SUNKEN, bd=1)
        list_frame.pack(fill=tk.BOTH, expand=True)

        # Treeview per tecnici
        columns = ('ID', 'Nome', 'Cognome', 'Telefono', 'Telegram')
        self.tech_tree = ttk.Treeview(list_frame, columns=columns, show='headings')

        for col in columns:
            self.tech_tree.heading(col, text=col)
            self.tech_tree.column(col, width=120)

        # Scrollbar
        scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tech_tree.yview)
        self.tech_tree.config(yscrollcommand=scrollbar.set)

        self.tech_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def on_entry_focus_in(self, event, entry):
        """Gestisce focus in sui campi entry"""
        if entry.get() == entry.placeholder:
            entry.delete(0, tk.END)
            entry.config(fg='black')

    def on_entry_focus_out(self, event, entry, placeholder):
        """Gestisce focus out sui campi entry"""
        if not entry.get():
            entry.insert(0, placeholder)
            entry.config(fg='gray')
        entry.placeholder = placeholder

    def load_initial_data(self):
        """Carica dati iniziali"""
        self.load_dashboard_stats()
        self.load_works()
        self.load_technicians()

    def load_dashboard_stats(self):
        """Carica statistiche per dashboard"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Statistiche base
            cursor.execute("SELECT COUNT(*) FROM works")
            self.stats_labels['total_works'].config(text=str(cursor.fetchone()[0]))

            cursor.execute("SELECT stato, COUNT(*) FROM works GROUP BY stato")
            status_counts = dict(cursor.fetchall())

            for status in ['aperto', 'in_corso', 'sospeso', 'chiuso']:
                count = status_counts.get(status, 0)
                self.stats_labels[status].config(text=str(count))

            # ONT/Modem richiesti
            cursor.execute("SELECT COUNT(*) FROM works WHERE requires_ont = 1")
            self.stats_labels['ont_required'].config(text=str(cursor.fetchone()[0]))

            cursor.execute("SELECT COUNT(*) FROM works WHERE requires_modem = 1")
            self.stats_labels['modem_required'].config(text=str(cursor.fetchone()[0]))

            # Lavori recenti
            cursor.execute("""
                SELECT numero_wr, nome_cliente, stato, data_apertura
                FROM works
                ORDER BY id DESC LIMIT 10
            """)

            self.recent_listbox.delete(0, tk.END)
            for row in cursor.fetchall():
                wr, cliente, stato, data = row
                display_text = f"{wr} - {cliente or 'N/A'} ({stato})"
                self.recent_listbox.insert(tk.END, display_text)

        except Exception as e:
            messagebox.showerror("Errore", f"Errore caricamento statistiche:\n{str(e)}")
        finally:
            conn.close()

    def load_works(self, search_term="", status_filter="Tutti"):
        """Carica e mostra i lavori nella tabella"""
        # Pulisci tabella
        for item in self.works_tree.get_children():
            self.works_tree.delete(item)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            query = """
                SELECT w.id, w.numero_wr, w.nome_cliente, w.indirizzo, w.tipo_lavoro,
                       w.stato, w.operatore, w.data_apertura, w.requires_ont, w.requires_modem
                FROM works w
            """
            params = []

            where_clauses = []
            if search_term:
                where_clauses.append("(w.numero_wr LIKE ? OR w.nome_cliente LIKE ? OR w.indirizzo LIKE ?)")
                params.extend([f"%{search_term}%"] * 3)

            if status_filter != "Tutti":
                where_clauses.append("w.stato = ?")
                params.append(status_filter)

            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)

            query += " ORDER BY w.id DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            for row in rows:
                ont_status = "✅" if row[8] else "❌"
                modem_status = "✅" if row[9] else "❌"

                # Formatta data
                data_display = row[7][:10] if row[7] else ""

                self.works_tree.insert('', tk.END, values=(
                    row[0], row[1], row[2], row[3], row[4], row[5],
                    row[6] or "", data_display, ont_status, modem_status
                ))

            self.status_var.set(f"Lavori trovati: {len(rows)}")

        except Exception as e:
            messagebox.showerror("Errore", f"Errore caricamento lavori:\n{str(e)}")
        finally:
            conn.close()

    def load_technicians(self):
        """Carica tecnici nella tabella"""
        # Pulisci tabella
        for item in self.tech_tree.get_children():
            self.tech_tree.delete(item)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, nome, cognome, telefono, telegram_id
                FROM technicians
                ORDER BY nome, cognome
            """)

            for row in cursor.fetchall():
                telegram_status = "📱" if row[4] else "❌"
                self.tech_tree.insert('', tk.END, values=(
                    row[0], row[1], row[2], row[3] or "", telegram_status
                ))

        except Exception as e:
            messagebox.showerror("Errore", f"Errore caricamento tecnici:\n{str(e)}")
        finally:
            conn.close()

    def on_search_change(self, event=None):
        """Callback per ricerca in tempo reale"""
        search_term = self.search_var.get().strip()
        status_filter = self.status_filter.get()
        self.load_works(search_term, status_filter)

    def on_filter_change(self, event=None):
        """Callback per cambio filtro stato"""
        search_term = self.search_var.get().strip()
        status_filter = self.status_filter.get()
        self.load_works(search_term, status_filter)

    def load_pdf(self):
        """Carica e processa un file PDF WR"""
        file_path = filedialog.askopenfilename(
            title="Seleziona file PDF WR",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )

        if not file_path:
            return

        # Mostra loading
        self.status_var.set("Caricamento PDF in corso...")
        self.root.update()

        # Processa in thread separato per non bloccare UI
        def process_pdf():
            try:
                # Estrai testo dal PDF
                text_content = self.extract_text_from_pdf(file_path)

                # Estrai works
                works = self.extract_works_from_text(text_content)

                # Salva nel database
                saved_count = self.save_works_to_db(works)

                # Aggiorna UI
                self.root.after(0, lambda: self.on_pdf_processed(saved_count, len(works)))

            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Errore", f"Errore nel processamento PDF:\n{str(e)}"))
                self.root.after(0, lambda: self.status_var.set("Errore nel caricamento PDF"))

        thread = threading.Thread(target=process_pdf, daemon=True)
        thread.start()

    def on_pdf_processed(self, saved_count, total_count):
        """Callback dopo processamento PDF"""
        self.status_var.set(f"PDF processato: {saved_count}/{total_count} lavori salvati")
        messagebox.showinfo("Successo",
                          f"PDF processato con successo!\n\n"
                          f"Lavori estratti: {total_count}\n"
                          f"Lavori salvati: {saved_count}")

        # Ricarica dati
        self.load_dashboard_stats()
        self.load_works()

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Estrae testo da un file PDF"""
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text

    def extract_works_from_text(self, text_content: str) -> List[WorkData]:
        """Estrae dati completi WR da testo"""
        works = []
        lines = text_content.split('\n')
        current_work = WorkData()

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Estrazione numero WR
            if line.startswith('WR:') or 'WR:' in line:
                if current_work.numero_wr and current_work.nome_cliente:
                    works.append(current_work)
                current_work = WorkData()
                wr_match = re.search(r'WR:\s*([^\s]+)', line)
                if wr_match:
                    current_work.numero_wr = wr_match.group(1).strip()

            # Cliente
            elif 'Cliente:' in line or 'NOME_CLIENTE -' in line:
                if 'Cliente:' in line:
                    cliente_part = line.split('Cliente:', 1)[1].strip()
                else:
                    cliente_part = line.split('NOME_CLIENTE -', 1)[1].strip()

                cliente_part = cliente_part.split('Indiriz')[0].strip()
                cliente_part = cliente_part.split('Telefono')[0].strip()
                current_work.nome_cliente = cliente_part

            # Indirizzo
            elif 'Indiriz' in line and ':' in line:
                indiriz_part = line.split(':', 1)[1].strip()
                indiriz_part = indiriz_part.split('Comune')[0].strip()
                indiriz_part = indiriz_part.split('Telefono')[0].strip()
                current_work.indirizzo = indiriz_part

            # Tipo lavoro
            elif 'Tipo lavoro:' in line or 'TIPO_LAVORO -' in line:
                if 'Tipo lavoro:' in line:
                    tipo_part = line.split('Tipo lavoro:', 1)[1].strip()
                else:
                    tipo_part = line.split('TIPO_LAVORO -', 1)[1].strip()
                current_work.tipo_lavoro = tipo_part

            # Stato
            elif 'Stato:' in line or 'STATO -' in line:
                if 'Stato:' in line:
                    stato_part = line.split('Stato:', 1)[1].strip()
                else:
                    stato_part = line.split('STATO -', 1)[1].strip()
                current_work.stato = stato_part.lower()

            # Data apertura
            elif 'Data apertura:' in line or 'DATA_APERTURA -' in line:
                if 'Data apertura:' in line:
                    data_part = line.split('Data apertura:', 1)[1].strip()
                else:
                    data_part = line.split('DATA_APERTURA -', 1)[1].strip()
                current_work.data_apertura = data_part

            # Note
            elif 'Note:' in line or 'NOTE -' in line:
                if 'Note:' in line:
                    note_part = line.split('Note:', 1)[1].strip()
                else:
                    note_part = line.split('NOTE -', 1)[1].strip()
                current_work.note = note_part

            # Campi tecnici
            elif ' - ' in line:
                parts = line.split(' - ', 1)
                if len(parts) == 2:
                    key, value = parts[0].strip(), parts[1].strip()
                    if any(tech in key.upper() for tech in ['PTE', 'SPLITTER', 'PORTA', 'ODF', 'BUILDING', 'OLT', 'GPON', 'PATCH', 'PERMUTATORE', 'NUMERO', 'NOME', 'TIPO', 'MODELLO']):
                        current_work.extra_fields[key] = value

                        if 'ONT' in key.upper() or 'FIBRA' in key.upper():
                            current_work.requires_ont = True
                        if 'MODEM' in key.upper() or 'ADSL' in key.upper() or 'VDSL' in key.upper():
                            current_work.requires_modem = True

        # Aggiungi l'ultimo work
        if current_work.numero_wr and current_work.nome_cliente:
            works.append(current_work)

        return works

    def save_works_to_db(self, works: List[WorkData]) -> int:
        """Salva works nel database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        saved_count = 0
        try:
            for work in works:
                cursor.execute("SELECT id FROM works WHERE numero_wr = ?", (work.numero_wr,))
                if cursor.fetchone():
                    continue

                extra_fields_json = json.dumps(work.extra_fields) if work.extra_fields else None

                cursor.execute("""
                    INSERT INTO works (
                        numero_wr, operatore, indirizzo, tipo_lavoro,
                        nome_cliente, stato, data_apertura, note,
                        requires_ont, requires_modem, ont_delivered, modem_delivered,
                        extra_fields
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    work.numero_wr,
                    work.operatore or "Da PDF WR",
                    work.indirizzo,
                    work.tipo_lavoro or "Installazione FTTH",
                    work.nome_cliente,
                    work.stato or "aperto",
                    work.data_apertura or datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    work.note,
                    work.requires_ont,
                    work.requires_modem,
                    work.ont_delivered,
                    work.modem_delivered,
                    extra_fields_json
                ))
                saved_count += 1

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

        return saved_count

    def save_new_work(self):
        """Salva un nuovo lavoro dal form"""
        try:
            # Raccogli dati dal form
            work_data = WorkData()
            work_data.numero_wr = self.form_vars['numero_wr'].get().strip()
            work_data.nome_cliente = self.form_vars['nome_cliente'].get().strip()
            work_data.indirizzo = self.form_vars['indirizzo'].get().strip()
            work_data.tipo_lavoro = self.form_vars['tipo_lavoro'].get()
            work_data.stato = self.form_vars['stato'].get()
            work_data.operatore = self.form_vars['operatore'].get().strip()
            work_data.data_apertura = self.form_vars['data_apertura'].get().strip()
            work_data.note = self.form_vars['note'].get("1.0", tk.END).strip()
            work_data.requires_ont = self.form_vars['requires_ont'].get()
            work_data.requires_modem = self.form_vars['requires_modem'].get()
            work_data.ont_delivered = self.form_vars['ont_delivered'].get()
            work_data.modem_delivered = self.form_vars['modem_delivered'].get()

            # Validazione
            if not work_data.numero_wr:
                messagebox.showerror("Errore", "Il numero WR è obbligatorio!")
                return

            if not work_data.nome_cliente:
                messagebox.showerror("Errore", "Il nome cliente è obbligatorio!")
                return

            # Salva nel database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            try:
                cursor.execute("SELECT id FROM works WHERE numero_wr = ?", (work_data.numero_wr,))
                if cursor.fetchone():
                    messagebox.showerror("Errore", f"Il lavoro WR {work_data.numero_wr} esiste già!")
                    return

                extra_fields_json = json.dumps(work_data.extra_fields) if work_data.extra_fields else None

                cursor.execute("""
                    INSERT INTO works (
                        numero_wr, operatore, indirizzo, tipo_lavoro,
                        nome_cliente, stato, data_apertura, note,
                        requires_ont, requires_modem, ont_delivered, modem_delivered,
                        extra_fields
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    work_data.numero_wr,
                    work_data.operatore or None,
                    work_data.indirizzo or None,
                    work_data.tipo_lavoro or "Installazione FTTH",
                    work_data.nome_cliente,
                    work_data.stato or "aperto",
                    work_data.data_apertura or datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    work_data.note or None,
                    work_data.requires_ont,
                    work_data.requires_modem,
                    work_data.ont_delivered,
                    work_data.modem_delivered,
                    extra_fields_json
                ))

                conn.commit()

                messagebox.showinfo("Successo", f"Lavoro {work_data.numero_wr} salvato con successo!")

                # Pulisci form e ricarica dati
                self.clear_form()
                self.load_dashboard_stats()
                self.load_works()

            except Exception as e:
                conn.rollback()
                messagebox.showerror("Errore", f"Errore nel salvataggio:\n{str(e)}")
            finally:
                conn.close()

        except Exception as e:
            messagebox.showerror("Errore", f"Errore nel processamento del form:\n{str(e)}")

    def clear_form(self):
        """Pulisce tutti i campi del form"""
        for var_name, var in self.form_vars.items():
            if hasattr(var, 'set'):  # StringVar, BooleanVar
                if 'check' in var_name or var_name in ['requires_ont', 'requires_modem', 'ont_delivered', 'modem_delivered']:
                    var.set(False)
                else:
                    var.set("")
            elif hasattr(var, 'delete'):  # Text widget
                var.delete("1.0", tk.END)

    def show_work_details(self, event):
        """Mostra dettagli completi del lavoro selezionato"""
        tree = event.widget
        selection = tree.selection()
        if not selection:
            return

        item = tree.item(selection[0])
        work_id = item['values'][0]

        # Carica dettagli completi
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT numero_wr, operatore, indirizzo, tipo_lavoro, nome_cliente, stato,
                       data_apertura, note, requires_ont, requires_modem, extra_fields
                FROM works WHERE id = ?
            """, (work_id,))

            row = cursor.fetchone()
            if row:
                # Crea finestra dettagli
                details_window = tk.Toplevel(self.root)
                details_window.title(f"Dettagli Lavoro {row[0]}")
                details_window.geometry("700x600")

                # Frame scrollabile
                canvas = tk.Canvas(details_window)
                scrollbar = tk.Scrollbar(details_window, orient=tk.VERTICAL, command=canvas.yview)
                scrollable_frame = tk.Frame(canvas)

                scrollable_frame.bind(
                    "<Configure>",
                    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
                )

                canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

                # Dati principali
                tk.Label(scrollable_frame, text=f"🏗️ LAVORO: {row[0]}", font=('Arial', 14, 'bold')).pack(pady=(20, 20))

                info_frame = tk.Frame(scrollable_frame)
                info_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

                fields = [
                    ("Cliente:", row[4]),
                    ("Indirizzo:", row[2]),
                    ("Tipo Lavoro:", row[3]),
                    ("Stato:", row[5]),
                    ("Data Apertura:", row[6]),
                    ("Operatore:", row[1]),
                    ("Richiede ONT:", "Sì" if row[8] else "No"),
                    ("Richiede Modem:", "Sì" if row[9] else "No"),
                ]

                for i, (label, value) in enumerate(fields):
                    row_frame = tk.Frame(info_frame)
                    row_frame.pack(fill=tk.X, pady=2)

                    tk.Label(row_frame, text=label, font=('Arial', 10, 'bold'), width=15, anchor=tk.W).pack(side=tk.LEFT)
                    tk.Label(row_frame, text=str(value or ""), font=('Arial', 10)).pack(side=tk.LEFT, padx=(10, 0))

                # Note
                if row[7]:
                    tk.Label(scrollable_frame, text="📝 Note:", font=('Arial', 11, 'bold')).pack(anchor=tk.W, padx=20, pady=(20, 5))
                    note_text = scrolledtext.ScrolledText(scrollable_frame, height=4, wrap=tk.WORD)
                    note_text.insert(tk.END, row[7])
                    note_text.config(state=tk.DISABLED)
                    note_text.pack(fill=tk.X, padx=20, pady=(0, 20))

                # Campi tecnici extra
                if row[10]:
                    tk.Label(scrollable_frame, text="🔧 Dati Tecnici FTTH:", font=('Arial', 11, 'bold')).pack(anchor=tk.W, padx=20, pady=(20, 5))

                    try:
                        extra_fields = json.loads(row[10])
                        tech_frame = tk.Frame(scrollable_frame)
                        tech_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

                        for key, value in extra_fields.items():
                            field_frame = tk.Frame(tech_frame)
                            field_frame.pack(fill=tk.X, pady=1)

                            tk.Label(field_frame, text=f"{key}:", font=('Arial', 9, 'bold'), width=25, anchor=tk.W).pack(side=tk.LEFT)
                            tk.Label(field_frame, text=str(value), font=('Arial', 9)).pack(side=tk.LEFT, padx=(10, 0))

                    except:
                        tk.Label(scrollable_frame, text="Errore nel caricamento dati tecnici", fg='red').pack(anchor=tk.W, padx=20)

                # Pulsanti
                button_frame = tk.Frame(scrollable_frame)
                button_frame.pack(fill=tk.X, padx=20, pady=20)

                tk.Button(button_frame, text="✏️ Modifica", command=lambda: self.edit_work(work_id, details_window)).pack(side=tk.LEFT, padx=(0, 10))
                tk.Button(button_frame, text="🗑️ Elimina", command=lambda: self.delete_work(work_id, details_window)).pack(side=tk.LEFT, padx=(0, 10))
                tk.Button(button_frame, text="❌ Chiudi", command=details_window.destroy).pack(side=tk.RIGHT)

                canvas.pack(side="left", fill="both", expand=True)
                scrollbar.pack(side="right", fill="y")

        except Exception as e:
            messagebox.showerror("Errore", f"Errore nel caricamento dettagli:\n{str(e)}")
        finally:
            conn.close()

    def edit_selected_work(self):
        """Modifica il lavoro selezionato"""
        selection = self.works_tree.selection()
        if not selection:
            messagebox.showwarning("Attenzione", "Seleziona un lavoro dalla tabella!")
            return

        item = self.works_tree.item(selection[0])
        work_id = item['values'][0]
        self.edit_work(work_id)

    def edit_work(self, work_id, parent_window=None):
        """Modifica un lavoro esistente"""
        # Carica dati esistenti
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT numero_wr, operatore, indirizzo, tipo_lavoro, nome_cliente, stato,
                       data_apertura, note, requires_ont, requires_modem, ont_delivered, modem_delivered
                FROM works WHERE id = ?
            """, (work_id,))

            row = cursor.fetchone()
            if not row:
                messagebox.showerror("Errore", "Lavoro non trovato!")
                return

            # Crea finestra modifica
            edit_window = tk.Toplevel(self.root)
            edit_window.title(f"Modifica Lavoro {row[0]}")
            edit_window.geometry("600x500")

            # Form
            form_frame = tk.Frame(edit_window, padx=20, pady=20)
            form_frame.pack(fill=tk.BOTH, expand=True)

            tk.Label(form_frame, text=f"✏️ MODIFICA LAVORO: {row[0]}", font=('Arial', 12, 'bold')).pack(pady=(0, 20))

            # Campi editabili
            edit_vars = {}

            fields = [
                ("nome_cliente", "Cliente", row[4]),
                ("indirizzo", "Indirizzo", row[2]),
                ("tipo_lavoro", "Tipo Lavoro", row[3]),
                ("stato", "Stato", row[5]),
                ("operatore", "Operatore", row[1] or ""),
                ("data_apertura", "Data Apertura", row[6]),
            ]

            for field_name, label, value in fields:
                field_frame = tk.Frame(form_frame)
                field_frame.pack(fill=tk.X, pady=(0, 10))

                tk.Label(field_frame, text=f"{label}:", font=('Arial', 10, 'bold'), width=15, anchor=tk.W).pack(side=tk.LEFT)

                if field_name in ['tipo_lavoro', 'stato']:
                    var = tk.StringVar(value=value or "")
                    edit_vars[field_name] = var
                    if field_name == 'tipo_lavoro':
                        values = ["Attivazione FTTH", "Guasto", "Manutenzione", "Sostituzione"]
                    else:
                        values = ["aperto", "in_corso", "sospeso", "chiuso"]
                    combo = ttk.Combobox(field_frame, textvariable=var, values=values, state="readonly", width=30)
                    combo.pack(side=tk.LEFT, padx=(10, 0))
                else:
                    var = tk.StringVar(value=value or "")
                    edit_vars[field_name] = var
                    tk.Entry(field_frame, textvariable=var, width=32).pack(side=tk.LEFT, padx=(10, 0))

            # Checkbox
            check_frame = tk.Frame(form_frame)
            check_frame.pack(fill=tk.X, pady=(10, 20))

            tk.Label(check_frame, text="Equipaggiamento:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(0, 10))

            ont_var = tk.BooleanVar(value=row[8])
            modem_var = tk.BooleanVar(value=row[9])
            ont_delivered_var = tk.BooleanVar(value=row[10])
            modem_delivered_var = tk.BooleanVar(value=row[11])

            edit_vars.update({
                'requires_ont': ont_var,
                'requires_modem': modem_var,
                'ont_delivered': ont_delivered_var,
                'modem_delivered': modem_delivered_var
            })

            tk.Checkbutton(check_frame, text="Richiede ONT", variable=ont_var).pack(anchor=tk.W)
            tk.Checkbutton(check_frame, text="Richiede Modem", variable=modem_var).pack(anchor=tk.W)
            tk.Checkbutton(check_frame, text="ONT Consegnato", variable=ont_delivered_var).pack(anchor=tk.W)
            tk.Checkbutton(check_frame, text="Modem Consegnato", variable=modem_delivered_var).pack(anchor=tk.W)

            # Pulsanti
            button_frame = tk.Frame(form_frame)
            button_frame.pack(fill=tk.X, pady=(20, 0))

            def save_edit():
                try:
                    # Aggiorna database
                    cursor.execute("""
                        UPDATE works SET
                            nome_cliente = ?, indirizzo = ?, tipo_lavoro = ?, stato = ?,
                            operatore = ?, data_apertura = ?, requires_ont = ?, requires_modem = ?,
                            ont_delivered = ?, modem_delivered = ?
                        WHERE id = ?
                    """, (
                        edit_vars['nome_cliente'].get(),
                        edit_vars['indirizzo'].get(),
                        edit_vars['tipo_lavoro'].get(),
                        edit_vars['stato'].get(),
                        edit_vars['operatore'].get(),
                        edit_vars['data_apertura'].get(),
                        edit_vars['requires_ont'].get(),
                        edit_vars['requires_modem'].get(),
                        edit_vars['ont_delivered'].get(),
                        edit_vars['modem_delivered'].get(),
                        work_id
                    ))

                    conn.commit()

                    messagebox.showinfo("Successo", "Lavoro aggiornato con successo!")
                    edit_window.destroy()

                    # Chiudi finestra dettagli se aperta
                    if parent_window:
                        parent_window.destroy()

                    # Ricarica dati
                    self.load_dashboard_stats()
                    self.load_works()

                except Exception as e:
                    messagebox.showerror("Errore", f"Errore nell'aggiornamento:\n{str(e)}")

            tk.Button(button_frame, text="💾 Salva Modifiche", command=save_edit,
                     font=('Arial', 10, 'bold'), bg='#4CAF50', fg='white').pack(side=tk.LEFT, padx=(0, 10))

            tk.Button(button_frame, text="❌ Annulla", command=edit_window.destroy,
                     font=('Arial', 10)).pack(side=tk.RIGHT)

        except Exception as e:
            messagebox.showerror("Errore", f"Errore nel caricamento dati:\n{str(e)}")
        finally:
            conn.close()

    def delete_selected_work(self):
        """Elimina il lavoro selezionato"""
        selection = self.works_tree.selection()
        if not selection:
            messagebox.showwarning("Attenzione", "Seleziona un lavoro dalla tabella!")
            return

        item = self.works_tree.item(selection[0])
        work_id = item['values'][0]
        work_wr = item['values'][1]

        if messagebox.askyesno("Conferma Eliminazione",
                              f"Sei sicuro di voler eliminare il lavoro WR {work_wr}?\n\nQuesta azione non può essere annullata."):
            self.delete_work(work_id)

    def delete_work(self, work_id, parent_window=None):
        """Elimina un lavoro"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM works WHERE id = ?", (work_id,))
            conn.commit()

            messagebox.showinfo("Successo", "Lavoro eliminato con successo!")

            # Chiudi finestra dettagli se aperta
            if parent_window:
                parent_window.destroy()

            # Ricarica dati
            self.load_dashboard_stats()
            self.load_works()

        except Exception as e:
            messagebox.showerror("Errore", f"Errore nell'eliminazione:\n{str(e)}")
        finally:
            conn.close()

    def add_technician(self):
        """Aggiunge un nuovo tecnico"""
        # Finestra aggiunta tecnico
        add_window = tk.Toplevel(self.root)
        add_window.title("Aggiungi Nuovo Tecnico")
        add_window.geometry("400x300")

        form_frame = tk.Frame(add_window, padx=20, pady=20)
        form_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(form_frame, text="👷 AGGIUNGI NUOVO TECNICO", font=('Arial', 12, 'bold')).pack(pady=(0, 20))

        # Campi
        tk.Label(form_frame, text="Nome:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        nome_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=nome_var).pack(fill=tk.X, pady=(0, 10))

        tk.Label(form_frame, text="Cognome:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        cognome_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=cognome_var).pack(fill=tk.X, pady=(0, 10))

        tk.Label(form_frame, text="Telefono:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        telefono_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=telefono_var).pack(fill=tk.X, pady=(0, 10))

        tk.Label(form_frame, text="Telegram ID (opzionale):", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        telegram_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=telegram_var).pack(fill=tk.X, pady=(0, 20))

        def save_technician():
            nome = nome_var.get().strip()
            cognome = cognome_var.get().strip()

            if not nome or not cognome:
                messagebox.showerror("Errore", "Nome e cognome sono obbligatori!")
                return

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            try:
                cursor.execute("""
                    INSERT INTO technicians (nome, cognome, telefono, telegram_id)
                    VALUES (?, ?, ?, ?)
                """, (nome, cognome, telefono_var.get().strip(), telegram_var.get().strip() or None))

                conn.commit()

                messagebox.showinfo("Successo", f"Tecnico {nome} {cognome} aggiunto con successo!")
                add_window.destroy()
                self.load_technicians()

            except Exception as e:
                messagebox.showerror("Errore", f"Errore nell'aggiunta:\n{str(e)}")
            finally:
                conn.close()

        button_frame = tk.Frame(form_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        tk.Button(button_frame, text="💾 Salva", command=save_technician,
                 font=('Arial', 10, 'bold'), bg='#4CAF50', fg='white').pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(button_frame, text="❌ Annulla", command=add_window.destroy,
                 font=('Arial', 10)).pack(side=tk.RIGHT)

    def clear_database(self):
        """Svuota completamente il database"""
        if messagebox.askyesno("Conferma", "Sei sicuro di voler svuotare completamente il database?\n\nQuesta azione eliminerà TUTTI i dati e non può essere annullata."):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            try:
                cursor.execute("DELETE FROM works")
                cursor.execute("DELETE FROM technicians")
                cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('works', 'technicians')")
                conn.commit()

                messagebox.showinfo("Successo", "Database svuotato completamente")
                self.load_dashboard_stats()
                self.load_works()
                self.load_technicians()

            except Exception as e:
                messagebox.showerror("Errore", f"Errore nella pulizia database:\n{str(e)}")
            finally:
                conn.close()

    def show_dashboard(self):
        """Mostra il tab Dashboard"""
        self.notebook.select(0)  # Seleziona tab Dashboard
        self.load_dashboard_stats()  # Ricarica statistiche

    def show_info(self):
        """Mostra informazioni sull'applicazione"""
        info_text = """
GESTIONALE FTTH LOCALE - Versione Desktop Completa

🛠️ FUNZIONALITÀ:
• Estrazione automatica dati da PDF WR (74+ campi)
• Database SQLite locale (zero internet)
• Interfaccia completa con tabs
• Dashboard con statistiche real-time
• Gestione completa lavori FTTH
• Gestione tecnici e squadre
• Ricerca e filtri avanzati

📊 DATI ESTRATTI:
• Dati amministrativi (WR, cliente, indirizzo, stato)
• Dati tecnici FTTH completi (PTE, splitter, OLT, ODF, etc.)
• Equipaggiamento (ONT, Modem, consegna)
• Date e note operative

💾 DATABASE:
• File: gestionale_ftth.db
• Tipo: SQLite (locale)
• Backup: copia il file .db

🔧 INSTALLAZIONE WINDOWS:
1. Installa Python (seleziona "Add to PATH")
2. pip install pdfplumber
3. python gestionale_ftth_desktop.py

📞 SUPPORTO:
Sistema completamente locale - nessun costo operativo.
Backup semplice, dati sempre accessibili.

🚀 PRONTO PER L'USO IMMEDIATO!
        """

        info_window = tk.Toplevel(self.root)
        info_window.title("Informazioni Gestionale FTTH")
        info_window.geometry("600x500")

        text_widget = scrolledtext.ScrolledText(info_window, wrap=tk.WORD, padx=20, pady=20)
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert(tk.END, info_text)
        text_widget.config(state=tk.DISABLED)

        tk.Button(info_window, text="❌ Chiudi", command=info_window.destroy).pack(pady=10)

def main():
    root = tk.Tk()
    app = FTTHCompleteDesktopApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()