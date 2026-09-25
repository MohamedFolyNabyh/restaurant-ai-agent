from pydantic import BaseModel, Field


class SearchRestaurantsInput(BaseModel):
    city: str = Field(
        description="The city where the user wants to find restaurants."
    )


class SearchRestaurantsByCuisineInput(BaseModel):

    city: str = Field(
        description="The city where the user wants to find restaurants."
    )

    cuisine: str = Field(
        description=(
            "The cuisine type, such as Italian, Egyptian, "
            "American, seafood, or pizza."
        )
    )



class GetRestaurantDetailsInput(BaseModel):

    restaurant_name: str = Field(
        description="The name of the restaurant."
    )

    city: str = Field(
        description="The city where the restaurant is located."
    )