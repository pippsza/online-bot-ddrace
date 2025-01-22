from abc import ABC
from typing import Optional, TypeVar, Type, Any

import aiohttp
from aiohttp import ClientSession, ClientConnectorError
from aiohttp.typedefs import DEFAULT_JSON_DECODER

ModelType = TypeVar('ModelType', bound='Model')


class API(ABC):
    def __init__(
            self,
            session: ClientSession = None,
            json_loads: Any = DEFAULT_JSON_DECODER
    ):
        self.__session = session
        self.json_loads = json_loads

    @staticmethod
    def powered() -> None:
        return None

    async def _get(self, url: str) -> Optional[dict]:
        """Send a GET request to the given URL and return the response as JSON."""
        if self.__session is None:
            self.__session = aiohttp.ClientSession()

        try:
            async with self.__session.get(url) as req:
                if req.status == 200:
                    return await req.json(loads=self.json_loads)
                return
        except ClientConnectorError:
            return

    async def _generate_model_instance(
            self,
            url: str,
            model: Type[ModelType],
            k: Optional[str] = None
    ) -> Optional[ModelType]:
        """Generate a model instance from the given URL and optional keyword arguments.

        Args:
            url (str): The URL to fetch data from.
            model (Type[ModelType]): The model class to instantiate.
            k (str, optional): An optional keyword to wrap the data in a dictionary.

        Returns:
            Optional[ModelType]: A model instance.
        """
        dat = await self._get(url)
        if dat is None or not dat:
            return

        data_to_pass = {k: dat} if k is not None else dat
        return model(**data_to_pass)

    async def is_closed(self) -> bool:
        """True is closed, False otherwise."""
        return self.__session is None or self.__session.closed

    async def close(self) -> None:
        """Close the aiohttp session."""
        if self.__session is not None:
            await self.__session.close()
        self.__session = None
