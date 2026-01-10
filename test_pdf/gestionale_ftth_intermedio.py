#!/usr/bin/env python3
"""
GESTIONALE FTTH LOCALE INTERMEDIO - Versione con Equipment Tracking
Sistema desktop completo con gestione essenziale modem/ONT per FTTH
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

class Equipment:
    def __init__(self):
        self.id = None
        self.serial_number = None
        self.model = None
        self.type = None  # 'modem' or 'ont'
        self.manufacturer = None
        self.status = 'available'  # available, assigned, configured, installed, faulty
        self.location = None
        self.work_id = None
        self.assigned_date = None
        self.installed_at = None
        self.returned_date = None
        self.configured_date = None
        # Campi specifici modem
        self.wifi_ssid = None
        self.wifi_password = None
        self.admin_username = 'admin'
        self.admin_password = None
        self.sync_method = None  # bridge, pppoe, dhcp
        self.sync_config = None  # dict/JSON
        # Campi specifici ONT
        self.pon_port = None
        self.vlan_id = None
        self.ip_address = None
        # Campi comuni
        self.configuration_notes = None
        self.installation_notes = None
        self.technician_notes = None
        self.created_at = None
        self.updated_at = None

class WorkData:
    def __init__(self):
        self.id = None
        self.numero_wr = None
        self.operatore = None
        self.indirizzo = None
        self.nome_cliente = None
        self.tipo_lavoro = None
        self.stato = 'aperto'
        self.data_apertura = None
        self.note = None
        self.tecnico_assegnato_id = None
        self.modem_id = None
        self.ont_id = None
        self.modem_delivered = False
        self.ont_delivered = False
        self.extra_fields = {}

class Technician:
    def __init__(self):
        self.id = None
        self.nome = None
        self.cognome = None
        self.telefono = None
        self.telegram_id = None

class Team:
    def __init__(self):
        self.id = None
        self.nome = None
        self.created_at = None

class WorkEvent:
    def __init__(self):
        self.id = None
        self.work_id = None
        self.timestamp = None
        self.event_type = None
        self.description = None
        self.user_id = None

class Document:
    def __init__(self):
        self.id = None
        self.filename = None
        self.file_path = None
        self.file_type = None
        self.extracted_text = None
        self.ocr_data = None  # JSON string
        self.uploaded_at = None

class FTTHDesktopIntermediate:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestionale FTTH Locale Intermedio v2.1 - Con Equipment")
        self.root.geometry("1500x900")
        self.root.configure(bg='#f0f0f0')

        # Database path
        self.db_path = os.path.join(os.path.dirname(__file__), "gestionale_ftth_intermedio.db")

        # Inizializza database completo
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
                modem_id INTEGER,
                ont_id INTEGER,
                modem_delivered BOOLEAN DEFAULT FALSE,
                ont_delivered BOOLEAN DEFAULT FALSE,
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

        # Tabella equipment (modem e ont) - SOSTITUISCE LA VECCHIA
        cursor.execute("""
            DROP TABLE IF EXISTS equipment
        """)
        
        # Tabella ONT completa
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS onts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                serial_number TEXT UNIQUE,
                model TEXT,
                manufacturer TEXT,
                status TEXT DEFAULT 'available',
                work_id INTEGER,
                assigned_date TEXT,
                installed_at TEXT,
                returned_date TEXT,
                pon_port TEXT,
                vlan_id INTEGER,
                ip_address TEXT,
                installation_notes TEXT,
                technician_notes TEXT,
                location TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabella Modem completa
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS modems (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                serial_number TEXT UNIQUE,
                model TEXT,
                type TEXT,
                manufacturer TEXT,
                status TEXT DEFAULT 'available',
                work_id INTEGER,
                wifi_ssid TEXT,
                wifi_password TEXT,
                admin_username TEXT DEFAULT 'admin',
                admin_password TEXT,
                sync_method TEXT,
                sync_config TEXT,
                configured_date TEXT,
                installed_at TEXT,
                configuration_notes TEXT,
                installation_notes TEXT,
                location TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabella work_events per audit trail
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS work_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                work_id INTEGER,
                timestamp TEXT,
                event_type TEXT,
                description TEXT,
                user_id INTEGER
            )
        """)

        # Tabella documents per gestione documenti
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                mime TEXT,
                content BLOB,
                uploaded_at TEXT,
                parsed BOOLEAN DEFAULT FALSE,
                parsed_data TEXT,
                applied_work_id INTEGER
            )
        """)

        # Tabella document_applied_works per relazioni many-to-many
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_applied_works (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER,
                work_id INTEGER,
                applied_at TEXT,
                UNIQUE(document_id, work_id)
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

        title_label = tk.Label(title_frame, text="🛠️ GESTIONALE FTTH LOCALE INTERMEDIO",
                              font=('Arial', 18, 'bold'), bg='#f0f0f0', fg='#2E8B57')
        title_label.pack()

        subtitle_label = tk.Label(title_frame, text="Sistema completo gestione lavori + equipment tracking essenziale - Tutto locale, zero internet",
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

        # Tab 5: Equipment (NUOVO)
        self.equipment_frame = tk.Frame(self.notebook, bg='#f0f0f0')
        self.notebook.add(self.equipment_frame, text="📡 Equipment")

        # Tab 6: Documenti
        self.documents_frame = tk.Frame(self.notebook, bg='#f0f0f0')
        self.notebook.add(self.documents_frame, text="📄 Documenti")

        # Tab 7: Statistiche Avanzate
        self.stats_frame = tk.Frame(self.notebook, bg='#f0f0f0')
        self.notebook.add(self.stats_frame, text="📊 Statistiche")

        # Tab 8: Telegram Bot
        self.telegram_frame = tk.Frame(self.notebook, bg='#f0f0f0')
        self.notebook.add(self.telegram_frame, text="📱 Telegram")

        # Inizializza tabs
        self.create_dashboard_tab()
        self.create_works_tab()
        self.create_new_work_tab()
        self.create_technicians_tab()
        self.create_equipment_tab()  # NUOVO
        self.create_documents_tab()
        self.create_stats_tab()
        self.create_telegram_tab()

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Pronto - Database: gestionale_ftth_intermedio.db")
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
            ("📡 Modem Assegnati", "modem_assigned"),
            ("🔧 ONT Assegnati", "ont_assigned"),
            ("📦 Modem Installati", "modem_installed"),
            ("🔌 ONT Installati", "ont_installed")
        ]

        # Crea griglia di statistiche
        for i, (label_text, key) in enumerate(stats_data):
            row = i // 4
            col = i % 4

            stat_frame = tk.Frame(stats_frame, bg='white', relief='raised', bd=2)
            stat_frame.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')

            label = tk.Label(stat_frame, text=label_text, font=('Arial', 10, 'bold'),
                           bg='white', fg='#333')
            label.pack(pady=(10, 5))

            value_label = tk.Label(stat_frame, text="0", font=('Arial', 16, 'bold'),
                                 bg='white', fg='#2E8B57')
            value_label.pack(pady=(0, 10))

            self.stats_labels[key] = value_label

        # Configura grid
        for i in range(4):
            stats_frame.grid_columnconfigure(i, weight=1)

        # Pulsante refresh
        refresh_btn = tk.Button(stats_frame, text="🔄 Aggiorna", command=self.update_dashboard,
                              font=('Arial', 10), bg='#FF9800', fg='white', padx=20, pady=5)
        refresh_btn.grid(row=2, column=0, columnspan=4, pady=(20, 0))

    def create_equipment_tab(self):
        """Crea il tab Equipment per gestione modem/ONT completa"""
        # Toolbar equipment espansa
        toolbar_frame = tk.Frame(self.equipment_frame, bg='#f0f0f0')
        toolbar_frame.pack(fill=tk.X, pady=10)

        # Riga 1: Aggiungi equipment
        add_frame = tk.Frame(toolbar_frame, bg='#f0f0f0')
        add_frame.pack(fill=tk.X, pady=(0, 5))

        tk.Button(add_frame, text="➕ Modem", command=lambda: self.add_equipment('modem'),
                 font=('Arial', 10, 'bold'), bg='#4CAF50', fg='white',
                 padx=15, pady=8).pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(add_frame, text="➕ ONT", command=lambda: self.add_equipment('ont'),
                 font=('Arial', 10, 'bold'), bg='#4CAF50', fg='white',
                 padx=15, pady=8).pack(side=tk.LEFT, padx=(0, 10))

        # Riga 2: Azioni equipment
        actions_frame = tk.Frame(toolbar_frame, bg='#f0f0f0')
        actions_frame.pack(fill=tk.X, pady=(0, 5))

        tk.Button(actions_frame, text="✏️ Modifica", command=self.edit_equipment,
                 font=('Arial', 10), bg='#2196F3', fg='white',
                 padx=15, pady=8).pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(actions_frame, text="🗑️ Elimina", command=self.delete_equipment,
                 font=('Arial', 10), bg='#f44336', fg='white',
                 padx=15, pady=8).pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(actions_frame, text="⚙️ Configura", command=self.configure_equipment,
                 font=('Arial', 10), bg='#FF9800', fg='white',
                 padx=15, pady=8).pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(actions_frame, text="✅ Installato", command=self.mark_equipment_installed,
                 font=('Arial', 10), bg='#9C27B0', fg='white',
                 padx=15, pady=8).pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(actions_frame, text="↩️ Restituisci", command=self.return_equipment,
                 font=('Arial', 10), bg='#607D8B', fg='white',
                 padx=15, pady=8).pack(side=tk.LEFT, padx=(0, 10))

        # Riga 3: Filtri e refresh
        filter_frame = tk.Frame(toolbar_frame, bg='#f0f0f0')
        filter_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(filter_frame, text="Filtro Status:", font=('Arial', 9), bg='#f0f0f0').pack(side=tk.LEFT, padx=(0, 5))

        self.equipment_status_filter = ttk.Combobox(filter_frame, values=['Tutti', 'available', 'assigned', 'configured', 'installed', 'faulty'],
                                                   state='readonly', width=15)
        self.equipment_status_filter.set('Tutti')
        self.equipment_status_filter.pack(side=tk.LEFT, padx=(0, 10))
        self.equipment_status_filter.bind('<<ComboboxSelected>>', lambda e: self.load_equipment_data())

        tk.Label(filter_frame, text="Tipo:", font=('Arial', 9), bg='#f0f0f0').pack(side=tk.LEFT, padx=(0, 5))

        self.equipment_type_filter = ttk.Combobox(filter_frame, values=['Tutti', 'modem', 'ont'],
                                                 state='readonly', width=10)
        self.equipment_type_filter.set('Tutti')
        self.equipment_type_filter.pack(side=tk.LEFT, padx=(0, 10))
        self.equipment_type_filter.bind('<<ComboboxSelected>>', lambda e: self.load_equipment_data())

        tk.Button(filter_frame, text="🔄 Aggiorna", command=self.load_equipment_data,
                 font=('Arial', 10), bg='#607D8B', fg='white',
                 padx=15, pady=8).pack(side=tk.RIGHT)

        # Treeview per equipment
        tree_frame = tk.Frame(self.equipment_frame, bg='white', relief=tk.RAISED, bd=1)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Scrollbars
        v_scrollbar = tk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        h_scrollbar = tk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)

        self.equipment_tree = ttk.Treeview(tree_frame,
                                          yscrollcommand=v_scrollbar.set,
                                          xscrollcommand=h_scrollbar.set)

        v_scrollbar.config(command=self.equipment_tree.yview)
        h_scrollbar.config(command=self.equipment_tree.xview)

        # Colonne
        columns = ('ID', 'Serial Number', 'Tipo', 'Modello', 'Status', 'Work ID', 'Location', 'Installato', 'Note')
        self.equipment_tree['columns'] = columns
        self.equipment_tree.heading('#0', text='')
        self.equipment_tree.column('#0', width=0, stretch=tk.NO)

        for col in columns:
            self.equipment_tree.heading(col, text=col)
            if col == 'ID':
                self.equipment_tree.column(col, width=50, anchor=tk.CENTER)
            elif col == 'Work ID':
                self.equipment_tree.column(col, width=70, anchor=tk.CENTER)
            elif col == 'Installato':
                self.equipment_tree.column(col, width=120, anchor=tk.CENTER)
            else:
                self.equipment_tree.column(col, width=120, anchor=tk.W)

        # Menu contestuale
        self.equipment_menu = tk.Menu(self.equipment_tree, tearoff=0)
        self.equipment_menu.add_command(label="Assegna a Lavoro", command=self.assign_equipment_to_work)
        self.equipment_menu.add_command(label="Modifica", command=self.edit_equipment)
        self.equipment_menu.add_command(label="Configura", command=self.configure_equipment)
        self.equipment_menu.add_command(label="Segna Installato", command=self.mark_equipment_installed)
        self.equipment_menu.add_command(label="Restituisci", command=self.return_equipment)
        self.equipment_menu.add_separator()
        self.equipment_menu.add_command(label="Elimina", command=self.delete_equipment)

        self.equipment_tree.bind("<Button-3>", self.show_equipment_context_menu)

        # Layout
        self.equipment_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Statistiche equipment
        stats_frame = tk.Frame(self.equipment_frame, bg='#f0f0f0')
        stats_frame.pack(fill=tk.X, pady=(0, 10))

        self.equipment_stats_labels = {}
        stats_items = [
            ("📡 Totale Equipment", "total_equipment"),
            ("🟢 Disponibili", "available"),
            ("🟡 Assegnati", "assigned"),
            ("🔵 Configurati", "configured"),
            ("✅ Installati", "installed"),
            ("🔴 Guasti", "faulty"),
        ]

        for i, (label, key) in enumerate(stats_items):
            frame = tk.Frame(stats_frame, bg='#f0f0f0')
            frame.pack(side=tk.LEFT, padx=20 if i > 0 else 10)

            tk.Label(frame, text=label, font=('Arial', 9), bg='#f0f0f0').pack()
            self.equipment_stats_labels[key] = tk.Label(frame, text="0", font=('Arial', 12, 'bold'),
                                                      bg='#f0f0f0', fg='#2E8B57')
            self.equipment_stats_labels[key].pack()

    def show_equipment_context_menu(self, event):
        """Mostra menu contestuale per equipment"""
        item = self.equipment_tree.identify_row(event.y)
        if item:
            self.equipment_tree.selection_set(item)
            self.equipment_menu.post(event.x_root, event.y_root)

    def add_equipment(self, eq_type):
        """Aggiungi nuovo equipment (modem o ONT)"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Aggiungi Nuovo {eq_type.upper()}")
        dialog.geometry("500x600")

        # Form fields comuni
        fields = [
            ("Serial Number", "serial_number", "entry", ""),
            ("Modello", "model", "entry", ""),
            ("Produttore", "manufacturer", "entry", ""),
            ("Location", "location", "entry", ""),
        ]

        # Campi specifici per modem
        if eq_type == 'modem':
            fields.extend([
                ("Tipo Modem", "modem_type", "combo", ["adsl", "vdsl", "fiber"]),
                ("WiFi SSID", "wifi_ssid", "entry", ""),
                ("WiFi Password", "wifi_password", "entry", ""),
                ("Admin Username", "admin_username", "entry", "admin"),
                ("Admin Password", "admin_password", "entry", ""),
                ("Sync Method", "sync_method", "combo", ["bridge", "pppoe", "dhcp"]),
                ("Configuration Notes", "configuration_notes", "text", ""),
            ])
        else:  # ONT
            fields.extend([
                ("PON Port", "pon_port", "entry", ""),
                ("VLAN ID", "vlan_id", "entry", ""),
                ("IP Address", "ip_address", "entry", ""),
            ])

        # Installation Notes comune
        fields.extend([
            ("Installation Notes", "installation_notes", "text", ""),
            ("Technician Notes", "technician_notes", "text", ""),
        ])

        entries = {}
        row = 0

        for label, field_name, field_type, default in fields:
            tk.Label(dialog, text=label).grid(row=row, column=0, sticky='w', padx=10, pady=5)

            if field_type == "entry":
                entry = tk.Entry(dialog, width=40)
                if default:
                    entry.insert(0, default)
                entry.grid(row=row, column=1, padx=10, pady=5)
                entries[field_name] = entry
            elif field_type == "combo":
                combo = ttk.Combobox(dialog, values=default, state='readonly', width=37)
                if default:
                    combo.set(default[0])
                combo.grid(row=row, column=1, padx=10, pady=5)
                entries[field_name] = combo
            elif field_type == "text":
                text = scrolledtext.ScrolledText(dialog, height=3, width=30)
                if default:
                    text.insert(tk.END, default)
                text.grid(row=row, column=1, padx=10, pady=5)
                entries[field_name] = text

            row += 1

        def save_equipment():
            try:
                # Raccogli dati
                data = {
                    'serial_number': entries['serial_number'].get().strip(),
                    'model': entries['model'].get().strip(),
                    'type': eq_type,
                    'manufacturer': entries['manufacturer'].get().strip() or None,
                    'location': entries['location'].get().strip() or None,
                    'status': 'available'
                }

                # Campi specifici
                if eq_type == 'modem':
                    data.update({
                        'wifi_ssid': entries['wifi_ssid'].get().strip() or None,
                        'wifi_password': entries['wifi_password'].get().strip() or None,
                        'admin_username': entries['admin_username'].get().strip() or 'admin',
                        'admin_password': entries['admin_password'].get().strip() or None,
                        'sync_method': entries['sync_method'].get() or None,
                        'configuration_notes': entries['configuration_notes'].get("1.0", tk.END).strip() or None,
                    })
                else:  # ONT
                    data.update({
                        'pon_port': entries['pon_port'].get().strip() or None,
                        'vlan_id': int(entries['vlan_id'].get().strip()) if entries['vlan_id'].get().strip() else None,
                        'ip_address': entries['ip_address'].get().strip() or None,
                    })

                # Campi comuni
                data.update({
                    'installation_notes': entries['installation_notes'].get("1.0", tk.END).strip() or None,
                    'technician_notes': entries['technician_notes'].get("1.0", tk.END).strip() or None,
                })

                # Validazione
                if not data['serial_number'] or not data['model']:
                    messagebox.showerror("Errore", "Serial Number e Modello sono obbligatori!")
                    return

                # Salva nel database
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                # Verifica duplicato
                cursor.execute("SELECT id FROM equipment WHERE serial_number = ?", (data['serial_number'],))
                if cursor.fetchone():
                    messagebox.showerror("Errore", f"Equipment con serial number {data['serial_number']} già esistente!")
                    conn.close()
                    return

                # Converti dict per database
                db_data = data.copy()
                if 'modem_type' in db_data:
                    # Non salvare modem_type separatamente, è già nel type
                    del db_data['modem_type']
                if db_data.get('sync_config'):
                    db_data['sync_config'] = json.dumps(db_data['sync_config'])

                columns = ', '.join(db_data.keys())
                placeholders = ', '.join(['?' for _ in db_data])
                values = list(db_data.values())

                cursor.execute(f"INSERT INTO equipment ({columns}) VALUES ({placeholders})", values)
                conn.commit()
                conn.close()

                messagebox.showinfo("Successo", f"{eq_type.upper()} aggiunto con successo!")
                dialog.destroy()
                self.load_equipment_data()

            except Exception as e:
                messagebox.showerror("Errore", f"Errore nel salvataggio: {str(e)}")

        # Pulsanti
        button_frame = tk.Frame(dialog)
        button_frame.grid(row=row, column=0, columnspan=2, pady=20)

        tk.Button(button_frame, text="💾 Salva", command=save_equipment,
                 bg='#4CAF50', fg='white', padx=20, pady=10).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="❌ Annulla", command=dialog.destroy,
                 bg='#f44336', fg='white', padx=20, pady=10).pack(side=tk.LEFT)

    def edit_equipment(self):
        """Modifica equipment selezionato"""
        selected = self.equipment_tree.selection()
        if not selected:
            messagebox.showwarning("Attenzione", "Seleziona un equipment da modificare!")
            return

        item = self.equipment_tree.item(selected[0])
        eq_id = item['values'][0]
        eq_type = item['values'][2]

        # Carica dati attuali
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM equipment WHERE id = ?", (eq_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            messagebox.showerror("Errore", "Equipment non trovato!")
            return

        # Mappa colonne
        columns = ['id', 'serial_number', 'model', 'type', 'manufacturer', 'status', 'location',
                  'work_id', 'assigned_date', 'installed_at', 'returned_date', 'configured_date',
                  'wifi_ssid', 'wifi_password', 'admin_username', 'admin_password', 'sync_method',
                  'sync_config', 'pon_port', 'vlan_id', 'ip_address', 'configuration_notes',
                  'installation_notes', 'technician_notes', 'created_at', 'updated_at']

        eq_data = dict(zip(columns, row))

        # Dialog modifica
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Modifica {eq_type.upper()}")
        dialog.geometry("500x600")

        # Form simile ad add_equipment ma pre-popolato
        fields = [
            ("Serial Number", "serial_number", "entry", eq_data.get('serial_number', '')),
            ("Modello", "model", "entry", eq_data.get('model', '')),
            ("Produttore", "manufacturer", "entry", eq_data.get('manufacturer', '')),
            ("Location", "location", "entry", eq_data.get('location', '')),
            ("Status", "status", "combo", ["available", "assigned", "configured", "installed", "faulty"]),
        ]

        if eq_type == 'modem':
            fields.extend([
                ("WiFi SSID", "wifi_ssid", "entry", eq_data.get('wifi_ssid', '')),
                ("WiFi Password", "wifi_password", "entry", eq_data.get('wifi_password', '')),
                ("Admin Username", "admin_username", "entry", eq_data.get('admin_username', 'admin')),
                ("Admin Password", "admin_password", "entry", eq_data.get('admin_password', '')),
                ("Sync Method", "sync_method", "combo", ["bridge", "pppoe", "dhcp"]),
                ("Configuration Notes", "configuration_notes", "text", eq_data.get('configuration_notes', '')),
            ])
        else:  # ONT
            fields.extend([
                ("PON Port", "pon_port", "entry", eq_data.get('pon_port', '')),
                ("VLAN ID", "vlan_id", "entry", str(eq_data.get('vlan_id', ''))),
                ("IP Address", "ip_address", "entry", eq_data.get('ip_address', '')),
            ])

        fields.extend([
            ("Installation Notes", "installation_notes", "text", eq_data.get('installation_notes', '')),
            ("Technician Notes", "technician_notes", "text", eq_data.get('technician_notes', '')),
        ])

        entries = {}
        row = 0

        for label, field_name, field_type, default in fields:
            tk.Label(dialog, text=label).grid(row=row, column=0, sticky='w', padx=10, pady=5)

            if field_type == "entry":
                entry = tk.Entry(dialog, width=40)
                entry.insert(0, default or "")
                entry.grid(row=row, column=1, padx=10, pady=5)
                entries[field_name] = entry
            elif field_type == "combo":
                combo = ttk.Combobox(dialog, values=default if isinstance(default, list) else ["available", "assigned", "configured", "installed", "faulty"],
                                   state='readonly', width=37)
                combo.set(default if not isinstance(default, list) else (default[0] if default else "available"))
                combo.grid(row=row, column=1, padx=10, pady=5)
                entries[field_name] = combo
            elif field_type == "text":
                text = scrolledtext.ScrolledText(dialog, height=3, width=30)
                text.insert(tk.END, default or "")
                text.grid(row=row, column=1, padx=10, pady=5)
                entries[field_name] = text

            row += 1

        def update_equipment():
            try:
                # Raccogli dati aggiornati
                data = {
                    'serial_number': entries['serial_number'].get().strip(),
                    'model': entries['model'].get().strip(),
                    'manufacturer': entries['manufacturer'].get().strip() or None,
                    'location': entries['location'].get().strip() or None,
                    'status': entries['status'].get(),
                }

                if eq_type == 'modem':
                    data.update({
                        'wifi_ssid': entries['wifi_ssid'].get().strip() or None,
                        'wifi_password': entries['wifi_password'].get().strip() or None,
                        'admin_username': entries['admin_username'].get().strip() or 'admin',
                        'admin_password': entries['admin_password'].get().strip() or None,
                        'sync_method': entries['sync_method'].get() or None,
                        'configuration_notes': entries['configuration_notes'].get("1.0", tk.END).strip() or None,
                    })
                else:  # ONT
                    data.update({
                        'pon_port': entries['pon_port'].get().strip() or None,
                        'vlan_id': int(entries['vlan_id'].get().strip()) if entries['vlan_id'].get().strip() else None,
                        'ip_address': entries['ip_address'].get().strip() or None,
                    })

                data.update({
                    'installation_notes': entries['installation_notes'].get("1.0", tk.END).strip() or None,
                    'technician_notes': entries['technician_notes'].get("1.0", tk.END).strip() or None,
                    'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })

                # Validazione
                if not data['serial_number'] or not data['model']:
                    messagebox.showerror("Errore", "Serial Number e Modello sono obbligatori!")
                    return

                # Aggiorna database
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                # Verifica che non ci siano duplicati (eccetto se stesso)
                cursor.execute("SELECT id FROM equipment WHERE serial_number = ? AND id != ?",
                             (data['serial_number'], eq_id))
                if cursor.fetchone():
                    messagebox.showerror("Errore", f"Equipment con serial number {data['serial_number']} già esistente!")
                    conn.close()
                    return

                # Costruisci query update
                set_parts = []
                values = []
                for key, value in data.items():
                    if key != 'id':  # Non aggiornare ID
                        set_parts.append(f"{key} = ?")
                        values.append(value)

                values.append(eq_id)  # Per WHERE clause

                cursor.execute(f"UPDATE equipment SET {', '.join(set_parts)} WHERE id = ?", values)
                conn.commit()
                conn.close()

                messagebox.showinfo("Successo", f"{eq_type.upper()} aggiornato con successo!")
                dialog.destroy()
                self.load_equipment_data()

            except Exception as e:
                messagebox.showerror("Errore", f"Errore nell'aggiornamento: {str(e)}")

        # Pulsanti
        button_frame = tk.Frame(dialog)
        button_frame.grid(row=row, column=0, columnspan=2, pady=20)

        tk.Button(button_frame, text="💾 Aggiorna", command=update_equipment,
                 bg='#2196F3', fg='white', padx=20, pady=10).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="❌ Annulla", command=dialog.destroy,
                 bg='#f44336', fg='white', padx=20, pady=10).pack(side=tk.LEFT)

    def delete_equipment(self):
        """Elimina equipment selezionato"""
        selected = self.equipment_tree.selection()
        if not selected:
            messagebox.showwarning("Attenzione", "Seleziona un equipment da eliminare!")
            return

        item = self.equipment_tree.item(selected[0])
        eq_id = item['values'][0]
        eq_type = item['values'][2]
        status = item['values'][4]

        # Verifica se può essere eliminato
        if status in ['assigned', 'installed']:
            messagebox.showerror("Errore", f"Non puoi eliminare equipment {status}!")
            return

        if messagebox.askyesno("Conferma", f"Eliminare {eq_type.upper()} {item['values'][1]}?"):
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM equipment WHERE id = ?", (eq_id,))
                conn.commit()
                conn.close()

                messagebox.showinfo("Successo", f"{eq_type.upper()} eliminato con successo!")
                self.load_equipment_data()

            except Exception as e:
                messagebox.showerror("Errore", f"Errore nell'eliminazione: {str(e)}")

    def configure_equipment(self):
        """Configura equipment selezionato"""
        selected = self.equipment_tree.selection()
        if not selected:
            messagebox.showwarning("Attenzione", "Seleziona un equipment da configurare!")
            return

        item = self.equipment_tree.item(selected[0])
        eq_id = item['values'][0]
        eq_type = item['values'][2]

        if eq_type != 'modem':
            messagebox.showinfo("Info", "La configurazione è disponibile solo per i modem!")
            return

        # Dialog configurazione
        dialog = tk.Toplevel(self.root)
        dialog.title("Configura Modem")
        dialog.geometry("400x500")

        fields = [
            ("WiFi SSID", "wifi_ssid", "entry", ""),
            ("WiFi Password", "wifi_password", "entry", ""),
            ("Admin Password", "admin_password", "entry", ""),
            ("Sync Method", "sync_method", "combo", ["bridge", "pppoe", "dhcp"]),
            ("Configuration Notes", "configuration_notes", "text", ""),
        ]

        entries = {}
        row = 0

        for label, field_name, field_type, default in fields:
            tk.Label(dialog, text=label).grid(row=row, column=0, sticky='w', padx=10, pady=5)

            if field_type == "entry":
                entry = tk.Entry(dialog, width=30)
                entry.grid(row=row, column=1, padx=10, pady=5)
                entries[field_name] = entry
            elif field_type == "combo":
                combo = ttk.Combobox(dialog, values=default, state='readonly', width=27)
                combo.grid(row=row, column=1, padx=10, pady=5)
                entries[field_name] = combo
            elif field_type == "text":
                text = scrolledtext.ScrolledText(dialog, height=3, width=23)
                text.grid(row=row, column=1, padx=10, pady=5)
                entries[field_name] = text

            row += 1

        def save_configuration():
            try:
                config_data = {
                    'wifi_ssid': entries['wifi_ssid'].get().strip() or None,
                    'wifi_password': entries['wifi_password'].get().strip() or None,
                    'admin_password': entries['admin_password'].get().strip() or None,
                    'sync_method': entries['sync_method'].get() or None,
                    'configuration_notes': entries['configuration_notes'].get("1.0", tk.END).strip() or None,
                    'status': 'configured',
                    'configured_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }

                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                set_parts = [f"{key} = ?" for key in config_data.keys()]
                values = list(config_data.values())
                values.append(eq_id)

                cursor.execute(f"UPDATE equipment SET {', '.join(set_parts)} WHERE id = ?", values)
                conn.commit()
                conn.close()

                messagebox.showinfo("Successo", "Modem configurato con successo!")
                dialog.destroy()
                self.load_equipment_data()

            except Exception as e:
                messagebox.showerror("Errore", f"Errore nella configurazione: {str(e)}")

        # Pulsanti
        button_frame = tk.Frame(dialog)
        button_frame.grid(row=row, column=0, columnspan=2, pady=20)

        tk.Button(button_frame, text="⚙️ Configura", command=save_configuration,
                 bg='#FF9800', fg='white', padx=20, pady=10).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="❌ Annulla", command=dialog.destroy,
                 bg='#f44336', fg='white', padx=20, pady=10).pack(side=tk.LEFT)

    def mark_equipment_installed(self):
        """Segna equipment come installato"""
        selected = self.equipment_tree.selection()
        if not selected:
            messagebox.showwarning("Attenzione", "Seleziona un equipment da segnare come installato!")
            return

        item = self.equipment_tree.item(selected[0])
        eq_id = item['values'][0]
        eq_type = item['values'][2]
        status = item['values'][4]

        if status != 'assigned':
            messagebox.showerror("Errore", "L'equipment deve essere assegnato prima di poter essere installato!")
            return

        if messagebox.askyesno("Conferma", f"Segnare {eq_type.upper()} {item['values'][1]} come installato?"):
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute("""
                    UPDATE equipment
                    SET status = 'installed', installed_at = ?, updated_at = ?
                    WHERE id = ?
                """, (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                      datetime.now().strftime('%Y-%m-%d %H:%M:%S'), eq_id))

                conn.commit()
                conn.close()

                messagebox.showinfo("Successo", f"{eq_type.upper()} segnato come installato!")
                self.load_equipment_data()

            except Exception as e:
                messagebox.showerror("Errore", f"Errore nell'aggiornamento: {str(e)}")

    def return_equipment(self):
        """Restituisce equipment al magazzino"""
        selected_items = self.equipment_tree.selection()
        if not selected_items:
            messagebox.showerror("Errore", "Seleziona equipment da restituire!")
            return

        if messagebox.askyesno("Conferma", "Restituire gli equipment selezionati al magazzino?"):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            for item in selected_items:
                eq_item = self.equipment_tree.item(item)
                eq_id = eq_item['values'][0]
                eq_type = eq_item['values'][1]

                try:
                    # Trova lavoro associato
                    cursor.execute("SELECT work_id FROM equipment WHERE id = ?", (eq_id,))
                    work_result = cursor.fetchone()
                    work_id = work_result[0] if work_result else None

                    # Restituisci equipment
                    cursor.execute("""
                        UPDATE equipment
                        SET status = 'available', work_id = NULL, updated_at = ?
                        WHERE id = ?
                    """, (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), eq_id))

                    # Rimuovi associazione dal lavoro
                    if work_id:
                        if eq_type.lower() == 'modem':
                            cursor.execute("UPDATE works SET modem_id = NULL WHERE id = ?", (work_id,))
                        elif eq_type.lower() == 'ont':
                            cursor.execute("UPDATE works SET ont_id = NULL WHERE id = ?", (work_id,))

                        # Aggiungi evento
                        self.add_work_event(work_id, f"Equipment {eq_type} {eq_id} restituito", "returned")

                except Exception as e:
                    messagebox.showerror("Errore", f"Errore restituzione equipment {eq_id}: {str(e)}")

            conn.commit()
            conn.close()

            messagebox.showinfo("Successo", "Equipment restituiti al magazzino!")
            self.load_equipment_data()
            self.load_works_data()

    def delete_equipment(self):
        """Elimina equipment (solo se disponibile)"""
        selected_items = self.equipment_tree.selection()
        if not selected_items:
            messagebox.showerror("Errore", "Seleziona equipment da eliminare!")
            return

        if messagebox.askyesno("Conferma", "Eliminare definitivamente gli equipment selezionati?"):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            for item in selected_items:
                eq_item = self.equipment_tree.item(item)
                eq_id = eq_item['values'][0]

                try:
                    # Verifica che sia disponibile
                    cursor.execute("SELECT status FROM equipment WHERE id = ?", (eq_id,))
                    status = cursor.fetchone()

                    if status and status[0] in ['assigned', 'installed']:
                        messagebox.showerror("Errore", f"Non puoi eliminare equipment {eq_id} - è assegnato/installato!")
                        continue

                    # Elimina
                    cursor.execute("DELETE FROM equipment WHERE id = ?", (eq_id,))

                except Exception as e:
                    messagebox.showerror("Errore", f"Errore eliminazione equipment {eq_id}: {str(e)}")

            conn.commit()
            conn.close()

            messagebox.showinfo("Successo", "Equipment eliminati!")
            self.load_equipment_data()

    def mark_equipment_faulty(self):
        """Marca equipment come guasto"""
        selected_items = self.equipment_tree.selection()
        if not selected_items:
            messagebox.showerror("Errore", "Seleziona equipment guasto!")
            return

        item_id = selected_items[0]

        # Finestra per note guasto
        faulty_window = tk.Toplevel(self.root)
        faulty_window.title("Segnala Guasto Equipment")
        faulty_window.geometry("500x300")

        tk.Label(faulty_window, text="📝 Descrivi il problema riscontrato:",
                font=('Arial', 12, 'bold')).pack(pady=10)

        problem_text = scrolledtext.ScrolledText(faulty_window, height=8, width=50)
        problem_text.pack(pady=10)
        problem_text.insert(tk.END, "Descrivi il guasto riscontrato...")

        def save_faulty():
            problem_desc = problem_text.get("1.0", tk.END).strip()
            if not problem_desc or problem_desc == "Descrivi il guasto riscontrato...":
                messagebox.showerror("Errore", "Descrivi il problema!")
                return

            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                # Get current work_id for logging
                cursor.execute("SELECT work_id, type FROM equipment WHERE id = ?", (item_id,))
                eq_info = cursor.fetchone()

                # Update equipment status
                cursor.execute("""
                    UPDATE equipment SET
                        status = 'faulty',
                        technician_notes = ?,
                        installed_at = NULL
                    WHERE id = ?
                """, (f"GUASTO: {problem_desc}", item_id))

                # Log event
                cursor.execute("""
                    INSERT INTO work_events (event_type, description, equipment_id, work_id, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    'equipment_faulty',
                    f'Equipment segnalato guasto: {problem_desc}',
                    item_id,
                    eq_info[0] if eq_info else None,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ))

                conn.commit()
                conn.close()

                messagebox.showinfo("Successo", "Equipment segnalato come guasto!")
                faulty_window.destroy()
                self.load_equipment_data()

            except Exception as e:
                messagebox.showerror("Errore", f"Errore nel salvataggio: {str(e)}")

        tk.Button(faulty_window, text="💾 Salva Guasto", command=save_faulty,
                 bg='#FF9800', fg='white', padx=20, pady=10).pack(pady=10)

    def configure_equipment_menu(self):
        """Configura il menu contestuale per equipment"""
        self.equipment_menu = tk.Menu(self.equipment_frame, tearoff=0)
        self.equipment_menu.add_command(label="Assegna a Lavoro", command=self.assign_equipment_to_work)
        self.equipment_menu.add_command(label="Installa Equipment", command=self.mark_equipment_installed)
        self.equipment_menu.add_command(label="Restituisci in Magazzino", command=self.return_equipment_to_stock)
        self.equipment_menu.add_command(label="Segnala Guasto", command=self.mark_equipment_faulty)
        self.equipment_menu.add_separator()
        self.equipment_menu.add_command(label="Elimina Equipment", command=self.delete_equipment)

        # Bind right-click
        self.equipment_tree.bind("<Button-3>", self.show_equipment_menu)

    def show_equipment_menu(self, event):
        """Mostra menu contestuale equipment"""
        try:
            self.equipment_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.equipment_menu.grab_release()

    def show_work_details(self):
        """Mostra dettagli lavoro selezionato"""
        selected = self.works_tree.selection()
        if not selected:
            messagebox.showwarning("Attenzione", "Seleziona un lavoro per vedere i dettagli!")
            return

        item = self.works_tree.item(selected[0])
        work_id = item['values'][0]

        # Finestra dettagli lavoro
        details_window = tk.Toplevel(self.root)
        details_window.title(f"Dettagli Lavoro {work_id}")
        details_window.geometry("600x700")

        # Mostra tutti i campi lavoro
        fields = [
            ("ID", item['values'][0]),
            ("WR", item['values'][1]),
            ("Cliente", item['values'][2]),
            ("Indirizzo", item['values'][3]),
            ("Tipo Lavoro", item['values'][4]),
            ("Stato", item['values'][5]),
            ("Tecnico", item['values'][6]),
            ("Data Apertura", item['values'][7]),
            ("Modem ID", item['values'][8]),
            ("ONT ID", item['values'][9]),
        ]

        for label, value in fields:
            frame = tk.Frame(details_window)
            frame.pack(fill=tk.X, padx=20, pady=5)

            tk.Label(frame, text=f"{label}:", font=('Arial', 10, 'bold'), width=20, anchor=tk.W).pack(side=tk.LEFT)
            tk.Label(frame, text=str(value or "N/A"), font=('Arial', 10), anchor=tk.W).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Dettagli modem e ONT se presenti
        if item['values'][8]:
            modem_details = self.get_equipment_details(item['values'][8], 'modem')
            tk.Label(details_window, text="📦 Dettagli Modem", font=('Arial', 12, 'bold')).pack(pady=10)
            self.show_equipment_details_in_window(modem_details, details_window)

        if item['values'][9]:
            ont_details = self.get_equipment_details(item['values'][9], 'ont')
            tk.Label(details_window, text="🔌 Dettagli ONT", font=('Arial', 12, 'bold')).pack(pady=10)
            self.show_equipment_details_in_window(ont_details, details_window)

        tk.Button(details_window, text="❌ Chiudi", command=details_window.destroy).pack(pady=20)

    def get_equipment_details(self, equipment_id, equipment_type):
        """Recupera dettagli equipment da database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        table = "modems" if equipment_type == "modem" else "onts"
        cursor.execute(f"SELECT * FROM {table} WHERE id = ?", (equipment_id,))
        details = cursor.fetchone()

        conn.close()
        return details

    def show_equipment_details_in_window(self, details, window):
        """Mostra dettagli equipment in finestra"""
        if not details:
            return

        columns = ['id', 'serial_number', 'model', 'manufacturer', 'status', 'work_id',
                   'assigned_date', 'installed_at', 'returned_date', 'configured_date',
                   'wifi_ssid', 'wifi_password', 'admin_username', 'admin_password',
                   'sync_method', 'sync_config', 'pon_port', 'vlan_id', 'ip_address',
                   'installation_notes', 'technician_notes', 'created_at', 'updated_at']

        for i, (label, value) in enumerate(zip(columns, details)):
            frame = tk.Frame(window)
            frame.pack(fill=tk.X, padx=20, pady=2)

            tk.Label(frame, text=f"{label}:", font=('Arial', 10, 'bold'), width=20, anchor=tk.W).pack(side=tk.LEFT)
            tk.Label(frame, text=str(value or "N/A"), font=('Arial', 10), anchor=tk.W).pack(side=tk.LEFT, fill=tk.X, expand=True)

    def load_equipment_data(self):
        """Carica dati equipment con filtri"""
        # Pulisci treeview
        for item in self.equipment_tree.get_children():
            self.equipment_tree.delete(item)

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Query con filtri
            query = """
                SELECT id, serial_number, type, model, status, work_id, location,
                       installed_at, installation_notes
                FROM equipment
            """
            params = []

            # Filtro status
            status_filter = self.equipment_status_filter.get()
            if status_filter != 'Tutti':
                query += " WHERE status = ?"
                params.append(status_filter)

            # Filtro tipo
            type_filter = self.equipment_type_filter.get()
            if type_filter != 'Tutti':
                if 'WHERE' in query:
                    query += " AND type = ?"
                else:
                    query += " WHERE type = ?"
                params.append(type_filter)

            query += " ORDER BY id DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            for row in rows:
                eq_id, serial, eq_type, model, status, work_id, location, installed_at, notes = row

                # Formatta installed_at
                installed_str = installed_at[:10] if installed_at else ""

                # Colori per status
                tags = []
                if status == 'available':
                    tags.append('available')
                elif status == 'assigned':
                    tags.append('assigned')
                elif status == 'configured':
                    tags.append('configured')
                elif status == 'installed':
                    tags.append('installed')
                elif status == 'faulty':
                    tags.append('faulty')

                self.equipment_tree.insert('', tk.END, values=(
                    eq_id, serial, eq_type.upper(), model, status, work_id or "", location or "",
                    installed_str, notes or ""
                ), tags=tags)

            # Configura colori
            self.equipment_tree.tag_configure('available', background='#E8F5E8')
            self.equipment_tree.tag_configure('assigned', background='#FFF3E0')
            self.equipment_tree.tag_configure('configured', background='#E3F2FD')
            self.equipment_tree.tag_configure('installed', background='#F3E5F5')
            self.equipment_tree.tag_configure('faulty', background='#FFEBEE')

            # Carica statistiche
            self.load_equipment_stats(cursor)

            conn.close()

        except Exception as e:
            messagebox.showerror("Errore", f"Errore nel caricamento equipment: {str(e)}")

    def assign_equipment_to_work(self):
        """Assegna equipment selezionato a un lavoro"""
        selected_items = self.equipment_tree.selection()
        if not selected_items:
            messagebox.showerror("Errore", "Seleziona un equipment da assegnare!")
            return

        # Finestra selezione lavoro
        work_window = tk.Toplevel(self.root)
        work_window.title("Seleziona Lavoro")
        work_window.geometry("800x600")

        # Lista lavori
        columns = ("ID", "WR", "Cliente", "Indirizzo", "Stato")
        work_tree = ttk.Treeview(work_window, columns=columns, show="headings", height=15)

        for col in columns:
            work_tree.heading(col, text=col)
            work_tree.column(col, width=150)

        scrollbar = ttk.Scrollbar(work_window, orient=tk.VERTICAL, command=work_tree.yview)
        work_tree.configure(yscrollcommand=scrollbar.set)

        work_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)

        # Carica lavori
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, numero_wr, nome_cliente, indirizzo, stato
            FROM works
            WHERE stato IN ('aperto', 'in_corso')
            ORDER BY id DESC
        """)

        for work in cursor.fetchall():
            work_tree.insert("", tk.END, values=work)
        conn.close()

        def assign_selected():
            work_selection = work_tree.selection()
            if not work_selection:
                messagebox.showerror("Errore", "Seleziona un lavoro!")
                return

            work_item = work_tree.item(work_selection[0])
            work_id = work_item['values'][0]

            # Assegna tutti gli equipment selezionati
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            for item in selected_items:
                eq_item = self.equipment_tree.item(item)
                eq_id = eq_item['values'][0]
                eq_type = eq_item['values'][1]

                try:
                    # Verifica che l'equipment sia disponibile
                    cursor.execute("SELECT status, work_id FROM equipment WHERE id = ?", (eq_id,))
                    current = cursor.fetchone()

                    if current and current[0] != 'available':
                        messagebox.showerror("Errore", f"Equipment {eq_id} non disponibile!")
                        continue

                    # Aggiorna equipment
                    cursor.execute("""
                        UPDATE equipment
                        SET status = 'assigned', work_id = ?, updated_at = ?
                        WHERE id = ?
                    """, (work_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), eq_id))

                    # Aggiorna lavoro
                    if eq_type.lower() == 'modem':
                        cursor.execute("UPDATE works SET modem_id = ? WHERE id = ?", (eq_id, work_id))
                    elif eq_type.lower() == 'ont':
                        cursor.execute("UPDATE works SET ont_id = ? WHERE id = ?", (eq_id, work_id))

                    # Aggiungi evento
                    self.add_work_event(work_id, f"Equipment {eq_type} {eq_id} assegnato", "assigned")

                except Exception as e:
                    messagebox.showerror("Errore", f"Errore assegnazione equipment {eq_id}: {str(e)}")

            conn.commit()
            conn.close()

            messagebox.showinfo("Successo", "Equipment assegnati con successo!")
            work_window.destroy()
            self.load_equipment_data()
            self.load_works_data()

        tk.Button(work_window, text="Assegna Selezionati", command=assign_selected,
                 bg='#4CAF50', fg='white', padx=20, pady=10).pack(pady=10)

    def mark_equipment_installed(self):
        """Marca equipment come installato"""
        selected_items = self.equipment_tree.selection()
        if not selected_items:
            messagebox.showerror("Errore", "Seleziona equipment da installare!")
            return

        # Finestra configurazione
        config_window = tk.Toplevel(self.root)
        config_window.title("Configurazione Installazione")
        config_window.geometry("600x500")

        # Form configurazione
        form_frame = tk.Frame(config_window, bg='white', relief=tk.RAISED, bd=2)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        tk.Label(form_frame, text="📡 CONFIGURAZIONE INSTALLAZIONE", font=('Arial', 14, 'bold'),
                bg='white', fg='#2E8B57').pack(pady=(20, 30))

        self.config_vars = {}

        # Sezione WiFi
        self.create_form_section(form_frame, "📶 CONFIGURAZIONE WIFI", [
            ("wifi_ssid", "WiFi SSID", "entry", "Es: ClienteCasa_2.4GHz"),
            ("wifi_password", "WiFi Password", "entry", "Es: Password123"),
        ])

        # Sezione Credenziali Admin
        self.create_form_section(form_frame, "🔐 CREDENZIALI ADMIN", [
            ("admin_username", "Username Admin", "entry", "Es: admin"),
            ("admin_password", "Password Admin", "entry", "Es: password"),
        ])

        # Sezione Note Tecniche
        self.create_form_section(form_frame, "📝 NOTE TECNICHE", [
            ("installation_notes", "Note Installazione", "text", "Descrivi l'installazione..."),
            ("technician_notes", "Note Tecnico", "text", "Note aggiuntive del tecnico..."),
        ])

        # Sezione Problemi
        self.create_form_section(form_frame, "⚠️ PROBLEMI E SOLUZIONI", [
            ("problems", "Problemi Riscontrati", "text", "Descrivi eventuali problemi..."),
            ("solutions", "Soluzioni Applicate", "text", "Descrivi le soluzioni..."),
        ])

        # Pulsanti
        buttons_frame = tk.Frame(form_frame, bg='white')
        buttons_frame.pack(fill=tk.X, padx=20, pady=20)

        tk.Button(buttons_frame, text="✅ Completa Installazione", command=lambda: self.save_installation_config(config_window, selected_items[0]),
                 font=('Arial', 11, 'bold'), bg='#4CAF50', fg='white',
                 padx=30, pady=10).pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(buttons_frame, text="❌ Annulla", command=config_window.destroy,
                 font=('Arial', 11), bg='#f44336', fg='white',
                 padx=30, pady=10).pack(side=tk.LEFT)

    def save_installation_config(self, window, item_id):
        """Salva la configurazione dell'installazione"""
        try:
            # Raccogli dati configurazione
            config_data = {}
            for field_name, var in self.config_vars.items():
                if isinstance(var, tk.StringVar):
                    config_data[field_name] = var.get()
                elif hasattr(var, 'get'):
                    config_data[field_name] = var.get("1.0", tk.END).strip()

            # Aggiorna database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Update equipment con configurazione completa
            cursor.execute("""
                UPDATE equipment SET
                    status = 'installed',
                    installed_at = ?,
                    wifi_ssid = ?,
                    wifi_password = ?,
                    admin_username = ?,
                    admin_password = ?,
                    installation_notes = ?,
                    technician_notes = ?,
                    problems = ?,
                    solutions = ?
                WHERE id = ?
            """, (
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                config_data.get('wifi_ssid'),
                config_data.get('wifi_password'),
                config_data.get('admin_username'),
                config_data.get('admin_password'),
                config_data.get('installation_notes'),
                config_data.get('technician_notes'),
                config_data.get('problems'),
                config_data.get('solutions'),
                item_id
            ))

            # Log event
            cursor.execute("""
                INSERT INTO work_events (event_type, description, equipment_id, created_at)
                VALUES (?, ?, ?, ?)
            """, (
                'equipment_installed',
                f'Equipment installato con configurazione WiFi: {config_data.get("wifi_ssid", "N/A")}',
                item_id,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))

            conn.commit()
            conn.close()

            messagebox.showinfo("Successo", "Installazione completata con successo!")
            window.destroy()
            self.load_equipment_data()

        except Exception as e:
            messagebox.showerror("Errore", f"Errore nel salvataggio configurazione: {str(e)}")

    def return_equipment_to_stock(self):
        """Restituisce equipment in magazzino"""
        selected_items = self.equipment_tree.selection()
        if not selected_items:
            messagebox.showerror("Errore", "Seleziona equipment da restituire!")
            return

        item_id = selected_items[0]

        # Conferma restituzione
        if not messagebox.askyesno("Conferma", "Restituire questo equipment in magazzino?\nLo stato tornerà 'available' e verrà scollegato dal lavoro."):
            return

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get current equipment info
            cursor.execute("SELECT work_id, type FROM equipment WHERE id = ?", (item_id,))
            eq_info = cursor.fetchone()

            if eq_info:
                work_id, eq_type = eq_info

                # Update equipment
                cursor.execute("""
                    UPDATE equipment SET
                        status = 'available',
                        work_id = NULL,
                        installed_at = NULL,
                        wifi_ssid = NULL,
                        wifi_password = NULL,
                        admin_username = NULL,
                        admin_password = NULL,
                        installation_notes = NULL,
                        technician_notes = NULL,
                        problems = NULL,
                        solutions = NULL
                    WHERE id = ?
                """, (item_id,))

                # Update work (remove equipment reference)
                if work_id:
                    if eq_type == 'modem':
                        cursor.execute("UPDATE works SET modem_id = NULL, modem_delivered = FALSE WHERE id = ?", (work_id,))
                    elif eq_type == 'ont':
                        cursor.execute("UPDATE works SET ont_id = NULL, ont_delivered = FALSE WHERE id = ?", (work_id,))

                # Log event
                cursor.execute("""
                    INSERT INTO work_events (event_type, description, equipment_id, work_id, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    'equipment_returned',
                    f'Equipment {eq_type} restituito in magazzino',
                    item_id,
                    work_id,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ))

            conn.commit()
            conn.close()

            messagebox.showinfo("Successo", "Equipment restituito in magazzino!")
            self.load_equipment_data()
            self.load_works_data()

        except Exception as e:
            messagebox.showerror("Errore", f"Errore nella restituzione: {str(e)}")

    def delete_equipment(self):
        """Elimina equipment dal sistema"""
        selected_items = self.equipment_tree.selection()
        if not selected_items:
            messagebox.showerror("Errore", "Seleziona equipment da eliminare!")
            return

        item_id = selected_items[0]

        # Get equipment info for validation
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT status, work_id, type FROM equipment WHERE id = ?", (item_id,))
        eq_info = cursor.fetchone()
        conn.close()

        if eq_info:
            status, work_id, eq_type = eq_info

            # Validation: can only delete available equipment
            if status != 'available':
                messagebox.showerror("Errore", f"Non puoi eliminare equipment con stato '{status}'.\nPrima restituire in magazzino se necessario.")
                return

            if work_id:
                messagebox.showerror("Errore", "Equipment ancora assegnato a un lavoro.\nPrima restituire in magazzino.")
                return

        # Double confirmation
        if not messagebox.askyesno("Conferma Eliminazione",
                                 f"Sei sicuro di voler eliminare questo equipment {eq_type}?\n\nQuesta azione è irreversibile!"):
            return

        if not messagebox.askyesno("ULTIMA CONFERMA",
                                 "Questa è l'ultima possibilità!\nEliminare definitivamente l'equipment?"):
            return

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Log deletion before deleting
            cursor.execute("""
                INSERT INTO work_events (event_type, description, equipment_id, created_at)
                VALUES (?, ?, ?, ?)
            """, (
                'equipment_deleted',
                f'Equipment {eq_type} eliminato dal sistema',
                item_id,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))

            # Delete equipment
            cursor.execute("DELETE FROM equipment WHERE id = ?", (item_id,))

            conn.commit()
            conn.close()

            messagebox.showinfo("Successo", "Equipment eliminato con successo!")
            self.load_equipment_data()

        except Exception as e:
            messagebox.showerror("Errore", f"Errore nell'eliminazione: {str(e)}")

    def add_work_event(self, work_id, description, event_type):
        """Aggiunge un evento al log del lavoro"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO work_events (work_id, timestamp, event_type, description)
                VALUES (?, ?, ?, ?)
            """, (work_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), event_type, description))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Errore log evento: {e}")

    def create_form_section(self, parent, title, fields):
        """Crea una sezione del form"""
        section_frame = tk.Frame(parent, bg='white')
        section_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        tk.Label(section_frame, text=title, font=('Arial', 11, 'bold'),
                bg='white', fg='#666').pack(anchor=tk.W, pady=(0, 10))

        for field_name, label, field_type, default in fields:
            field_frame = tk.Frame(section_frame, bg='white')
            field_frame.pack(fill=tk.X, pady=(0, 8))

            tk.Label(field_frame, text=label, font=('Arial', 10), bg='white',
                    width=15, anchor=tk.W).pack(side=tk.LEFT)

            if field_type == "entry":
                var = tk.StringVar()
                entry = tk.Entry(field_frame, textvariable=var, font=('Arial', 10), width=40)
                entry.pack(side=tk.LEFT, padx=(10, 0))
                if default and default.startswith("Es:"):
                    entry.insert(0, default[4:])
                    entry.config(fg='gray')
                self.form_vars[field_name] = var

            elif field_type == "combo":
                var = tk.StringVar()
                combo = ttk.Combobox(field_frame, textvariable=var, values=default, state='readonly', width=37)
                combo.pack(side=tk.LEFT, padx=(10, 0))
                if isinstance(default, list) and len(default) > 0:
                    combo.set(default[0])
                self.form_vars[field_name] = var

            elif field_type == "check":
                var = tk.BooleanVar(value=default)
                check = tk.Checkbutton(field_frame, variable=var, bg='white')
                check.pack(side=tk.LEFT, padx=(10, 0))
                self.form_vars[field_name] = var

            elif field_type == "text":
                text = scrolledtext.ScrolledText(field_frame, height=3, width=40, font=('Arial', 10))
                text.pack(side=tk.LEFT, padx=(10, 0))
                text.insert(tk.END, default)
                self.form_vars[field_name] = text

    def load_initial_data(self):
        """Carica tutti i dati iniziali"""
        self.update_dashboard()
        self.load_works_data()
        self.load_equipment_data()
        self.load_technicians_data()

    def update_dashboard(self):
        """Aggiorna le statistiche del dashboard"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Totale lavori
            cursor.execute("SELECT COUNT(*) FROM works")
            total = cursor.fetchone()[0]
            self.stats_labels['total_works'].config(text=str(total))

            # Per stato
            for stato in ['aperto', 'in_corso', 'sospeso', 'chiuso']:
                cursor.execute("SELECT COUNT(*) FROM works WHERE stato = ?", (stato,))
                count = cursor.fetchone()[0]
                if stato in self.stats_labels:
                    self.stats_labels[stato].config(text=str(count))

            # Equipment stats
            cursor.execute("SELECT COUNT(*) FROM equipment WHERE type='modem' AND status='assigned'")
            self.stats_labels['modem_assigned'].config(text=str(cursor.fetchone()[0]))

            cursor.execute("SELECT COUNT(*) FROM equipment WHERE type='ont' AND status='assigned'")
            self.stats_labels['ont_assigned'].config(text=str(cursor.fetchone()[0]))

            cursor.execute("SELECT COUNT(*) FROM equipment WHERE type='modem' AND status='installed'")
            self.stats_labels['modem_installed'].config(text=str(cursor.fetchone()[0]))

            cursor.execute("SELECT COUNT(*) FROM equipment WHERE type='ont' AND status='installed'")
            self.stats_labels['ont_installed'].config(text=str(cursor.fetchone()[0]))

            conn.close()
        except Exception as e:
            print(f"Errore aggiornamento dashboard: {e}")

    def load_works_data(self):
        """Carica i lavori nella tabella"""
        # Pulisci tabella
        for item in self.works_tree.get_children():
            self.works_tree.delete(item)

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            query = """
                SELECT w.id, w.numero_wr, w.nome_cliente, w.indirizzo, w.tipo_lavoro, w.stato,
                       t.nome || ' ' || t.cognome, w.modem_id, w.ont_id
                FROM works w
                LEFT JOIN technicians t ON w.tecnico_assegnato_id = t.id
            """
            params = []

            # Filtro stato
            status_filter = self.status_filter.get()
            if status_filter != 'Tutti':
                query += " WHERE w.stato = ?"
                params.append(status_filter)

            # Filtro ricerca
            search_term = self.search_var.get().strip()
            if search_term:
                if 'WHERE' in query:
                    query += " AND (w.numero_wr LIKE ? OR w.nome_cliente LIKE ? OR w.indirizzo LIKE ?)"
                else:
                    query += " WHERE (w.numero_wr LIKE ? OR w.nome_cliente LIKE ? OR w.indirizzo LIKE ?)"
                params.extend([f'%{search_term}%'] * 3)

            query += " ORDER BY w.id DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            for row in rows:
                modem_info = f"M:{row[7]}" if row[7] else "-"
                ont_info = f"O:{row[8]}" if row[8] else "-"
                self.works_tree.insert('', tk.END, values=(row[0], row[1], row[2], row[3], row[4], row[5], row[6] or "-", f"{modem_info}/{ont_info}"))

            conn.close()
        except Exception as e:
            messagebox.showerror("Errore", f"Errore caricamento lavori: {str(e)}")

    def load_technicians_data(self):
        """Carica i tecnici nella tabella"""
        for item in self.technicians_tree.get_children():
            self.technicians_tree.delete(item)

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome, cognome, telefono, telegram_id FROM technicians ORDER BY nome")
            rows = cursor.fetchall()
            for row in rows:
                self.technicians_tree.insert('', tk.END, values=row)
            conn.close()
        except Exception as e:
            print(f"Errore caricamento tecnici: {e}")

    def create_works_tab(self):
        """Crea il tab Lavori"""
        # Toolbar
        toolbar = tk.Frame(self.works_frame, bg='#f0f0f0')
        toolbar.pack(fill=tk.X, pady=10)

        # Ricerca
        tk.Label(toolbar, text="🔍 Cerca:", bg='#f0f0f0').pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(toolbar, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind('<KeyRelease>', lambda e: self.load_works_data())

        # Filtro stato
        tk.Label(toolbar, text="Stato:", bg='#f0f0f0').pack(side=tk.LEFT, padx=(20, 5))
        self.status_filter = ttk.Combobox(toolbar, values=['Tutti', 'aperto', 'in_corso', 'sospeso', 'chiuso'], state='readonly', width=12)
        self.status_filter.set('Tutti')
        self.status_filter.pack(side=tk.LEFT)
        self.status_filter.bind('<<ComboboxSelected>>', lambda e: self.load_works_data())

        # Tabella lavori
        columns = ('ID', 'WR', 'Cliente', 'Indirizzo', 'Tipo', 'Stato', 'Tecnico', 'Equipment')
        self.works_tree = ttk.Treeview(self.works_frame, columns=columns, show='headings', height=20)

        for col in columns:
            self.works_tree.heading(col, text=col)
            self.works_tree.column(col, width=100)

        self.works_tree.pack(fill=tk.BOTH, expand=True, pady=10)

        # Scrollbar
        scrollbar = ttk.Scrollbar(self.works_frame, orient=tk.VERTICAL, command=self.works_tree.yview)
        self.works_tree.configure(yscrollcommand=scrollbar.set)

    def create_new_work_tab(self):
        """Crea il tab Nuovo Lavoro"""
        canvas = tk.Canvas(self.new_work_frame, bg='#f0f0f0')
        scrollbar = tk.Scrollbar(self.new_work_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#f0f0f0')

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        form_frame = tk.Frame(scrollable_frame, bg='white', relief=tk.RAISED, bd=2)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        tk.Label(form_frame, text="➕ NUOVO LAVORO FTTH", font=('Arial', 14, 'bold'),
                bg='white', fg='#2E8B57').pack(pady=(20, 30))

        self.form_vars = {}

        self.create_form_section(form_frame, "📋 DATI PRINCIPALI", [
            ("numero_wr", "Numero WR *", "entry", "Es: 15699897"),
            ("nome_cliente", "Cliente", "entry", "Es: Mario Rossi"),
            ("indirizzo", "Indirizzo", "entry", "Es: Via Roma 123"),
            ("tipo_lavoro", "Tipo Lavoro", "combo", ["Attivazione FTTH", "Guasto", "Manutenzione"]),
            ("stato", "Stato", "combo", ["aperto", "in_corso", "sospeso", "chiuso"]),
            ("operatore", "Operatore", "entry", "Es: Fastweb"),
        ])

        self.create_form_section(form_frame, "📝 NOTE", [
            ("note", "Note", "text", "Note aggiuntive..."),
        ])

        # Pulsanti
        btn_frame = tk.Frame(form_frame, bg='white')
        btn_frame.pack(fill=tk.X, padx=20, pady=20)

        tk.Button(btn_frame, text="💾 Salva Lavoro", command=self.save_new_work,
                 font=('Arial', 11, 'bold'), bg='#4CAF50', fg='white', padx=30, pady=10).pack(side=tk.LEFT)

        tk.Button(btn_frame, text="📄 Carica da PDF", command=self.load_pdf,
                 font=('Arial', 11), bg='#2196F3', fg='white', padx=30, pady=10).pack(side=tk.RIGHT)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def save_new_work(self):
        """Salva nuovo lavoro nel database"""
        try:
            work_data = {}
            for field_name, var in self.form_vars.items():
                if isinstance(var, tk.StringVar):
                    work_data[field_name] = var.get()
                elif isinstance(var, tk.BooleanVar):
                    work_data[field_name] = var.get()
                elif hasattr(var, 'get'):
                    work_data[field_name] = var.get("1.0", tk.END).strip()

            if not work_data.get('numero_wr', '').strip():
                messagebox.showerror("Errore", "Il numero WR è obbligatorio!")
                return

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO works (numero_wr, operatore, indirizzo, tipo_lavoro, nome_cliente, stato, data_apertura, note)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                work_data.get('numero_wr'),
                work_data.get('operatore'),
                work_data.get('indirizzo'),
                work_data.get('tipo_lavoro'),
                work_data.get('nome_cliente'),
                work_data.get('stato', 'aperto'),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                work_data.get('note')
            ))

            conn.commit()
            conn.close()

            messagebox.showinfo("Successo", "Lavoro salvato con successo!")
            self.load_initial_data()

        except Exception as e:
            messagebox.showerror("Errore", f"Errore nel salvataggio: {str(e)}")

    def create_technicians_tab(self):
        """Crea il tab Tecnici"""
        toolbar = tk.Frame(self.technicians_frame, bg='#f0f0f0')
        toolbar.pack(fill=tk.X, pady=10)

        tk.Button(toolbar, text="➕ Nuovo Tecnico", command=self.add_technician,
                 bg='#4CAF50', fg='white', padx=15, pady=5).pack(side=tk.LEFT)

        columns = ('ID', 'Nome', 'Cognome', 'Telefono', 'Telegram')
        self.technicians_tree = ttk.Treeview(self.technicians_frame, columns=columns, show='headings', height=15)

        for col in columns:
            self.technicians_tree.heading(col, text=col)
            self.technicians_tree.column(col, width=120)

        self.technicians_tree.pack(fill=tk.BOTH, expand=True, pady=10)

    def add_technician(self):
        """Aggiunge un nuovo tecnico"""
        add_window = tk.Toplevel(self.root)
        add_window.title("Nuovo Tecnico")
        add_window.geometry("400x300")

        form_frame = tk.Frame(add_window, bg='white', padx=20, pady=20)
        form_frame.pack(fill=tk.BOTH, expand=True)

        entries = {}
        for label in ['Nome', 'Cognome', 'Telefono', 'Telegram ID']:
            row = tk.Frame(form_frame, bg='white')
            row.pack(fill=tk.X, pady=5)
            tk.Label(row, text=label, width=12, anchor='w', bg='white').pack(side=tk.LEFT)
            entry = tk.Entry(row, width=30)
            entry.pack(side=tk.LEFT)
            entries[label.lower().replace(' ', '_')] = entry

        def save():
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO technicians (nome, cognome, telefono, telegram_id)
                    VALUES (?, ?, ?, ?)
                """, (entries['nome'].get(), entries['cognome'].get(), entries['telefono'].get(), entries['telegram_id'].get()))
                conn.commit()
                conn.close()
                messagebox.showinfo("Successo", "Tecnico aggiunto!")
                add_window.destroy()
                self.load_technicians_data()
            except Exception as e:
                messagebox.showerror("Errore", str(e))

        tk.Button(form_frame, text="💾 Salva", command=save, bg='#4CAF50', fg='white', padx=20, pady=10).pack(pady=20)

    def create_documents_tab(self):
        """Crea il tab Documenti"""
        toolbar = tk.Frame(self.documents_frame, bg='#f0f0f0')
        toolbar.pack(fill=tk.X, pady=10)

        tk.Button(toolbar, text="📄 Carica Documento", command=self.upload_document,
                 bg='#4CAF50', fg='white', padx=15, pady=5).pack(side=tk.LEFT)

        tk.Label(self.documents_frame, text="� Gestione Documenti\n\nCarica PDF/immagini per estrazione automatica dati",
                font=('Arial', 12), bg='#f0f0f0').pack(pady=50)

    def upload_document(self):
        """Carica un documento"""
        file_path = filedialog.askopenfilename(
            title="Seleziona documento",
            filetypes=[("PDF files", "*.pdf"), ("Images", "*.png *.jpg *.jpeg"), ("All files", "*.*")]
        )
        if file_path:
            messagebox.showinfo("Info", f"Documento selezionato: {os.path.basename(file_path)}\n\nFunzionalità in sviluppo...")

    def create_stats_tab(self):
        """Crea il tab Statistiche"""
        tk.Label(self.stats_frame, text="📊 Statistiche Avanzate\n\nReport settimanali, KPI, analisi performance",
                font=('Arial', 12), bg='#f0f0f0').pack(pady=50)

        tk.Button(self.stats_frame, text="📈 Genera Report", command=lambda: messagebox.showinfo("Info", "Funzionalità in sviluppo..."),
                 bg='#2196F3', fg='white', padx=20, pady=10).pack()

    def create_telegram_tab(self):
        """Crea il tab Telegram"""
        tk.Label(self.telegram_frame, text="📱 Telegram Bot\n\nNotifiche automatiche e linking tecnici",
                font=('Arial', 12), bg='#f0f0f0').pack(pady=50)

        tk.Button(self.telegram_frame, text="🔗 Configura Bot", command=lambda: messagebox.showinfo("Info", "Funzionalità in sviluppo..."),
                 bg='#9C27B0', fg='white', padx=20, pady=10).pack()

    def load_pdf(self):
        """Carica dati da PDF"""
        file_path = filedialog.askopenfilename(
            title="Seleziona PDF WR",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with pdfplumber.open(file_path) as pdf:
                    text = ""
                    for page in pdf.pages:
                        text += page.extract_text() or ""

                    # Parse basic data from text
                    self.parse_pdf_data(text)
                    messagebox.showinfo("Successo", "PDF caricato! Verifica i dati nel form.")
            except Exception as e:
                messagebox.showerror("Errore", f"Errore lettura PDF: {str(e)}")

    def parse_pdf_data(self, text):
        """Estrae dati dal testo PDF"""
        lines = text.split('\n')
        for line in lines:
            line_lower = line.lower()
            if 'wr' in line_lower and ':' in line:
                value = line.split(':')[-1].strip()
                if 'numero_wr' in self.form_vars:
                    self.form_vars['numero_wr'].set(value)
            elif 'cliente' in line_lower and ':' in line:
                value = line.split(':')[-1].strip()
                if 'nome_cliente' in self.form_vars:
                    self.form_vars['nome_cliente'].set(value)
            elif 'indirizzo' in line_lower and ':' in line:
                value = line.split(':')[-1].strip()
                if 'indirizzo' in self.form_vars:
                    self.form_vars['indirizzo'].set(value)

    def show_info(self):
        """Mostra info applicazione"""
        info = """
GESTIONALE FTTH INTERMEDIO v2.2

✅ Gestione Lavori completa
✅ Equipment Tracking (Modem/ONT)
✅ Tecnici
✅ Dashboard statistiche
✅ Estrazione PDF
✅ Audit Trail

📁 Database: gestionale_ftth_intermedio.db
🖥️ Tutto locale, zero internet
        """
        messagebox.showinfo("Info", info)

    def clear_database(self):
        """Svuota il database"""
        if messagebox.askyesno("Conferma", "Svuotare TUTTO il database?\n\nQuesta azione è irreversibile!"):
            if messagebox.askyesno("ULTIMA CONFERMA", "Sei SICURO? Tutti i dati verranno eliminati!"):
                try:
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM works")
                    cursor.execute("DELETE FROM equipment")
                    cursor.execute("DELETE FROM technicians")
                    cursor.execute("DELETE FROM work_events")
                    cursor.execute("DELETE FROM documents")
                    conn.commit()
                    conn.close()
                    messagebox.showinfo("Successo", "Database svuotato!")
                    self.load_initial_data()
                except Exception as e:
                    messagebox.showerror("Errore", str(e))

    def show_dashboard(self):
        """Mostra tab dashboard"""
        self.notebook.select(0)

def main():
    root = tk.Tk()
    app = FTTHDesktopIntermediate(root)
    root.mainloop()

if __name__ == "__main__":
    main()