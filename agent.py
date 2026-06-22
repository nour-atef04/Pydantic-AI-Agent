"""
Simple Pydantic Agent that answers questions based on docs
"""

import os
import re
from typing import Optional
from pydantic import BaseModel, Field
import requests


class QueryRequest(BaseModel):
    """Validated user query"""
    question: str = Field(..., min_length=1, max_length=500, description="User's question")
    

class AgentResponse(BaseModel):
    """Validated agent response"""
    answer: str = Field(..., description="Short answer from the agent")
    source: Optional[str] = Field(None, description="Source from docs")


class PydanticAgent:
    def __init__(self, api_key: str, model: str = "openai/gpt-oss-20b:free"):
        self.api_key = api_key
        self.model = model
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Load documentation
        self.docs = self._load_docs()
        
    def _load_docs(self) -> str:
        """Load docs.md file"""
        try:
            with open("docs.md", "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return "No documentation found"
    
    def _extract_relevant_context(self, question: str, max_chars: int = 2000) -> str:
        """Extract relevant context from docs based on question"""
        # Simple keyword matching
        keywords = question.lower().split()
        
        # Find relevant sections
        lines = self.docs.split('\n')
        relevant_lines = []
        
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in keywords if len(keyword) > 2):
                # Include context around matching line
                start = max(0, i - 1)
                end = min(len(lines), i + 3)
                relevant_lines.extend(lines[start:end])
        
        context = '\n'.join(relevant_lines)[:max_chars]
        return context if context else "General Pydantic documentation available"
    
    def query(self, question: str) -> AgentResponse:
            """Process user query and return answer"""
            # Validate input
            try:
                request = QueryRequest(question=question)
            except ValueError as e:
                return AgentResponse(answer="Invalid question format", source=None)
            
            # Extract relevant context
            context = self._extract_relevant_context(request.question)
            
            # Prepare prompt
            system_prompt = """You are a helpful Pydantic expert assistant. 
    Answer questions about Pydantic briefly and clearly in 1-2 sentences max.
    Keep answers short and to the point.
    Be based on the provided documentation."""
            
            user_prompt = f"""Based on this documentation:
    {context}

    Answer this question briefly (1-2 sentences max): {request.question}"""
            
            try:
                # Call OpenRouter API
                response = requests.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.7,
                        "max_tokens": 150,
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        
                        # Safely navigate the JSON and handle None values
                        choices = data.get('choices', [])
                        if not choices:
                            return AgentResponse(answer="API returned no choices.", source=None)
                            
                        content = choices[0].get('message', {}).get('content')
                        
                        # If content is None, provide a fallback message instead of crashing
                        answer = content.strip() if content else "The model returned an empty response."
                        
                        return AgentResponse(
                            answer=answer,
                            source="Pydantic Documentation"
                        )
                    except ValueError:
                        return AgentResponse(
                            answer=f"API returned invalid JSON. Raw response: {response.text[:200]}", 
                            source=None
                        )
                else:
                    # Handle non-200 responses gracefully
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("error", {}).get("message", "API Error")
                    except ValueError:
                        # If it's not JSON, grab the raw text to see the real HTTP error
                        error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                    
                    return AgentResponse(
                        answer=f"Error: {error_msg}",
                        source=None
                    )
                    
            except requests.exceptions.Timeout:
                return AgentResponse(answer="Request timed out. Please try again.", source=None)
            except requests.exceptions.RequestException as e:
                return AgentResponse(answer=f"Connection error: {str(e)}", source=None)
            except Exception as e:
                return AgentResponse(answer=f"Error processing request: {str(e)}", source=None)

def main():
    """Test the agent"""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not set")
        return
    
    agent = PydanticAgent(api_key)
    
    # Test query
    test_question = "What is Pydantic used for?"
    response = agent.query(test_question)
    print(f"Q: {test_question}")
    print(f"A: {response.answer}")
    print(f"Source: {response.source}")


if __name__ == "__main__":
    main()
