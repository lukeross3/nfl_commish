import json
import logging
import os
import traceback
from typing import Any, Callable, Dict, Set

import gspread
import yaml
from loguru import logger
from pydantic import BaseModel
from tenacity import after_log, before_sleep_log, retry, wait_exponential

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


@retry(
    wait=wait_exponential(max=90),
    before_sleep=before_sleep_log(logger, logging.INFO),
    after=after_log(logger, logging.INFO),
)
def update_cell(ws: gspread.worksheet, row: int, col: int, value: Any) -> None:
    """Update a cell value, with retries to avoid write rate limiting

    Args:
        ws (gspread.worksheet): gspread worksheet object
        row (int): Row index to update
        col (int): Column index to update
        value (Any): Value to insert
    """
    ws.update_cell(row, col, value)


def read_config(config_path: str, config_class: BaseModel) -> BaseModel:
    """Read the yaml config from the config_path and return an instance of the given config_class

    Args:
        config_path (str): Path to the config yaml file
        config_class (BaseModel): Config class to instantiate

    Returns:
        BaseModel: Instance of the config class with values from config path
    """
    with open(config_path, "r") as f:
        config_dict = yaml.safe_load(f)
    return config_class(**config_dict)


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
    words = name.lower().strip().replace("-", " ").split()
    return "-".join(words)


def add_timezone(date_str: str) -> str:
    """Adds the timezone to a date string from the-odds API

    Args:
        date_str (str): Input date string from the-odds API

    Returns:
        str: Modified date string with time zone
    """
    return date_str.replace("Z", "+00:00")


def catch_with_logging(fn: Callable, args: Dict, error_log_template: str = "{}") -> Any:
    try:
        return fn(**args)
    except Exception:
        logger.error(error_log_template.format(traceback.format_exc()))
