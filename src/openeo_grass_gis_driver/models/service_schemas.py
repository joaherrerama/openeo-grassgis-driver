# -*- coding: utf-8 -*-
"""This file includes all required openEO response schemas
"""
from typing import List, Optional, Dict
from openeo_grass_gis_driver.models.schema_base import JsonableObject, EoLinks
from openeo_grass_gis_driver.models.process_graph_schemas import ProcessGraphNode

__author__ = "Anika Bettge"
__copyright__ = "Copyright 2018, mundialis"
__maintainer__ = "Anika Bettge"


class Service(JsonableObject):
    """	The base data for the secondary web service to create

    id:
        required
        string (service_id) ^[A-Za-z0-9_\-\.~]+$
        Unique identifier of a secondary web service that is generated by the
        back-end during creation. MUST match the specified pattern.

    title:
        string (title) Nullable
        A short description to easily distinguish entities.

    description:
        string (description) Nullable
        Detailed description to fully explain the entity.
        CommonMark 0.28 syntax MAY be used for rich text representation.

    process_graph:
        required
        object (Process Graph)
        A process graph defines a graph-like structure as a connected set
        of executable processes. Each key is a unique identifier (node id)
        that is used to refer to the process in the graph.

    url:
        required
        string <url> (service_url)
        URL at which the secondary web service is accessible. Doesn't
        necessarily need to be located within the API.

    type
        required
        string (service_type)
        Definintion of the service type to access result data. All available
        service types can be retrieved via GET /service_types. Service types
        MUST be accepted case insensitive.

    enabled:
        boolean (service_enabled)
        Default: true
        Describes whether a secondary web service is responding to requests
        (true) or not (false). Defaults to true. Disabled services don't
        produce any costs.

    parameters:
        object (Service Parameters)
        List of arguments, i.e. the parameter names supported by the
        secondary web service combined with actual values. See GET
        /service_types for supported parameters and valid arguments.
        For example, this could specify the required version of the
        service, visualization details or any other service dependant
        configuration.

    attributes:
        required
        object (Secondary Web Service Attributes)
        Additional attributes of the secondary web service, e.g. available
        layers for a WMS based on the bands in the underlying GeoTiff. See
        GET /service_types for supported attributes.

    submitted:
        string <date-time> (submitted)
        Date and time of creation, formatted as a RFC 3339 date-time.

    plan:
        string (billing_plan_defaultable) Nullable
        The billing plan to process and charge the job with.
        The plans and the default plan can be retrieved by calling GET /.
        Billing plans MUST be accepted case insensitive. Billing plans not on
        the list of available plans MUST be rejected with openEO error
        BillingPlanInvalid.
        If no billing plan is specified by the client, the server MUST default
        to the default billing plan in GET /. If the default billing plan of
        the provider changes, the job or service MUST not be affected by the
        change, i.e. the default plan which is valid during job or service
        creation must be permanently assigned to the job or service until the
        client requests to change it.

    costs:
        number (money)
        An amount of money or credits. The value MUST be specified in the
        currency the back-end is working with. The currency can be retrieved
        by calling GET /.

    budget:
        number (budget) Nullable
        Default: null
        Maximum amount of costs the user is allowed to produce. The value MUST
        be specified in the currency the back-end is working with. The currency
        can be retrieved by calling GET /. If possible, back-ends SHOULD
        reject jobs with openEO error PaymentRequired if the budget is too low
        to process the request completely. Otherwise, when reaching the budget
        jobs MAY try to return partial results if possible. Otherwise the
        request and results are discarded. Users SHOULD be warned by clients
        that reaching the budget MAY discard the results and that setting this
        value should be well-wrought. Setting the buget to null means there is
        no specified budget.

    """

    def __init__(self,
                 process_graph: ProcessGraphNode,
                 url: str, type: str, parameters: Dict,
                 attributes: Dict, submitted: str = None,
                 title: str = None, description: str = None,
                 enabled: bool = True,
                 plan: str = None, costs: float = None, budget: float = None):

        self.title = title
        self.description = description
        self.process_graph = process_graph
        self.url = url
        self.type = type
        self.enabled = enabled
        self.parameters = parameters
        self.attributes = attributes
        self.submitted = submitted
        self.plan = plan
        self.costs = costs
        self.budget = budget

        # Test id in pattern
        pattern = r"^[A-Za-z0-9_\-\.~]+$"
        x = re.search(pattern, id)
        if not x:
            es = ErrorSchema(id=str(datetime.now()), code=400,
                             message="The id MUST match the following pattern: %s" % pattern)
            return make_response(es.to_json(), 400)
        self.id = id
