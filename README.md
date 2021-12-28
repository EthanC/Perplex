# Perplex

Perplex is a Discord Rich Presence implementation for Plex.

<p align="center">
    <img src="https://i.imgur.com/lGzUmW9.png" draggable="false">
</p>

## Features

-   Modern and beautiful Rich Presence for both movies and TV shows
-   Lightweight console application that runs in the background
-   Support for two-factor authentication at login
-   Optional minimal mode for Rich Presence to hide granular information

## Installation

Perplex requires Python 3.10 or greater. Required dependencies can be found in [`pyproject.toml`](https://github.com/EthanC/Perplex/blob/main/pyproject.toml).

A [TMDB API Key](https://www.themoviedb.org/settings/api) is required to enable media art and external information.

## Usage

Open `config_example.json` and provide the configurable values, then save and rename the file to `config.json`.

```py
python perplex.py
```

Note: A Discord desktop client must be open on the same device that Perplex is running on.
