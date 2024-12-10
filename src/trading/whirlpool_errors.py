from enum import IntEnum

class WhirlpoolError(IntEnum):
    # Core Errors (6000-6010)
    INVALID_ENUM = 6000
    INVALID_START_TICK = 6001
    TICK_ARRAY_EXIST_IN_POOL = 6002
    TICK_ARRAY_INDEX_OUT_OF_BOUNDS = 6003
    INVALID_TICK_SPACING = 6004
    CLOSE_POSITION_NOT_EMPTY = 6005
    DIVIDE_BY_ZERO = 6006
    NUMBER_CAST_ERROR = 6007
    NUMBER_DOWNCAST_ERROR = 6008
    TICK_NOT_FOUND = 6009
    INVALID_TICK_INDEX = 6010

    # Price & Liquidity Errors (6011-6016)
    SQRT_PRICE_OUT_OF_BOUNDS = 6011
    LIQUIDITY_ZERO = 6012
    LIQUIDITY_TOO_HIGH = 6013
    LIQUIDITY_OVERFLOW = 6014
    LIQUIDITY_UNDERFLOW = 6015
    LIQUIDITY_NET_ERROR = 6016

    # Token Errors (6017-6020)
    TOKEN_MAX_EXCEEDED = 6017
    TOKEN_MIN_SUBCEEDED = 6018
    MISSING_OR_INVALID_DELEGATE = 6019
    INVALID_POSITION_TOKEN_AMOUNT = 6020

    # Trading Errors (6034-6037)
    INVALID_SQRT_PRICE_LIMIT_DIRECTION = 6034
    ZERO_TRADABLE_AMOUNT = 6035
    AMOUNT_OUT_BELOW_MINIMUM = 6036
    AMOUNT_IN_ABOVE_MAXIMUM = 6037

    # Calculation Errors (6039-6040)
    AMOUNT_CALC_OVERFLOW = 6039
    AMOUNT_REMAINING_OVERFLOW = 6040

    # Two-Hop Errors (6041-6042)
    INVALID_INTERMEDIARY_MINT = 6041
    DUPLICATE_TWO_HOP_POOL = 6042

    # Transfer Errors (6050-6053)
    NO_EXTRA_ACCOUNTS_FOR_TRANSFER_HOOK = 6050
    INTERMEDIATE_TOKEN_AMOUNT_MISMATCH = 6051
    TRANSFER_FEE_CALCULATION_ERROR = 6052
    REMAINING_ACCOUNTS_DUPLICATED = 6053

    # Position Errors (6054-6057)
    FULL_RANGE_ONLY_POOL = 6054
    TOO_MANY_SUPPLEMENTAL_TICK_ARRAYS = 6055
    DIFFERENT_WHIRLPOOL_TICK_ARRAY = 6056
    PARTIAL_FILL_ERROR = 6057

    @classmethod
    def get_error_message(cls, code: int) -> str:
        error_messages = {
            # Core Errors
            cls.INVALID_ENUM: "Ungültiger Enum-Wert",
            cls.INVALID_START_TICK: "Ungültiger Start-Tick",
            cls.TICK_ARRAY_EXIST_IN_POOL: "Tick-Array existiert bereits",
            cls.INVALID_TICK_SPACING: "Ungültiges Tick-Spacing",
            
            # Price & Liquidity Errors
            cls.SQRT_PRICE_OUT_OF_BOUNDS: "Preis außerhalb der Grenzen",
            cls.LIQUIDITY_ZERO: "Liquidität muss größer als 0 sein",
            cls.LIQUIDITY_TOO_HIGH: "Liquidität zu hoch",
            cls.LIQUIDITY_OVERFLOW: "Liquiditäts-Überlauf",
            
            # Token Errors
            cls.TOKEN_MAX_EXCEEDED: "Token Maximum überschritten",
            cls.TOKEN_MIN_SUBCEEDED: "Token Minimum unterschritten",
            
            # Trading Errors
            cls.ZERO_TRADABLE_AMOUNT: "Keine handelbare Menge",
            cls.AMOUNT_OUT_BELOW_MINIMUM: "Ausgabemenge unter Minimum",
            cls.AMOUNT_IN_ABOVE_MAXIMUM: "Eingabemenge über Maximum",
            
            # Calculation Errors
            cls.AMOUNT_CALC_OVERFLOW: "Berechnungsüberlauf",
            cls.AMOUNT_REMAINING_OVERFLOW: "Restbetrag-Überlauf",
            
            # Transfer Errors
            cls.TRANSFER_FEE_CALCULATION_ERROR: "Fehler bei Gebührenberechnung",
            cls.INTERMEDIATE_TOKEN_AMOUNT_MISMATCH: "Token-Mengen stimmen nicht überein",
            
            # Position Errors
            cls.FULL_RANGE_ONLY_POOL: "Pool unterstützt nur Full-Range Positionen",
            cls.PARTIAL_FILL_ERROR: "Trade wurde nur teilweise ausgeführt"
        }
        return error_messages.get(code, f"Unbekannter Fehler: {code}")

    @classmethod
    def is_insufficient_funds_error(cls, code: int) -> bool:
        """Prüft ob es sich um einen Insufficient Funds Fehler handelt"""
        return code in [
            cls.TOKEN_MIN_SUBCEEDED,
            cls.LIQUIDITY_ZERO,
            cls.ZERO_TRADABLE_AMOUNT
        ]

    @classmethod
    def is_price_impact_error(cls, code: int) -> bool:
        """Prüft ob es sich um einen Price Impact Fehler handelt"""
        return code in [
            cls.SQRT_PRICE_OUT_OF_BOUNDS,
            cls.AMOUNT_OUT_BELOW_MINIMUM,
            cls.AMOUNT_IN_ABOVE_MAXIMUM
        ]