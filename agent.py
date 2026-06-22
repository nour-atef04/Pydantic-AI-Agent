import os
import re
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
import requests

# =====================================================================
# Pydantic Schemas for Structured Research Flow
# =====================================================================

class InputClassification(BaseModel): # Defining a schema (Pydantic automatically translates this Python code into a JSON Schema). BaseModel of Pydantic ensures type enforcement, JSON parsing, and validation error generation
    """Classifies the user input to customize search strategy""" # Pydantic AI takes this docstring and passes it to the LLM as instruction
    is_ticker: bool = Field(..., description="True if the input is a stock ticker or symbol") # Field() allows to attach extra metadata and validation rules to a specifc attribute. "..." means it's a required field. description is also passed to the AI model.
    resolved_name: str = Field(..., description="The full company name or expanded query text")
    context: str = Field(..., description="Industry sector, core product focus, or overarching context")

class ResearchAngles(BaseModel):
    """The generated independent research paths"""
    angles: List[str] = Field(..., description="List of 3 to 4 distinct keywords or search phrases")

class SearchResult(BaseModel):
    """A verified container for clean search engine extractions"""
    title: str
    url: str
    snippet: str

class DeepResearchReport(BaseModel):
    """The ultimate structured analytical payload"""
    executive_summary: str = Field(..., description="High-level synthesis of findings")
    sections: Dict[str, str] = Field(..., description="Dictionary mapping each research angle to its deep-dive analysis")
    evidence_and_citations: List[str] = Field(..., description="Clean bullet points linking specific claims to URLs")
    risks_and_uncertainties: str = Field(..., description="Conflicting info, data gaps, or structural risks")
    what_to_watch_for: List[str] = Field(..., description="Forward-looking catalysts or trigger conditions") # an upcoming event that could cause a stock price to jump up or crash down

# Interface communication adapter (bridge between backend and Gradio frontend)
class AgentResponse(BaseModel):
    answer: str
    source: Optional[str] = None


# =====================================================================
# Deep Research Agent Core Logic
# =====================================================================

