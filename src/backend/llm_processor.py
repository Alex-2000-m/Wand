import json
import os
import sys
from api_client import chat_completion_stream

class LLMProcessor:
    """
    LLM处理系统
    """
    def __init__(self, config):
        self.config = config
        self.api_key = config.get('apiKey')
        self.base_url = config.get('baseUrl')

    def _read_file_content(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.pdf':
            try:
                from pypdf import PdfReader
                reader = PdfReader(file_path)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
            except ImportError:
                return "[Error: pypdf not installed, cannot read PDF]"
            except Exception as e:
                return f"[Error reading PDF: {str(e)}]"
        else:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            except Exception as e:
                return f"[Error reading file: {str(e)}]"

    def process(self, query, context_files, model_id):
        # 1. Read Context
        context_content = ""
        for file_path in context_files:
            content = self._read_file_content(file_path)
            # Limit file content to avoid context overflow (simple truncation)
            if len(content) > 20000:
                content = content[:20000] + "\n...[truncated]..."
            context_content += f"\n--- File: {file_path} ---\n{content}\n"

        # 2. Construct Prompt
        system_prompt = """You are an advanced AI assistant capable of analyzing code and performing tasks.
You have access to the following files in the workspace.

Process:
1. THINK: Analyze the user's request and the provided context. Plan your steps.
2. ACTION: Generate the final response.

IMPORTANT regarding Code Execution:
- The `python:interpreter` block is ONLY for executing code to MODIFY files (create, edit, delete) or run specific scripts explicitly requested by the user.
- Do NOT generate code for "tool calling", "auxiliary calculation", or "data processing" unless it results in a file change.
- If no file modification is needed, DO NOT include the code block.

Format your response exactly as follows:

<thinking>
[Your thought process here]
</thinking>

<action>
[Your response text to the user. This is REQUIRED.]

```python:interpreter
[Python code to execute ONLY if modifying files. Omit this block if no file changes are needed.]
```
</action>
"""

        user_prompt = f"""
Context Files:
{context_content}

User Query: {query}
"""
        # DEBUG LOGGING
        try:
            sys.stderr.write(f"\n[DEBUG] Processor System Prompt:\n{system_prompt}\n")
            sys.stderr.write(f"\n[DEBUG] Processor User Prompt:\n{user_prompt}\n")
            sys.stderr.flush()
        except Exception as e:
            pass # Ignore logging errors

        # 3. Call LLM
        stream = chat_completion_stream(
            self.api_key,
            self.base_url,
            model_id,
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        # Wrap stream to log response
        def debug_stream_wrapper(s):
            full_resp = ""
            for chunk in s:
                content = chunk.choices[0].delta.content
                if content:
                    full_resp += content
                yield chunk
            try:
                sys.stderr.write(f"\n[DEBUG] Processor Response:\n{full_resp}\n")
                sys.stderr.flush()
            except Exception:
                pass

        return debug_stream_wrapper(stream)
