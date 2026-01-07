import requests

with open("request.json", "r") as f:
    data = f.read()

response = requests.post(
    "http://localhost:8000/v1/budget/optimize",
    headers={"Content-Type": "application/json"},
    data=data
)
print(response.text)
