import requests
from typing import Optional, List


class MistralLLM:
    """
    класс для работы с апишкой к ллм
    """
    def __init__(self, endpoint: str):
        self.endpoint = endpoint

    def call(self, prompt: str) -> str:
        response = requests.post(
            f"{self.endpoint}/api/generate",
            json={"prompt": prompt, "temperature": 0.7},
            timeout=60
        )
        response.raise_for_status()
        return response.json()["output"]


class Agent:
    "вместо crewAi сделал простой пайплайн из агентов синхронный"
    def __init__(self, role: str, goal: str, backstory: str, llm: MistralLLM):
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.llm = llm

    def run(self, task_description: str) -> str:
        prompt = f"""You are a {self.role}.
Goal: {self.goal}
Background: {self.backstory}

Task: {task_description}

Your detailed response:"""
        print(f"\n--- Running agent: {self.role} ---")
        output = self.llm.call(prompt)
        print(output.strip())
        return output.strip()


# эндпоинт 
llm = MistralLLM(endpoint="http://89.169.145.2:9090")

topic_extractor = Agent(
    role="Topic Extractor",
    goal="Identify key topics, hypotheses, and directions in the article.",
    backstory="A researcher skilled at extracting essence from scientific texts.",
    llm=llm
)

weakness_finder = Agent(
    role="Weakness Finder",
    goal="Identify weaknesses in argumentation, methodological flaws, and gaps.",
    backstory="A sharp critic who detects vulnerabilities in academic works.",
    llm=llm
)

strength_finder = Agent(
    role="Strength Finder",
    goal="Identify the strong points of the paper: innovations, relevance, practical value.",
    backstory="An expert in evaluating originality and evidence quality.",
    llm=llm
)

contradiction_detector = Agent(
    role="Contradiction Detector",
    goal="Detect contradictions, inconsistencies, and logical fallacies.",
    backstory="An analyst focused on internal consistency.",
    llm=llm
)

reviewer = Agent(
    role="Reviewer",
    goal="Generate a final peer review summarizing all other agents' insights.",
    backstory="A journal reviewer tasked with producing a comprehensive evaluation.",
    llm=llm
)

# Сюда текст статьи, взял синтетику
article_text = """Title: The Impact of Sleep on Cognitive Function in Adults

This study investigates the relationship between sleep duration and cognitive performance among adults aged 25 to 50. A sample of 300 participants was divided into three groups based on self-reported average sleep duration: short (<6 hours), normal (7–8 hours), and long (>9 hours). Cognitive tests covering memory, attention, and problem-solving were administered.
"""

# пайплайн
topics = topic_extractor.run(f"Analyze this article and extract key topics, hypotheses, and core ideas:\n\n{article_text}")
weaknesses = weakness_finder.run(f"Based on the following topics, analyze weaknesses in the article:\n\n{topics}")
strengths = strength_finder.run(f"Based on the following topics, analyze strengths in the article:\n\n{topics}")
contradictions = contradiction_detector.run(f"Based on the following topics, identify any contradictions or inconsistencies:\n\n{topics}")

final_review = reviewer.run(
    f"""Summarize all the following insights into a final peer review:
Topics:
{topics}

Weaknesses:
{weaknesses}

Strengths:
{strengths}

Contradictions:
{contradictions}
"""
)


print("\n================= Final Peer Review =================\n")
print(final_review)
