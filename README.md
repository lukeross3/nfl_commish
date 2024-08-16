<h1 align="center">
  NFL Commish
</h1>

<h4 align=center>
  
  ![CI Build](https://github.com/lukeross3/nfl_commish/actions/workflows/ci.yaml/badge.svg)

</h4>

This repo is a personal project to help me run my [NFL confidence league](#what-is-a-confidence-league) with some friends. This project grabs game times and results from an API, locks in picks, calculates scores for a given week, and updates the standings in a google sheet. Thank you **Robo Commish**!

## What is a Confidence League?

Every week, `n` NFL games are played (at most 16). League participants pick a winner for each game and then rank the games by their confidence in the winner, assigning a confidence value from `17 - n` up to `16` for each game. If your pick wins, then you get the confidence value for that game added to your score. If your pick loses, you get no points for that game. The league participant with the most points at the end of the regular season wins!