import pytest

from nfl_commish.utils import get_valid_team_names

# Get lists of team names and their cities
team_names = sorted(list(get_valid_team_names()))
mascots, cities = [], []
for team_name in team_names:
    words = team_name.split("-")
    mascots.append(words.pop())
    cities.append(" ".join(words))

# Set up args
args = []
for team_name, mascot, city in zip(team_names, mascots, cities):
    for opposing_team in team_names:
        if opposing_team == team_name:
            continue
        if city.replace(" ", "-") in opposing_team:
            continue
        args.append((mascot, team_name, [team_name, opposing_team]))
        args.append((city, team_name, [team_name, opposing_team]))


@pytest.mark.parametrize(["input_str", "gt_team", "possible_teams"], args)
def test_staged_classify_team_names(input_str, gt_team, possible_teams, classifier):
    pred, conf = classifier.staged_classify(
        str_to_classify=input_str,
        candidate_labels=possible_teams,
    )
    assert pred == gt_team
    assert conf == 1.0
