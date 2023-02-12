# Perplex

Perplex is a Discord Rich Presence implementation for Plex.

<p align="center">
    <img src="https://i.imgur.com/M7tBxzg.png" draggable="false">
</p>

## Features

-   Modern and beautiful Rich Presence for movies, TV shows, and music.
-   [The Movie Database (TMDB)](https://www.themoviedb.org/) integration for enhanced media information.
-   Optional minimal mode for Rich Presence to hide granular information
-   Lightweight console application that runs in the background.
-   Support for two-factor authentication (2FA) at login.
-   Prioritize multiple Plex media servers and users with one configuration.

## Setup

Perplex is built for [Python 3.11](https://www.python.org/) or greater. [TMDB API](https://www.themoviedb.org/settings/api) credentials are required to enable media art and external information.

Note: A Discord desktop client must be connected on the same device that Perplex is running on.

1. Install required dependencies using [Poetry](https://python-poetry.org/): `poetry install`
2. Rename `config_example.json` to `config.json`, then provide the configurable values.
3. Start Perplex: `python perplex.py`

**Configurable Values:**

-   `logging`:`severity`: Minimum [Loguru](https://loguru.readthedocs.io/en/stable/api/logger.html) severity level to display in the console (do not modify unless necessary).
-   `plex`:`username`: Plex username for login.
-   `plex`:`password`: Plex password for login.
-   `plex`:`twoFactor`: `true` or `false` toggle for two-factor authentication prompt at login.
-   `plex`:`servers`: List of Plex media servers, in order of priority.
-   `plex`:`users`: List of Plex users, in order of priority.
-   `tmdb`:`enable`: `true` or `false` toggle for enhanced media information in Rich Presence.
-   `tmdb`:`apiKey`: [TMDB API](https://www.themoviedb.org/settings/api) key (only used if `tmdb` `enable` is `true`).
-   `discord`:`appId`: Discord application ID (do not modify unless necessary).
-   `discord`:`minimal`: `true` or `false` toggle for minimal media information in Rich Presence.
