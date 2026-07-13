from fastapi import APIRouter

from app.data.universe import UNIVERSE
from app.schemas import TickerInfo

router = APIRouter()


@router.get("", response_model=list[TickerInfo])
def get_tickers():
    """The fixed universe of tickers this instance supports."""
    return UNIVERSE
