from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Optional, List
import numpy as np
from datetime import datetime
import logging
from config import BotConfig

@dataclass
class StrategyResult:
    should_trade: bool
    trade_type: str  # 'buy' or 'sell'
    amount: float
    price: float
    confidence: float
    reason: str
    stop_loss: float
    take_profit: float

class MemeSniper:
    def __init__(self, config: BotConfig):
        self.config = config
        self.meme_config = config.meme_sniping
        self.tracked_tokens = {}
        self.active_positions = []
        self._running = False
        self.source_timing_cache = {}  # Cache for source timing patterns
        
    def start(self):
        """Starts the strategy"""
        self._running = True
        
    def stop(self):
        """Stops the strategy"""
        self._running = False
        
    def analyze_token(self, token_data: Dict) -> StrategyResult:
        """Analyzes a token for trading signals with timing analysis"""
        if not self._running:
            return StrategyResult(False, '', 0, 0, 0, "Strategy stopped", 0, 0)
            
        try:
            # Analyze timing patterns
            timing_signal = self._analyze_timing_patterns(token_data)
            
            # Early Stage Check with timing consideration
            if self._is_early_stage(token_data):
                growth_rate = self._calculate_growth_rate(token_data)
                
                # Adjust confidence based on timing signal
                base_confidence = min(growth_rate, 0.95)
                timing_adjusted_confidence = base_confidence * (1 + timing_signal)
                
                if growth_rate > self.meme_config.min_price_growth:
                    # Calculate position size with timing factor
                    position_size = self._calculate_position_size(token_data)
                    if timing_signal > 0.1:  # Strong timing signal
                        position_size *= (1 + timing_signal)  # Increase position size
                        
                    return StrategyResult(
                        should_trade=True,
                        trade_type='buy',
                        amount=position_size,
                        price=token_data['price'],
                        confidence=timing_adjusted_confidence,
                        reason=f'Growth: {growth_rate*100:.1f}%, Timing: {timing_signal*100:.1f}%',
                        stop_loss=token_data['price'] * (1 - self.meme_config.stop_loss),
                        take_profit=token_data['price'] * (1 + self.meme_config.take_profit)
                    )
            
            return StrategyResult(False, '', 0, 0, 0, "No signal", 0, 0)
            
        except Exception as e:
            logging.error(f"Analysis error: {e}")
            return StrategyResult(False, '', 0, 0, 0, str(e), 0, 0)
            
    def _is_early_stage(self, token_data: Dict) -> bool:
        """Checks if token is in early stage"""
        return (
            token_data['price'] <= self.meme_config.max_token_price and
            token_data['liquidity'] >= self.meme_config.min_liquidity and
            token_data.get('holders', 0) >= self.meme_config.min_holders
        )
        
    def _calculate_growth_rate(self, token_data: Dict) -> float:
        """Calculates growth rate"""
        if 'price_history' not in token_data or len(token_data['price_history']) < 2:
            return 0
        prices = token_data['price_history']
        return (prices[-1] / prices[0]) - 1
        
    def _calculate_position_size(self, token_data: Dict) -> float:
        """Calculates optimal position size"""
        max_by_liquidity = token_data['liquidity'] * self.meme_config.max_liquidity_percentage
        return min(self.meme_config.max_position_size, max_by_liquidity)
        
    def _analyze_timing_patterns(self, token_data: Dict) -> float:
        """Analyzes source timing patterns to detect early signals
        Returns a signal strength multiplier (0.0 to 0.5)"""
        try:
            if 'timing' not in token_data:
                return 0.0
                
            timing_info = token_data['timing']
            token_address = token_data.get('address', '')
            
            # Get historical timing pattern for this token
            if token_address not in self.source_timing_cache:
                self.source_timing_cache[token_address] = {
                    'patterns': [],
                    'last_update': datetime.now()
                }
            
            cache = self.source_timing_cache[token_address]
            
            # Add new pattern
            cache['patterns'].append({
                'fastest_source': timing_info['fastest_source'],
                'latency': timing_info['fastest_latency'],
                'timestamp': datetime.now()
            })
            
            # Keep last 100 patterns
            if len(cache['patterns']) > 100:
                cache['patterns'] = cache['patterns'][-100:]
            
            # Analyze patterns
            signal_strength = 0.0
            
            # 1. Check if we're getting data from typically fast sources
            if timing_info['fastest_source'] in ['jupiter', 'birdeye', 'orca']:
                signal_strength += 0.1
            
            # 2. Check if latency is lower than usual
            recent_latencies = [p['latency'] for p in cache['patterns'][-10:]]
            if recent_latencies:
                avg_latency = sum(recent_latencies) / len(recent_latencies)
                if timing_info['fastest_latency'] < avg_latency * 0.8:  # 20% faster than average
                    signal_strength += 0.1
            
            # 3. Check for consistent source patterns
            recent_sources = [p['fastest_source'] for p in cache['patterns'][-5:]]
            if len(set(recent_sources)) == 1:  # Same source consistently first
                signal_strength += 0.1
            
            # 4. Check for accelerating updates
            if len(cache['patterns']) >= 2:
                current_interval = (datetime.now() - cache['patterns'][-2]['timestamp']).total_seconds()
                if current_interval < 1.0:  # Updates coming in very quickly
                    signal_strength += 0.2
            
            return min(signal_strength, 0.5)  # Cap at 0.5 (50% boost)
            
        except Exception as e:
            logging.error(f"Timing analysis error: {e}")
            return 0.0