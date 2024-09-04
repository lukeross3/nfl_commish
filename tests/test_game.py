from datetime import date, datetime, time

import pytest

from nfl_commish.game import (
    convert_team_name,
    get_completed_games,
    get_the_odds_json,
    get_this_weeks_games,
    is_same_team,
    parse_the_odds_json,
)


def test_convert_team_name():
    assert convert_team_name(name="New Orleans Saints") == "new-orleans-saints"


def test_get_the_odds_bad_endpoint():
    with pytest.raises(ValueError) as e:
        get_the_odds_json(api_key="test", endpoint="bad_endpoint")
        assert str(e) == "Endpoint must be one of 'events' or 'scores', got 'bad_endpoint'"


def test_parse_events(the_odds_events_resp_json):
    games = parse_the_odds_json(the_odds_events_resp_json)
    assert len(games) == 272
    assert games[0].id == "612c2c3f6ca9e10d4b7ead21a2b0ff38"
    assert games[0].home_team.value == "kansas-city-chiefs"
    assert games[0].away_team.value == "baltimore-ravens"
    assert games[0].completed is None  # Not T/F, just not provided
    assert games[0].scores is None
    assert games[0].local_date == date(2024, 9, 5)  # MNF :)
    assert games[0].local_time == time(hour=20, minute=20)  # 8:20 PM


def test_parse_scores(the_odds_scores_resp_json):
    games = parse_the_odds_json(the_odds_scores_resp_json)
    assert len(games) == 272
    assert games[0].id == "612c2c3f6ca9e10d4b7ead21a2b0ff38"
    assert games[0].home_team.value == "kansas-city-chiefs"
    assert games[0].away_team.value == "baltimore-ravens"
    assert games[0].completed
    assert games[0].scores[0].name.value == "kansas-city-chiefs"
    assert games[0].scores[0].score == 5
    assert games[0].scores[1].name.value == "baltimore-ravens"
    assert games[0].scores[1].score == 9356
    assert games[0].winner.value == "baltimore-ravens"
    assert games[0].local_date == date(2024, 9, 5)  # MNF :)
    assert games[0].local_time == time(hour=20, minute=20)  # 8:20 PM


def test_parse_scores_not_completed(the_odds_scores_resp_json):
    games = parse_the_odds_json(the_odds_scores_resp_json)
    assert len(games) == 272
    assert games[1].id == "eca3b71919531e7ae0b4f3f501157e6c"
    assert games[1].home_team.value == "philadelphia-eagles"
    assert games[1].away_team.value == "green-bay-packers"
    assert not games[1].completed
    assert games[1].scores is not None
    assert len(games[1].scores) == 2
    assert games[1].winner is None


def test_parse_scores_not_started(the_odds_scores_resp_json):
    games = parse_the_odds_json(the_odds_scores_resp_json)
    assert len(games) == 272
    assert games[2].id == "7a5e353202d40a844491fa5753bc3097"
    assert games[2].home_team.value == "buffalo-bills"
    assert games[2].away_team.value == "arizona-cardinals"
    assert not games[2].completed
    assert games[2].scores is None
    assert games[1].winner is None


def test_get_this_weeks_games_tuesday(the_odds_events_resp_json, mocker):
    # Mock the current day
    tuesday = datetime.fromisoformat("2024-09-03 20:06:00+00:00")
    assert tuesday.weekday() == 1  # Monday is 0
    mock_datetime = mocker.patch("nfl_commish.game.datetime")
    mock_datetime.now.return_value = tuesday

    # Check the number of games
    games = parse_the_odds_json(the_odds_events_resp_json)
    assert len(games) == 272
    this_weeks_games = get_this_weeks_games(games=games)
    assert len(this_weeks_games) == 16


def test_get_this_weeks_games_wednesday(the_odds_events_resp_json, mocker):
    # Mock the current day
    wednesday = datetime.fromisoformat("2024-09-04 20:06:00+00:00")
    assert wednesday.weekday() == 2  # monday is 0
    mock_datetime = mocker.patch("nfl_commish.game.datetime")
    mock_datetime.now.return_value = wednesday

    # Check the number of games
    games = parse_the_odds_json(the_odds_events_resp_json)
    assert len(games) == 272
    this_weeks_games = get_this_weeks_games(games=games)
    assert len(this_weeks_games) == 16


def test_get_this_weeks_games_friday(the_odds_events_resp_json, mocker):
    # Mock the current day
    friday = datetime.fromisoformat("2024-09-06 20:06:00+00:00")
    assert friday.weekday() == 4  # monday is 0
    mock_datetime = mocker.patch("nfl_commish.game.datetime")
    mock_datetime.now.return_value = friday

    # Check the number of games
    games = parse_the_odds_json(the_odds_events_resp_json)
    assert len(games) == 272
    this_weeks_games = get_this_weeks_games(games=games)
    assert len(this_weeks_games) == 15  # Excluding TNF


def test_get_this_weeks_games_monday(the_odds_events_resp_json, mocker):
    # Mock the current day
    monday = datetime.fromisoformat("2024-09-09 20:06:00+00:00")  # MNF starts at 8:20 PM
    assert monday.weekday() == 0  # monday is 0
    mock_datetime = mocker.patch("nfl_commish.game.datetime")
    mock_datetime.now.return_value = monday

    # Check the number of games
    games = parse_the_odds_json(the_odds_events_resp_json)
    assert len(games) == 272
    this_weeks_games = get_this_weeks_games(games=games)
    assert len(this_weeks_games) == 1  # MNF is the only remaining game


def test_get_completed_games(the_odds_scores_resp_json):
    games = parse_the_odds_json(the_odds_scores_resp_json)
    assert len(games) == 272
    games = get_completed_games(games=games)
    assert len(games) == 1
    assert games[0].id == "612c2c3f6ca9e10d4b7ead21a2b0ff38"


def test_is_same_team():
    assert is_same_team("new-orleans-saints", "new-orleans-saints")
    assert is_same_team("new-orleans-saints", "New-Orleans-SAINTS")  # Ignore case
    assert is_same_team("new-orleans-saints", " new-orleans-saints  ")  # Ignore whitespace
    assert is_same_team("new-orleans-saints", "new orleans  saints")  # Ignore whitespace
    assert not is_same_team("new-orleans-saints", "new-england-patriots")
    assert not is_same_team("new-orleans-saints", "new-orleans-saints-2")
    assert not is_same_team("new-orleans-saints", "new-orleans-saint")
