from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from urllib.parse import urlparse, parse_qs
import cgi

with open(r'C:\Users\User\Desktop\otsimo\DATASET.json', 'r') as f:
        data = json.load(f)
class RequestHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status_code=200, content_type='application/json'):
        self.send_response(status_code)
        self.send_header('Content-type', content_type)
        self.end_headers()

    def do_GET(self):
        query_params = parse_qs(urlparse(self.path).query)
        if self.path.startswith('/listMeals'):
            meals = data.get('meals', [])
            sort_by = query_params.get('sort', [None])[0]
            is_vegetarian = query_params.get('is_vegetarian', ['true'])[0] == 'false'
            is_vegan = query_params.get('is_vegan', ['true'])[0] == 'false'
            if is_vegetarian:
                meals = [meal for meal in meals if all(any('vegetarian' in option['groups'] or 'vegan' in option['groups'] for option in ingredient['options']) for ingredient in meal['ingredients'])]            
            elif is_vegan:
                meals = [meal for meal in meals if all(any('vegan' in option['groups'] for option in ingredient['options']) for ingredient in meal['ingredients'])]            
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

    def do_POST(self):
        if self.path == '/quality':
            content_type, _ = cgi.parse_header(self.headers.get('content-type'))
            if content_type == 'application/x-www-form-urlencoded':
                length = int(self.headers.get('content-length'))
                post_vars = parse_qs(self.rfile.read(length), keep_blank_values=1)
                meal_id = post_vars.get(b'meal_id', [None])[0]
                if meal_id:
                    meal_id = int(meal_id)
                    meal = next((meal for meal in data.get('meals', []) if meal['id'] == meal_id), None)
                    if meal:
                        quality_scores = {"low": 10, "medium": 20, "high": 30}
                        ingredient_qualities = {key.decode(): value[0].decode() for key, value in post_vars.items() if key != b'meal_id'}
                        meal_quality = self.calculate_meal_quality(meal, ingredient_qualities, quality_scores)
                        if meal_quality is None:
                            return
                        self._set_headers()
                        self.wfile.write(json.dumps({"quality": meal_quality}).encode())
                        return
                    else:
                        self._set_headers(404)
                        self.wfile.write(json.dumps({"error": "Meal not found"}).encode())
                        return
                else:
                    self._set_headers(400)
                    self.wfile.write(json.dumps({"error": "Meal ID is required"}).encode())
                    return
            else:
                self._set_headers(415)
                self.wfile.write(json.dumps({"error": "Unsupported Media Type"}).encode())

    def calculate_meal_quality(self, meal, ingredient_qualities, quality_scores):
        total_score = 0
        num_ingredients = 0
        errors = []
        for ingredient in meal.get('ingredients', []):
            ingredient_name = ingredient['name']
            quality = ingredient_qualities.get(ingredient_name)
            if quality is None:
                errors.append(f"Ingredient name '{ingredient_name}' is incorrect or missing in the quality data")
            else:
                total_score += quality_scores.get(quality, 0)
                num_ingredients += 1
        if errors:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": errors}).encode())
            return None
        return total_score / num_ingredients if num_ingredients > 0 else 0

def run(server_class=HTTPServer, handler_class=RequestHandler, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting httpd on port {port}...')
    httpd.serve_forever()

if __name__ == "__main__": 
    run()
