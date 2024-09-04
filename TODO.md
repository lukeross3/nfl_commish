# TODO
<!-- - Create methods for 2 Odds endpoints: scores, events -->
<!-- - test the methods -->
- Add support for ties
- Create functions to:
    - Initialize a new week
    - Copy/lock picks to the main sheet (incl 16 selection)
    - Update scores
- Admin script that schedules each of the above functions
    - Initialize new week 6 hours after last game starts
        - Grab commence times and schedule based on this
    - Copy/lock picks 5 mins before each commence time
    - Update scores ~6 hours after each commence time