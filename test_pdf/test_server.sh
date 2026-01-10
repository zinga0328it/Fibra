#!/bin/bash
cd /home/aaa/fibra/test_pdf

echo "Avvio server..."
python3 pdf_client_upload.py &
SERVER_PID=$!

echo "Attesa avvio server..."
sleep 5

echo "Test richiesta GET /"
curl -s http://127.0.0.1:8001/ | head -3

echo -e "\nTest upload PDF..."
curl -X POST "http://127.0.0.1:8001/upload-file" \
     -F "file=@lavoro domani.PDF" \
     -s | jq '.message' 2>/dev/null || echo "Risposta ricevuta"

echo -e "\nUccisione server..."
kill $SERVER_PID
wait $SERVER_PID 2>/dev/null

echo "Test completato"