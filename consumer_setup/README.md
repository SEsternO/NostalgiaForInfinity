# NFI CONSUMER SETUP (proof-of-concept)

Better docs coming soon! (probably...)

This is an attempt to parallelize NFI X6 heavy pair population between multiple dry-run producer bots in order for the bot to react to the market changes faster.

## Usage (docker)

1. Set up the vanilla bot with instructions from the README.md in the repo root if you didn't already. If you already have a working setup, copy this consumer_setup catalog into your bot catalog and replace NostalgiaForInfinityX6.py strategy file with the file from this repo, and regularly update it.
2. Open `consumer_setup/.env` file and edit the variables to your need, **very carefully** following the instruction comments inside the file.
3. Inside consumer_setup catalog, in the terminal type `docker compose up -d` to start the bots.

### Cheatsheet

Reload the bots: `docker compose up -d --force-recreate`

Stop the bots: `docker compose down`

Watch logs: `docker compose logs -f`
