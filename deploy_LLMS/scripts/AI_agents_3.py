import httpx
from typing import Optional, List
from langchain_core.language_models.llms import LLM
from pydantic import Field
from crewai import Agent, Task, Crew

# кастомный LLM для апишки 
class MyLLM(LLM):
    url: str = "http://89.169.145.2:9090/api/generate"

    @property
    def _llm_type(self) -> str:
        return "custom-mistral-api"

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        payload = {
            "prompt": prompt,
            "system_prompt": "You are friendly AI assistant",
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 256
        }
        headers = {"Content-Type": "application/json"}
        response = httpx.post(self.url, json=payload, headers=headers, timeout=30.0)
        response.raise_for_status()
        return response.json()["output"]


llm = MyLLM()

article_text = """
Title: The Impact of Sleep on Cognitive Function in Adults

This study investigates the relationship between sleep duration and cognitive performance among adults aged 25 to 50. A sample of 300 participants was divided into three groups based on self-reported average sleep duration: short (<6 hours), normal (7–8 hours), and long (>9 hours). Cognitive tests covering memory, attention, and problem-solving were administered.
"""

# блок агентов
topic_extractor = Agent(
    role="Topic Extractor",
    goal="Identify key topics, hypotheses, and directions in the article.",
    backstory="A researcher skilled at extracting essence from scientific texts.",
    llm=llm,
    verbose=True
)

weakness_finder = Agent(
    role="Weakness Finder",
    goal="Identify weaknesses in argumentation, methodological flaws, and gaps.",
    backstory="A sharp critic who detects vulnerabilities in academic works.",
    llm=llm,
    verbose=True
)

strength_finder = Agent(
    role="Strength Finder",
    goal="Identify the strong points of the paper: innovations, relevance, practical value.",
    backstory="An expert in evaluating originality and evidence quality.",
    llm=llm,
    verbose=True
)

contradiction_detector = Agent(
    role="Contradiction Detector",
    goal="Detect contradictions, inconsistencies, and logical fallacies.",
    backstory="An analyst focused on internal consistency.",
    llm=llm,
    verbose=True
)

reviewer = Agent(
    role="Reviewer",
    goal="Generate a final peer review summarizing all other agents' insights.",
    backstory="A journal reviewer tasked with producing a comprehensive evaluation.",
    llm=llm,
    verbose=True
)

# блок тасок
task_topics = Task(
    description=f"Read the article and extract key topics, hypotheses, and core ideas:\n\n{article_text}",
    agent=topic_extractor,
    expected_output="A list of key topics and hypotheses from the article."
)

task_weak = Task(
    description="Based on the extracted topics, analyze weaknesses in the article's reasoning.",
    agent=weakness_finder,
    depends_on=[task_topics],
    expected_output="A critical analysis of weaknesses and methodological issues."
)

task_strong = Task(
    description="Based on the extracted topics, identify the strengths of the article.",
    agent=strength_finder,
    depends_on=[task_topics],
    expected_output="A list or summary of the article’s strong points."
)

task_contra = Task(
    description="Based on the extracted topics, detect contradictions or inconsistencies.",
    agent=contradiction_detector,
    depends_on=[task_topics],
    expected_output="Identified contradictions, logical issues, or inconsistencies."
)

task_review = Task(
    description="Using all previous insights, write a complete academic peer review.",
    agent=reviewer,
    depends_on=[task_weak, task_strong, task_contra],
    expected_output="A comprehensive, well-written peer review of the article."
)

# Запуск команды подручных 
crew = Crew(
    agents=[
        topic_extractor,
        weakness_finder,
        strength_finder,
        contradiction_detector,
        reviewer
    ],
    tasks=[
        task_topics,
        task_weak,
        task_strong,
        task_contra,
        task_review
    ],
    verbose=True
)

if __name__ == "__main__":
    result = crew.kickoff()
    print("\n================= Final Peer Review =================\n")
    print(result)
