import os
import json
import hashlib
import sys
from datetime import datetime
from api_client import chat_completion, chat_completion_stream

class PrePlanner:
    def __init__(self, config):
        self.config = config
        self.api_key = config.get('apiKey')
        self.base_url = config.get('baseUrl')
        self.high_speed_model = config.get('highSpeedTextModel') or 'gpt-3.5-turbo'

    def _calculate_file_hash(self, file_path):
        """Simple hash to simulate Merkle tree node"""
        hasher = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                buf = f.read(65536)
                while len(buf) > 0:
                    hasher.update(buf)
                    buf = f.read(65536)
            return hasher.hexdigest()
        except:
            return None

    def scan_workspace(self, workspace_path):
        file_list = []
        ignore_dirs = {'.git', 'node_modules', '__pycache__', '.vscode', 'dist', 'build', 'coverage', '.wand'}
        
        for root, dirs, files in os.walk(workspace_path):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            for file in files:
                if file.startswith('.'): continue
                file_path = os.path.join(root, file)
                file_list.append(file_path)
        return file_list

    def _is_binary_file(self, file_path):
        # Common text extensions to skip binary check for performance/safety
        text_extensions = {'.txt', '.md', '.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.json', '.xml', '.yaml', '.yml', '.ini', '.conf', '.sh', '.bat', '.ps1', '.c', '.cpp', '.h', '.java', '.cs', '.go', '.rs', '.php', '.rb', '.lua', '.sql', '.log'}
        ext = os.path.splitext(file_path)[1].lower()
        if ext in text_extensions:
            return False
            
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(4096)
                return b'\x00' in chunk
        except:
            return True

    def get_file_description(self, file_path):
        try:
            # Get file metadata
            try:
                file_stat = os.stat(file_path)
                file_size = file_stat.st_size
                mod_time = datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                create_time = datetime.fromtimestamp(file_stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
                metadata_str = f"[路径: {file_path}, 大小: {file_size} bytes, 创建: {create_time}, 修改: {mod_time}]"
            except:
                metadata_str = f"[路径: {file_path}, 元数据获取失败]"

            ext = os.path.splitext(file_path)[1].lower()
            filename = os.path.basename(file_path)
            content = ""
            is_text = True
            
            if ext == '.pdf':
                try:
                    from pypdf import PdfReader
                    reader = PdfReader(file_path)
                    text_list = []
                    for page in reader.pages:
                        text_list.append(page.extract_text())
                    content = "\n".join(text_list)
                except ImportError:
                    return f"{metadata_str} PDF文件 (未安装pypdf)"
                except Exception as e:
                    return f"{metadata_str} PDF文件 (读取错误: {str(e)})"
            
            elif self._is_binary_file(file_path):
                is_text = False
            
            else:
                # Text file
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                except Exception:
                    is_text = False

            if is_text:
                # Limit to ~50k chars to avoid context overflow on typical high-speed models (approx 10k-15k tokens)
                if len(content) > 50000:
                    content = content[:50000] + "\n...[内容过长已截断]..."
                
                prompt = f"请根据以下文件内容，概括该文件包含的主题、功能模块或知识点类别。请注意：\n1. 不需要列出具体的数值、代码细节或详细内容。\n2. 重点在于描述“这个文件里有什么”，而不是“这个文件里的内容是什么”。\n3. 总结应简洁明了，方便后续根据主题进行检索。\n\n文件名：{filename}\n\n文件内容：\n{content}"
            else:
                prompt = f"这是一个非文本文件（如二进制、图片或无法读取的文件）。请仅根据文件名推测其用途。文件名：{filename}"
            
            summary = chat_completion(
                self.api_key, 
                self.base_url, 
                self.high_speed_model, 
                [{"role": "user", "content": prompt}]
            )
            return f"{metadata_str} {summary}"
        except Exception as e:
            return f"Error: {str(e)}"

    def whichFiles(self, context):
        """
        Decides which files to provide to the LLM.
        Returns a generator that yields status updates and finally the selected files.
        """
        workspace_path = context.get('workspacePath')
        query = context.get('query')
        specified_files = context.get('files', [])

        # Determine files to analyze
        all_files = []
        if specified_files:
            all_files = specified_files
        elif workspace_path:
            all_files = self.scan_workspace(workspace_path)
        else:
            yield {"type": "result", "files": []}
            return

        # Ensure 'out' directory exists for workspace index cache
        workspace_index = {}
        index_path = None
        
        if workspace_path:
            cache_dir = os.path.join(workspace_path, '.wand')
            if not os.path.exists(cache_dir):
                try:
                    os.makedirs(cache_dir)
                except:
                    pass
            
            if os.path.exists(cache_dir):
                index_path = os.path.join(cache_dir, 'workspace_index.json')
                if os.path.exists(index_path):
                    try:
                        with open(index_path, 'r', encoding='utf-8') as f:
                            workspace_index = json.load(f)
                    except:
                        pass

        # 1. Build "Workspace Index" (Scan & Hash)
        yield {"type": "status", "content": "<details><summary>预处理：扫描工作区</summary>\n<div style='font-family: monospace; font-size: 0.85em; line-height: 1.4;'>\n"}
        
        files_to_process = []
        
        # Limit for demo performance
        max_files = 20 
        processed_count = 0

        # Track current descriptions for selection step
        current_descriptions = {}

        # Sort files to simulate tree structure
        sorted_files = sorted(all_files)

        for file_path in sorted_files:
            if processed_count >= max_files:
                break
            
            # Determine key for cache (relative path if in workspace, else absolute)
            if workspace_path and file_path.startswith(workspace_path):
                rel_path = os.path.relpath(file_path, workspace_path)
            else:
                rel_path = file_path # Use absolute path as key for external files

            current_hash = self._calculate_file_hash(file_path)
            
            cached_data = workspace_index.get(rel_path)
            
            # Tree formatting
            depth = rel_path.count(os.sep)
            indent = "&nbsp;&nbsp;" * depth
            icon = "📄"
            
            if not cached_data or cached_data.get('hash') != current_hash:
                # File changed or new
                status_color = "#eab308" # Yellow for modified
                status_text = "M" if cached_data else "N"
                
                yield {"type": "status", "content": f"{indent}{icon} <span style='color:{status_color}'>[{status_text}]</span> {os.path.basename(file_path)}<br/>"}
                
                desc = self.get_file_description(file_path)
                workspace_index[rel_path] = {
                    'hash': current_hash,
                    'description': desc,
                    'path': file_path
                }
                files_to_process.append(file_path)
            else:
                # Unchanged
                status_color = "#4ade80" # Green for unchanged
                yield {"type": "status", "content": f"{indent}{icon} <span style='color:{status_color}'>[✓]</span> {os.path.basename(file_path)}<br/>"}
            
            # Store description for selection step
            current_descriptions[file_path] = workspace_index[rel_path]['description']
            
            processed_count += 1

        yield {"type": "status", "content": "</div></details>\n\n"}

        # Save updated Workspace Index
        if index_path:
            try:
                with open(index_path, 'w', encoding='utf-8') as f:
                    json.dump(workspace_index, f, indent=2, ensure_ascii=False)
            except Exception as e:
                yield {"type": "status", "content": f"Warning: Failed to save cache: {e}\n"}

        # 2. Select Relevant Files using the Merkle Tree descriptions
        # Create stable indexed list for LLM selection
        indexed_files = list(current_descriptions.items()) # List of (path, description) tuples

        descriptions_text = "\n".join([f"{i}. {os.path.basename(path)}: {desc}" for i, (path, desc) in enumerate(indexed_files)])
        
        selection_prompt = f"""
User Query: "{query}"

Available Files:
{descriptions_text}

Task: Select the files that are most relevant to answering the user's query.
1. Explain your reasoning for selecting specific files in 1-2 sentences.
2. Provide the JSON array of the INDICES (integers) of the files.

IMPORTANT:
- DO NOT answer the user's query directly.
- ONLY provide the reasoning and the file indices.

Example Output:
I selected file A because it contains the definition of the class mentioned in the query.
```json
[0, 2]
```
"""
        # DEBUG LOGGING
        sys.stderr.write(f"\n[DEBUG] Preprocessor Prompt:\n{selection_prompt}\n")
        sys.stderr.flush()

        selected_files = []
        full_response = ""
        
        yield {"type": "status", "content": "<details><summary>预处理：文件筛选</summary>\n<div style='color: #a1a1aa; font-size: 0.9em; margin-bottom: 8px; padding-left: 4px;'>\n"}
        
        try:
            stream = chat_completion_stream(
                self.api_key,
                self.base_url,
                self.high_speed_model,
                [{"role": "user", "content": selection_prompt}]
            )
            
            is_json_part = False
            for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    full_response += content
                    
                    # Check if we've reached the JSON code block
                    if "```" in full_response and not is_json_part:
                        # If this chunk completes the backticks, we might have printed some backticks already.
                        # It's cleaner to just stop printing as soon as we detect the start of the block.
                        # However, we need to handle the case where "```" is split across chunks.
                        # A simple heuristic: if full_response contains "```", we stop yielding content.
                        is_json_part = True
                        continue

                    # Check if response starts with [ (raw JSON without code block)
                    if full_response.strip().startswith("[") and not is_json_part:
                        is_json_part = True
                        continue
                    
                    if not is_json_part:
                        # Escape HTML characters for display
                        safe_content = content.replace("<", "&lt;").replace(">", "&gt;")
                        yield {"type": "status", "content": safe_content}
            
            yield {"type": "status", "content": "</div>\n"}
            
            # DEBUG LOGGING
            sys.stderr.write(f"\n[DEBUG] Preprocessor Response:\n{full_response}\n")
            sys.stderr.flush()

            # Parse JSON from full_response
            json_str = full_response
            if "```json" in full_response:
                json_str = full_response.split("```json")[1].split("```")[0]
            elif "```" in full_response:
                json_str = full_response.split("```")[1].split("```")[0]
            
            # Find list in string if not using code blocks
            if "[" in json_str and "]" in json_str:
                start = json_str.find("[")
                end = json_str.rfind("]") + 1
                json_str = json_str[start:end]

            selected_indices = json.loads(json_str)
            if isinstance(selected_indices, list):
                for idx in selected_indices:
                    if isinstance(idx, int) and 0 <= idx < len(indexed_files):
                        selected_files.append(indexed_files[idx][0])
            
        except Exception as e:
            yield {"type": "status", "content": f"\nError in selection: {str(e)}</div>\n"}
            selected_files = [f[0] for f in indexed_files[:5]] # Fallback

        # Display selected files list
        selected_names = [os.path.basename(f) for f in selected_files]
        yield {"type": "status", "content": "\n\n" + "\n".join([f"- 已选中 `{name}`" for name in selected_names]) + "\n</details>\n\n"}
        
        yield {"type": "result", "files": selected_files}

    def whichModels(self, selected_files):
        """
        Decides which model to use based on file types.
        """
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
        has_image = False
        
        for f in selected_files:
            ext = os.path.splitext(f)[1].lower()
            if ext in image_extensions:
                has_image = True
                break
        
        if has_image:
            return self.config.get('standardMultimodalModel') or 'gpt-4-vision-preview'
        else:
            return self.config.get('standardTextModel') or 'gpt-4'

