import os
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from dotenv import load_dotenv
from rag.models import KnowledgeChunk

load_dotenv()
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", ".env"))

logger = logging.getLogger("isense_llm")

class LLMGenerationResult(BaseModel):
    text: str
    is_success: bool
    provider: str
    error_message: Optional[str] = None
    token_usage: Optional[Dict[str, int]] = None

class BaseLLMProvider(ABC):
    @abstractmethod
    def generate(
        self,
        query: str,
        system_instruction: str,
        retrieved_chunks: List[KnowledgeChunk],
        application_context: Optional[Dict[str, Any]] = None
    ) -> LLMGenerationResult:
        pass

class GeminiLLMProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model_name = model_name
        self._init_client()

    def _init_client(self):
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)
        self.client = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config={
                "temperature": 0.1,
                "top_p": 0.95,
                "max_output_tokens": 1024
            }
        )

    def generate(
        self,
        query: str,
        system_instruction: str,
        retrieved_chunks: List[KnowledgeChunk],
        application_context: Optional[Dict[str, Any]] = None
    ) -> LLMGenerationResult:
        try:
            # Build structured context with XML isolation to guard against prompt injection
            context_blocks = []
            for i, chunk in enumerate(retrieved_chunks):
                context_blocks.append(
                    f"<source_evidence id='{chunk.chunk_id}' standard='{chunk.standard_code}' clause='{chunk.clause}' page='{chunk.page or 'N/A'}'>\n"
                    f"{chunk.content}\n"
                    f"</source_evidence>"
                )
            context_str = "\n\n".join(context_blocks) if context_blocks else "NO_RETRIEVED_EVIDENCE_AVAILABLE"

            app_info = ""
            if application_context:
                app_info = (
                    f"\n<applicant_context>\n"
                    f"Product: {application_context.get('productName')}\n"
                    f"Category: {application_context.get('productCategory')}\n"
                    f"Active Standard: {application_context.get('standardCode')}\n"
                    f"</applicant_context>\n"
                )

            full_prompt = (
                f"{system_instruction}\n\n"
                f"### RETRIEVED STATUTORY & REGULATORY EVIDENCE:\n"
                f"{context_str}\n"
                f"{app_info}\n"
                f"### USER INQUIRY:\n"
                f"<user_query>{query}</user_query>\n\n"
                f"Provide a direct, factual answer strictly grounded in the evidence above. "
                f"Include specific standard numbers and clauses from the evidence. "
                f"If the evidence does not provide enough information, explicitly state that."
            )

            response = self.client.generate_content(full_prompt)
            if response and response.text:
                return LLMGenerationResult(
                    text=response.text.strip(),
                    is_success=True,
                    provider="Google Gemini (gemini-1.5-flash)"
                )
            else:
                return LLMGenerationResult(
                    text="Provider returned empty response.",
                    is_success=False,
                    provider="Google Gemini",
                    error_message="Empty response"
                )
        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            return LLMGenerationResult(
                text=f"LLM generation failed: {str(e)}",
                is_success=False,
                provider="Google Gemini",
                error_message=str(e)
            )

class OpenAILLMProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model_name: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model_name = model_name

    def generate(
        self,
        query: str,
        system_instruction: str,
        retrieved_chunks: List[KnowledgeChunk],
        application_context: Optional[Dict[str, Any]] = None
    ) -> LLMGenerationResult:
        try:
            import httpx
            context_blocks = [
                f"<evidence id='{c.chunk_id}' standard='{c.standard_code}' clause='{c.clause}'>{c.content}</evidence>"
                for c in retrieved_chunks
            ]
            context_str = "\n".join(context_blocks)

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            body = {
                "model": self.model_name,
                "temperature": 0.1,
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": f"Context:\n{context_str}\n\nUser Question: {query}"}
                ]
            }
            with httpx.Client(timeout=30.0) as client:
                res = client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=body)
                if res.status_code == 200:
                    ans = res.json()["choices"][0]["message"]["content"]
                    return LLMGenerationResult(text=ans.strip(), is_success=True, provider="OpenAI")
                else:
                    return LLMGenerationResult(
                        text=f"OpenAI error {res.status_code}",
                        is_success=False,
                        provider="OpenAI",
                        error_message=res.text
                    )
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            return LLMGenerationResult(
                text=f"OpenAI generation error: {str(e)}",
                is_success=False,
                provider="OpenAI",
                error_message=str(e)
            )

