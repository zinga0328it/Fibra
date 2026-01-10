# 🔄 Workflow Equipment - Da Implementare

**Data**: 7 Gennaio 2026
**Riferimento**: FTTH-Equipment-Workflow.md (Obsidian)

## 🎯 WORKFLOW COMPLETO EQUIPMENT (Target)

Basato sul workflow documentato nel sistema FTTH originale.

### Stati Equipment
```
available → assigned → delivered → installed → returned/faulty
```

### Operazioni Necessarie (Mancanti)

## 1. 📦 CONSEGNA EQUIPMENT (Delivery)

### Attuale: Parziale
- [x] Assegnazione equipment al lavoro (`assign_equipment_to_work`)
- [ ] **MANCANTE**: Segnatura consegna al cliente

### Necessario Implementare
```python
def mark_equipment_delivered(self, equipment_id, work_id):
    """Segna equipment come consegnato al cliente"""
    # Update work: modem_delivered = True / ont_delivered = True
    # Update equipment: status rimane 'assigned'
    # Log event: delivery timestamp
```

**UI**: Checkbox "Consegnato" nel dettaglio lavoro

## 2. ✅ INSTALLAZIONE EQUIPMENT (Installation)

### Attuale: Incompleto
- [ ] Funzione `mark_equipment_installed()` esistente ma incompleta

### Necessario Implementare
```python
def complete_equipment_installation(self, equipment_id):
    """Form completo installazione con configurazione"""
    # Form fields necessari:
    # - Data installazione (auto)
    # - Note tecniche
    # - Configurazione WiFi (SSID, password, sicurezza)
    # - Credenziali admin (username, password)
    # - Note tecnico
    # - Problemi riscontrati
```

**UI**: Finestra popup "Installazione Equipment" con form dettagliato

## 3. 🔄 RESTITUZIONE EQUIPMENT (Return)

### Attuale: Assente
- [ ] Completamente da implementare

### Necessario Implementare
```python
def return_equipment_to_stock(self, equipment_id, reason):
    """Restituisce equipment in magazzino"""
    # Update equipment: status = 'available', work_id = NULL
    # Update work: modem_id/ont_id = NULL, delivered = False
    # Log event: return reason
```

**UI**: Pulsante "Restituisci" nel menu equipment

## 4. 🗑️ ELIMINAZIONE EQUIPMENT (Delete)

### Attuale: Assente
- [ ] Completamente da implementare

### Necessario Implementare
```python
def delete_equipment(self, equipment_id):
    """Elimina equipment dal sistema"""
    # Check: non assigned a lavori attivi
    # Delete from database
    # Log event: deletion
```

**UI**: Pulsante "Elimina" con conferma

## 5. ⚙️ CONFIGURAZIONE EQUIPMENT (Configuration)

### Attuale: Base
- [ ] Solo campi base implementati

### Necessario Estendere
**Campi mancanti nel form installazione**:
- WiFi SSID (multipli per dual-band)
- WiFi Password (WPA2/WPA3)
- Sicurezza WiFi
- Username admin router
- Password admin router
- IP statico (se applicabile)
- VLAN ID (se FTTH)
- Note connessione (velocità, stabilità)
- Problemi riscontrati
- Soluzioni applicate

## 🔗 INTEGRAZIONI MANCANTI

### 1. Work Details Integration
**Problema**: Tab lavori non mostra dettagli equipment assegnato
**Soluzione**: Aggiungere sezione "Equipment Assegnato" nel dettaglio lavoro

### 2. Status Validation
**Problema**: Nessun controllo stati consistente
**Soluzione**: Validazioni per prevenire operazioni invalide

### 3. Bulk Operations
**Problema**: Operazioni solo singole
**Soluzione**: Azioni multiple (assegna a più lavori, installa multipli)

## 📊 STATISTICHE EQUIPMENT (Da Implementare)

### Dashboard Equipment
- Equipment disponibili per tipo
- Installazioni giornaliere
- Equipment in garanzia/scaduti
- Tassi successo installazioni

### Report Operativi
- Equipment per tecnico
- Tempi medi installazione
- Problemi comuni per modello
- Inventario valore

## 🎨 UI/UX MIGLIORAMENTI

### Equipment Tab
- [ ] Filtri avanzati (tipo, stato, modello, location)
- [ ] Ricerca per serial number
- [ ] Vista tabella/espandibile
- [ ] Azioni bulk (assegna multipli, installa multipli)

### Work Details
- [ ] Sezione equipment visuale
- [ ] Status consegna/installazione
- [ ] Link diretto a equipment
- [ ] Storico operazioni equipment

### Installation Form
- [ ] Tabs per categorie (WiFi, Admin, Note)
- [ ] Validazione campi obbligatori
- [ ] Preview configurazione
- [ ] Template per modelli comuni

## 🔧 IMPLEMENTAZIONE TECNICA

### Database Updates Necessari
```sql
-- Aggiungere campi mancanti
ALTER TABLE equipment ADD COLUMN wifi_ssid_2g TEXT;
ALTER TABLE equipment ADD COLUMN wifi_password_2g TEXT;
ALTER TABLE equipment ADD COLUMN wifi_ssid_5g TEXT;
ALTER TABLE equipment ADD COLUMN wifi_password_5g TEXT;
ALTER TABLE equipment ADD COLUMN admin_username TEXT;
ALTER TABLE equipment ADD COLUMN admin_password TEXT;
ALTER TABLE equipment ADD COLUMN installation_problems TEXT;
ALTER TABLE equipment ADD COLUMN installation_solutions TEXT;
```

### Classi da Estendere
```python
class EquipmentInstallation:
    """Classe per gestire dati installazione"""
    wifi_configs: List[WiFiConfig]
    admin_credentials: AdminCredentials
    technical_notes: str
    problems: str
    solutions: str
```

### Validazioni da Implementare
- Equipment non può essere assegnato se già assigned
- Installazione possibile solo se delivered
- Return possibile solo se assigned
- Delete possibile solo se available

## 📋 CHECKLIST IMPLEMENTAZIONE

### Fase 1: Core Operations
- [ ] Implementare `mark_equipment_delivered()`
- [ ] Completare `mark_equipment_installed()` con form completo
- [ ] Implementare `return_equipment_to_stock()`
- [ ] Implementare `delete_equipment()`

### Fase 2: UI Integration
- [ ] Migliorare tab Equipment con filtri/ricerca
- [ ] Aggiungere sezione equipment in work details
- [ ] Creare form installazione completo
- [ ] Aggiungere menu contestuali

### Fase 3: Validations & Stats
- [ ] Implementare validazioni workflow
- [ ] Aggiungere statistiche equipment dashboard
- [ ] Implementare audit trail equipment
- [ ] Test workflow completo

### Fase 4: Advanced Features
- [ ] Bulk operations
- [ ] Template configurazioni
- [ ] Report avanzati
- [ ] Integrazione documenti (foto installazione)

## 🎯 SUCCESS CRITERIA

### Funzionale
- [ ] Workflow completo: assign → deliver → install → return
- [ ] Form installazione raccoglie tutti i dati necessari
- [ ] Validazioni prevengono errori operativi
- [ ] Statistiche accurate e utili

### Usabilità
- [ ] UI intuitiva e veloce
- [ ] Workflow guidato (no possibilità errori)
- [ ] Ricerca veloce equipment
- [ ] Report chiari e esportabili

### Robustezza
- [ ] Gestione errori completa
- [ ] Backup automatico dati
- [ ] Recovery da crash
- [ ] Audit trail completo