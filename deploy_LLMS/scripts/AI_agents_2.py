import asyncio
import httpx
from typing import Optional, List
from langchain.llms.base import LLM
from pydantic import Field
from crewai import Agent, Task, Crew


class AsyncMistralLLM(LLM):
    endpoint: str = Field(default="http://89.169.145.2:9090", exclude=True)

    @property
    def _llm_type(self) -> str:
        return "mistral-async-api"

    async def _acall(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.endpoint}/api/generate",
                json={"prompt": prompt, "temperature": 0.7}
            )
            response.raise_for_status()
            return response.json()["output"]

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                nest_asyncio.apply()
                return loop.run_until_complete(self._acall(prompt, stop=stop))
            else:
                return loop.run_until_complete(self._acall(prompt, stop=stop))
        except RuntimeError:
            return asyncio.run(self._acall(prompt, stop=stop))
        


llm = AsyncMistralLLM(endpoint="http://158.160.51.184:9090")

article_text = """
Title: The Impact of Sleep on Cognitive Function in Adults

This study investigates the relationship between sleep duration and cognitive performance among adults aged 25 to 50. A sample of 300 participants was divided into three groups based on self-reported average sleep duration: short (<6 hours), normal (7–8 hours), and long (>9 hours). Cognitive tests covering memory, attention, and problem-solving were administered.

Results showed that participants in the normal sleep group consistently outperformed those in the short and long sleep groups across all tests. Short sleep was associated with reduced attention span and memory recall, while long sleep was correlated with slower problem-solving times.

The findings support the hypothesis that 7–8 hours of sleep is optimal for cognitive functioning in adults. Further research is required to understand the mechanisms behind the cognitive decline associated with long sleep duration.
"""

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



async def main():
    result = await crew.kickoff()
    print("\n================= Final Peer Review =================\n")
    print(result)

if __name__ == "__main__":
    import nest_asyncio
    import asyncio
    nest_asyncio.apply()  # важно: позволяет перезапустить event loop
    asyncio.run(main())

