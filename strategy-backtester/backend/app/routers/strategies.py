from fastapi import APIRouter

from app.schemas import StrategyInfo
from app.strategies.registry import list_strategy_infos

router = APIRouter()


@router.get("", response_model=list[StrategyInfo])
def get_strategies():
    """List the available rule-based strategies and their configurable parameters."""
    return list_strategy_infos()
