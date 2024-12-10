from flask import Flask, render_template_string
import logging

logger = logging.getLogger(__name__)

class PhantomConnector:
    def __init__(self, port=5000):
        self.app = Flask(__name__)
        self.port = port
        self.public_key = None
        
        # HTML Template
        self.html_template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Phantom Wallet Connector</title>
        </head>
        <body>
            <h1>Verbinde mit Phantom Wallet</h1>
            <button id="connect-button">Wallet verbinden</button>
            <p id="status"></p>
            <p id="public-key"></p>

            <script>
                document.getElementById("connect-button").addEventListener("click", async () => {
                    try {
                        if (!window.solana || !window.solana.isPhantom) {
                            throw new Error("Phantom Wallet nicht gefunden!");
                        }
                        
                        const resp = await window.solana.connect();
                        const pubKey = resp.publicKey.toString();
                        
                        document.getElementById("status").textContent = "✅ Verbunden!";
                        document.getElementById("public-key").textContent = 
                            "Public Key: " + pubKey;
                            
                        // Sende Key an Backend
                        fetch('/set_pubkey', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({public_key: pubKey})
                        });
                    } catch (err) {
                        document.getElementById("status").textContent = 
                            "❌ Fehler: " + err.message;
                    }
                });
            </script>
        </body>
        </html>
        """
        
        # Routes
        @self.app.route('/')
        def index():
            return render_template_string(self.html_template)
            
        @self.app.route('/set_pubkey', methods=['POST'])
        def set_pubkey():
            data = request.get_json()
            self.public_key = data.get('public_key')
            logger.info(f"Phantom Wallet verbunden: {self.public_key}")
            return {"status": "success"}
            
    def start(self):
        """Startet den Flask Server"""
        self.app.run(port=self.port)
        
    def get_public_key(self):
        """Gibt den gespeicherten Public Key zurück"""
        return self.public_key 