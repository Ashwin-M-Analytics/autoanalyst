# core/insight_generator.py

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model_name="llama-3.3-70b-versatile",
    temperature=0.3
)

INSIGHT_PROMPT = PromptTemplate(
    input_variables=["question", "sql", "result"],
    template="""
You are a business analyst. A user asked a data question and got the following result.
Write 2-3 sentences of clear, actionable business insight based on the result.
Be specific -- mention actual numbers from the result.
Do not repeat the question. Do not explain the SQL.

Question: {question}
SQL Used: {sql}
Result:
{result}

Insight:
"""
)


def generate_insight(question: str, sql: str, df) -> str:
    result_str = df.head(20).to_string(index=False)
    chain = INSIGHT_PROMPT | llm | StrOutputParser()
    insight = chain.invoke({
        "question": question,
        "sql": sql,
        "result": result_str,
    })
    return insight.strip()