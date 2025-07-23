import requests

url = "http://89.169.145.2:9090/api/generate"

prompt = """
Read the article and extract key topics, hypotheses, and core ideas: \n\n
Title: The Impact of Sleep on Cognitive Function in Adults
This study investigates the relationship between sleep duration and cognitive performance among adults aged 25 to 50. A sample of 300 participants was divided into three groups based on self-reported average sleep duration: short (<6 hours), normal (7–8 hours), and long (>9 hours). Cognitive tests covering memory, attention, and problem-solving were administered.
"""

# prompt = "how are you?"

payload = {
    "prompt":  prompt,  
    "system_prompt": "You are friendly ai assistant",
    "temperature": 0.7,
    "top_p": 0.9,
    "max_tokens": 256
}

headers = {
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.status_code)
print(response.json())