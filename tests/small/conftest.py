import json
import os

import pytest


@pytest.fixture
def the_odds_scores_file_path():
    current_file = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file)
    return os.path.join(current_dir, os.pardir, "assets", "scores.json")


@pytest.fixture
def the_odds_events_file_path():
    current_file = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file)
    return os.path.join(current_dir, os.pardir, "assets", "events.json")


@pytest.fixture
def the_odds_scores_resp_json(the_odds_scores_file_path):
    with open(the_odds_scores_file_path, "r") as f:
        return json.load(f)


@pytest.fixture
def the_odds_events_resp_json(the_odds_events_file_path):
    with open(the_odds_events_file_path, "r") as f:
        return json.load(f)
