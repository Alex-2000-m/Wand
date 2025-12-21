import json
import os
import sys
import re
from api_client import chat_completion_stream
from tools import get_tools_definitions, execute_tool, set_llm_config

# Ensure stdout/stderr use UTF-8 to prevent encoding errors on Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        # In case sys.stdout/stderr are not standard streams (e.g. in some environments)
        pass

class MockDelta:
    def __init__(self, content):
        self.content = content

class MockChoice:
    def __init__(self, content):
        self.delta = MockDelta(content)

class MockChunk:
    def __init__(self, content):
        self.choices = [MockChoice(content)]

class LLMProcessor:
    """
    LLM处理系统
    """
    def __init__(self, config):
        self.config = config
        self.api_key = config.get('apiKey')
        self.base_url = config.get('baseUrl')
        set_llm_config(config)

    def process(self, query, history, context_files, model_id):
        # Update config with current model so tools can use it
        self.config['model'] = model_id
        set_llm_config(self.config)

        # 1. Construct System Prompt with Tools
        tools_definitions = get_tools_definitions()
        tools_json = json.dumps(tools_definitions, indent=2)
        
        system_prompt = f"""You are an advanced AI assistant capable of analyzing code and performing tasks.
You have access to the following tools:

{tools_json}

Process:
1. THINK: Analyze the user's request. Plan your steps.
2. ACTION: If you need more information or need to perform an action, call a tool.
3. RESPONSE: When you have the answer, provide the final response.

To call a tool, use the following format inside a <tool> tag:

<tool>
✿FUNCTION✿: tool_name
✿ARGS✿: {{"arg1": "value1", "arg2": "value2"}}
</tool>

IMPORTANT:
- The content inside <tool> must strictly follow the `✿FUNCTION✿: name` and `✿ARGS✿: json_object` format.
- `✿ARGS✿` must be a valid JSON object.
- You can only call one tool at a time.
- STOP generating immediately after the closing </tool> tag.
- Wait for the tool result before proceeding.
- **PRIORITY 1: USE EXISTING TOOLS.** Before creating a new tool, you MUST check if the task can be accomplished by:
  1. Using an existing tool from the list above.
  2. Combining your own capabilities (e.g., generating text, code, or logic) with an existing tool (e.g., `write_file`).
- **DO NOT create tools for simple content generation.**
  - BAD: Create a tool to generate a joke. (You can generate the joke yourself!)
  - BAD: Create a tool to write a specific file. (Use `write_file` with the content you generated.)
- **ONLY use `create_tool` if:**
  - The task requires executing code that you cannot simulate (e.g., complex math, external API calls, system operations).
  - The functionality is completely missing from the provided tools.
- If you truly need a new tool, use `create_tool`:
  - Provide a detailed description of the tool you need in the `requirement` argument.
  - The system will generate the tool code for you.
  - Once created, you can call the new tool in the next turn.
- **CRITICAL: When requesting new tools, describe them as GENERIC and REUSABLE functions.**
  - BAD Requirement: "Create a tool that writes a joke about cats to cat.txt"
  - GOOD Requirement: "Create a tool that writes text content to a file at a given path."
  - Always design tools to accept arguments for dynamic data.

Format your response:

<thinking>
[Your thought process]
</thinking>
<subtitle>[Short summary of the thought process]</subtitle>

[Tool Call or Final Response]
"""

        # Initial User Prompt
        # We don't pre-read files anymore, the LLM must decide to read them.
        # But if context_files are provided (e.g. from manual selection), we can list them.
        
        context_info = ""
        if context_files:
            context_info = f"The user has explicitly provided these files (you may need to read them):\n" + "\n".join(context_files)

        user_prompt = f"""
{context_info}

User Query: {query}
"""

        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add history
        for msg in history:
            if msg.get('content'):
                messages.append({"role": msg['role'], "content": msg['content']})

        messages.append({"role": "user", "content": user_prompt})

        # Loop for tool calls
        max_turns = 10
        current_turn = 0
        
        while current_turn < max_turns:
            current_turn += 1
            
            # Call LLM
            stream = chat_completion_stream(
                self.api_key,
                self.base_url,
                model_id,
                messages
            )
            
            full_response = ""
            
            # Yield chunks to the caller (cli.py)
            for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    full_response += content
                    yield chunk
            
            # Add assistant response to history
            messages.append({"role": "assistant", "content": full_response})
            
            # Check for tool call
            # Matches <tool> ... </tool>
            tool_call_pattern = r"<tool>(.*?)</tool>"
            match = re.search(tool_call_pattern, full_response, re.DOTALL)
            
            if match:
                try:
                    tool_content = match.group(1)
                    
                    # Extract function name
                    # Matches ✿FUNCTION✿: name
                    func_match = re.search(r"✿FUNCTION✿:\s*(.+)", tool_content)
                    if not func_match:
                        raise ValueError("Missing '✿FUNCTION✿:' identifier in tool call")
                    tool_name = func_match.group(1).strip()
                    
                    # Extract arguments
                    # Matches ✿ARGS✿: json_string
                    args_match = re.search(r"✿ARGS✿:\s*(.+)", tool_content, re.DOTALL)
                    tool_args = {}
                    if args_match:
                        args_json = args_match.group(1).strip()
                        tool_args = json.loads(args_json)
                    
                    # DEBUG: Print tool call details to stderr
                    sys.stderr.write(f"\n[DEBUG] Tool Call: {tool_name}\nArguments: {json.dumps(tool_args, indent=2, ensure_ascii=False)}\n")
                    sys.stderr.flush()

                    # Notify user of execution (optional, via a special chunk if cli.py supports it)
                    # For now, we just execute.
                    
                    result = execute_tool(tool_name, **tool_args)
                    
                    # DEBUG: Print tool result to stderr
                    sys.stderr.write(f"\n[DEBUG] Tool Result: {result}\n")
                    sys.stderr.flush()
                    
                    # Add result to history
                    tool_output = f"\nTool '{tool_name}' Output:\n{result}\n"
                    messages.append({"role": "user", "content": tool_output})
                    
                    # Yield the tool result to the frontend so it can be rendered
                    # We wrap it in a special tag <tool_result>
                    result_chunk = f"\n<tool_result>\n{result}\n</tool_result>\n"
                    yield MockChunk(result_chunk)
                    
                    # Yield a separator or status update
                    # yield ... 
                    
                except json.JSONDecodeError:
                    error_msg = "Error: Invalid JSON in ✿ARGS✿."
                    sys.stderr.write(f"\n[DEBUG] {error_msg}\n")
                    messages.append({"role": "user", "content": error_msg})
                except Exception as e:
                    error_msg = f"Error executing tool: {str(e)}"
                    sys.stderr.write(f"\n[DEBUG] {error_msg}\n")
                    messages.append({"role": "user", "content": error_msg})
            else:
                # No tool call, assume completion
                break

