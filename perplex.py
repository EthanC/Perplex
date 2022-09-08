import json
import urllib.parse
from datetime import datetime
from pathlib import Path
from sys import exit, stderr
from time import sleep
from typing import Any, Dict, List, Optional, Union

import httpx
from httpx import Response
from loguru import logger
from plexapi.audio import TrackSession
from plexapi.media import Media
from plexapi.myplex import MyPlexAccount, MyPlexResource, PlexServer
from plexapi.video import EpisodeSession, MovieSession
from pypresence import Presence


class Perplex:
    """
    Discord Rich Presence implementation for Plex.

    https://github.com/EthanC/Perplex
    """

    def Initialize(self: Any) -> None:
        """Initialize Perplex and begin primary functionality."""

        logger.info("Perplex")
        logger.info("https://github.com/EthanC/Perplex")

        self.config: Dict[str, Any] = Perplex.LoadConfig(self)

        Perplex.SetupLogging(self)

        plex: MyPlexAccount = Perplex.LoginPlex(self)
        discord: Presence = Perplex.LoginDiscord(self)

        while True:
            session: Optional[Union[MovieSession, EpisodeSession, TrackSession]] = Perplex.FetchSession(
                self, plex
            )

            if session is not None:
                logger.success(f"Fetched active media session")

                if type(session) is MovieSession:
                    status: Dict[str, Any] = Perplex.BuildMoviePresence(self, session)
                elif type(session) is EpisodeSession:
                    status: Dict[str, Any] = Perplex.BuildEpisodePresence(self, session)
                elif type(session) is TrackSession:
                    status: Dict[str, Any] = Perplex.BuildTrackPresence(self, session)

                success: Optional[bool] = Perplex.SetPresence(self, discord, status)

                # Reestablish a failed Discord Rich Presence connection
                if success is False:
                    discord = Perplex.LoginDiscord(self)
            else:
                try:
                    discord.clear()
                except Exception:
                    pass

            # Presence updates have a rate limit of 1 update per 15 seconds
            # https://discord.com/developers/docs/rich-presence/how-to#updating-presence
            logger.info("Sleeping for 15s...")

            sleep(15.0)

    def LoadConfig(self: Any) -> Dict[str, Any]:
        """Load the configuration values specified in config.json"""

        try:
            with open("config.json", "r") as file:
                config: Dict[str, Any] = json.loads(file.read())
        except Exception as e:
            logger.critical(f"Failed to load configuration, {e}")

            exit(1)

        logger.success("Loaded configuration")

        return config

    def SetupLogging(self: Any) -> None:
        """Setup the logger using the configured values."""

        settings: Dict[str, Any] = self.config["logging"]

        if (level := settings["severity"].upper()) != "DEBUG":
            try:
                logger.remove()
                logger.add(stderr, level=level)

                logger.success(f"Set logger severity to {level}")
            except Exception as e:
                # Fallback to default logger settings
                logger.add(stderr, level="DEBUG")

                logger.error(f"Failed to set logger severity to {level}, {e}")

    def LoginPlex(self: Any) -> MyPlexAccount:
        """Authenticate with Plex using the configured credentials."""

        settings: Dict[str, Any] = self.config["plex"]

        account: Optional[MyPlexAccount] = None

        if Path("auth.txt").is_file() is True:
            try:
                with open("auth.txt", "r") as file:
                    auth: str = file.read()

                account = MyPlexAccount(token=auth)
            except Exception as e:
                logger.error(f"Failed to authenticate with Plex using token, {e}")

        if account is None:
            username: str = settings["username"]
            password: str = settings["password"]

            if settings["twoFactor"] is True:
                print(f"Enter Verification Code: ", end="")
                code: str = input()

                if (code == "") or (code.isspace()):
                    logger.warning(
                        "Two-Factor Authentication is enabled but code was not supplied"
                    )
                else:
                    password = f"{password}{code}"

            try:
                account = MyPlexAccount(username, password)
            except Exception as e:
                logger.critical(f"Failed to authenticate with Plex, {e}")

                exit(1)

        logger.success("Authenticated with Plex")

        try:
            with open("auth.txt", "w+") as file:
                file.write(account.authenticationToken)
        except Exception as e:
            logger.error(
                f"Failed to save Plex authentication token for future logins, {e}"
            )

        return account

    def LoginDiscord(self: Any) -> Presence:
        """Authenticate with Discord using the configured credentials."""

        client: Optional[Presence] = None

        while client is None:
            try:
                client = Presence(self.config["discord"]["appId"])
                client.connect()
            except Exception as e:
                logger.error(f"Failed to connect to Discord ({e}) retry in 15s...")

                sleep(15.0)

        logger.success("Authenticated with Discord")

        return client

    def FetchSession(
        self: Any, client: MyPlexAccount
    ) -> Optional[Union[MovieSession, EpisodeSession, TrackSession]]:
        """
        Connect to the configured Plex Media Server and return the active
        media session.
        """

        settings: Dict[str, Any] = self.config["plex"]

        resource: Optional[MyPlexResource] = None
        server: Optional[PlexServer] = None

        for entry in settings["servers"]:
            for result in client.resources():
                if entry.lower() == result.name.lower():
                    resource = result

                    break

            if resource is not None:
                break

        if resource is None:
            logger.critical("Failed to locate configured Plex Media Server")

            exit(1)

        try:
            server = resource.connect()
        except Exception as e:
            logger.critical(
                f"Failed to connect to configured Plex Media Server ({resource.name}), {e}"
            )

            exit(1)

        sessions: List[Media] = server.sessions()
        active: Optional[Union[MovieSession, EpisodeSession, TrackSession]] = None

        if len(sessions) > 0:
            i: int = 0

            for entry in settings["users"]:
                for result in sessions:
                    if entry.lower() in [alias.lower() for alias in result.usernames]:
                        active = sessions[i]

                        break

                    i += 1

        if active is None:
            logger.info("No active media sessions found for configured users")

            return

        if type(active) is MovieSession:
            return active
        elif type(active) is EpisodeSession:
            return active
        elif type(active) is TrackSession:
            return active

        logger.error(f"Fetched active media session of unknown type: {type(active)}")

    def BuildMoviePresence(self: Any, active: MovieSession) -> Dict[str, Any]:
        """Build a Discord Rich Presence status for the active movie session."""

        minimal: bool = self.config["discord"]["minimal"]

        result: Dict[str, Any] = {}

        metadata: Optional[Dict[str, Any]] = Perplex.FetchMetadata(
            self, active.title, active.year, "movie"
        )

        if minimal is True:
            result["primary"] = active.title
        else:
            result["primary"] = f"{active.title} ({active.year})"

            details: List[str] = []

            if len(active.genres) > 0:
                details.append(active.genres[0].tag)

            if len(active.directors) > 0:
                details.append(f"Dir. {active.directors[0].tag}")

            if len(details) > 1:
                result["secondary"] = ", ".join(details)

        if metadata is None:
            # Default to image uploaded via Discord Developer Portal
            result["image"] = "movie"
            result["buttons"] = []
        else:
            mId: int = metadata["id"]
            mType: str = metadata["media_type"]
            imgPath: str = metadata["poster_path"]

            result["image"] = f"https://image.tmdb.org/t/p/original{imgPath}"

            result["buttons"] = [
                {"label": "TMDB", "url": f"https://themoviedb.org/{mType}/{mId}"}
            ]

        result["remaining"] = int((active.duration / 1000) - (active.viewOffset / 1000))
        result["imageText"] = active.title

        logger.trace(result)

        return result

    def BuildEpisodePresence(self: Any, active: EpisodeSession) -> Dict[str, Any]:
        """Build a Discord Rich Presence status for the active episode session."""

        result: Dict[str, Any] = {}

        metadata: Optional[Dict[str, Any]] = Perplex.FetchMetadata(
            self, active.show().title, active.show().year, "tv"
        )

        result["primary"] = active.show().title
        result["secondary"] = active.title
        result["remaining"] = int((active.duration / 1000) - (active.viewOffset / 1000))
        result["imageText"] = active.show().title

        if (active.seasonNumber is not None) and (active.episodeNumber is not None):
            result["secondary"] += f" (S{active.seasonNumber}:E{active.episodeNumber})"

        if metadata is None:
            # Default to image uploaded via Discord Developer Portal
            result["image"] = "tv"
            result["buttons"] = []
        else:
            mId: int = metadata["id"]
            mType: str = metadata["media_type"]
            imgPath: str = metadata["poster_path"]

            result["image"] = f"https://image.tmdb.org/t/p/original{imgPath}"

            result["buttons"] = [
                {"label": "TMDB", "url": f"https://themoviedb.org/{mType}/{mId}"}
            ]

        logger.trace(result)

        return result

    def BuildTrackPresence(self: Any, active: TrackSession) -> Dict[str, Any]:
        """Build a Discord Rich Presence status for the active music session."""

        result: Dict[str, Any] = {}

        result["primary"] = active.titleSort
        result["secondary"] = f"by {active.artist().title}"
        result["remaining"] = int((active.duration / 1000) - (active.viewOffset / 1000))
        result["imageText"] = active.parentTitle

        # Default to image uploaded via Discord Developer Portal
        result["image"] = "music"
        result["buttons"] = []

        logger.trace(result)

        return result

    def FetchMetadata(
        self: Any, title: str, year: int, format: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch metadata for the provided title from TMDB."""

        settings: Dict[str, Any] = self.config["tmdb"]
        key: str = settings["apiKey"]

        if settings["enable"] is not True:
            logger.warning(f"TMDB disabled, some features will not be available")

            return

        try:
            res: Response = httpx.get(
                f"https://api.themoviedb.org/3/search/multi?api_key={key}&query={urllib.parse.quote(title)}"
            )
            res.raise_for_status()

            logger.debug(f"(HTTP {res.status_code}) GET {res.url}")
            logger.trace(res.text)
        except Exception as e:
            logger.error(f"Failed to fetch metadata for {title} ({year}), {e}")

            return

        data: Dict[str, Any] = res.json()

        for entry in data.get("results", []):
            if format == "movie":
                if entry["media_type"] != format:
                    continue
                elif title.lower() != entry["title"].lower():
                    continue
                elif entry["release_date"].startswith(str(year)) is False:
                    continue
            elif format == "tv":
                if entry["media_type"] != format:
                    continue
                elif title.lower() != entry["name"].lower():
                    continue
                elif entry["first_air_date"].startswith(str(year)) is False:
                    continue

            return entry

        logger.warning(f"Could not locate metadata for {title} ({year})")

    def SetPresence(
        self: Any, client: Presence, data: Dict[str, Any]
    ) -> Optional[bool]:
        """Set the Rich Presence status for the provided Discord client."""

        title: str = data["primary"]

        data["buttons"].append(
            {"label": "Get Perplex", "url": "https://github.com/EthanC/Perplex"}
        )

        try:
            client.update(
                details=title,
                state=data.get("secondary"),
                end=int(datetime.now().timestamp() + data["remaining"]),
                large_image=data["image"],
                large_text=data["imageText"],
                small_image="plex",
                small_text="Plex",
                buttons=data["buttons"],
            )
        except Exception as e:
            logger.error(f"Failed to set Discord Rich Presence to {title}, {e}")

            return False

        logger.success(f"Set Discord Rich Presence to {title}")


if __name__ == "__main__":
    try:
        Perplex.Initialize(Perplex)
    except KeyboardInterrupt:
        exit()
