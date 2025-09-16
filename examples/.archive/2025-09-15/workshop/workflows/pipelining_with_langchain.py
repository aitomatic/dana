"""
LangChain-based Daytrip Itinerary Generator (Chained: itinerary then cost estimation)
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

import dana

load_dotenv(dotenv_path=Path(dana.__path__[0]).parent / ".env", verbose=True, override=True, encoding="utf-8")


@dataclass
class ItineraryItemNoCost:
    time: str
    activity: str
    location: str
    description: str


@dataclass
class ItineraryItem:
    time: str
    activity: str
    location: str
    description: str
    estimated_cost: float


@dataclass
class DaytripItinerary:
    location: str
    weather_condition: str
    total_estimated_cost: float
    itinerary_items: list[ItineraryItem]
    recommendations: list[str]
    weather_considerations: list[str]


class ItineraryNoCostResponse(BaseModel):
    location: str = Field(description="The destination location")
    weather_condition: str = Field(description="The weather condition")
    itinerary_items: list[dict[str, Any]] = Field(description="List of itinerary items (no cost)")
    recommendations: list[str] = Field(description="General recommendations")
    weather_considerations: list[str] = Field(description="Weather-specific considerations")


class ItineraryWithCostResponse(BaseModel):
    location: str = Field(description="The destination location")
    weather_condition: str = Field(description="The weather condition")
    total_estimated_cost: float = Field(description="Total estimated cost in USD")
    itinerary_items: list[dict[str, Any]] = Field(
        description="List of itinerary items with time, activity, location, description, and estimated_cost fields"
    )
    recommendations: list[str] = Field(description="General recommendations")
    weather_considerations: list[str] = Field(description="Weather-specific considerations")


def generate_daytrip_itinerary(location: str, weather_condition: str) -> DaytripItinerary:
    """
    Step 1: Generate itinerary (no costs), Step 2: Estimate costs for each activity.
    """
    if not location or not weather_condition:
        raise ValueError("Location and weather condition are required")

    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)

    # Step 1: Generate itinerary without costs
    parser1 = PydanticOutputParser(pydantic_object=ItineraryNoCostResponse)
    prompt1 = PromptTemplate(
        input_variables=["location", "weather_condition"],
        partial_variables={"format_instructions": parser1.get_format_instructions()},
        template="""
        Create a detailed daytrip itinerary for {location} considering weather: {weather_condition}.
        Requirements:
        - Include 6-8 activities with realistic timing (morning to evening)
        - Each itinerary item must have: time, activity, location, description (NO cost)
        - Consider weather-appropriate activities (indoor vs outdoor)
        - Include popular attractions and local recommendations
        - Account for weather conditions in planning
        {format_instructions}
        Make sure each itinerary item follows this exact structure:
        {{
            "time": "9:00 AM",
            "activity": "Activity name",
            "location": "Specific location",
            "description": "Brief description"
        }}
        """,
    )
    chain1 = prompt1 | llm | parser1
    response1 = chain1.invoke({"location": location, "weather_condition": weather_condition})

    # Step 2: Estimate costs for each activity
    parser2 = PydanticOutputParser(pydantic_object=ItineraryWithCostResponse)
    prompt2 = PromptTemplate(
        input_variables=["location", "weather_condition", "itinerary_items", "recommendations", "weather_considerations"],
        partial_variables={"format_instructions": parser2.get_format_instructions()},
        template="""
        Given the following daytrip itinerary for {location} with weather: {weather_condition}, estimate a realistic cost in USD for each activity. Add an 'estimated_cost' field to each item. Also, provide the total estimated cost for the day.

        ITINERARY:
        {itinerary_items}

        RECOMMENDATIONS:
        {recommendations}

        WEATHER CONSIDERATIONS:
        {weather_considerations}

        {format_instructions}

        Each itinerary item must have: time, activity, location, description, estimated_cost
        """,
    )
    chain2 = prompt2 | llm | parser2
    response2 = chain2.invoke(
        {
            "location": response1.location,
            "weather_condition": response1.weather_condition,
            "itinerary_items": response1.itinerary_items,
            "recommendations": response1.recommendations,
            "weather_considerations": response1.weather_considerations,
        }
    )

    itinerary_items = []
    for item in response2.itinerary_items:
        itinerary_items.append(
            ItineraryItem(
                time=item["time"],
                activity=item["activity"],
                location=item["location"],
                description=item["description"],
                estimated_cost=float(item["estimated_cost"]),
            )
        )

    return DaytripItinerary(
        location=response2.location,
        weather_condition=response2.weather_condition,
        total_estimated_cost=response2.total_estimated_cost,
        itinerary_items=itinerary_items,
        recommendations=response2.recommendations,
        weather_considerations=response2.weather_considerations,
    )


def format_itinerary_output(itinerary: DaytripItinerary) -> str:
    """Format the itinerary for display."""
    output = []
    output.append(f"🌍 Daytrip Itinerary for {itinerary.location}")
    output.append(f"🌤️  Weather: {itinerary.weather_condition}")
    output.append(f"💰 Total Cost: ${itinerary.total_estimated_cost:.2f}")
    output.append("")

    output.append("📅 ITINERARY:")
    for i, item in enumerate(itinerary.itinerary_items, 1):
        output.append(f"{i}. {item.time} - {item.activity}")
        output.append(f"   📍 {item.location}")
        output.append(f"   💬 {item.description}")
        output.append(f"   💵 ${item.estimated_cost:.2f}")
        output.append("")

    if itinerary.recommendations:
        output.append("💡 RECOMMENDATIONS:")
        for rec in itinerary.recommendations:
            output.append(f"   • {rec}")
        output.append("")

    if itinerary.weather_considerations:
        output.append("🌦️  WEATHER CONSIDERATIONS:")
        for consideration in itinerary.weather_considerations:
            output.append(f"   • {consideration}")

    return "\n".join(output)


if __name__ == "__main__":
    itinerary = generate_daytrip_itinerary(location="Tokyo", weather_condition="sunny")
    print(format_itinerary_output(itinerary))
