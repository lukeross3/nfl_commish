import json

from nfl_commish.admin import (  # get_current_week_num,; init_admin_week,
    copy_predictions_to_admin,
)
from nfl_commish.game import parse_the_odds_json

player_names = [
    "Luke",
    # "Andrew",
    # "Shivam",
    # "Spuff",
    # "Benjie",
    # "Brett",
]
admin_sheet_name = "NFL Confidence '24-'25"
gspread_secret_path = "secrets/lukeross-google-secret.json"

with open("tests/assets/events.json", "r") as f:
    the_odds_json = json.load(f)
games = parse_the_odds_json(the_odds_json=the_odds_json)
this_weeks_games = games[:16]

copy_predictions_to_admin(
    week_number=1,
    player_names=player_names,
    admin_sheet_name=admin_sheet_name,
    gspread_secret_path=gspread_secret_path,
)

# try:
#     init_admin_week(
#         player_names=player_names,
#         admin_sheet_name=admin_sheet_name,
#         gspread_secret_path=gspread_secret_path,
#         this_weeks_games=this_weeks_games,
#         week_number=1,
#     )
# except Exception as e:
#     print(str(e))
#     x = f'A sheet with the name "Week {1}" already exists.' in str(e)
#     print(x)

# num = get_current_week_num(
#     admin_sheet_name=admin_sheet_name,
#     gspread_secret_path=gspread_secret_path,
# )

# print(num)
