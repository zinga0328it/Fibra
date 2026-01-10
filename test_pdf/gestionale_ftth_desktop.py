#!/usr/bin/env python3
"""
GESTIONALE FTTH LOCALE - Versione Desktop Windows
Applicazione standalone per gestione lavori FTTH con estrazione automatica da PDF WR
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
import sqlite3
import os
import json
from datetime import datetime
import pdfplumber
import re
from typing import List, Dict
import threading
import sys

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
        # Campi extra per ONT/modem
        self.requires_ont = False
        self.requires_modem = False
        self.ont_delivered = False
        self.modem_delivered = False
        # Dizionario per campi aggiuntivi da salvare in extra_fields JSON
        self.extra_fields = {}

class FTTHDesktopApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestionale FTTH Locale v1.0")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')

        # Database path
        self.db_path = os.path.join(os.path.dirname(__file__), "gestionale_ftth.db")

        # Inizializza database
        self.init_database()

        # Crea interfaccia
        self.create_widgets()

        # Carica dati esistenti
        self.load_works()

    def init_database(self):
        """Inizializza il database SQLite"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Crea tabella works con tutti i campi
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
                note TEXT,
                requires_ont BOOLEAN DEFAULT FALSE,
                requires_modem BOOLEAN DEFAULT FALSE,
                ont_delivered BOOLEAN DEFAULT FALSE,
                modem_delivered BOOLEAN DEFAULT FALSE,
                extra_fields TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def create_widgets(self):
        """Crea tutti i widget dell'interfaccia"""
        # Frame principale
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Titolo
        title_label = tk.Label(main_frame, text="GESTIONALE FTTH LOCALE",
                              font=('Arial', 16, 'bold'), bg='#f0f0f0', fg='#2E8B57')
        title_label.pack(pady=(0, 20))

        # Frame pulsanti
        button_frame = tk.Frame(main_frame, bg='#f0f0f0')
        button_frame.pack(fill=tk.X, pady=(0, 10))

        # Pulsanti principali
        tk.Button(button_frame, text="📁 Carica PDF WR", command=self.load_pdf,
                 font=('Arial', 10, 'bold'), bg='#4CAF50', fg='white',
                 padx=20, pady=10).pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(button_frame, text="🔍 Cerca Lavori", command=self.search_works,
                 font=('Arial', 10), bg='#2196F3', fg='white',
                 padx=20, pady=10).pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(button_frame, text="📊 Statistiche", command=self.show_stats,
                 font=('Arial', 10), bg='#FF9800', fg='white',
                 padx=20, pady=10).pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(button_frame, text="🗑️ Svuota Database", command=self.clear_database,
                 font=('Arial', 10), bg='#f44336', fg='white',
                 padx=20, pady=10).pack(side=tk.LEFT)

        # Frame ricerca
        search_frame = tk.Frame(main_frame, bg='#f0f0f0')
        search_frame.pack(fill=tk.X, pady=(10, 5))

        tk.Label(search_frame, text="Cerca:", font=('Arial', 10), bg='#f0f0f0').pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=('Arial', 10), width=30)
        self.search_entry.pack(side=tk.LEFT, padx=(5, 10))
        self.search_entry.bind('<KeyRelease>', self.on_search_change)

        # Frame tabella
        table_frame = tk.Frame(main_frame, bg='white', relief=tk.SUNKEN, bd=1)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        # Scrollbar per la tabella
        tree_scroll_y = tk.Scrollbar(table_frame)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        tree_scroll_x = tk.Scrollbar(table_frame, orient=tk.HORIZONTAL)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        # Tabella Treeview
        columns = ('ID', 'WR', 'Cliente', 'Indirizzo', 'Tipo', 'Stato', 'Data', 'ONT', 'Modem')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)

        # Configura colonne
        self.tree.heading('ID', text='ID')
        self.tree.heading('WR', text='N° WR')
        self.tree.heading('Cliente', text='Cliente')
        self.tree.heading('Indirizzo', text='Indirizzo')
        self.tree.heading('Tipo', text='Tipo Lavoro')
        self.tree.heading('Stato', text='Stato')
        self.tree.heading('Data', text='Data Apertura')
        self.tree.heading('ONT', text='ONT')
        self.tree.heading('Modem', text='Modem')

        self.tree.column('ID', width=50, minwidth=50)
        self.tree.column('WR', width=100, minwidth=100)
        self.tree.column('Cliente', width=150, minwidth=150)
        self.tree.column('Indirizzo', width=200, minwidth=200)
        self.tree.column('Tipo', width=120, minwidth=120)
        self.tree.column('Stato', width=80, minwidth=80)
        self.tree.column('Data', width=100, minwidth=100)
        self.tree.column('ONT', width=60, minwidth=60)
        self.tree.column('Modem', width=60, minwidth=60)

        self.tree.pack(fill=tk.BOTH, expand=True)

        tree_scroll_y.config(command=self.tree.yview)
        tree_scroll_x.config(command=self.tree.xview)

        # Bind doppio click per dettagli
        self.tree.bind('<Double-1>', self.show_work_details)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Pronto - Database: gestionale_ftth.db")
        status_bar = tk.Label(main_frame, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

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

        # Ricarica la tabella
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
        """Estrae dati completi WR da testo - versione semplificata per desktop"""
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
                # Estrai numero WR
                wr_match = re.search(r'WR:\s*([^\s]+)', line)
                if wr_match:
                    current_work.numero_wr = wr_match.group(1).strip()

            # Cliente
            elif 'Cliente:' in line or 'NOME_CLIENTE -' in line:
                if 'Cliente:' in line:
                    cliente_part = line.split('Cliente:', 1)[1].strip()
                else:
                    cliente_part = line.split('NOME_CLIENTE -', 1)[1].strip()

                # Rimuovi parti extra
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

            # Campi tecnici - estrai tutto nei extra_fields
            elif ' - ' in line:
                parts = line.split(' - ', 1)
                if len(parts) == 2:
                    key, value = parts[0].strip(), parts[1].strip()
                    # Salva tutti i campi tecnici
                    if any(tech in key.upper() for tech in ['PTE', 'SPLITTER', 'PORTA', 'ODF', 'BUILDING', 'OLT', 'GPON', 'PATCH', 'PERMUTATORE', 'NUMERO', 'NOME', 'TIPO', 'MODELLO']):
                        current_work.extra_fields[key] = value

                        # Flag speciali per ONT/Modem
                        if 'ONT' in key.upper() or 'FIBRA' in key.upper():
                            current_work.requires_ont = True
                        if 'MODEM' in key.upper() or 'ADSL' in key.upper() or 'VDSL' in key.upper():
                            current_work.requires_modem = True

        # Aggiungi l'ultimo work se completo
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
                # Verifica se WR già esiste
                cursor.execute("SELECT id FROM works WHERE numero_wr = ?", (work.numero_wr,))
                if cursor.fetchone():
                    continue  # Salta duplicati

                # Converti extra_fields in JSON
                extra_fields_json = json.dumps(work.extra_fields) if work.extra_fields else None

                # Inserisci work
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

    def load_works(self, search_term=""):
        """Carica e mostra i lavori nella tabella"""
        # Pulisci tabella
        for item in self.tree.get_children():
            self.tree.delete(item)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            if search_term:
                query = """
                    SELECT id, numero_wr, nome_cliente, indirizzo, tipo_lavoro, stato, data_apertura, requires_ont, requires_modem
                    FROM works
                    WHERE numero_wr LIKE ? OR nome_cliente LIKE ? OR indirizzo LIKE ?
                    ORDER BY id DESC
                """
                search_pattern = f"%{search_term}%"
                cursor.execute(query, (search_pattern, search_pattern, search_pattern))
            else:
                cursor.execute("""
                    SELECT id, numero_wr, nome_cliente, indirizzo, tipo_lavoro, stato, data_apertura, requires_ont, requires_modem
                    FROM works
                    ORDER BY id DESC
                """)

            rows = cursor.fetchall()

            for row in rows:
                ont_status = "✅" if row[7] else "❌"
                modem_status = "✅" if row[8] else "❌"

                # Formatta data
                data_display = row[6][:10] if row[6] else ""

                self.tree.insert('', tk.END, values=(
                    row[0], row[1], row[2], row[3], row[4], row[5], data_display, ont_status, modem_status
                ))

            self.status_var.set(f"Trovati {len(rows)} lavori")

        except Exception as e:
            messagebox.showerror("Errore", f"Errore nel caricamento dati:\n{str(e)}")
        finally:
            conn.close()

    def on_search_change(self, event=None):
        """Callback per ricerca in tempo reale"""
        search_term = self.search_var.get().strip()
        self.load_works(search_term)

    def search_works(self):
        """Ricerca avanzata"""
        search_term = self.search_var.get().strip()
        if not search_term:
            messagebox.showinfo("Ricerca", "Inserisci un termine di ricerca")
            return
        self.load_works(search_term)

    def show_work_details(self, event):
        """Mostra dettagli completi del lavoro selezionato"""
        selection = self.tree.selection()
        if not selection:
            return

        item = self.tree.item(selection[0])
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
                details_window.geometry("800x600")

                # Frame scrollabile
                main_frame = tk.Frame(details_window)
                main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

                canvas = tk.Canvas(main_frame)
                scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
                scrollable_frame = tk.Frame(canvas)

                scrollable_frame.bind(
                    "<Configure>",
                    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
                )

                canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
                canvas.configure(yscrollcommand=scrollbar.set)

                # Dati principali
                tk.Label(scrollable_frame, text=f"WR: {row[0]}", font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=(0, 10))

                info_frame = tk.Frame(scrollable_frame)
                info_frame.pack(fill=tk.X, pady=(0, 20))

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
                    tk.Label(scrollable_frame, text="Note:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(20, 5))
                    note_text = scrolledtext.ScrolledText(scrollable_frame, height=3, wrap=tk.WORD)
                    note_text.insert(tk.END, row[7])
                    note_text.config(state=tk.DISABLED)
                    note_text.pack(fill=tk.X, pady=(0, 20))

                # Campi tecnici extra
                if row[10]:
                    tk.Label(scrollable_frame, text="Dati Tecnici FTTH:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(20, 5))

                    try:
                        extra_fields = json.loads(row[10])
                        tech_frame = tk.Frame(scrollable_frame)
                        tech_frame.pack(fill=tk.X, pady=(0, 10))

                        for key, value in extra_fields.items():
                            field_frame = tk.Frame(tech_frame)
                            field_frame.pack(fill=tk.X, pady=1)

                            tk.Label(field_frame, text=f"{key}:", font=('Arial', 9, 'bold'), width=25, anchor=tk.W).pack(side=tk.LEFT)
                            tk.Label(field_frame, text=str(value), font=('Arial', 9)).pack(side=tk.LEFT, padx=(10, 0))

                    except:
                        tk.Label(scrollable_frame, text="Errore nel caricamento dati tecnici", fg='red').pack(anchor=tk.W)

                # Pulsanti
                button_frame = tk.Frame(scrollable_frame)
                button_frame.pack(fill=tk.X, pady=(20, 0))

                tk.Button(button_frame, text="Chiudi", command=details_window.destroy).pack(side=tk.RIGHT)

                canvas.pack(side="left", fill="both", expand=True)
                scrollbar.pack(side="right", fill="y")

        except Exception as e:
            messagebox.showerror("Errore", f"Errore nel caricamento dettagli:\n{str(e)}")
        finally:
            conn.close()

    def show_stats(self):
        """Mostra statistiche del database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Statistiche generali
            cursor.execute("SELECT COUNT(*) FROM works")
            total_works = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM works WHERE stato = 'aperto'")
            open_works = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM works WHERE requires_ont = 1")
            ont_works = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM works WHERE requires_modem = 1")
            modem_works = cursor.fetchone()[0]

            # Finestra statistiche
            stats_window = tk.Toplevel(self.root)
            stats_window.title("Statistiche Gestionale FTTH")
            stats_window.geometry("400x300")

            tk.Label(stats_window, text="📊 STATISTICHE GESTIONALE", font=('Arial', 14, 'bold')).pack(pady=20)

            stats_frame = tk.Frame(stats_window)
            stats_frame.pack(pady=10)

            stats_data = [
                ("Totale Lavori:", total_works),
                ("Lavori Aperti:", open_works),
                ("Richiesta ONT:", ont_works),
                ("Richiesta Modem:", modem_works),
                ("Lavori Chiusi:", total_works - open_works),
            ]

            for label, value in stats_data:
                frame = tk.Frame(stats_frame)
                frame.pack(fill=tk.X, pady=5)
                tk.Label(frame, text=label, font=('Arial', 10, 'bold'), width=15, anchor=tk.W).pack(side=tk.LEFT)
                tk.Label(frame, text=str(value), font=('Arial', 10)).pack(side=tk.LEFT, padx=(10, 0))

            tk.Button(stats_window, text="Chiudi", command=stats_window.destroy).pack(pady=20)

        except Exception as e:
            messagebox.showerror("Errore", f"Errore nel calcolo statistiche:\n{str(e)}")
        finally:
            conn.close()

    def clear_database(self):
        """Svuota completamente il database"""
        if messagebox.askyesno("Conferma", "Sei sicuro di voler svuotare completamente il database?\nQuesta azione non può essere annullata."):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            try:
                cursor.execute("DELETE FROM works")
                cursor.execute("DELETE FROM sqlite_sequence WHERE name='works'")
                conn.commit()

                messagebox.showinfo("Successo", "Database svuotato completamente")
                self.load_works()

            except Exception as e:
                messagebox.showerror("Errore", f"Errore nella pulizia database:\n{str(e)}")
            finally:
                conn.close()

def main():
    root = tk.Tk()
    app = FTTHDesktopApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()