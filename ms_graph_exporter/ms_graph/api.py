# -*- coding: utf-8 -*-
"""Module implements :class:`MsGraph` class to perform authenticated queries to the API.

:class:`MsGraph` obtains an OAuth 2.0 token from Azure AD with Service Principal
for subsequent non-interactive authentication with the API endpoint. It also maintains
persistent HTTPS session to the endpoint for efficient network communications.

Example
-------
Use the :class:`MsGraph` like this::

    from datetime import datetime, timedelta
    from os import environ
    from logging import Logger, getLogger
    from typing import Any, Dict, List

    from ms_graph_exporter.ms_graph.api import MsGraph
    from ms_graph_exporter.ms_graph.response import MsGraphResponse

    logger: Logger
    graph: MsGraph
    t_now: datetime
    response: MsGraphResponse
    batch: List
    record: Dict[str, Any]

    logger = getLogger(__name__)

    graph = MsGraph(
        client_id=environ.get("GRAPH_CLIENT_ID"),
        client_secret=environ.get("GRAPH_CLIENT_SECRET"),
        tenant=environ.get("GRAPH_TENANT"),
    )

    t_now = datetime.utcnow()

    response = graph.get_signins(
        user_id="badc0ffe42@cafe.com",
        timestamp_start=(t_now - timedelta(minutes=10)),
        timestamp_end=(t_now - timedelta(minutes=5)),
        page_size=50
    )

    for batch in response:
        for record in batch:
            logger.info(
                "%s: %s: %s",
                signins,
                record["id"],
                record["ipAddress"],
            )

"""
from datetime import datetime
from http.client import responses
from logging import Logger, getLogger
from time import sleep
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from adal.authentication_context import AuthenticationContext

from requests import Response, Session

from ms_graph_exporter.ms_graph import response as api_response


