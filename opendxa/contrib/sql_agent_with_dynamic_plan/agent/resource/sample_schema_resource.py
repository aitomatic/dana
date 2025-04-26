"""
Dummy RAG Resource

This is a dummy RAG resource that returns a static schema of existing tables.
"""

# from opendxa.contrib.sql_agent_with_dynamic_plan.base.resource import BaseResource

from pydantic import BaseModel, Field
from opendxa.base.resource import BaseResource
from opendxa.common.mixins import ToolCallable
from opendxa.common.types import BaseResponse
from typing import Dict, Any

# flake8: noqa: E501
table_schemas = """
### product_combo_input.prod_combo_churn_food_user_in_transport_pool_by_nb_transactions
dataset_id : product_combo_input  
table_id : prod_combo_churn_food_user_in_transport_pool_by_nb_transactions  
schema : 
    - month : DATE - Represents the month for which the data is recorded.  
    - nb_food_trip : INTEGER - Indicates the number of food trips made by users in the specified month.  
    - rider_id : INTEGER - Unique identifier for the rider associated with the food trips.  
description : This table contains data related to food trips made by riders, organized by month and rider ID.  
usage : The table can be used to analyze user behavior in terms of food delivery trips, track trends over time, and assess rider activity within a transport pool context.

### product_combo_input.prod_combo_food_usage_in_transport_pool
dataset_id : product_combo_input  
table_id : prod_combo_food_usage_in_transport_pool  
schema : 
    - month : DATE - Represents the month of the recorded data, indicating the time period for the food usage.  
    - tag : STRING - A categorical label or identifier that may represent a specific type of food or usage category.  
    - rider_id : INTEGER - A unique identifier for the rider, which may be used to track individual usage patterns or behaviors.  
description : This table contains records of food usage in transport, categorized by month, type of food (tag), and associated rider identifiers.  
usage : The table is likely used for analyzing food consumption patterns over time, understanding rider behaviors, and optimizing food delivery logistics in a transport context.

### product_combo_input.prod_combo_no_food_user_in_transport_pool_by_active_level
dataset_id : product_combo_input  
table_id : prod_combo_no_food_user_in_transport_pool_by_active_level  
schema : 
    - month : DATE - Represents the month associated with the data entry.  
    - new_tag : STRING - A tag that categorizes or labels the data entry.  
    - rider_id : INTEGER - A unique identifier for the rider associated with the data entry.  
description : This table contains data related to riders and their associated tags for specific months, focusing on users who are not involved in food transport activities.  
usage : This table can be used for analyzing rider activity levels, categorizing riders based on tags, and understanding trends over time in relation to non-food transport activities.

### product_combo_input.prod_combo_ticketing_users_by_transport_active_level
dataset_id : product_combo_input  
table_id : prod_combo_ticketing_users_by_transport_active_level  
schema : 
    - month : DATE - Represents the month for which the data is recorded.  
    - service : STRING - Indicates the type of transport service (e.g., bus, train, etc.).  
    - time_diff_coal : INTEGER - Represents the time difference in coal transport (specific context may be needed for clarity).  
    - nb_user_buy_tix : INTEGER - The number of users who purchased tickets for the transport service.  
    - nb_user_eyeball_transport : INTEGER - The number of users who viewed or engaged with the transport service offerings.  
    - nb_user_book_transport : INTEGER - The number of users who booked transport services.  
description : This table contains data related to user interactions with transport services, including ticket purchases and bookings, segmented by month and service type.  
usage : This table can be used for analyzing user behavior and trends in transport service usage, helping to inform marketing strategies, service improvements, and operational decisions.

### shared_data.tb_all_DGs_trans
dataset_id : shared_data  
table_id : tb_all_DGs_trans  
schema : 
    - date : DATE - Represents the date of the transactions.  
    - user_id : INTEGER - Unique identifier for the user involved in the transaction.  
    - service_name : STRING - Name of the service associated with the transaction.  
    - city_id : INTEGER - Unique identifier for the city where the transaction took place.  
    - city_name : STRING - Name of the city where the transaction occurred.  
    - no_transactions : INTEGER - Total number of transactions made by the user on that date.  
    - total_spend_by_rider : FLOAT - Total amount spent by the rider on that date.  
    - total_promo_by_be : FLOAT - Total amount of promotions applied to the rider's transactions on that date.  
description : This table contains transaction data for users, detailing their spending and promotional usage across different services and cities on specific dates.  
usage : The table can be used for analyzing user behavior, transaction trends, and the effectiveness of promotions in various cities and services. It is useful for business intelligence, reporting, and decision-making processes related to user engagement and financial performance.

### shared_data.tb_all_rh_trans
dataset_id : shared_data  
table_id : tb_all_rh_trans  
schema : 
- date : DATE - The date of the transaction.
- user_id : INTEGER - Unique identifier for the user involved in the transaction.
- eyeball_id : INTEGER - Unique identifier for the eyeball (possibly a session or request identifier).
- is_request : BOOLEAN - Indicates if the record is a request.
- is_driver_found : BOOLEAN - Indicates if a driver was found for the request.
- is_trip : BOOLEAN - Indicates if the record represents a trip.
- service_id : INTEGER - Unique identifier for the service provided.
- service_name : STRING - Name of the service provided.
- city_id : INTEGER - Unique identifier for the city where the transaction took place.
- city_name : STRING - Name of the city where the transaction took place.
- user_persona : STRING - Describes the persona of the user (e.g., passenger, driver).
- payment_method : STRING - Method of payment used for the transaction.
- trip_distance : FLOAT - Distance of the trip in appropriate units (e.g., kilometers or miles).
- trip_duration : INTEGER - Duration of the trip in seconds.
- eta_time : FLOAT - Estimated time of arrival in appropriate units.
- ata_time : FLOAT - Actual time of arrival in appropriate units.
- discount_amount : FLOAT - Amount of discount applied to the transaction.
- paid_amount : FLOAT - Total amount paid for the transaction.
- accept_time : TIMESTAMP - Timestamp when the request was accepted.
- pickup_time : TIMESTAMP - Timestamp when the user was picked up.
- drop_time : TIMESTAMP - Timestamp when the user was dropped off.
- request_longitude : FLOAT - Longitude of the request location.
- request_latitude : FLOAT - Latitude of the request location.
- pickup_longitude : FLOAT - Longitude of the pickup location.
- pickup_latitude : FLOAT - Latitude of the pickup location.
- drop_longitude : FLOAT - Longitude of the drop-off location.
- drop_latitude : FLOAT - Latitude of the drop-off location.
- is_cancelled_by_user : BOOLEAN - Indicates if the transaction was cancelled by the user.
- cancellation_reasons : STRING - Reasons provided for the cancellation, if applicable.
- eyeball_created_at : DATETIME - Timestamp when the eyeball (session/request) was created.
- request_created_at : TIMESTAMP - Timestamp when the request was created.
description : This table contains transaction records related to ride-hailing services, capturing details about user requests, trips, and associated metadata.  
usage : The table is used for analyzing ride-hailing transactions, user behavior, service performance, and operational metrics, enabling insights into demand, trip efficiency, and user satisfaction.
"""


class SampleSchemaResource(BaseResource):
    """Dummy RAG Resource."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    class QueryRequest(BaseModel):
        """xxx Request for querying the sample schema resource."""
        table_name: str = Field(description="The name of the table to be queried.")

    @ToolCallable.tool
    async def query(self, request: QueryRequest) -> BaseResponse:
        """Query the sample schema resource.
        
        Args:
            request: A dictionary containing the request parameters.
                - table_name: A string containing the name of the table to be queried.

        Returns:
            A BaseResponse object containing the success status and content.
        """
        return BaseResponse(success=True, content=table_schemas)

    async def bad_query(self, text: str) -> str:
        """Retrieve Schema of Existing Tables.

        Args:
            text: Any text for similarity search with RAG

        Returns:
            str : Schema of Existing Tables in text format
        """
        return table_schemas
