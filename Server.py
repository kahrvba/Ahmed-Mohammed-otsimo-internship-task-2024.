from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from urllib.parse import urlparse, parse_qs
import cgi

# Load meal data from a JSON file on disk
with open(r'C:\Users\User\Desktop\otsimo\DATASET.json', 'r') as f:
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
            meals = data.get('meals', [])
            sort_by = query_params.get('sort', [None])[0]
            is_vegetarian = query_params.get('is_vegetarian', ['true'])[0] == 'false'
            is_vegan = query_params.get('is_vegan', ['true'])[0] == 'false'
            if is_vegetarian:
                 meals = [meal for meal in meals if all(('vegetarian' in option['groups']) for ingredient in meal['ingredients'] if 'options' in ingredient for option in ingredient['options'] if option)]           
            if is_vegan:
                meals = [meal for meal in meals if all(all('vegan' in option['groups'] for option in ingredient['options']) for ingredient in meal['ingredients'] if 'options' in ingredient and ingredient['options'])]            
            if sort_by == 'name':
                meals.sort(key=lambda x: x['name'])
            self._set_headers()
            self.wfile.write(json.dumps(meals).encode())
        elif self.path.startswith('/getMeal'):
            meal_id = query_params.get('id', [None])[0]
            if meal_id:
                meal_id = int(meal_id)
                meals = data.get('meals', [])
                meal = next((meal for meal in meals if meal['id'] == meal_id), None)
                if meal:
                    self._set_headers()
                    self.wfile.write(json.dumps(meal).encode())
                    return
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Meal not found"}).encode())
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode())

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
            return None
    # Handle POST requests to modify or interact with meal dat
    def do_POST(self):
        content_type, _ = cgi.parse_header(self.headers.get('content-type'))
        if content_type != 'application/x-www-form-urlencoded':
            self._set_headers(415)
            self.wfile.write(json.dumps({"error": "Unsupported Media Type"}).encode())
            return

        length = int(self.headers.get('content-length'))
        post_vars = parse_qs(self.rfile.read(length), keep_blank_values=1)
        meal_id = self.parse_meal_id(post_vars)
        if meal_id is None:
            return

        if self.path == '/quality':
            self.handle_quality(post_vars, meal_id)
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

        ingredient_qualities = {key.decode(): value[0].decode() for key, value in post_vars.items() if key != b'meal_id'}
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

        price = 0
        ingredient_qualities = {key.decode(): post_vars.get(key, [self.DEFAULT_QUALITY.encode()])[0].decode() for key in post_vars if key != b'meal_id'}
        for ingredient in meal.get('ingredients', []):
            ingredient_name = ingredient['name']
            print(f"Processing ingredient: {ingredient_name}, Data: {ingredient}")
            if 'options' not in ingredient:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": f"Missing 'options' for {ingredient_name}"}).encode())
                return
            quality = ingredient_qualities.get(ingredient_name, self.DEFAULT_QUALITY)
            quality_price = next((option['price'] for option in ingredient['options'] if option['quality'] == quality), None)
            if quality_price is None:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": f"No price found for the specified quality '{quality}' of {ingredient_name}"}).encode())
                return
            
            if quality not in self.QUALITY_COSTS:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": f"Invalid quality value for {ingredient_name}"}).encode())
                return
            price += quality_price

        self._set_headers()
        self.wfile.write(json.dumps({"price": price}).encode())
    # Calculate the overall quality score of a meal based on individual ingredient qualities
    def calculate_meal_quality(self, meal, ingredient_qualities):
        # Calculate the overall quality score of a meal based on individual ingredient qualities
        total_score = 0
        num_ingredients = 0
        errors = []
        for ingredient in meal.get('ingredients', []):
            ingredient_name = ingredient['name']
            quality = ingredient_qualities.get(ingredient_name)
            if quality is None:
                errors.append(f"Ingredient name '{ingredient_name}' is incorrect or missing in the quality data")
            else:
                total_score += self.QUALITY_SCORES.get(quality, 0)
                num_ingredients += 1
        if errors:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": errors}).encode())
            return None
        return total_score / num_ingredients if num_ingredients > 0 else 0 
# Configure and start the HTTP server
def run(server_class=HTTPServer, handler_class=RequestHandler, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting httpd on port {port}...')
    httpd.serve_forever()

if __name__ == "__main__": 
    run()
