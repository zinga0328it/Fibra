#!/bin/bash
# Script per avviare il test PDF Client Upload

echo "🧪 Avvio Test PDF Client Upload..."
echo "📁 Cartella: $(pwd)"
echo "🗄️ Database isolato: test_pdf.db"
echo ""

# Avvia il server
echo "🚀 Avvio server su http://localhost:8001"
python3 pdf_client_upload.py &
SERVER_PID=$!

# Aspetta che si avvii
sleep 3

# Test automatico
echo ""
echo "🧪 Eseguo test automatico con test_clients.txt..."
curl -s -X POST "http://localhost:8001/upload-file" -F "file=@test_clients.txt" | python3 -m json.tool

echo ""
echo "📊 Controllo database..."
sqlite3 test_pdf.db "SELECT COUNT(*) as clienti_totali FROM works;"

echo ""
echo "🌐 Apri browser su: http://localhost:8001"
echo "📁 File di test: test_clients.txt, test_clients_2.txt"
echo ""
echo "Premi Ctrl+C per terminare..."

# Aspetta input utente
trap "echo ''; echo '🛑 Terminazione server...'; kill $SERVER_PID; exit" INT
wait