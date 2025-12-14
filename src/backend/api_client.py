import sys
import json
from openai import OpenAI

# Set encoding to utf-8 for stdin/stdout
sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')

def fetch_available_models(api_key, base_url):
    try:
        client = OpenAI(
            api_key=api_key,
            base_url=base_url if base_url else None
        )
        
        # List models
        models_page = client.models.list()
        
        # Extract model IDs
        model_list = [model.id for model in models_page.data]
        
        return {'models': model_list}
    except Exception as e:
        return {'error': str(e)}

def chat_completion(api_key, base_url, model, messages, temperature=0.7):
    try:
        client = OpenAI(
            api_key=api_key,
            base_url=base_url if base_url else None
        )
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            stream=False
        )
        
        return response.choices[0].message.content
    except Exception as e:
        raise e

def chat_completion_stream(api_key, base_url, model, messages, temperature=0.7):
    try:
        client = OpenAI(
            api_key=api_key,
            base_url=base_url if base_url else None
        )
        
        return client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            stream=True
        )
    except Exception as e:
        raise e


if __name__ == '__main__':
    # This block is for testing or standalone execution if needed
    # In production, this file is imported by cli.py
    pass
