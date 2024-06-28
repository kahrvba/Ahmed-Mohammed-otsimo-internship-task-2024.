from http.server import BaseHTTPRequestHandler, HTTPServer #Import necessary modules for HTTP server
import json  # Module to work with JSON data
from urllib.parse import urlparse, parse_qs
import cgi # Module to handle CGI (Common Gateway Interface)
import random # Module to generate random numbers

# Load meal data from a JSON file on disk
with open(r'C:\Users\User\OneDrive\Desktop\otsimo\DATASET.json', 'r') as f:
        data = json.load(f)
        
class RequestHandler(BaseHTTPRequestHandler):
    # Define quality scores for different levels
    QUALITY_SCORES = {"low": 30, "medium": 40, "high": 50}
    # Define additional costs based on quality
    QUALITY_COSTS = {"high": 0, "medium": 0.05, "low": 0.10}
    # Default quality level for ingredients if not specified
    DEFAULT_QUALITY = "high"
    # Helper method to set HTTP headers and status code
    
    def _set_headers(self, status_code=200, content_type='application/json'):
        # Send HTTP status code and header content type
        self.send_response(status_code)
        self.send_header('Content-type', content_type)
        self.end_headers()
        
    # Handle GET requests to the server
    def do_GET(self):
        # Parse query parameters from the URL
        query_params = parse_qs(urlparse(self.path).query)
        # Handle requests to list meals with optional sorting and filtering
        if self.path.startswith('/listMeals'):
            meals = data.get('meals', []) # getting all the meals and list it 
            sort_by = query_params.get('sort', [None])[0] #sort parameter by name 
            # Option for filter based on dietary 
            global_ingredients = data.get('ingredients', [])
            is_vegetarian = query_params.get('is_vegetarian', ['false'])[0] == 'true'
            is_vegan = query_params.get('is_vegan', ['false'])[0] == 'true'
            # is_vegetarian for meals that have vegetairain or vegetarian and vegan ingrediants 
            if is_vegetarian:
                  meals = [
                    meal for meal in meals
                    if all(
                        any(
                            ('vegetarian' in global_ingredient.get('groups', []) or 'vegan' in global_ingredient.get('groups', []))
                            for global_ingredient in global_ingredients
                            if global_ingredient['name'] == ingredient['name']
                            )
                        for ingredient in meal['ingredients']
                        )
                    ]

            if is_vegan:
              meals = [
                meal for meal in meals
                if all(
                        any(
                            'vegan' in global_ingredient.get('groups', [])
                            for global_ingredient in global_ingredients
                            if global_ingredient['name'] == ingredient['name']
                        )
                        for ingredient in meal['ingredients']
                    )
                ]              
            #quary : http://localhost:8080/listMeals?sort=name
            # Sort meals by name if specified
            if sort_by == 'name':
                meals.sort(key=lambda x: x['name'])
            self._set_headers()
            self.wfile.write(json.dumps(meals).encode())
         # Endpoint to get detailed information about a specific meal   
        elif self.path.startswith('/getMeal'):
                meal_id = query_params.get('id', [None])[0] # getting required meal_id
                if meal_id:
                    meal_id = int(meal_id)
                    meals = data.get('meals', [])
                    meal = next((meal for meal in meals if meal['id'] == meal_id), None)
                
                    if meal:
                    # Retrieve full ingredient details from the global ingredients list
                        full_ingredients_info = [] # list to store all ingrediant infomations 
                        ingredients = data.get('ingredients', [])
                        for ingredient in meal['ingredients']:
                            ingredient_detail = next((item for item in ingredients if item['name'] == ingredient['name']), None) # itreate over each meal ingrediant
                            if ingredient_detail:
                            #response with all ingrediant info
                                full_ingredients_info.append({
                                "name": ingredient_detail['name'],
                                "groups": ingredient_detail.get('groups', []),
                                "options": ingredient_detail.get('options', [])
                            })
                        else:
                            full_ingredients_info.append({"name": ingredient['name'], "error": "Details not found"}) #return error if no information found
            
                        meal_details = {
                        "id": meal['id'],
                        "name": meal['name'],
                        "ingredients": full_ingredients_info
                        }
                        self._set_headers()
                        self.wfile.write(json.dumps(meal_details).encode())
                        return
                    else:
                        self._set_headers(404)
                        self.wfile.write(json.dumps({"error": "Please choose a Meal to get details."}).encode())
                else:
                    self._set_headers(404)
                    self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode())
        elif self.path.startswith('/search'):
                search_query = query_params.get('query', [None])[0]
                if search_query:
                    search_query = search_query.lower()
                    meals = data.get('meals', [])
                    filtered_meals = [meal for meal in meals if search_query in meal['name'].lower()]
                    self._set_headers()
                    self.wfile.write(json.dumps(filtered_meals).encode())
                else:
                    self._set_headers(400)
                    self.wfile.write(json.dumps({"error": "Search query is required"}).encode())
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode())
    # parse_meal_id funtion to get the meal_id input from client
    def parse_meal_id(self, post_vars):
        meal_id = post_vars.get(b'meal_id', [None])[0]
        if meal_id:
            try:
                return int(meal_id)
            except ValueError:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "Invalid meal ID"}).encode())
                return None
        else:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "Meal ID is required"}).encode())
            print(f"this is the budget")
            return None   
    def parse_budget(self, post_vars):
        budget_entry = post_vars.get(b'budget', [None])[0]
        if budget_entry is None:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "Budget parameter is missing"}).encode())
            print(f"parse_budge")
            return None
        try:
            budget = float(post_vars.get(b'budget', [None])[0].decode())
            return budget
        except (TypeError, ValueError):
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "Invalid or missing budget"}).encode())
            return None  
    def calculate_lowest_price(self, meal):
            price = 0
            global_ingredients = data.get('ingredients', [])
            for ingredient in meal['ingredients']:
                ingredient_name = ingredient['name']
                global_ingredient = next((item for item in global_ingredients if item['name'] == ingredient_name), None)
                if global_ingredient and 'options' in global_ingredient:
                    lowest_price = min(option['price'] for option in global_ingredient['options'])
                    price += lowest_price
            return price
    def handle_random(self, post_vars):
    # Parse budget if provided
        try:
            budget = float(post_vars.get(b'budget', [float('inf')])[0].decode())
        except ValueError:
            budget = float('inf')
    # Calculate price for each meal and sort by closeness to the budgetmeal_price_diffs = []
        meal_price_diffs = []
        for meal in data.get('meals', []):
            price = self.calculate_lowest_price(meal)
            price_diff = abs(price - budget)
            meal_price_diffs.append((meal, price, price_diff))
        
        meal_price_diffs.sort(key=lambda x: x[2])
        
        # Check if there are any meals
        if not meal_price_diffs:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "No meals available"}).encode())
            return
        
        # Select the meal with the smallest difference to the budget
        selected_meal, selected_meal_price, _ = meal_price_diffs[0]
        
        # Apply random quality to the selected meal
        meal_price, quality_score = self.apply_random_quality(selected_meal, budget)
        

    # Prepare response
        
        response = {
            "id": selected_meal['id'],
            "name": selected_meal['name'],
            "price": meal_price,
            "quality_score": quality_score,
            "ingredients":selected_meal['ingredients']
            }
        self._set_headers()
        self.wfile.write(json.dumps(response).encode())
        # Handle POST requests to modify or interact with meal data
    def do_POST(self): # Method to handle POST requests
        # POST Header
        content_type, _ = cgi.parse_header(self.headers.get('content-type'))
        #post content type
        if content_type != 'application/x-www-form-urlencoded':
            self._set_headers(415)
            self.wfile.write(json.dumps({"error": "Unsupported Media Type"}).encode())
            return
        length = int(self.headers.get('content-length'))
        post_vars = parse_qs(self.rfile.read(length), keep_blank_values=1)
        if self.path == '/findHighest':
            # To separate post_varse to handle budget and meal id independently
            budget = self.parse_budget(post_vars)
            if budget is None:
                return
            self.handle_find_highest(post_vars)
        elif self.path == '/findHighestOfMeal':
            meal_id = self.parse_meal_id(post_vars)
            if meal_id is None:
                return
            budget = self.parse_budget(post_vars)
            if budget is None:
                    return
            self.handle_find_highest_of_meal(meal_id, budget)
        elif self.path == '/random':
            # To separate post_varse to handle budget and meal id independently
            budget = self.parse_budget(post_vars)
            if budget is None:
                return
            self.handle_random(post_vars)
        else:
            meal_id = self.parse_meal_id(post_vars)
            if meal_id is None:
                return
        #http://localhost:8080/quality
            if self.path == '/quality':
                self.handle_quality(post_vars, meal_id)
        #http://localhost:8080/price
            elif self.path == '/price':
                self.handle_price(post_vars, meal_id)    
            else:
                self._set_headers(404)
                self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode())     
        
    # Handle quality update requests for a specific meal
    def handle_quality(self, post_vars, meal_id):
        # Update and respond with the quality score of a specific meal
        meal = next((meal for meal in data.get('meals', []) if meal['id'] == meal_id), None)
        if not meal:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Meal not found"}).encode())
            return
        ingredient_qualities = {key.decode(): value[0].decode() if value[0] else self.DEFAULT_QUALITY for key, value in post_vars.items() if key != b'meal_id'}
        meal_ingredient_names = [ingredient['name'] for ingredient in meal.get('ingredients', [])]
        # Check if all ingredient names in post_vars are in the meal's ingredients
        unmatched_ingredients = [name for name in ingredient_qualities if name not in meal_ingredient_names]
        if unmatched_ingredients:
            self._set_headers(400)
            self.wfile.write(json.dumps({
                    "error": f"Ingredient names required for meal_id: {meal_id} do not match: {', '.join(unmatched_ingredients)}",
                    "expected_ingredient_names": [ingredient['name'] for ingredient in meal.get('ingredients', [])]
                }).encode())
            return
        #take ingrediant qualitys and set 'high' for any non specified quality ingrediant
        for ingredient in meal.get('ingredients', []):
            if ingredient['name'] not in ingredient_qualities:
                ingredient_qualities[ingredient['name']] = self.DEFAULT_QUALITY
        
        meal_quality = self.calculate_meal_quality(meal, ingredient_qualities)
        if meal_quality is None:
            return
        self._set_headers()
        self.wfile.write(json.dumps({"quality": meal_quality}).encode())
    # Calculate and respond with the price of a meal based on ingredient qualities
    def handle_price(self, post_vars, meal_id):
        # Calculate and respond with the price of a meal based on ingredient qualities
        meal = next((meal for meal in data.get('meals', []) if meal['id'] == meal_id), None)
        if not meal:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Meal not found"}).encode())
            return
        # extract ingrediants quality and set default ='high' for any unprovided meal quality
        ingredient_qualities = {key.decode(): post_vars.get(key, [self.DEFAULT_QUALITY.encode()])[0].decode() for key in post_vars if key != b'meal_id'}
        # Validate if all provided ingredient names are in the meal's ingredients
        meal_ingredient_names = [ingredient['name'] for ingredient in meal.get('ingredients', [])]
        unmatched_ingredients = [name for name in ingredient_qualities if name not in meal_ingredient_names]
        #check if there mismatch in ingerdiants names 
        if unmatched_ingredients:
            self._set_headers(400)
            self.wfile.write(json.dumps({
            "error": f"Ingredient names provided do not match the meal ingredients: {', '.join(unmatched_ingredients)}",
            "expected_ingredient_names": meal_ingredient_names
        }).encode())
            return
        
        price = 0
        global_ingredients = data.get('ingredients', [])  #'ingredients' is the global list
        for ingredient in meal.get('ingredients', []):
            ingredient_name = ingredient['name']
            global_ingredient = next((item for item in global_ingredients if item['name'] == ingredient_name), None)
            if not global_ingredient or 'options' not in global_ingredient:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": f"Missing 'options' for {ingredient_name}"}).encode())
                return
            #calculate the price based on quality
            quality = ingredient_qualities.get(ingredient_name, self.DEFAULT_QUALITY)
            quality_price = next((option['price'] for option in global_ingredient['options'] if option['quality'] == quality), None)
            if quality_price is None:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": f"No price found for the specified quality '{quality}' of {ingredient_name}"}).encode())
                return
            
            if quality not in self.QUALITY_COSTS:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": f"Invalid quality value for {ingredient_name}"}).encode())
                return
            #additional_cost added if there downgrade in meal qualities
            additional_cost = self.QUALITY_COSTS[quality]
            price += quality_price + additional_cost

        self._set_headers()
        self.wfile.write(json.dumps({"price": price}).encode())
    # Calculate the overall quality score of a meal based on individual ingredient qualities over number of ingrediants 
    def calculate_meal_quality(self, meal, ingredient_qualities):
        # Calculate the overall quality score of a meal based on individual ingredient qualities
        total_score = 0
        num_ingredients = 0
        # continue to calculate quality even if there space in ingrediant quality value bar
        errors = []
        for ingredient in meal.get('ingredients', []):
            ingredient_name = ingredient['name']
            quality = ingredient_qualities.get(ingredient_name)
            if quality is None:
                errors.append(f"It's '{ingredient_name}' in dictionery.. ")
            else:
                total_score += self.QUALITY_SCORES.get(quality, 0)
                num_ingredients += 1
        if errors:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": errors}).encode())
            return None
        return total_score / num_ingredients if num_ingredients > 0 else 0 
    # handle_random return randomly selcected meal of a randomly quality parameters with option to set a budget
    
    
    def apply_random_quality(self, meal, budget):
        # Apply random quality levels to a meal while considering a budge
        meal_price = 0
        total_quality_score = 0
        global_ingredients = data.get('ingredients', [])
        for ingredient in meal['ingredients']:
            ingredient_name = ingredient['name']
            global_ingredient = next((item for item in global_ingredients if item['name'] == ingredient_name), None)
            if not global_ingredient or 'options' not in global_ingredient:
                self._set_headers(404)
                self.wfile.write(json.dumps({"error": "No meals available"}).encode())
                continue
            
            quality = random.choice(list(self.QUALITY_SCORES.keys()))
            quality_price = next((option['price'] for option in global_ingredient['options'] if option['quality'] == quality), None)
            if quality_price is None:
                continue
            meal_price += quality_price
            total_quality_score += self.QUALITY_SCORES[quality]
            average_quality_score = total_quality_score / len(meal['ingredients'])
        return meal_price, average_quality_score
    
      

    def apply_highest_quality_within_budget(self, meal, budget):
        meal_price = 0
        total_quality_score = 0
        global_ingredients = data.get('ingredients', [])

        for ingredient in meal['ingredients']:
            ingredient_name = ingredient['name']
            global_ingredient = next((item for item in global_ingredients if item['name'] == ingredient_name), None)
            if not global_ingredient or 'options' not in global_ingredient:
                self._set_headers(404)
                self.wfile.write(json.dumps({"error": f"Missing ingredient list or options for {ingredient_name}."}).encode())
                return None, None  # Return None to indicate failure

            sorted_options = sorted(global_ingredient['options'], key=lambda x: self.QUALITY_SCORES.get(x['quality'], 0), reverse=True)
            for option in sorted_options:
                if meal_price + option['price'] <= budget:
                    meal_price += option['price']
                    total_quality_score += self.QUALITY_SCORES[option['quality']]

        average_quality_score = total_quality_score / len(meal['ingredients']) if meal['ingredients'] else 0
        return meal_price, average_quality_score

    def find_highest_quality_meal(meals, global_ingredients, quality_scores):
        highest_quality_meal = None
        highest_total_quality_score = 0

        for meal in meals:
            total_quality_score = 0
            all_ingredients_found = True

        for ingredient in meal['ingredients']:
            ingredient_name = ingredient['name']
            global_ingredient = next((item for item in global_ingredients if item['name'] == ingredient_name), None)

            if not global_ingredient or 'options' not in global_ingredient:
                all_ingredients_found = False
                break

            highest_quality_option = max(global_ingredient['options'], key=lambda x: quality_scores.get(x['quality'], 0))
            total_quality_score += quality_scores.get(highest_quality_option['quality'], 0)

        if all_ingredients_found and (highest_quality_meal is None or total_quality_score > highest_total_quality_score):
            highest_quality_meal = meal
            highest_total_quality_score = total_quality_score

        return highest_quality_meal, highest_total_quality_score

    def handle_find_highest(self, post_vars):
        query_params = parse_qs(urlparse(self.path).query)
        budget = self.parse_budget(post_vars)
        if budget is None:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error":"Budget parameter is missing"}))
            return

        global_ingredients = data.get('ingredients', [])
        meals = data.get('meals', [])
        is_vegetarian = query_params.get('is_vegetarian', ['false'])[0] == 'true'
        is_vegan = query_params.get('is_vegan', ['false'])[0] == 'true'

        if is_vegetarian or is_vegan:
            meals = [
                meal for meal in meals
                if all(
                    any(
                        (is_vegetarian and 'vegetarian' in global_ingredient.get('groups', [])) or
                        (is_vegan and 'vegan' in global_ingredient.get('groups', []))
                        for global_ingredient in global_ingredients
                        if global_ingredient['name'] == ingredient['name']
                    )
                    for ingredient in meal['ingredients']
                )
    ]

        best_meal = None
        highest_quality_score = 0
        best_meal_price = 0
        for meal in meals:
            meal_price, quality_score = self.apply_highest_quality_within_budget(meal, budget)
            if meal_price is not None and meal_price <= budget and quality_score > highest_quality_score:
                highest_quality_score = quality_score
                best_meal = meal
                best_meal_price = meal_price

        if best_meal:
            response = {
            "id": best_meal['id'],
            "name": best_meal['name'],
            "price": best_meal_price,
            "quality_score": highest_quality_score,
            "ingredients": [
                {
                "name": ingredient['name'],
                "quality": random.choice(list(self.QUALITY_SCORES.keys()))  # Randomly assign a quality score
                }for ingredient in best_meal['ingredients']
            ]
        }
            self._set_headers()
            self.wfile.write(json.dumps(response).encode())
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "No suitable meal found within the budget"}).encode())

    def handle_find_highest_of_meal(self, meal_id, budget):
        meals = data.get('meals', [])
        meal = next((meal for meal in meals if meal['id'] == meal_id), None)
        if not meal:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Meal not found"}).encode())
            return

        meal_price, quality_score = self.apply_highest_quality_within_budget(meal, budget)
        if meal_price is None:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Cannot fit meal within budget"}).encode())
            return

        response = {
            "id": meal['id'],
            "name": meal['name'],
            "price": meal_price,
            "quality_score": quality_score,
            "ingredients": [
                {
                    "name": ingredient['name'],
                    "quality": list(self.QUALITY_SCORES.keys())[-3]  # Assuming the highest quality is the last key
                }for ingredient in meal['ingredients']
            ]
        }
        self._set_headers()
        self.wfile.write(json.dumps(response).encode())
# Configure and start the HTTP server
def run(server_class=HTTPServer, handler_class=RequestHandler, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting httpd on port {port}...')
    httpd.serve_forever()

if __name__ == "__main__": 
    run()
