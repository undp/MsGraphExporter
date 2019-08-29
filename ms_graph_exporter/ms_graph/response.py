# -*- coding: utf-8 -*-
"""Module implements :class:`MsGraphResponse` class to handle MS Graph API responses.

:class:`MsGraphResponse` maintains context to allow efficient retrieval of paginated
responses to a query.

"""
from logging import Logger, getLogger
from typing import Any, Dict, List, Optional
from uuid import uuid4

from requests import Response

from ms_graph_exporter.ms_graph import api


class MsGraphResponse:
    """Class to handle MS Graph API responses.

    Store data from a single query to MS Graph API. Maintain reference to specific
    :obj:`~ms_graph_exporter.ms_graph.api.MsGraph` instance which initiated the query
    and uses it to retrieve subsequent parts of the paginated response.

    Attributes
    ----------
    __logger : :obj:`~logging.Logger`
        Channel to be used for log output specific to the module.

    _cache: :obj:`~typing.Dict` [:obj:`str`, :obj:`~typing.Optional` [:obj:`~typing.Dict` [:obj:`str`, :obj:`~typing.Any`]]]
        Dictionary holding URLs paged through or queried if no pagination
        is required and, optionally, responses received.

    _cache_enabled : :obj:`bool`
        Flag indicating if response data should be cached (``True``)
        or not (``False``).

    _complete : :obj:`bool`
        Flag indicating if the response is complete (``True``)
        or partial (``False``) and there are more paginated records
        to fetch.

    _data_page: :obj:`~typing.List` [:obj:`~typing.Dict` [:obj:`str`, :obj:`~typing.Any`]]
        Last data batch fetched from the API.

    _ms_graph : :obj:`~ms_graph_exporter.ms_graph.api.MsGraph`
        API instance to be used for queries.

    _next_url : :obj:`str`
        URL to retrieve next data batch if response is paginated.

    _uuid : :obj:`str`
        Universally unique identifier of the class instance to be used in logging.

    """  # noqa: E501

    __logger: Logger = getLogger(__name__)

    _cache: Dict[str, Optional[Dict[str, Any]]]

    _cache_enabled: bool = False

    _complete: bool = False

    _data_page: List[Dict[str, Any]]

    _ms_graph: "api.MsGraph"

    _next_stop: bool = False

    _next_url: str = "<undefined>"

    _uuid: str = "<undefined>"

    def __init__(
        self,
        ms_graph: "api.MsGraph",
        initial_data: Dict[str, Any],
        initial_url: str,
        cache_enabled: bool = False,
    ) -> None:
        """Initialize class instance.

        Parameters
        ----------
        ms_graph
            MS Graph API client instance to be used for queries.

        initial_data
            Data structure returned by MS Graph API from initial query.

        initial_url
            Initial query URL producing ``initial_data``.

        cache_enabled
            Flag indicating if response data should be cached (``True``)
            or not (``False``).

        """
        self._uuid = str(uuid4())

        self._cache = {}

        self._cache_enabled = cache_enabled

        self._ms_graph = ms_graph

        self._update(initial_data, initial_url)

        self.__logger.info("%s: Initialized", self)
        self.__logger.debug("%s: pushed: %s records", self, len(self._data_page))
        self.__logger.debug("%s: complete flag: %s", self, self._complete)
        self.__logger.debug("%s: next_url: %s", self, self._next_url)

    def __repr__(self) -> str:
        """Return string representation of class instance."""
        return "MsGraphResponse[{}]".format(self._uuid)

    def __iter__(self):
        """Return the object itself as iterator."""
        return self

    def __next__(self) -> List[Dict[str, Any]]:
        """Return cached data and prefetch more, if available."""
        self.__logger.debug("%s: [__next__]: Invoked", self)
        if self._next_stop:
            raise StopIteration
        else:
            if self._complete:
                self._next_stop = True

            old_data: List = self._data_page

            self._prefetch_next()

            self.__logger.debug(
                "%s: [__next__]: pulled: %s records", self, len(old_data)
            )
            self.__logger.debug(
                "%s: [__next__]: complete flag: %s", self, self._complete
            )
            self.__logger.debug(
                "%s: [__next__]: next_stop flag: %s", self, self._next_stop
            )

            return old_data

    def _prefetch_next(self) -> None:
        """Prefetch more responses.

        Prefetch next data batch, if more paginated records are available.

        """
        if not self._complete:
            response: Response = self._ms_graph._http_get_with_auth(self._next_url)

            if response.status_code == 200:
                response_data: Dict[str, Any] = response.json()

                self._update(response_data, response.url)

                self.__logger.info(
                    "%s: Prefetched next %s records", self, len(response_data["value"])
                )

    def _push_to_cache(self, api_response: Dict[str, Any], query_url: str) -> None:
        """Update cache.

        Save ``api_response``, if ``query_url`` is not yet committed to cache.

        """
        if query_url not in self._cache:
            self._cache[query_url] = api_response if self._cache_enabled else None

    def _update(self, api_response: Dict[str, Any], query_url: str) -> None:
        """Update internal state.

        Save the latest ``api_response`` received, ensure consistency
        of the internal metadata and push to cache if enabled.

        Raises
        ------
        ValueError
            If ``api_response`` does not have ``value`` key where the list
            with response data must reside (even if empty).

        """
        if "value" in api_response:
            self._data_page = api_response["value"]

            self._next_url = api_response.get("@odata.nextLink", "")

            self._complete = self._next_url == ""

            self._push_to_cache(api_response, query_url)
        else:
            self.__logger.exception(
                "%s: Exception: 'api_response' must have 'value' key present", self
            )
            raise ValueError("'api_response' must have 'value' key present")