class PydanticAgent:
    def __init__(self, api_key: str, model: str = "openai/gpt-oss-120b:free"):
        self.api_key = api_key
        self.model = model
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        
    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Internal "_" helper to manage clean OpenRouter communications"""
        try:
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
                    "temperature": 0.2,
                    "max_tokens": 1500,
                },
                timeout=45
            )
            if response.status_code == 200:
                data = response.json()
                content = data.get('choices', [])[0].get('message', {}).get('content') # Instead of writing data['choices'][0]['message']['content'] (which would crash your entire app if one of those keys was missing), .get() safely looks for the key
                return content.strip() if content else ""
            return f"Error: HTTP {response.status_code}"
        except Exception as e:
            return f"LLM Call Exception: {str(e)}"

    def _duckduckgo_search(self, query: str, max_results: int = 4) -> List[SearchResult]:
        """Performs structured extraction against the zero-auth DuckDuckGo Lite endpoint"""
        url = "https://html.duckduckgo.com/html/" # perfect for scraping
        headers = { # since websites try to block automated bots, pass 'User-Agent' to tell DuckDuckGo that it's a normal human using Google Chrome
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        payload = {'q': query}
        results = []
        
        try:
            res = requests.post(url, data=payload, headers=headers, timeout=15)
            if res.status_code != 200:
                return results # safely fallback to []
                
            # Regex patterns to safely scrape individual components from the HTML structure (from DuckDuckGo HTML search result)
            blocks = re.findall(r'<td class="result-snippet">.*?</td>', res.text, re.DOTALL) # re.DOTALL to ignore line-breaks and space in the HTML code
            links = re.findall(r'<a class="result-url" href="(.*?)".*?>(.*?)</a>', res.text, re.DOTALL)
            titles = re.findall(r'<a class="result-link" href=".*?">(.*?)</a>', res.text, re.DOTALL)
            
            for i in range(min(len(blocks), len(links), len(titles), max_results)): # min to not go out of bounds
                # Clean up raw HTML text fragments
                clean_title = re.sub(r'<[^>]*>', '', titles[i]).strip() # find any leftover HTML tags inside the text and substitutes (sub) them with nothing ('').
                clean_url = links[i][0].strip()
                clean_snippet = re.sub(r'<[^>]*>', '', blocks[i]).strip()
                
                results.append(SearchResult(title=clean_title, url=clean_url, snippet=clean_snippet))
        except Exception:
            pass # Return whatever was partially collected or empty on failure
        return results

    def query(self, user_input: str, progress_cb=None) -> AgentResponse:
        """Executes the systematic, deep multi-turn research pipeline"""
        
        # Helper to safely call the progress tracker if it exists
        def report_progress(fraction, desc):
            if progress_cb:
                progress_cb(fraction, desc=desc)

        # --- Step 1: Input Analysis and Structural Target Resolution ---
        report_progress(0.1, "Step 1/5: Analyzing input and resolving target...")
        classification_sys = "You are a data analyst. Classify if the query is a financial stock ticker symbol or general term. Return your output EXACTLY as valid JSON matching keys: 'is_ticker' (bool), 'resolved_name' (str), 'context' (str)."
        classification_raw = self._call_llm(classification_sys, f"Classify this input: '{user_input}'")
        
        # Fallback tracking parsing
        is_ticker = any(word.isupper() and 2 <= len(word) <= 5 for word in user_input.split())
        resolved_name = user_input
        context = "General Research"
        
        if "{" in classification_raw:
            try:
                # Basic string processing to cleanly capture JSON fields if model outputs wrapper prose
                json_str = classification_raw[classification_raw.find("{"):classification_raw.rfind("}")+1]
                parsed = InputClassification.model_validate_json(json_str)
                is_ticker = parsed.is_ticker
                resolved_name = parsed.resolved_name
                context = parsed.context
            except Exception:
                pass

        # --- Step 2: Discovery Search Phase ---
        # performs a broad web search to gather general context to be able to gather angles to dive into later
        report_progress(0.3, "Step 2/5: Executing broad discovery search...")
        discovery_query = f"{resolved_name} {context} update" if is_ticker else resolved_name # 'update' to give latest news on the ticker
        discovery_results = self._duckduckgo_search(discovery_query, max_results=5)
        discovery_context = "\n".join([f"- {r.title} ({r.url}): {r.snippet}" for r in discovery_results]) # converts the raw list of search results into a neatly formatted block of text that a LLM can easily understand

        # --- Step 3: Architectural Strategy & Angle Generation ---
        report_progress(0.5, "Step 3/5: Architecting research strategy & generating angles...")
        angle_sys = "Based on the initial research context, generate exactly 3-4 distinct, non-overlapping target phrases/keywords to run comprehensive follow-up investigations. Return output as a clean JSON object with the key 'angles' containing a list of strings."
        angle_user = f"Context for {resolved_name}:\n{discovery_context}\n\nGenerate target phrases."
        angle_raw = self._call_llm(angle_sys, angle_user)
        
        search_angles = [f"{resolved_name} recent analysis", f"{resolved_name} news outlook", f"{resolved_name} updates"]
        if "{" in angle_raw:
            try:
                json_str = angle_raw[angle_raw.find("{"):angle_raw.rfind("}")+1]
                search_angles = ResearchAngles.model_validate_json(json_str).angles
            except Exception:
                pass

        # --- Step 4: Targeted Explorations ---
        report_progress(0.7, "Step 4/5: Running targeted deep web explorations...")
        master_sources: List[SearchResult] = list(discovery_results) # copy general sources found in step 2
        deep_dive_logs = ""
        
        for angle in search_angles:
            dive_results = self._duckduckgo_search(angle, max_results=3)
            master_sources.extend(dive_results) # update the bibliography (takes 3 new search results and adds them to master bibliography list)
            deep_dive_logs += f"\n### Research Angle: {angle}\n"
            if not dive_results:
                deep_dive_logs += "No active source matches found.\n"
            for res in dive_results:
                deep_dive_logs += f"Source: {res.title} | URL: {res.url}\nFacts/Snippets: {res.snippet}\n\n"

        # --- Step 5: High-Fidelity Knowledge Synthesis ---
        report_progress(0.9, "Step 5/5: Synthesizing final high-fidelity report...")
        synthesis_sys = """You are an elite institutional equity researcher and data analyst. 
Synthesize all collected intelligence into an exhaustive, structured final report. 
Prioritize hard metrics, timelines, specific numbers, and verify contradictions across sources.
Your response MUST be formatted in clean, clear markdown sections."""

        synthesis_user = f"""Synthesize a comprehensive deep-dive report on: **{resolved_name}**
Core Focus Sector: {context}

All Gathered Intelligence Streams:
{deep_dive_logs}

Please construct a comprehensive report matching these exact structural headings:
# Deep Research Executive Summary
[Provide an authoritative, high-density synthesis of findings here]

# Core Findings by Investigation Vector
{chr(10).join([f'## Analysis of {angle}' for angle in search_angles])}
[Flesh out each of the sections thoroughly with findings and statistics]

# Evidence, Claims, and Grounded Citations
[Provide an explicit list of verifiable claims tied directly to their respective source URLs]

# Risk Profiling and Structural Uncertainties
[Detail any conflicting information, hidden risks, or metrics that diverge across sources]

# Catalysts and Variables to Watch
[Provide actionable, forward-looking target markers, earnings events, or industry triggers]
"""

        final_markdown_report = self._call_llm(synthesis_sys, synthesis_user)

        # Deduplicate citation tracking
        unique_urls = list({src.url: src for src in master_sources if src.url}.values())
        citations_footer = "\n\n### Verifiable Source Registry:\n" + "\n".join([f"- [{s.title}]({s.url})" for s in unique_urls[:10]])

        report_progress(1.0, "Research Complete!")
        return AgentResponse(
            answer=final_markdown_report + citations_footer,
            source="Multi-Source Web Intelligence Synthesis"
        )

def main():
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY environment variable not configured.")
        return
        
    agent = PydanticAgent(api_key=api_key)
    print("Initiating Deep Research Test Run...")
    report = agent.query("NVDA")
    print("\n" + "="*40 + "\nFINAL OUTPUT REPORT\n" + "="*40)
    print(report.answer)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    main()