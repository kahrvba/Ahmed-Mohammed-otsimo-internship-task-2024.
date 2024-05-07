# Transparent Restaurant Backend
 implement a REST API for a interacting with a menu of a restaurant. The menu is given to you as a JSON file which you will parse and perform operations on. The required features will be 
 listed below.

 # Description

**restaurant declares that differing quality of ingredients are used in their meals.**

it also allows the customers to choose the ingredients of each meal in different qualities. Each ingredient has the following quality levels:

``low``: the cheapest

``medium``: moderate

``high``: the most expensive

# Main Features and Requirements
Therefore, they require a system where customers can:

View a list of the menu with the following ``filtering`` and ``sorting``options:

``Sort by name``

``Filter`` by dietary preferences (such as ``vegetarian`` or ``vegan``)

``vegetarian meal`` is one that contains only ``vegetarian`` or ``vegan`` ingredients and a ``vegan`` meal is one that contains only ``vegan`` ingredients.

``Get details of a single meal``

``Price`` and ``quality-score`` calculation for a given set of quality parameters`
 
# HTTP API
implement only``5 endpoints`` for this task

``bonus``ones as well.

``The server should take a dataset as a JSON file and parse it before launch``

# 1/Listing the menu 

list the ``meals`` in the menu and their ``ingredients``.

    PATH: /listMeals
    METHOD: GET
    PARAMS:
    is_vegetarian: (boolean, optional) default=false
    is_vegan: (boolean, optional) default=false
    SAMPLE: http://localhost:8080/listMeals?is_vegetarian=true

**filter**:
``vegetarian`` or ``vegan``  

**Example JSON output:**

     curl http://localhost:8080/listMeals
    {
    "id": 1,
    "name": "Shrimp-fried Rice",
    "ingredients": [
      "shrimp",
      "rice"
    ]
    },


# 2/ getting the item from the menu :

Take the ``meal ID`` and returns its name and ingredients with ``each option of ingredients included``


    PATH: /getMeal
    METHOD: GET
    PARAMS:
    id: N (integer, required)
    SAMPLE: http://localhost:8080/getMeal?id=2

# 3/ Quality Calculation with the ingredient Qualities: 

Take a ``meal ID`` and ``ingredients quality`` 

selections and returns ``resulting quality score`` 

** IF an ingredients quality is not specified ``"high"`` quality should be assumed by default 


    PATH: /quality
    METHOD: POST
    PARAMS:
    meal_id: (integer, required)
    <ingredient-1>: (enum, values: ["high", "medium", "low"], optional) default="high"
    <ingredient-2>: (enum, values: ["high", "medium", "low"], optional) default="high"
    ...

# 4/ Price calculation with ingredient Qialities : 

take ``meal ID`` and ingredient quality and returns the ``resulting price``

# 5/ I'm feeling lucky 

return a ``randomly`` selected meal of a random ``quality`` parameterd with an option to set a ``budget``

# API ERRORS

in any case the API needs to return an ``error`` (e.g. when an ``invalid id`` is passed to /getMeal endpoint), it should ``do`` so by conforming to the ``HTTP standard`` and should return a ``JSON body`` that ``states the error properly`` 

# 6/ Seraching for a meal :

take a search text and returns the meals that contain the search text, 
``Search will be made in a case-insensitive manner``

# 7/ Finding the Highest quality meal for given budget : 

takes a ``budget`` as input and yields the highest -quality meal that be ``prepared`` for that budget and ``how much it cost`` 

    PATH: /findHighest
    METHOD: POST
    PARAMS:
    budget: (double, required)
    is_vegetarian: (boolean, optional) default=false
    is_vegan: (boolean, optional) default=fals

# Dataset: 

    You should not base your implementation on the exact data in this dataset as we will use a different one during evaluation, but the data structure will be the same.

# Quality and Price Calculation

Corresponting score for each quality level 


    The scores of each ingredient used in a meal are summed and divided to the number of ingredients to find the overall score of the meal

    This overall score represents the quality of the meal.
