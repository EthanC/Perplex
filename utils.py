import json
from time import sleep
from typing import Any, Optional, Union

import httpx
from httpx import HTTPError, Response, TimeoutException
from loguru import logger


class Utility:
    """Utilitarian functions designed for Perplex."""

    def Prompt(self: Any, message: str) -> Optional[str]:
        """Prompt the user for input with the specified message."""

        print(f"\n{message}: ", end="")
        result: Optional[str] = input()
        print()

        if result == "":
            result = None

        return result

    def GET(self: Any, url: str, isRetry: bool = False) -> Optional[Union[str, bytes]]:
        """Perform an HTTP GET request and return its response."""

        logger.debug(f"GET {url}")

        status: int = 0

        try:
            res: Response = httpx.get(url, follow_redirects=True)
            status = res.status_code
            data: str = res.text

            res.raise_for_status()
        except HTTPError as e:
            if isRetry is False:
                logger.debug(f"(HTTP {status}) GET {url} failed, {e}... Retry in 10s")

                sleep(10)

                return Utility.GET(self, url, True)

            logger.error(f"(HTTP {status}) GET {url} failed, {e}")

            return
        except TimeoutException as e:
            if isRetry is False:
                logger.debug(f"GET {url} failed, {e}... Retry in 10s")

                sleep(10)

                return Utility.GET(self, url, True)

            # TimeoutException is common, no need to log as error
            logger.debug(f"GET {url} failed, {e}")

            return
        except Exception as e:
            if isRetry is False:
                logger.debug(f"GET {url} failed, {e}... Retry in 10s")

                sleep(10)

                return Utility.GET(self, url, True)

            logger.error(f"GET {url} failed, {e}")

            return

        logger.trace(data)

        return json.loads(data)
