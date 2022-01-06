# Perplex

Perplex is a Discord Rich Presence implementation for Plex.

<p align="center">
    <img src="https://i.imgur.com/M7tBxzg.png" draggable="false">
</p>

## Features

-   Modern and beautiful Rich Presence for moviesm, TV shows, and music
-   The Movie Database (TMDB) integration for enhanced media information
-   Optional minimal mode for Rich Presence to hide granular information
-   Lightweight console application that runs in the background
-   Support for two-factor authentication (2FA) at login
-   Prioritize multiple Plex Media Servers and users with one configuration

## Installation

Perplex requires Python 3.10 or greater. Required dependencies can be found in [`pyproject.toml`](https://github.com/EthanC/Perplex/blob/main/pyproject.toml).

A [TMDB API Key](https://www.themoviedb.org/settings/api) is required to enable media art and external information.

## Usage

Open `config_example.json` and provide the configurable values, then save and rename the file to `config.json`.

```py
python perplex.py
```

Note: A Discord desktop client must be open on the same device that Perplex is running on.
