from datetime import datetime

from nfl_commish.game import (
    convert_team_name,
    get_this_weeks_games,
    parse_the_odds_json,
)


def test_convert_team_name():
    assert convert_team_name(name="New Orleans Saints") == "new-orleans-saints"


def test_parse_odds(the_odds_resp_json):
    games = parse_the_odds_json(the_odds_resp_json)
    assert len(games) == 29


def test_get_this_weeks_games_tuesday(the_odds_resp_json, mocker):
    # Mock the current day
    wednesday = datetime.fromisoformat("2023-10-17 20:06:00+00:00")
    assert wednesday.weekday() == 1
    mock_datetime = mocker.patch("nfl_commish.game.datetime")
    mock_datetime.now.return_value = wednesday

    # Check the number of games
    games = parse_the_odds_json(the_odds_resp_json)
    this_weeks_games = get_this_weeks_games(games=games)
    assert len(this_weeks_games) == 13


def test_get_this_weeks_games_wednesday(the_odds_resp_json, mocker):
    # Mock the current day
    wednesday = datetime.fromisoformat("2023-10-18 20:06:00+00:00")
    assert wednesday.weekday() == 2
    mock_datetime = mocker.patch("nfl_commish.game.datetime")
    mock_datetime.now.return_value = wednesday

    # Check the number of games
    games = parse_the_odds_json(the_odds_resp_json)
    this_weeks_games = get_this_weeks_games(games=games)
    assert len(this_weeks_games) == 13


def test_get_this_weeks_games_friday(the_odds_resp_json, mocker):
    # Mock the current day
    wednesday = datetime.fromisoformat("2023-10-20 20:06:00+00:00")
    assert wednesday.weekday() == 4
    mock_datetime = mocker.patch("nfl_commish.game.datetime")
    mock_datetime.now.return_value = wednesday

    # Check the number of games
    games = parse_the_odds_json(the_odds_resp_json)
    this_weeks_games = get_this_weeks_games(games=games)
    assert len(this_weeks_games) == 12


def test_get_this_weeks_games_monday(the_odds_resp_json, mocker):
    # Mock the current day
    wednesday = datetime.fromisoformat("2023-10-23 20:06:00+00:00")
    assert wednesday.weekday() == 0
    mock_datetime = mocker.patch("nfl_commish.game.datetime")
    mock_datetime.now.return_value = wednesday

    # Check the number of games
    games = parse_the_odds_json(the_odds_resp_json)
    this_weeks_games = get_this_weeks_games(games=games)
    assert len(this_weeks_games) == 1


def test_game_id(the_odds_resp_json):
    games = parse_the_odds_json(the_odds_resp_json)
    assert games[0].home_team.value == "new-orleans-saints"
    assert games[0].away_team.value == "jacksonville-jaguars"
    assert games[0].id == "16143d5b3cfe34d32198da53771e14ee"
