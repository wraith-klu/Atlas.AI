"""
openrouter_client.py

A reusable API client for interacting with OpenRouter LLMs.
Includes rate limiting, primary/fallback model swapping, 429 handling,
and robust JSON extraction.
"""

import os
import time
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
from utils.logger import get_logger

logger = get_logger("OpenRouterClient")

# Load environment variables
load_dotenv()

# Track last request time for rate-limit spacing (1 second delay)
_last_request_time = 0.0

def _get_api_config():
    """
    Retrieves OpenRouter API Key and configuration.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    primary_model = os.getenv("PRIMARY_MODEL", "cohere/north-mini-code:free")
    fallback_model = os.getenv("FALLBACK_MODEL", "poolside/laguna-m.1:free")
    return api_key, primary_model, fallback_model

def log_api_call(model: str, prompt: str, status: str, response_text: str = None, error: str = None):
    """
    Logs every API call result to logs/api_calls.log.
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logs_dir = os.path.join(project_root, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    api_log_path = os.path.join(logs_dir, "api_calls.log")
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = (
        f"[{timestamp}] Model: {model} | Status: {status}\n"
        f"Prompt Snippet: {prompt[:150].strip()}...\n"
    )
    if response_text:
        log_entry += f"Response Snippet: {response_text[:300].strip()}...\n"
    if error:
        log_entry += f"Error: {error}\n"
    log_entry += "-" * 80 + "\n"
    
    try:
        with open(api_log_path, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        logger.error(f"Failed to write to api_calls.log: {e}")

def call_llm(prompt: str, model: str = None, max_tokens: int = 500) -> str:
    """
    Calls the OpenRouter API with rate-limiting, retry logic, and fallback support.
    
    Args:
        prompt (str): The prompt to send to the LLM.
        model (str, optional): Overrides the default model choice.
        max_tokens (int, optional): The maximum token limit for completion.
        
    Returns:
        str: Response text from the LLM or empty string on total failure.
    """
    global _last_request_time
    
    api_key, primary_model, fallback_model = _get_api_config()
    if not api_key or api_key == "your_key_here":
        logger.error("OPENROUTER_API_KEY is not set or is still the placeholder. Please configure it in .env.")
        return ""
        
    # Determine the model sequence (if model is specified, use only that model)
    models_to_try = [model] if model else [primary_model, fallback_model]
    
    for current_model in models_to_try:
        # Enforce a minimum 1-second delay between calls
        elapsed = time.time() - _last_request_time
        if elapsed < 1.0:
            time.sleep(1.0 - elapsed)
            
        _last_request_time = time.time()
        
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "AI-Job-Agent"
        }
        
        payload = {
            "model": current_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.1
        }
        
        logger.info(f"Calling OpenRouter model '{current_model}'...")
        
        # Retry logic for 429 and connection issues
        for attempt in range(2):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                
                # Check for rate-limiting
                if response.status_code == 429:
                    logger.warning(f"Rate limited (429) on attempt {attempt+1}. Waiting 60 seconds before retry...")
                    log_api_call(current_model, prompt, "RATE_LIMIT_429", error="429 Too Many Requests")
                    time.sleep(60.0)
                    continue
                    
                response.raise_for_status()
                
                # Successful call
                data = response.json()
                choices = data.get("choices", [])
                if choices:
                    message = choices[0].get("message", {})
                    content = message.get("content")
                    if content is None or str(content).strip().lower() == "none" or not str(content).strip():
                        # Support reasoning models that place output in 'reasoning' field
                        content = message.get("reasoning")
                        
                    if content is not None:
                        response_text = str(content).strip()
                        log_api_call(current_model, prompt, "SUCCESS", response_text=response_text)
                        return response_text
                    else:
                        raise ValueError(f"Message content is null and no reasoning field found. Full response: {data}")
                else:
                    error_info = data.get("error", {})
                    error_msg = error_info.get("message", "No choices returned from OpenRouter completions response.")
                    raise ValueError(f"OpenRouter Error: {error_msg}")
                    
            except Exception as e:
                logger.error(f"Error calling OpenRouter model '{current_model}' on attempt {attempt+1}: {e}")
                log_api_call(current_model, prompt, f"ERROR_ATTEMPT_{attempt+1}", error=str(e))
                if attempt == 0:
                    time.sleep(2.0)  # brief pause before retry
                    
        # If we failed both attempts and have fallback model next in list, we continue to the next model
        logger.warning(f"Model '{current_model}' failed. Trying next available model if any...")
        
    logger.error("All OpenRouter models failed to complete request.")
    return ""

def parse_json_response(text: str) -> dict:
    """
    Safely extracts and parses JSON content from the LLM response text,
    handling code block formatting or extra leading/trailing text.
    
    Args:
        text (str): Raw string output from LLM.
        
    Returns:
        dict: Parsed JSON as dictionary, or None if parsing fails.
    """
    if not text:
        return None
        
    # Attempt direct parsing first
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
        
    # Attempt to extract json from markdown code block format (e.g. ```json ... ```)
    cleaned = text.strip()
    if "```" in cleaned:
        try:
            # Look for ```json ... ```
            if "```json" in cleaned:
                parts = cleaned.split("```json")
                if len(parts) > 1:
                    json_str = parts[1].split("```")[0].strip()
                    return json.loads(json_str)
            # Look for generic ``` ... ```
            parts = cleaned.split("```")
            if len(parts) > 1:
                # Find the block containing the json (usually the second segment)
                for segment in parts[1:]:
                    segment_stripped = segment.strip()
                    if segment_stripped.startswith("{") or segment_stripped.startswith("["):
                        return json.loads(segment_stripped)
        except json.JSONDecodeError:
            pass
            
    # Try finding the first '{' and the last '}'
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        try:
            json_str = cleaned[first_brace:last_brace+1]
            # Replace common JSON errors (like single quoted keys)
            # However, direct json.loads requires double quotes.
            # Let's try simple json.loads first.
            return json.loads(json_str)
        except json.JSONDecodeError:
            # Try a quick replacement of single quotes to double quotes
            # ONLY for keys or strings, which is hard to do perfectly, but let's try a safe replacement.
            try:
                # Replace single quotes with double quotes around dictionary keys and values
                # Note: this is a fallback of a fallback, so it's a best-effort.
                import ast
                val = ast.literal_eval(json_str)
                if isinstance(val, dict):
                    return val
            except Exception:
                pass
                
    logger.error("Could not parse LLM response text as JSON.")
    return None
