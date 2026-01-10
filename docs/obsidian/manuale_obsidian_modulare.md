# 🚀 **Manuale del Sistema di Programmazione Modulare AiVigilanza**

  

## 📖 **Prefazione: Perché Questo Sistema**

  

Quando gestisci **server complessi** con componenti multipli (Apache2, Fail2Ban, nftables, Yggdrasil, VPN, Tor, porte modem, proxy reverse...), è **impossibile ricordare tutto**. Questo sistema trasforma il caos in ordine attraverso:

  

- **📚 Documentazione Vivente**: Non statica, ma che cresce con il codice

- **🎨 Visualizzazione Interattiva**: Canvas che mostrano relazioni complesse

- **🔧 Modularità**: Ogni componente è isolato ma integrato

- **🔍 Troubleshooting Guidato**: Quando dimentichi qualcosa, il sistema ti guida

  

---

  

## 🏗️ **Capitolo 1: La Filosofia Modulare**

  

### 1.1 **Principio Base: Separazione delle Responsabilità**

  

Come hai fatto con nftables, ogni componente ha il suo file dedicato:

  

```

nftables/

├── core.conf # Configurazione principale

├── banned.conf # Ban management

├── apache.conf # Web server rules

├── ssh.conf # SSH access

├── yggdrasil.conf # Yggdrasil network

└── app_service.conf # Applicazioni specifiche

```

  

**Regola d'Oro**: Un file = Una responsabilità = Un concetto

  

### 1.2 **Vantaggi della Modularità**

  

- **🔍 Isolamento**: Problema in Apache? Controlla solo `apache.conf`

- **🔄 Aggiornamenti**: Modifica un componente senza toccare gli altri

- **📊 Monitoraggio**: Sai esattamente dove cercare per ogni funzione

- **👥 Collaborazione**: Più persone possono lavorare su componenti diversi

  

---

  

## 🎨 **Capitolo 2: Obsidian come Cervello del Sistema**

  

### 2.1 **Canvas Index: Il Centro di Comando**

  

Apri sempre da qui: `obsidian/AiVigilanza-Canvas-Index.canvas`

  

**Cosa trovi:**

- 🏗️ **Architecture**: Vista generale del sistema

- 📦 **Installation Flow**: Come montare il "mobile IKEA"

- 🔄 **Daily Workflow**: Operazioni quotidiane

- 🆘 **Troubleshooting**: Quando qualcosa va storto

- 📚 **Module Canvas**: Dettagli di ogni componente

  

### 2.2 **Workflow di Sviluppo**

  

#### **Fase 1: Pianificazione**

```

Obsidian → Canvas Index → Architecture Canvas

```

- Disegna il nuovo componente

- Definisci interfacce con altri moduli

- Pianifica le dipendenze

  

#### **Fase 2: Implementazione**

```

Canvas → Codice → Test → Canvas Aggiornato

```

- Scrivi il codice modulare

- Aggiorna i canvas automaticamente

- Verifica le integrazioni

  

#### **Fase 3: Documentazione**

```bash

python3 generate_canvas.py # Genera canvas dal codice

./update_canvas_index.sh # Aggiorna l'indice

```

  

---

  

## 🔧 **Capitolo 3: Workflow Operativo Quotidiano**

  

### 3.1 **Avvio Sistema: Checklist Visiva**

  

1. **Canvas Index** → **Daily Workflow Canvas**

2. Segui i nodi colorati nell'ordine:

- 🔍 **Log Monitoring**: Controllo automatico log

- 📊 **Stats Collection**: Raccolta statistiche

- 🔍 **Threat Detection**: Rilevamento minacce

- 🚨 **Alert System**: Notifiche automatiche

- 🚫 **Ban Management**: Ban via nftables

  

### 3.2 **Quando Dimentichi Qualcosa**

  

**Scenario**: "Come si configura il proxy reverse per Apache?"

  

**Soluzione con Canvas:**

1. Canvas Index → Installation Flow

2. Cerca il nodo "Apache Configuration"

3. Leggi la configurazione specifica

4. Link diretto al file di configurazione

  

**Scenario**: "Quali porte sono aperte sul modem?"

  

**Soluzione con Canvas:**

1. Canvas Index → Architecture Canvas

2. Guarda il nodo "Network Configuration"

3. Vedi le connessioni e porte documentate

  

---

  

## 📊 **Capitolo 4: Manutenzione e Aggiornamenti**

  

### 4.1 **Aggiornamento Automatico Documentazione**

  

Ogni volta che modifichi il codice:

  

```bash

# Genera nuovi canvas dai moduli modificati

python3 generate_canvas.py

  

# Aggiorna l'indice centrale

./update_canvas_index.sh

  

# Verifica che tutto sia collegato

./verify_installation.sh

```

  

