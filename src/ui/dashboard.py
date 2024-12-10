from flask import Flask, render_template, jsonify
from threading import Thread
import asyncio

app = Flask(__name__)

class Dashboard:
    def __init__(self, bot):
        self.bot = bot
        self.app = app
        
    @app.route('/')
    def index():
        return render_template('index.html')
        
    @app.route('/api/status')
    def get_status():
        return jsonify({
            'wallet_connected': self.bot.wallet_manager.is_connected(),
            'current_balance': self.bot.wallet_manager.get_balance(),
            'active_trades': self.bot.get_active_trades()
        })
    
    def run(self):
        self.app.run(host='0.0.0.0', port=5000) 