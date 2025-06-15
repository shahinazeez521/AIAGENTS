
from crewai import Agent, Task, Crew, Process
from crewai_tools import SerperDevTool
from tools.gmail_tool import GmailTool
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

class EmailAutoResponderCrew:
    def __init__(self):
        self.agents = self._create_agents()
        self.tasks = self._create_tasks()
        self.crew = self._create_crew()

    def _create_agents(self):
        llm = ChatOpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"))
        gmail_tool = GmailTool()
        serper_tool = SerperDevTool()

        email_analyzer = Agent(
            role="Email Analyzer",
            goal="Identify relevant emails requiring out-of-office replies",
            backstory="Expert at filtering out newsletters, OTPs, and automated notifications.",
            llm=llm,
            tools=[gmail_tool, serper_tool],
            verbose=True,
            memory=True
        )

        email_responder = Agent(
            role="Email Responder",
            goal="Draft personalized out-of-office email replies",
            backstory="Skilled at crafting polite, personalized replies.",
            llm=llm,
            tools=[gmail_tool],
            verbose=True,
            memory=True
        )

        return {"email_analyzer": email_analyzer, "email_responder": email_responder}

    def _create_tasks(self):
        gmail_tool = GmailTool()

        analyze_emails_task = Task(
            description="Analyze unread emails to identify those requiring an out-of-office reply. Exclude newsletters, OTPs, and automated notifications. Return a JSON list of relevant emails.",
            expected_output="JSON list of emails with email_id, sender, subject.",
            agent=self.agents["email_analyzer"],
            tools=[gmail_tool]
            
        )

        draft_reply_task = Task(
            description="Draft an out-of-office reply for each relevant email using 'create_draft' action. Save as a draft in Gmail.",
            expected_output="Confirmation that drafts are saved.",
            agent=self.agents["email_responder"],
            tools=[gmail_tool],
            context=[analyze_emails_task]
        )

        return [analyze_emails_task, draft_reply_task]

    def _create_crew(self):
        return Crew(
            agents=list(self.agents.values()),
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            max_rpm=10,
            max_iter=25
        )

    def run(self, inputs=None):
        return self.crew.kickoff(inputs=inputs or {})