class MsGraph:
    """Class to maintain authenticated connection, and post queries to MS Graph API.

    Authenticates with Azure AD, maintains an OAuth 2.0 token and HTTP session
    with connection pool to interact with MS Graph API.

    Attributes
    ----------
    __api_endpoint : :obj:`str`
        MS Graph API endpoint to call.

    __api_version : :obj:`str`
        MS Graph API version to call.

    __logger : :obj:`~logging.Logger`
        Channel to be used for log output specific to the module.

    __throttling_retries : :obj:`int`
        Number of retries when getting API throttling response.

    _auth_context : :obj:`AuthenticationContext <adal:adal.AuthenticationContext>`
        Authentication context maintained by MS ADAL for Python.
        Manages OAuth 2.0 token cache and refreshes it if necessary.

    _authority_url : :obj:`str`
        A URL that identifies a token authority. Should be of the format
        ``https://login.microsoftonline.com/your_tenant``

    _client_id : :obj:`str`
        The OAuth client id of the calling application.
        (``appId`` part of the Service Principal)

    _client_secret : :obj:`str`
        The OAuth client secret of the calling application.
        (``password`` part of the Service Principal)

    _tenant : :obj:`str`
        The Azure AD tenant granting the token and where the calling application is
        registered. Can be in GUID or friendly name format.
        (``tenant`` part of the Service Principal)

    _uuid : :obj:`str`
        Universally unique identifier of the class instance to be used in logging.

    """

    __api_endpoint: str = "https://graph.microsoft.com"
    __api_version: str = "v1.0"

    __logger: Logger = getLogger(__name__)

    __http_session: Optional[Session] = None

    __throttling_retries: int = 5

    _auth_context: AuthenticationContext
    _authority_url: str = "https://login.microsoftonline.com/{tenant}"

    _client_id: str = "<undefined>"
    _client_secret: str = "<undefined>"
    _tenant: str = "<undefined>"

    _uuid: str = "<undefined>"

    def __init__(  # noqa: S107
        self,
        client_id: str = "",
        client_secret: str = "",
        tenant: str = "",
        *args,
        **kwargs,
    ) -> None:
        """Initialize class instance.

        Parameters
        ----------
        client_id
            The OAuth client id of the calling application.
            (``appId`` part of the Service Principal)

        client_secret
            The OAuth client secret of the calling application.
            (``password`` part of the Service Principal)

        tenant
            The Azure AD tenant granting the token and where the calling application is
            registered. Can be in GUID or friendly name format.
            (``tenant`` part of the Service Principal)

        *args
            Variable length argument list for possible extension with subclass.

        **kwargs
            Arbitrary keyword arguments for possible extension with subclass.

        """
        self._uuid = str(uuid4())

        self._client_id = client_id
        self._client_secret = client_secret
        self._tenant = tenant

        self._authority_url = self._authority_url.format(tenant=self._tenant)

        self._auth_context = AuthenticationContext(
            self._authority_url, validate_authority=True, verify_ssl=True
        )

        self.__logger.info("%s: Initialized with client_id[%s]", self, self._client_id)
        self.__logger.debug("%s: client_secret: %s", self, self._client_secret)
        self.__logger.debug("%s: tenant: %s", self, self._tenant)

    def __repr__(self) -> str:
        """Return string representation of class instance."""
        return "MsGraph[{}]".format(self._uuid)

    @property
    def http_session(self) -> Session:
        """Provide access to HTTP session instance.

        Open persistent HTTP session with connection pool, if one does not exist yet.

        Returns
        -------
        :obj:`Session <requests:requests.Session>`
            Persistent HTTP session instance.

        """
        if self.__http_session is None:
            self.__http_session = Session()
        return self.__http_session

    @property
    def token(self) -> Dict[str, Any]:
        """Token to interact with MS Graph API.

        Use client credentials within ADAL authentication context to get
        OAuth 2.0 token from cache if not expired or re-request token otherwise.

        Returns
        -------
        :obj:`~typing.Dict` [:obj:`str`, :obj:`~typing.Any`]
            Cached or newly (re-)issued OAuth 2.0 token. Token obtained with client
            credentials has the following structure:

            .. code-block::

                {
                    "tokenType": "Bearer",
                    "expiresIn": 3600,
                    "expiresOn": "2019-07-12 23:38:57.541597",
                    "resource": "https://graph.microsoft.com",
                    "accessToken": "{{token string}}",
                    "isMRRT": True,
                    "_clientId": "cafebabe-4242-4242-cafe-badc0ffebabe",
                    "_authority": "https://login.microsoftonline.com/cafebabe-4242-4242-cafe-badc0ffebabe" # noqa: E501
                }

        """
        token: Dict[str, Any]

        token = self._auth_context.acquire_token_with_client_credentials(
            self.__api_endpoint, self._client_id, self._client_secret
        )

        if "expiresOn" in token:
            self.__logger.info(
                "%s: Acquired token expires on: %s", self, token["expiresOn"]
            )
        else:
            self.__logger.error("%s: No valid API token received", self)

        return token

    def _build_filter(
        self,
        filter_options: List[Tuple[str, str, str]] = None,
        filter_join_op: str = "and",
    ) -> str:
        """Build OData filter.

        Construct an OData filter from a list of tuples with filtering
        parameters expressions and values.

        Parameters
        ----------
        filter_options
            List of ``("option", "operand", "value")`` tuples to construct OData
            request filter by joining them with ``filter_join_op`` operator.

        filter_join_op
            Logic operator (i.e. ``or`` or ``and``) to join ``filter_options`` with.

        Note
        ----
        ``filter_options`` parameter follows this structure:

        .. code-block:: python

            [
                ("userPrincipalName", "eq", "badc0ffe42@cafe.com"),
                ("createdDateTime",   "ge", "2019-07-26T02:02:02Z"),
                ("createdDateTime",   "le", "2019-07-26T04:04:04Z"),
            ]

        So, ``startwith()`` expression must be presented as:

        .. code-block:: python

            ("startwith(userPrincipalName, 'badcafe')", "", "")

        Returns
        -------
        :obj:`str`
            OData filter.

        """
        filter_results: str = ""

        if filter_options is not None:
            filter_results = " {} ".format(filter_join_op).join(
                "{} {} {}".format(option, operand, value)
                for option, operand, value in filter_options
            )

        return filter_results

    def _http_get_with_auth(
        self, api_url: str, params: Dict[str, Any] = None
    ) -> Response:
        """Perform authenticated GET request.

        Request ``api_url`` with ``params`` using available OAuth 2.0 token
        and a connection pool from the established HTTP session.

        Note
        ----
        MS Graph sends ``HTTP 429`` code to signal `API throttling`_ with
        ``Retry-After`` HTTP header specifying the wait period in seconds.

        Throttling is handled by sleeping for ``Retry-After`` seconds and
        retrying again up to ``__throttling_retries`` times.

        .. _API throttling:
            https://docs.microsoft.com/en-us/graph/throttling

        Parameters
        ----------
        api_url
            URL to be requested with available OAuth 2.0 token.

        params
            URL parameters to supply with the request.

        Returns
        -------
        :obj:`Response <requests:requests.Response>`
            HTTP response to the authenticated GET request.

        """
        headers: Dict[str, str] = {
            "Authorization": "Bearer {}".format(self.token["accessToken"]),
            "Accept": "application/json",
            "Content-Type": "application/json",
            "client-request-id": str(uuid4()),
            "return-client-request-id": "true",
        }

        params_log: str = ""

        if params is not None:
            params_log = "&".join("{}={}".format(k, v) for k, v in params.items())

        retry: int = self.__throttling_retries

        while retry >= 0:
            self.__logger.info(
                "%s: Sending HTTP Request[%s]", self, headers["client-request-id"]
            )
            self.__logger.debug(
                "Request[%s][HTTP GET]: %s?%s",
                headers["client-request-id"],
                api_url,
                params_log,
            )

            response: Response = self.http_session.get(
                api_url, headers=headers, params=params, timeout=(3, 30)
            )

            self.__logger.info(
                "Request[%s][HTTP %s]: %s",
                response.headers["client-request-id"],
                response.status_code,
                responses[response.status_code],
            )

            if response.status_code == 200:
                self.__logger.debug(
                    "Request[%s][HTTP %s]: @odata.context: %s",
                    response.headers["client-request-id"],
                    response.status_code,
                    ("present" if "@odata.context" in response.json() else "absent"),
                )
                self.__logger.debug(
                    "Request[%s][HTTP %s]: @odata.nextLink: %s",
                    response.headers["client-request-id"],
                    response.status_code,
                    ("present" if "@odata.nextLink" in response.json() else "absent"),
                )
                self.__logger.info(
                    "Request[%s][HTTP %s]: size: %s",
                    response.headers["client-request-id"],
                    response.status_code,
                    len(response.json()["value"]),
                )
                break

            elif response.status_code == 429:
                throttling_delay = int(response.headers["Retry-After"])

                self.__logger.warning(
                    "%s: Throttled for %s seconds (%s retries left)",
                    self,
                    throttling_delay,
                    retry,
                )

                sleep(throttling_delay)

                retry = retry - 1

            else:
                self.__logger.exception(
                    "Request[%s][HTTP %s]: Unexpected HTTP code [%s]: %s",
                    response.headers["client-request-id"],
                    response.status_code,
                    response.json()["error"]["code"],
                    response.json()["error"]["message"],
                )
                self.__logger.debug("%s: Headers: %s", self, response.headers)

                break

        return response

    def _query_api(
        self,
        resource: str = None,
        odata_filter: str = None,
        page_size: int = None,
        cache_enabled: bool = False,
    ) -> "api_response.MsGraphResponse":
        """Query MS Graph API.

        Perform authenticated request to MS Graph ``resource`` with ``odata_filter``.
        Returns paginated response, if ``page_size`` is defined and greater than zero.

        Parameters
        ----------
        resource
            Resource/relationship to be queried from MS Graph API endpoint
            (e.g. ``me/messages``). Expected to start with resource name,
            but not with ``/``.

        odata_filter
            Query filter allowing to retrieve a subset of available data
            (e.g. ``createdDateTime le 2019-07-14T05:20:00``).

        page_size
            Number of records to be returned in a single (paginated) response.
            See `paging in MS Graph API`_ for more details.

            .. _paging in MS Graph API:
                https://docs.microsoft.com/en-us/graph/paging

        cache_enabled
            Flag indicating if response data should be cached (``True``)
            or not (``False``).

        Note
        ----
        If all requested records do not fit into the initial response, iterating through
        :obj:`~ms_graph_exporter.ms_graph.response.MsGraphResponse` instance would be
        needed to retrieve all available records in batches of ``page_size`` size.


        Returns
        -------
        :obj:`~ms_graph_exporter.ms_graph.response.MsGraphResponse`
            Response which (depending on the ``page_size``) would either contain
            a full set of returned records, or just the first batch cached and an
            iterator to get all the subsequent paginated results.

        """
        query_api_url: str = "{api_endpoint}/{version}/{resource}".format(
            api_endpoint=self.__api_endpoint,
            version=self.__api_version,
            resource=resource,
        )

        query_api_params: Dict = {}

        if (page_size is not None) and (page_size > 0):
            query_api_params["$top"] = page_size

        query_api_params["$filter"] = odata_filter

        self.__logger.info("%s: Query '%s'", self, resource)
        self.__logger.debug("%s: odata_filter: '%s'", self, odata_filter)
        self.__logger.debug("%s: page_size: %s", self, page_size)

        msgraph_results: Optional["api_response.MsGraphResponse"] = None

        response: Response = self._http_get_with_auth(
            api_url=query_api_url, params=query_api_params
        )

        msgraph_results = api_response.MsGraphResponse(
            ms_graph=self,
            initial_data=response.json() if response.status_code == 200 else None,
            initial_url=response.url,
            cache_enabled=cache_enabled,
        )

        return msgraph_results

    def _query_api_time_domain(
        self,
        resource: str = None,
        filter_options: List[Tuple[str, str, str]] = None,
        filter_join_op: str = "and",
        timestamp_start: datetime = None,
        timestamp_end: datetime = None,
        page_size: int = None,
        cache_enabled: bool = False,
    ) -> "api_response.MsGraphResponse":
        """Query time-domain records from MS Graph API.

        Request ``resource`` for the time-frame starting at ``timestamp_start`` and
        ending at ``timestamp_end``. Returns paginated response, if ``page_size`` is
        defined.

        Note
        ----
        * Queries all available data up to ``timestamp_end``, if ``timestamp_start``
          is not defined.
        * Without ``timestamp_end`` defined, gets the data up to the moment of the query
          execution minus intrinsic (~2 minutes) data population delay of the API.

        Parameters
        ----------
        resource
            Resource/relationship to be queried from MS Graph API endpoint
            (e.g. ``me/messages``). Expected to start with resource name,
            but not with ``/``.

        filter_options
            List of ``("option", "operand", "value")`` tuples to construct OData
            request filter by joining them with ``filter_join_op`` operator.

        filter_join_op
            Logic operator (i.e. ``or`` or ``and``) to join ``filter_options`` with.

        timestamp_start
            Limit results to records with greater or equal ``createdDateTime`` values.
            See ``Note`` section below for more details.

        timestamp_end
            Limit results to records with lower or equal ``createdDateTime`` values.

        page_size
            Number of records to be returned in a single batch (paginated) response.
            See ``Note`` section below for more details.

        cache_enabled
            Flag indicating if response data should be cached (``True``)
            or not (``False``).

        Note
        ----
        MS Graph API v1.0 output below suggests that API operates with timestamps
        of ``0.1 microsecond precision``, resulting in **7 digits** after the point
        for ``createdDateTime``.

            .. code-block::

                {
                    "@odata.context": "...snip...",
                    "value": [
                        {
                            "id": "cafebabe-4242-4242-cafe-badc0ffebabe",
                            "createdDateTime": "2019-07-21T22:05:58.8424069Z",
                            "...snip...": "...snip..."
                        }
                    ]
                }

        On the other hand, Python ``datetime`` module allows to define time down to
        ``1 microsecond precision``, resulting in **6 digits** after the point.

        >>> import datetime
        >>> timestamp_start = datetime.datetime(2019, 8, 24, 21, 10, 30, 9999999)
        Traceback (most recent call last):
            ...
        ValueError: microsecond must be in 0..999999
        >>> timestamp_start = datetime.datetime(2019, 8, 24, 21, 10, 30, 999999)
        >>> timestamp_start.isoformat()
        '2019-08-24T21:10:30.999999'

        To ensure no records are missed due to difference in timestamp precision between
        ``datetime`` module and the API, both ``timestamp_start`` and ``timestamp_end``
        parameters are truncated to seconds (microseconds value is replaced by ``0``)
        for ``$filter`` construction.
        Then ``.0000000`` is added to the string representation of ``timestamp_start``
        and ``.9999999`` is added to ``timestamp_end``.

        In other words, request time-frame always starts at the beginning of a
        0.1 microsecond and ends at the end of the 0.1 microsecond as defined by the
        precision of the MS Graph API v1.0 timestamps.

        Returns
        -------
        :obj:`~ms_graph_exporter.ms_graph.response.MsGraphResponse`
            A response which (depending on the ``page_size``) would either contain
            a full set of returned records, or just the first batch cached and an
            iterator to get all the subsequent paginated results.

        """
        query_filter: List[Tuple[str, str, str]] = []

        if filter_options is not None:
            query_filter = filter_options

        if timestamp_start is not None:
            query_filter.append(
                (
                    "createdDateTime",
                    "ge",
                    "{}.0000000Z".format(
                        timestamp_start.replace(microsecond=0).isoformat()
                    ),
                )
            )

        if timestamp_end is not None:
            query_filter.append(
                (
                    "createdDateTime",
                    "le",
                    "{}.9999999Z".format(
                        timestamp_end.replace(microsecond=0).isoformat()
                    ),
                )
            )

        response: "api_response.MsGraphResponse" = self._query_api(
            resource=resource,
            odata_filter=self._build_filter(query_filter, filter_join_op),
            page_size=page_size,
            cache_enabled=cache_enabled,
        )

        return response

    def get_signins(
        self,
        user_id: str = None,
        timestamp_start: datetime = None,
        timestamp_end: datetime = None,
        page_size: int = None,
        cache_enabled: bool = False,
    ) -> "api_response.MsGraphResponse":
        """Get Azure AD signin log records from MS Graph API.

        Request ``user_id`` login data for the time-frame starting at
        ``timestamp_start`` and ending at ``timestamp_end``. Returns
        paginated response, if ``page_size`` is defined.

        Parameters
        ----------
        user_id
            Limit results to records with ``userPrincipalName`` equal to ``user_id``.

        timestamp_start
            Limit results to records with greater or equal ``createdDateTime`` values.
            See :meth:`_query_api_time_domain` for more details.

        timestamp_end
            Limit results to records with lower or equal ``createdDateTime`` values.

        page_size
            Number of records to be returned in a single batch (paginated) response.
            See :meth:`_query_api_time_domain` for more details.

        cache_enabled
            Flag indicating if response data should be cached (``True``)
            or not (``False``).

        Returns
        -------
        :obj:`~ms_graph_exporter.ms_graph.response.MsGraphResponse`
            A response which (depending on the ``page_size``) would either contain
            a full set of returned records, or just the first batch cached and an
            iterator to get all the subsequent paginated results.

        """
        filter_options: List = []

        if user_id is not None:
            filter_options.append(("userPrincipalName", "eq", "'{}'".format(user_id)))

        response: "api_response.MsGraphResponse" = self._query_api_time_domain(
            resource="auditLogs/signIns",
            filter_options=filter_options,
            timestamp_start=timestamp_start,
            timestamp_end=timestamp_end,
            page_size=page_size,
            cache_enabled=cache_enabled,
        )

        return response