class MockLLMProvider(BaseLLMProvider):
    """Deterministic mock provider strictly for unit and integration testing."""
    def __init__(self, custom_answer: Optional[str] = None):
        self.custom_answer = custom_answer

    def generate(
        self,
        query: str,
        system_instruction: str,
        retrieved_chunks: List[KnowledgeChunk],
        application_context: Optional[Dict[str, Any]] = None
    ) -> LLMGenerationResult:
        if self.custom_answer:
            return LLMGenerationResult(
                text=self.custom_answer,
                is_success=True,
                provider="MockLLMProvider (Deterministic Test Fixture)"
            )

        if not retrieved_chunks:
            return LLMGenerationResult(
                text="The retrieved regulatory evidence does not contain sufficient information to answer this inquiry.",
                is_success=True,
                provider="MockLLMProvider (Deterministic Test Fixture)"
            )

        # Synthesize from retrieved chunks
        chunk_summaries = []
        for c in retrieved_chunks:
            chunk_summaries.append(f"According to **{c.standard_code}** ({c.clause}): {c.content}")

        ans = (
            f"Based on the retrieved Bureau of Indian Standards documentation for \"{query}\":\n\n"
            + "\n\n".join(chunk_summaries) +
            "\n\n*Note: Final certification determinations remain solely with the Bureau of Indian Standards.*"
        )
        return LLMGenerationResult(
            text=ans,
            is_success=True,
            provider="MockLLMProvider (Deterministic Test Fixture)"
        )

class UnavailableLLMProvider(BaseLLMProvider):
    """
    Invoked when no valid LLM API key (GEMINI_API_KEY, OPENAI_API_KEY) is configured.
    Does not fake an LLM answer. Transparently communicates that generation could not be
    verified while directly presenting the grounded retrieved chunks.
    """
    def generate(
        self,
        query: str,
        system_instruction: str,
        retrieved_chunks: List[KnowledgeChunk],
        application_context: Optional[Dict[str, Any]] = None
    ) -> LLMGenerationResult:
        if not retrieved_chunks:
            msg = (
                "**No Relevant Regulatory Evidence Found**\n\n"
                f"The available BIS regulatory knowledge base does not contain verified requirements matching '{query}'.\n\n"
                "*(Generation provider is unconfigured: Set GEMINI_API_KEY or OPENAI_API_KEY to enable neural synthesis. "
                "ISense does not invent requirements when official evidence is absent.)*"
            )
            return LLMGenerationResult(
                text=msg,
                is_success=False,
                provider="UnavailableLLMProvider (No API key configured)"
            )

        # Format retrieved evidence cleanly without claiming neural generation
        evidence_lines = []
        for c in retrieved_chunks:
            page_info = f" (Page {c.page})" if c.page else ""
            evidence_lines.append(
                f"• **{c.standard_code} — {c.clause}{page_info}**:\n  {c.content}"
            )
        evidence_block = "\n\n".join(evidence_lines)

        msg = (
            f"### Grounded Regulatory Evidence for \"{query}\":\n\n"
            f"{evidence_block}\n\n"
            f"---\n"
            f"*(Notice: LLM generation provider is currently unconfigured. Set `GEMINI_API_KEY` or `OPENAI_API_KEY` in environment to enable neural synthesis. "
            f"The above findings are direct extracts from verified Bureau of Indian Standards source documents.)*"
        )
        return LLMGenerationResult(
            text=msg,
            is_success=True,
            provider="Direct Evidence Presentation (No LLM API key configured)"
        )

def get_llm_provider(mock_mode: bool = False, custom_mock_answer: Optional[str] = None) -> BaseLLMProvider:
    """Factory to instantiate the appropriate LLM provider based on environment variables."""
    if mock_mode:
        return MockLLMProvider(custom_answer=custom_mock_answer)

    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if gemini_key and gemini_key.strip():
        try:
            model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
            return GeminiLLMProvider(api_key=gemini_key.strip(), model_name=model)
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini provider: {e}")

    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key and openai_key.strip():
        try:
            return OpenAILLMProvider(api_key=openai_key.strip())
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI provider: {e}")

    return UnavailableLLMProvider()
