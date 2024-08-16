import json
import os
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Set

import requests
from pydantic import BaseModel, field_validator
from pytz import timezone


def get_valid_team_names() -> Set[str]:
    """Return a set containing all valid team names

    Returns:
        Set[str]: A set of all valid team names
    """
    current_file = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file)
    file_path = os.path.join(current_dir, "assets", "team_names.json")
    with open(file_path, "r") as f:
        name_map = json.load(f)
    return set(name_map)


def convert_team_name(name: str) -> str:
    """Convert The Odds team name to standardized valid team name

    Args:
        name (str): The Odds formatted team name

    Returns:
        str: Standardized valid team name
    """
    return name.lower().replace(" ", "-")


def add_timezone(date_str: str) -> str:
    """Adds the timezone to a date string from the-odds API

    Args:
        date_str (str): Input date string from the-odds API

    Returns:
        str: Modified date string with time zone
    """
    return date_str.replace("Z", "+00:00")


# Create an enum of valid team names
class StrEnum(str, Enum):
    pass


TeamNameEnum = StrEnum("TeamNameEnum", [(name, name) for name in get_valid_team_names()])


class Game(BaseModel, extra="allow"):
    id: str
    home_team: TeamNameEnum
    away_team: TeamNameEnum
    commence_time: datetime

    @field_validator("home_team", mode="before")
    @classmethod
    def convert_home_to_valid_team_name(cls, value):
        return convert_team_name(name=value)

    @field_validator("away_team", mode="before")
    @classmethod
    def convert_away_to_valid_team_name(cls, value):
        return convert_team_name(name=value)

    @field_validator("commence_time", mode="before")
    @classmethod
    def add_tz_to_commence_time(cls, value):
        return add_timezone(date_str=value)


def get_the_odds_json(api_key: str, odds_format: str = "american") -> List[Dict]:
    """Make request to the-odds API for bookmaker odds

    Args:
        api_key (str): The-odds API key
        odds_format (str, optional): Format for odds, one of "american" or "decimal" All downstream
        functions require "american" format. Defaults to "american".

    Returns:
        List[Dict]: The-odds response JSON
    """
    url = "https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds/"
    params = {
        "regions": "us",
        "apiKey": api_key,
        "markets": "h2h",
        "oddsFormat": odds_format,
    }
    resp = requests.get(url, params)
    resp.raise_for_status()
    return resp.json()


def parse_the_odds_json(the_odds_json: List[Dict]) -> List[Game]:
    """Parse the-odds JSON response into a list of Game objects

    Args:
        the_odds_json (List[Dict]): the-odds API response

    Returns:
        List[Game]: the-odds API response parsed into a list of Game objects
    """
    return [Game(**game) for game in the_odds_json]


def filter_games_by_date(
    games: List[Game], after: datetime = datetime.min, before: datetime = datetime.max
) -> List[Game]:
    """Filter the list of games down to only those with a commence_time between the given range.

    Args:
        games (List[Game]): List of Game objects
        after (datetime, optional): Keep only games with commence_time strictly greater than after.
            Defaults to datetime.min.
        before (datetime, optional): Keep only games with commence_time strictly less than after.
            Defaults to datetime.max.

    Returns:
        List[Game]: Filter game list
    """
    return [game for game in games if after < game.commence_time < before]


def get_this_weeks_games(games: List[Game]) -> List[Game]:
    """Filter games list to only those between now and the coming Tuesday (since Monday Night
    Football is the last game of the week)

    Args:
        games (List[Game]): List of games

    Returns:
        List[Game]: Filtered list of games
    """
    # Compute the number of days until Tuesday
    now = datetime.now(tz=timezone("US/Eastern"))
    today = now.weekday()
    tuesday = 1  # Tuesday has int value 1 in datetime
    days_til_tuesday = (tuesday - today) % 7

    # If today is Tuesday, get a week from today
    if days_til_tuesday == 0:
        days_til_tuesday = 7

    # Keep only games between now and the coming Tuesday
    next_tuesday = now + timedelta(days=days_til_tuesday)
    return filter_games_by_date(
        games=games,
        after=now,
        before=next_tuesday,
    )
