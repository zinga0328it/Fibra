#!/usr/bin/env python3
"""
FTTH Canvas Generator - Sistema di Programmazione Modulare AiVigilanza

Questo script genera automaticamente i canvas Obsidian dai moduli del sistema FTTH.
Implementa la filosofia "Documentazione Vivente" dove i canvas crescono con il codice.

Uso:
    python3 scripts/generate_canvas.py [--module nome_modulo] [--all]

Opzioni:
    --module: Genera solo il canvas del modulo specificato
    --all: Rigenera tutti i canvas (default)
    --verify: Verifica collegamenti senza generare
"""

import os
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any

class CanvasGenerator:
    """Generatore di canvas Obsidian per il sistema FTTH"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.obsidian_dir = self.project_root / "obsidian"
        self.obsidian_dir.mkdir(exist_ok=True)

    def generate_all_canvas(self) -> None:
        """Genera tutti i canvas del sistema"""
        print("🎨 Generando canvas modulari FTTH...")

        # Canvas principali
        self.generate_index_canvas()
        self.generate_backend_canvas()
        self.generate_yggdrasil_canvas()
        self.generate_apache_canvas()
        self.generate_database_canvas()
        self.generate_telegram_canvas()
        self.generate_security_canvas()
        self.generate_monitoring_canvas()

        print("✅ Tutti i canvas generati con successo!")

    def generate_index_canvas(self) -> None:
        """Genera il canvas index principale"""
        canvas_data = {
            "nodes": [
                {
                    "id": "architecture_overview",
                    "x": -400,
                    "y": -200,
                    "width": 300,
                    "height": 200,
                    "type": "text",
                    "text": f"# 🏗️ FTTH Management System Architecture\n\n**Sistema di Gestione FTTH Enterprise**\n\n- ✅ Backend FastAPI isolato su Yggdrasil\n- ✅ Frontend Apache con SSL pubblico\n- ✅ Database PostgreSQL/SQLite\n- ✅ Sicurezza Zero-Trust\n- ✅ Telegram Bot integrato\n\n**Status**: Production Ready"
                },
                {
                    "id": "core_components",
                    "x": 0,
                    "y": -200,
                    "width": 250,
                    "height": 180,
                    "type": "text",
                    "text": "# 🔧 Core Components\n\n## Backend Layer\n- **FastAPI** (Porta 6030)\n- **Yggdrasil IPv6**: 200:421e:...\n- **Database**: PostgreSQL/SQLite\n\n## Frontend Layer\n- **Apache2** con SSL\n- **Domain**: servicess.net\n\n## Security Layer\n- **nftables** firewall\n- **Yggdrasil-only** access"
                },
                {
                    "id": "workflow_daily",
                    "x": -400,
                    "y": 50,
                    "width": 200,
                    "height": 150,
                    "type": "text",
                    "text": "# 🔄 Daily Workflow\n\n## Morning Check\n1. **System Status**\n2. **Log Review**\n3. **Backup Verify**\n\n## Operations\n- Monitor WR processing\n- Check technician updates\n- Review analytics\n\n## Maintenance\n- Update SSL certs\n- Clean old logs"
                },
                {
                    "id": "troubleshooting",
                    "x": 200,
                    "y": 50,
                    "width": 200,
                    "height": 150,
                    "type": "text",
                    "text": "# 🆘 Troubleshooting\n\n## Common Issues\n- 🔴 Backend not responding\n- 🔴 Yggdrasil connection\n- 🔴 Database errors\n- 🔴 Telegram bot issues\n\n## Quick Fixes\n- Check systemd status\n- Verify Yggdrasil IP\n- Test database connection\n- Restart services"
                },
                {
                    "id": "module_canvas_links",
                    "x": -100,
                    "y": 250,
                    "width": 400,
                    "height": 200,
                    "type": "text",
                    "text": "# 📚 Module Canvas\n\n## Core Modules\n- [[FTTH-Backend-Module.canvas|Backend FastAPI]]\n- [[FTTH-Yggdrasil-Module.canvas|Yggdrasil Network]]\n- [[FTTH-Apache-Module.canvas|Apache Frontend]]\n- [[FTTH-Database-Module.canvas|Database Layer]]\n- [[FTTH-Telegram-Module.canvas|Telegram Bot]]\n- [[FTTH-Security-Module.canvas|Security & Firewall]]\n- [[FTTH-Monitoring-Module.canvas|Monitoring & Logs]]"
                }
            ],
            "edges": [
                {"id": "arch_to_components", "fromNode": "architecture_overview", "fromSide": "right", "toNode": "core_components", "toSide": "left", "label": "implements"},
                {"id": "arch_to_network", "fromNode": "architecture_overview", "fromSide": "bottom", "toNode": "module_canvas_links", "toSide": "top", "label": "detailed in"},
                {"id": "workflow_to_troubleshooting", "fromNode": "workflow_daily", "fromSide": "right", "toNode": "troubleshooting", "toSide": "left", "label": "when issues"},
                {"id": "components_to_modules", "fromNode": "core_components", "fromSide": "bottom", "toNode": "module_canvas_links", "toSide": "left", "label": "detailed in"}
            ]
        }

        self.save_canvas("FTTH-Index.canvas", canvas_data)
        print("✅ Canvas Index generato")

    def generate_backend_canvas(self) -> None:
        """Genera canvas del modulo backend"""
        # Qui si potrebbe analizzare il codice FastAPI per estrarre endpoint automaticamente
        canvas_data = {
            "nodes": [
                {
                    "id": "backend_overview",
                    "x": -300,
                    "y": -200,
                    "width": 250,
                    "height": 150,
                    "type": "text",
                    "text": "# 🚀 FastAPI Backend Module\n\n**Core Business Logic**\n\n- **Framework**: FastAPI (Python)\n- **Port**: 6030\n- **Host**: Yggdrasil IPv6 only\n- **Database**: SQLAlchemy + PostgreSQL\n- **Security**: API Key + JWT\n\n**Status**: ✅ Operational"
                },
                {
                    "id": "api_endpoints",
                    "x": 50,
                    "y": -200,
                    "width": 300,
                    "height": 200,
                    "type": "text",
                    "text": "# 📡 API Endpoints\n\n## Work Requests (WR)\n- `GET /works` - Lista WR\n- `POST /works` - Nuovo WR\n- `PUT /works/{id}` - Aggiorna WR\n- `DELETE /works/{id}` - Elimina WR\n\n## Upload & Processing\n- `POST /works/upload` - Upload PDF\n- `GET /works/{id}/pdf` - Download PDF\n\n## Analytics\n- `GET /analytics/summary` - Statistiche\n- `GET /analytics/performance` - KPI"
                }
            ],
            "edges": [
                {"id": "backend_to_endpoints", "fromNode": "backend_overview", "fromSide": "right", "toNode": "api_endpoints", "toSide": "left", "label": "exposes"}
            ]
        }

        self.save_canvas("FTTH-Backend-Module.canvas", canvas_data)
        print("✅ Canvas Backend generato")

    def generate_yggdrasil_canvas(self) -> None:
        """Genera canvas del modulo Yggdrasil"""
        canvas_data = {
            "nodes": [
                {
                    "id": "yggdrasil_overview",
                    "x": -300,
                    "y": -200,
                    "width": 250,
                    "height": 150,
                    "type": "text",
                    "text": "# 🕸️ Yggdrasil Network Module\n\n**Zero-Trust Security Core**\n\n- **Type**: IPv6 Mesh VPN\n- **Encryption**: End-to-end\n- **Backend IP**: 200:421e:6385:4a8b:dca7:cfb:197f:e9c3\n- **Client IP**: 201:27c:546:5df7:176:95f3:c909:6834\n- **Interface**: ygg0\n\n**Status**: ✅ Active & Secure"
                }
            ],
            "edges": []
        }

        self.save_canvas("FTTH-Yggdrasil-Module.canvas", canvas_data)
        print("✅ Canvas Yggdrasil generato")

    def generate_apache_canvas(self) -> None:
        """Genera canvas del modulo Apache"""
        canvas_data = {
            "nodes": [
                {
                    "id": "apache_overview",
                    "x": -300,
                    "y": -200,
                    "width": 250,
                    "height": 150,
                    "type": "text",
                    "text": "# 🌐 Apache Frontend Module\n\n**Public Web Interface**\n\n- **Domain**: servicess.net\n- **SSL**: Let's Encrypt\n- **Port**: 443 (HTTPS)\n- **Content**: Static frontend only\n- **Backend**: NO proxy (Security!)\n\n**Status**: ✅ Public & Secure"
                }
            ],
            "edges": []
        }

        self.save_canvas("FTTH-Apache-Module.canvas", canvas_data)
        print("✅ Canvas Apache generato")

    def generate_database_canvas(self) -> None:
        """Genera canvas del modulo database"""
        canvas_data = {
            "nodes": [
                {
                    "id": "database_overview",
                    "x": -300,
                    "y": -200,
                    "width": 250,
                    "height": 150,
                    "type": "text",
                    "text": "# 🗄️ Database Module\n\n**Data Persistence Layer**\n\n- **Production**: PostgreSQL 13+\n- **Development**: SQLite\n- **ORM**: SQLAlchemy\n- **Migrations**: Alembic\n- **Backup**: Automatic daily\n\n**Status**: ✅ Operational"
                }
            ],
            "edges": []
        }

        self.save_canvas("FTTH-Database-Module.canvas", canvas_data)
        print("✅ Canvas Database generato")

    def generate_telegram_canvas(self) -> None:
        """Genera canvas del modulo Telegram"""
        canvas_data = {
            "nodes": [
                {
                    "id": "telegram_overview",
                    "x": -300,
                    "y": -200,
                    "width": 250,
                    "height": 150,
                    "type": "text",
                    "text": "# 📱 Telegram Bot Module\n\n**Mobile Communication Hub**\n\n- **Bot**: @FTTH_Bot\n- **Features**: Real-time notifications\n- **Integration**: Work requests updates\n- **Security**: Token-based auth\n- **Mode**: Polling (production)\n\n**Status**: ✅ Active"
                }
            ],
            "edges": []
        }

        self.save_canvas("FTTH-Telegram-Module.canvas", canvas_data)
        print("✅ Canvas Telegram generato")

    def generate_security_canvas(self) -> None:
        """Genera canvas del modulo security"""
        canvas_data = {
            "nodes": [
                {
                    "id": "security_overview",
                    "x": -300,
                    "y": -200,
                    "width": 250,
                    "height": 150,
                    "type": "text",
                    "text": "# 🔐 Security & Firewall Module\n\n**Zero-Trust Architecture**\n\n- **Firewall**: nftables\n- **VPN**: Yggdrasil-only access\n- **Backend**: Completely isolated\n- **Frontend**: Public but secure\n- **Monitoring**: Fail2Ban integration\n\n**Status**: ✅ Maximum Security"
                }
            ],
            "edges": []
        }

        self.save_canvas("FTTH-Security-Module.canvas", canvas_data)
        print("✅ Canvas Security generato")

    def generate_monitoring_canvas(self) -> None:
        """Genera canvas del modulo monitoring"""
        canvas_data = {
            "nodes": [
                {
                    "id": "monitoring_overview",
                    "x": -300,
                    "y": -200,
                    "width": 250,
                    "height": 150,
                    "type": "text",
                    "text": "# 📊 Monitoring & Logs Module\n\n**System Observability**\n\n- **Logs**: Centralized logging\n- **Metrics**: Performance monitoring\n- **Alerts**: Automatic notifications\n- **Health Checks**: System status\n- **Analytics**: Usage statistics\n\n**Status**: ✅ Full Observability"
                }
            ],
            "edges": []
        }

        self.save_canvas("FTTH-Monitoring-Module.canvas", canvas_data)
        print("✅ Canvas Monitoring generato")

    def save_canvas(self, filename: str, data: Dict[str, Any]) -> None:
        """Salva il canvas come file JSON"""
        canvas_path = self.obsidian_dir / filename
        with open(canvas_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def verify_links(self) -> bool:
        """Verifica che tutti i collegamenti nei canvas siano validi"""
        print("🔍 Verificando collegamenti canvas...")

        canvas_files = list(self.obsidian_dir.glob("*.canvas"))
        all_good = True

        for canvas_file in canvas_files:
            try:
                with open(canvas_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Verifica collegamenti interni
                nodes = {node['id'] for node in data.get('nodes', [])}
                for edge in data.get('edges', []):
                    if edge['fromNode'] not in nodes or edge['toNode'] not in nodes:
                        print(f"❌ Link rotto in {canvas_file.name}: {edge}")
                        all_good = False

            except Exception as e:
                print(f"❌ Errore nel canvas {canvas_file.name}: {e}")
                all_good = False

        if all_good:
            print("✅ Tutti i collegamenti verificati con successo!")
        else:
            print("❌ Alcuni collegamenti sono rotti")

        return all_good


def main():
    parser = argparse.ArgumentParser(description="FTTH Canvas Generator")
    parser.add_argument("--module", help="Genera solo il canvas del modulo specificato")
    parser.add_argument("--all", action="store_true", help="Rigenera tutti i canvas")
    parser.add_argument("--verify", action="store_true", help="Verifica collegamenti senza generare")

    args = parser.parse_args()

    # Trova la root del progetto
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    generator = CanvasGenerator(project_root)

    if args.verify:
        generator.verify_links()
    elif args.module:
        print(f"🎨 Generando canvas per modulo: {args.module}")
        # Qui si potrebbe implementare generazione selettiva
        print("⚠️  Generazione selettiva non ancora implementata, usa --all")
    else:
        generator.generate_all_canvas()
        generator.verify_links()


if __name__ == "__main__":
    main()