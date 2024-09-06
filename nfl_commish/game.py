from datetime import date, datetime, time, timedelta
from enum import Enum
from typing import Dict, List, Optional

import numpy as np
import requests
from loguru import logger
from pydantic import BaseModel, computed_field, field_validator
from pytz import timezone, utc

from nfl_commish.utils import add_timezone, convert_team_name, get_valid_team_names


# Create an enum of valid team names
class StrEnum(str, Enum):
    pass


TeamNameEnum = StrEnum("TeamNameEnum", [(name, name) for name in get_valid_team_names()])


class TeamScore(BaseModel):
    name: TeamNameEnum
    score: int

    @field_validator("name", mode="before")
    @classmethod
    def convert_to_valid_team_name(cls, value):
        return convert_team_name(name=value)


class Game(BaseModel, extra="allow"):
    id: str
    home_team: TeamNameEnum
    away_team: TeamNameEnum
    commence_time: datetime  # In UTC
    completed: Optional[bool] = None
    scores: Optional[List[TeamScore]] = None

    @computed_field
    @property
    def local_date(self) -> date:  # In EST
        return self.commence_time.astimezone(timezone("US/Eastern")).date()

    @computed_field
    @property
    def local_time(self) -> time:  # In EST
        return self.commence_time.astimezone(timezone("US/Eastern")).time()

    @computed_field
    @property
    def local_commence_time(self) -> datetime:  # In EST
        return self.commence_time.astimezone(timezone("US/Eastern"))

    @computed_field
    @property
    def winner(self) -> Optional[TeamNameEnum]:
        if self.completed and self.scores is not None:
            return max(self.scores, key=lambda x: x.score).name
        return None

    @field_validator("home_team", "away_team", mode="before")
    @classmethod
    def convert_away_to_valid_team_name(cls, value):
        return convert_team_name(name=value)

    @field_validator("commence_time", mode="before")
    @classmethod
    def add_tz_to_commence_time(cls, value):
        return add_timezone(date_str=value)

    @field_validator("commence_time", mode="after")
    @classmethod
    def as_utc(cls, value):
        return value.replace(tzinfo=utc)


def get_the_odds_json(api_key: str, endpoint: str) -> List[Dict]:
    """Make request to the-odds API for bookmaker odds

    Args:
        api_key (str): The-odds API key
        endpoint (str): The API endpoint to hit. Must be one of 'events' or 'scores'

    Returns:
        List[Dict]: The-odds response JSON
    """
    # Validate the input
    if endpoint not in ["events", "scores"]:
        raise ValueError(f"Endpoint must be one of 'events' or 'scores', got '{endpoint}'")

    # Send the request
    url = f"https://api.the-odds-api.com/v4/sports/americanfootball_nfl/{endpoint}/"
    params = {
        "regions": "us",
        "apiKey": api_key,
    }
    if endpoint == "scores":
        params["daysFrom"] = 3
    resp = requests.get(url, params)
    resp.raise_for_status()

    # Log API quota from headers
    requests_used = resp.headers["x-requests-used"]
    requests_remaining = resp.headers["x-requests-remaining"]
    used_by_last_call = resp.headers["x-requests-last"]
    logger.info(
        f"Hit '{endpoint}' endpoint - {requests_used} requests used, {requests_remaining} "
        f"remaining, {used_by_last_call} used by last call"
    )

    # Return the JSON response
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


def get_completed_games(games: List[Game]) -> List[Game]:
    """Filter games to only include those which have already completed

    Args:
        games (List[Game]): List of games

    Returns:
        List[Game]: Filtered list of games
    """
    return [game for game in games if game.completed]


def is_same_team(team1: str, team2: str) -> bool:
    """Check if two team names are the same. If they share any words, they are the same (e.g.
    'Patriots' == 'new-england-patriots')

    Args:
        team1 (str): First team name
        team2 (str): Second team name

    Returns:
        bool: True if the team names are the same, False otherwise
    """
    ignore_words = {"new", "san", "las", "los", "city", "bay"}
    team1_words = set(convert_team_name(team1).split("-")) - ignore_words
    team2_words = set(convert_team_name(team2).split("-")) - ignore_words
    return len(team1_words.intersection(team2_words)) > 0


def str_match_team_name(str_to_classify: str, candidate_labels: List[str]) -> str:
    matches = [is_same_team(team1=str_to_classify, team2=cand) for cand in candidate_labels]
    n_matches = sum(matches)
    if n_matches == 1:  # Exactly one of the candidates match
        top_idx = np.argmax(matches)
        return candidate_labels[top_idx]

    # Otherwise, raise a ValueError
    raise ValueError(
        f"Failed to classify '{str_to_classify}' into {candidate_labels} - matched "
        f"{n_matches} candidates"
    )
