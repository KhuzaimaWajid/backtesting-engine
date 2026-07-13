from app.strategies.ma_crossover import MovingAverageCrossoverStrategy
from app.strategies.momentum import MomentumStrategy
from app.strategies.rsi_mean_reversion import RSIMeanReversionStrategy

STRATEGIES = {
    s.id: s
    for s in [
        MovingAverageCrossoverStrategy(),
        RSIMeanReversionStrategy(),
        MomentumStrategy(),
    ]
}

# Drives both GET /strategies (so the frontend can render the right inputs)
# and server-side validation/clamping of incoming params.
STRATEGY_PARAM_SCHEMAS: dict[str, list[dict]] = {
    "ma_crossover": [
        {"name": "fast_window", "label": "Fast MA window (days)", "type": "int", "default": 20, "min": 2, "max": 100, "step": 1},
        {"name": "slow_window", "label": "Slow MA window (days)", "type": "int", "default": 50, "min": 5, "max": 300, "step": 1},
    ],
    "rsi_mean_reversion": [
        {"name": "rsi_period", "label": "RSI period (days)", "type": "int", "default": 14, "min": 2, "max": 60, "step": 1},
        {"name": "oversold_threshold", "label": "Oversold entry level", "type": "float", "default": 30, "min": 5, "max": 45, "step": 1},
        {"name": "exit_threshold", "label": "Exit level", "type": "float", "default": 50, "min": 45, "max": 90, "step": 1},
    ],
    "momentum": [
        {"name": "lookback_days", "label": "Lookback window (days)", "type": "int", "default": 90, "min": 5, "max": 252, "step": 1},
        {"name": "threshold_pct", "label": "Entry threshold (% return)", "type": "float", "default": 0, "min": -20, "max": 20, "step": 0.5},
    ],
}


def get_strategy(strategy_id: str):
    if strategy_id not in STRATEGIES:
        raise KeyError(f"Unknown strategy_id '{strategy_id}'")
    return STRATEGIES[strategy_id]


def list_strategy_infos() -> list[dict]:
    return [
        {"id": s.id, "name": s.name, "description": s.description, "params": STRATEGY_PARAM_SCHEMAS[s.id]}
        for s in STRATEGIES.values()
    ]


def validate_params(strategy_id: str, params: dict) -> dict:
    """Fill missing params with defaults and clamp everything to its [min, max]."""
    schema = STRATEGY_PARAM_SCHEMAS[strategy_id]
    validated = {}
    for p in schema:
        value = params.get(p["name"], p["default"])
        value = max(p["min"], min(p["max"], value))
        validated[p["name"]] = int(value) if p["type"] == "int" else float(value)
    return validated
