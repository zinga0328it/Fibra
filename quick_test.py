#!/usr/bin/env python3
import subprocess
import json
import sys

def run_cmd(cmd, description):
    print(f"\n🔍 {description}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            try:
                data = json.loads(result.stdout)
                print(f"✅ SUCCESS: {data}")
                return True
            except:
                if len(result.stdout.strip()) > 10:
                    print(f"✅ SUCCESS: {len(result.stdout)} bytes received")
                    return True
                else:
                    print(f"❌ FAILED: Invalid response")
                    return False
        else:
            print(f"❌ FAILED: {result.stderr.strip() or 'No response'}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ FAILED: Timeout")
        return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

print("🌐 TEST ROTTE YGGDRASIL - FTTH System")
print("=" * 40)

# Avvia server
print("\n🚀 Avvio server...")
server = subprocess.Popen([
    sys.executable, "-m", "uvicorn", "app.main:app", 
    "--host", "0.0.0.0", "--port", "6030", "--log-level", "warning"
])
import time
time.sleep(3)

try:
    # Test localhost
    run_cmd("curl -s http://127.0.0.1:6030/health/", "Health Localhost")
    run_cmd("curl -s http://127.0.0.1:6030/works/", "Works Localhost")
    
    # Test Yggdrasil
    run_cmd("curl -s http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/health/", "Health Yggdrasil")
    run_cmd("curl -s http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/works/", "Works Yggdrasil")
    
    # Test equipment
    run_cmd('curl -s "http://127.0.0.1:6030/modems/" -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU="', "Modems Localhost")
    run_cmd('curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/modems/" -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU="', "Modems Yggdrasil")
    
    # Test web interface
    run_cmd("curl -s http://127.0.0.1:6030/gestionale.html | grep -o 'Gestionale' | head -1", "Gestionale Localhost")
    run_cmd("curl -s http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/gestionale.html | grep -o 'Gestionale' | head -1", "Gestionale Yggdrasil")

finally:
    print("\n🛑 Arresto server...")
    server.terminate()
    server.wait()

print("\n🎯 TEST COMPLETATO!")