### 4.2 **Versionamento Canvas**

  

I canvas **non vanno** nel git come file statici, ma:

  

- **Generali automaticamente** dal codice

- **Aggiornati** quando il codice cambia

- **Versionati indirettamente** attraverso il codice

  

### 4.3 **Pulizia Periodica**

  

Mensilmente:

- Rimuovi canvas obsoleti

- Rigenera tutti i canvas

- Verifica collegamenti interrotti

  

---

  

## 🆘 **Capitolo 5: Troubleshooting con Canvas**

  

### 5.1 **Metodo Sistematico**

  

Quando qualcosa non funziona:

  

1. **Canvas Index** → **Troubleshooting Canvas**

2. Segui il workflow guidato:

- Controlla log systemd

- Verifica configurazione .env

- Test nftables rules

- Verifica moduli Python

- Test bot Telegram

  

### 5.2 **Debug Visivo**

  

**Problema**: Bot Telegram non risponde

  

**Canvas Guide**:

- Nodo "Telegram Bot" → "Check Token"

- Nodo "Configuration" → "Verify .env"

- Nodo "Network" → "Test Connectivity"

  

### 5.3 **Isolamento Componenti**

  

Usa i canvas modulari per isolare problemi:

  

- **ban_manager-module.canvas**: Problemi ban?

- **detector-module.canvas**: Problemi rilevamento?

- **stats_manager-module.canvas**: Problemi statistiche?

  

---

  

## 🚀 **Capitolo 6: Scalabilità per Progetti Complessi**

  

### 6.1 **Aggiungere Nuovi Componenti**

  

**Template per nuovo modulo:**

  

1. **Canvas Planning**:

```

- Definisci responsabilità

- Identifica dipendenze

- Pianifica interfacce

```

  

2. **Implementazione**:

```python

class NuovoModulo:

def __init__(self, dipendenze):

# Logica modulare

```

  

3. **Documentazione**:

```bash

python3 generate_canvas.py # Genera canvas automatico

```

  

### 6.2 **Integrazione con Sistemi Esistenti**

  

**Esempio: Aggiungere Docker**

  

1. **Canvas**: Nuovo nodo in Architecture

2. **Config**: File separato `docker.conf`

3. **Codice**: Modulo Python per gestione container

4. **Test**: Verifica integrazione con nftables

  

### 6.3 **Team Collaboration**

  

- **Ogni developer** ha il suo canvas personale

- **Canvas condivisi** per componenti comuni

- **Code review** include revisione canvas

- **Documentazione** sempre aggiornata automaticamente

  

---

  

## 🎯 **Capitolo 7: Best Practices**

  

### 7.1 **Regole d'Oro**

  

1. **Un concetto = Un file** (come nftables)

2. **Un modulo = Un canvas**

3. **Ogni modifica = Aggiornamento documentazione**

4. **Test prima, documenta dopo**

  

### 7.2 **Struttura File Consigliata**

  

```

/progetto/

├── src/ # Codice sorgente

│ ├── modulo1.py

│ ├── modulo2.py

│ └── main.py

├── config/ # Configurazioni

│ ├── core.conf

│ ├── modulo1.conf

│ └── modulo2.conf

├── obsidian/ # Documentazione

│ ├── *-Index.canvas

│ ├── *-module.canvas

│ └── *.md

└── scripts/ # Tooling

├── generate_canvas.py

└── verify_installation.sh

```

  

### 7.3 **Workflow Giornaliero**

  

**Mattina:**

- Apri Canvas Index

- Controlla Daily Workflow

- Verifica alert/notifiche

  

**Durante il giorno:**

- Usa canvas per reference

- Aggiorna documentazione quando modifichi codice

  

**Sera:**

- Rigenera canvas

- Verifica tutto funzioni

- Prepara piano per domani

  

---

  

## 🌟 **Conclusione: Il Futuro della Programmazione Server**

  

Questo sistema trasforma la **programmazione server da arte oscura a scienza visuale**:

  

- **Prima**: "Spero di ricordare come configurare il proxy reverse..."

- **Ora**: "Canvas Index → Apache Config → File specifico"

  

- **Prima**: Debug caotico in terminale

- **Ora**: Troubleshooting Canvas guidato

  

- **Prima**: Documentazione che diventa obsoleta

- **Ora**: Documentazione che vive con il codice

  

**Ricorda**: In un mondo di server complessi, la differenza tra un sysadmin frustrato e uno efficace è la **documentazione interattiva che non dimentica mai**.

  

**Il tuo sistema nftables modulare + Obsidian canvas = La vittoria assicurata!** 🚀🎨

  

---

  

*Questo manuale è esso stesso un esempio del sistema: può essere trasformato in canvas interattivi per una navigazione ancora più intuitiva.*