# Token Decimals für häufig genutzte Token
TOKEN_DECIMALS = {
    "SOL": 9,
    "USDC": 6,
    "USDT": 6,
    "BONK": 5
}

# Whirlpool Konfigurationen
WHIRLPOOL_CONFIGS = {
    "SOL/USDC": {
        "address": "HJPjoWUrhoZzkNfRpHuieeFk9WcZWjwy6PBjZ81ngndJ",
        "tick_spacing": 64,
        "token_a": "SOL",
        "token_b": "USDC"
    },
    "SOL/USDT": {
        "address": "4GpUivZ2jvZqQ3vJRsoq5PwnYv6gdV9fJ9BzHT2JcRr7",
        "tick_spacing": 64,
        "token_a": "SOL",
        "token_b": "USDT"
    },
    "BONK/SOL": {
        "address": "8QaXeHBrShJTdtN1rWHbp3pPJGCuYKxqZn8M5YBV1HSF",
        "tick_spacing": 64,
        "token_a": "BONK",
        "token_b": "SOL"
    }
}
