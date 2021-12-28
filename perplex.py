import json
import urllib.parse
from datetime import datetime
from pathlib import Path
from sys import exit, stderr
from time import sleep
from typing import Any, Dict, List, Optional, Union

from loguru import logger
from plexapi.media import Media
from plexapi.myplex import MyPlexAccount, MyPlexResource, PlexServer
from plexapi.video import Episode, Movie
from pypresence import Presence

from utils import Utility


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

        plex: MyPlexAccount = Perplex.LoginPlex(self)

        discord: Presence = Presence(self.config["discord"]["appId"])
        discord.connect()

        while True:
            session: Optional[Union[Movie, Episode]] = Perplex.FetchSession(self, plex)

            if session is not None:
                logger.success(
                    f"Fetched an active media session from the connected Plex Media Server"
                )

                if type(session) is Movie:
                    status: Dict[str, Any] = Perplex.BuildMoviePresence(self, session)
                elif type(session) is Episode:
                    status: Dict[str, Any] = Perplex.BuildEpisodePresence(self, session)

                success: Optional[bool] = Perplex.SetPresence(self, discord, status)

                # Reestablish a failed Discord Rich Presence connection
                if success is False:
                    discord.connect()
            else:
                discord.clear()

            # Presence updates have a rate limit of 1 update per 15 seconds
            # https://discord.com/developers/docs/rich-presence/how-to#updating-presence
            logger.debug("Sleeping for 15s...")

            sleep(15.0)

    def LoadConfig(self: Any) -> Dict[str, Any]:
        """Load the configuration values specified in config.json"""

        try:
            with open("config.json", "r") as file:
                config: Dict[str, Any] = json.loads(file.read())
        except Exception as e:
            logger.critical(f"Failed to load configuration, {e}")

            exit(1)

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
                logger.error(f"Failed to authenticate with token, {e}")

        if account is None:
            username: str = settings["username"]
            password: str = settings["password"]

            if settings["twoFactor"] is True:
                code: Optional[str] = Utility.Prompt(self, "Enter Verification Code")

                if code is None:
                    logger.warning(
                        "Two-Factor Authentication is configured but code was not supplied at login"
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
            logger.error(f"Failed to save authentication token for future logins, {e}")

        return account

    def FetchSession(
        self: Any, client: MyPlexAccount
    ) -> Optional[Union[Movie, Episode]]:
        """
        Connect to the configured Plex Media Server and return the active
        media session.
        """

        settings: Dict[str, Any] = self.config["plex"]

        resource: Optional[MyPlexResource] = None
        server: Optional[PlexServer] = None

        for entry in settings["servers"]:
            for result in client.resources():
                if entry == result.name:
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

        if len(sessions) == 0:
            logger.info(
                "Failed to locate active media session on connected Plex Media Server"
            )

            return

        active: Union[Movie, Episode] = sessions[0]

        if type(active) is Movie:
            return active
        elif type(active) is Episode:
            return active

        logger.error(
            f"Fetched active media session of unknown type: {type(sessions[0])}"
        )

    def BuildMoviePresence(self: Any, active: Movie) -> Dict[str, Any]:
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
            result["image"] = "media"
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

        return result

    def BuildEpisodePresence(self: Any, active: Episode) -> Dict[str, Any]:
        """Build a Discord Rich Presence status for the active episode session."""

        result: Dict[str, Any] = {}

        metadata: Optional[Dict[str, Any]] = Perplex.FetchMetadata(
            self, active.show().title, None, "episode"
        )

        result["primary"] = active.show().title
        result["secondary"] = active.title
        result["remaining"] = int((active.duration / 1000) - (active.viewOffset / 1000))
        result["imageText"] = active.show().title

        if (active.seasonNumber is not None) and (active.episodeNumber is not None):
            result["secondary"] += f" (S{active.seasonNumber}:E{active.episodeNumber})"

        if metadata is None:
            # Default to image uploaded via Discord Developer Portal
            result["image"] = "media"
            result["buttons"] = []
        else:
            mId: int = metadata["id"]
            mType: str = metadata["media_type"]
            imgPath: str = metadata["poster_path"]

            result["image"] = f"https://image.tmdb.org/t/p/original{imgPath}"

            result["buttons"] = [
                {"label": "TMDB", "url": f"https://themoviedb.org/{mType}/{mId}"}
            ]

        return result

    def FetchMetadata(
        self: Any, title: str, year: Optional[int], format: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch metadata for the provided title from TMDB."""

        settings: Dict[str, Any] = self.config["tmdb"]
        key: str = settings["apiKey"]

        if settings["enable"] is not True:
            logger.warning(f"TMDB disabled, some features will not be available")

            return

        data: Dict[str, Any] = Utility.GET(
            self,
            f"https://api.themoviedb.org/3/search/multi?api_key={key}&query={urllib.parse.quote(title)}",
        )

        for entry in data.get("results", []):
            if format == "movie":
                if entry["media_type"] != "movie":
                    continue
                elif title.lower() != entry["title"].lower():
                    continue
                elif entry["release_date"].startswith(str(year)) is False:
                    continue
            elif format == "episode":
                if entry["media_type"] != "tv":
                    continue
                elif title.lower() != entry["name"].lower():
                    continue

            return entry

        logger.warning(
            f"Failed to fetch metadata for {title} ({year}), some features will not be available"
        )

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
            logger.error(f"Failed to set Discord Rich Presence ({title}), {e}")

            return False

        logger.success(f"Set Discord Rich Presence ({title})")


if __name__ == "__main__":
    try:
        Perplex.Initialize(Perplex)
    except KeyboardInterrupt:
        exit()
