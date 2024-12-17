"""Enhanced AutoGen agents with advanced capabilities."""
import logging
import sys
from typing import Dict, List, Optional, Union, Any
from termcolor import colored
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager, ConversableAgent
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import os
import datetime
import ast

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Constants
MAX_RETRIES = 3
TIMEOUT_SECONDS = 60

def handle_error(error: Exception, agent_name: str, retry_count: int) -> bool:
    """Handle errors during agent execution."""
    logging.error(f"Error in {agent_name}: {str(error)}")
    if retry_count < MAX_RETRIES:
        logging.info(f"Retrying... (Attempt {retry_count + 1}/{MAX_RETRIES})")
        return True
    return False

class EnhancedAgent(ConversableAgent):
    """Base class for enhanced agents with additional capabilities."""
    
    def __init__(self, name: str, system_message: str, **kwargs):
        super().__init__(name=name, system_message=system_message, **kwargs)
        self.retry_count = 0
        self.conversation_history = []
        
    def process_message(self, message: str, sender: str, silent: bool = False):
        try:
            self.conversation_history.append({"sender": sender, "message": message})
            return super().process_message(message, sender, silent)
        except Exception as e:
            if handle_error(e, self.name, self.retry_count):
                self.retry_count += 1
                return self.process_message(message, sender, silent)
            raise

class EnhancedUserProxy(UserProxyAgent, EnhancedAgent):
    """Enhanced User Proxy Agent with error handling and history tracking."""
    
    def __init__(self, name: str, **kwargs):
        super().__init__(
            name=name,
            human_input_mode="TERMINATE",
            max_consecutive_auto_reply=5,
            is_termination_msg=lambda x: "TASK COMPLETED" in x.get("content", "").upper(),
            code_execution_config={"work_dir": "workspace", "use_docker": False},
            **kwargs
        )

class EnhancedAssistant(AssistantAgent, EnhancedAgent):
    """Enhanced Assistant Agent with specialized capabilities."""
    
    def __init__(self, name: str, **kwargs):
        super().__init__(
            name=name,
            is_termination_msg=lambda x: "TASK COMPLETED" in x.get("content", "").upper(),
            **kwargs
        )

class CodeAssistant(EnhancedAssistant):
    """Specialized agent for code implementation."""
    
    def __init__(self, name: str, **kwargs):
        super().__init__(
            name=name,
            code_execution_config={"work_dir": "workspace", "use_docker": False},
            **kwargs
        )

class ReviewerAssistant(EnhancedAssistant):
    """Specialized agent for code review."""
    
    def __init__(self, name: str, **kwargs):
        super().__init__(name=name, **kwargs)
        self.review_history = []
    
    def review_code(self, code: str) -> Dict[str, List[str]]:
        """Perform code review and return feedback."""
        review_result = {
            "issues": [],
            "suggestions": [],
            "security_concerns": [],
            "optimizations": []
        }
        self.review_history.append(review_result)
        return review_result

class WebResearchAgent(EnhancedAssistant):
    """Agent specialized in web research and URL content analysis."""
    
    def __init__(self, name: str, **kwargs):
        super().__init__(name=name, **kwargs)
        self.url_cache = {}
        self.visited_urls = set()
        self.session = requests.Session()  # Use session for better performance
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def fetch_url_content(self, url: str, cache: bool = True) -> str:
        """Fetch content from a URL with caching and error handling."""
        if cache and url in self.url_cache:
            logging.info(f"Using cached content for URL: {url}")
            return self.url_cache[url]
        
        try:
            logging.info(f"Fetching content from URL: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract main content and clean it
            content = soup.get_text(separator='\n', strip=True)
            
            # Clean up the content
            content = '\n'.join(line.strip() for line in content.splitlines() if line.strip())
            
            if cache:
                self.url_cache[url] = content
                self.visited_urls.add(url)
            
            return content
        except requests.RequestException as e:
            error_msg = f"Error fetching URL {url}: {str(e)}"
            logging.error(error_msg)
            return error_msg
    
    def analyze_url_content(self, url: str) -> Dict[str, Any]:
        """Analyze content from a URL and extract key information."""
        content = self.fetch_url_content(url)
        
        analysis = {
            "url": url,
            "domain": urlparse(url).netloc,
            "content_length": len(content),
            "summary": content[:500] + "..." if len(content) > 500 else content,
            "key_points": [],
            "code_snippets": [],
            "metadata": {
                "timestamp": str(datetime.datetime.now()),
                "success": not content.startswith("Error:")
            }
        }
        
        try:
            # Extract code snippets if present
            soup = BeautifulSoup(content, 'html.parser')
            code_blocks = soup.find_all(['code', 'pre'])
            if code_blocks:
                analysis["code_snippets"] = [block.get_text(strip=True) for block in code_blocks]
            
            # Extract key points (e.g., headers)
            headers = soup.find_all(['h1', 'h2', 'h3'])
            if headers:
                analysis["key_points"] = [header.get_text(strip=True) for header in headers]
            
            # Extract links for potential further analysis
            links = soup.find_all('a', href=True)
            analysis["related_links"] = [
                link['href'] for link in links 
                if link['href'].startswith(('http://', 'https://'))
            ]
        except Exception as e:
            logging.error(f"Error analyzing URL content: {str(e)}")
            analysis["error"] = str(e)
        
        return analysis
    
    def process_message(self, message: str, sender: str, silent: bool = False):
        """Override to handle URLs in messages."""
        try:
            # Extract URLs from the message
            words = message.split()
            urls = [word for word in words if word.startswith(('http://', 'https://'))]
            
            if urls:
                response = "I found the following URLs and their content:\n\n"
                for url in urls:
                    analysis = self.analyze_url_content(url)
                    response += f"URL: {url}\n"
                    response += f"Domain: {analysis['domain']}\n"
                    response += f"Summary: {analysis['summary']}\n"
                    
                    if analysis.get('key_points'):
                        response += "\nKey Points:\n"
                        for point in analysis['key_points']:
                            response += f"- {point}\n"
                    
                    if analysis.get('code_snippets'):
                        response += "\nCode Snippets Found:\n"
                        for snippet in analysis['code_snippets']:
                            response += f"```\n{snippet}\n```\n"
                    
                    if analysis.get('related_links'):
                        response += "\nRelated Links:\n"
                        for link in analysis['related_links'][:5]:  # Limit to 5 related links
                            response += f"- {link}\n"
                    
                    response += "\n---\n\n"
                
                # Add URL analysis to the message
                message = f"{message}\n\nURL Analysis:\n{response}"
            
            return super().process_message(message, sender, silent)
        except Exception as e:
            if handle_error(e, self.name, self.retry_count):
                self.retry_count += 1
                return self.process_message(message, sender, silent)
            raise

class FileSystemAgent(EnhancedAssistant):
    """Agent specialized in handling local file system URLs and content."""
    
    def __init__(self, name: str, **kwargs):
        super().__init__(name=name, **kwargs)
        self.file_cache = {}
        self.file_metadata = {}
    
    def read_file_content(self, file_url: str, cache: bool = True) -> str:
        """Read content from a local file URL with enhanced error handling and metadata tracking."""
        if cache and file_url in self.file_cache:
            logging.info(f"Using cached content for file: {file_url}")
            return self.file_cache[file_url]
        
        try:
            # Convert file URL to path
            path = urlparse(file_url).path
            
            # Get file metadata
            file_stat = os.stat(path)
            self.file_metadata[file_url] = {
                "size": file_stat.st_size,
                "modified": datetime.datetime.fromtimestamp(file_stat.st_mtime),
                "created": datetime.datetime.fromtimestamp(file_stat.st_ctime),
                "type": "text" if path.endswith(('.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml', '.csv')) else "binary"
            }
            
            # Check if file is too large (e.g., > 10MB)
            if file_stat.st_size > 10 * 1024 * 1024:
                return f"Error: File {path} is too large to process (size: {file_stat.st_size} bytes)"
            
            # Read file content based on type
            if self.file_metadata[file_url]["type"] == "text":
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if cache:
                    self.file_cache[file_url] = content
                
                return content
            else:
                return f"Error: File {path} appears to be a binary file"
            
        except FileNotFoundError:
            error_msg = f"Error: File {path} not found"
            logging.error(error_msg)
            return error_msg
        except PermissionError:
            error_msg = f"Error: Permission denied for file {path}"
            logging.error(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"Error reading file {path}: {str(e)}"
            logging.error(error_msg)
            return error_msg
    
    def analyze_file_content(self, file_url: str) -> Dict[str, Any]:
        """Analyze content from a file and extract key information."""
        content = self.read_file_content(file_url)
        path = urlparse(file_url).path
        
        analysis = {
            "file_url": file_url,
            "path": path,
            "filename": os.path.basename(path),
            "extension": os.path.splitext(path)[1],
            "metadata": self.file_metadata.get(file_url, {}),
            "content_preview": content[:500] + "..." if len(content) > 500 else content,
            "error": content if content.startswith("Error:") else None
        }
        
        if not analysis["error"]:
            try:
                # Count lines of code for text files
                if analysis["metadata"].get("type") == "text":
                    analysis["line_count"] = len(content.splitlines())
                    
                    # Detect programming language
                    if path.endswith(('.py', '.js', '.java', '.cpp', '.cs')):
                        analysis["language"] = os.path.splitext(path)[1][1:]
                        
                        # Extract function and class definitions
                        if analysis["language"] == "py":
                            try:
                                tree = ast.parse(content)
                                analysis["functions"] = [
                                    node.name for node in ast.walk(tree) 
                                    if isinstance(node, ast.FunctionDef)
                                ]
                                analysis["classes"] = [
                                    node.name for node in ast.walk(tree) 
                                    if isinstance(node, ast.ClassDef)
                                ]
                            except SyntaxError:
                                analysis["parse_error"] = "Could not parse Python code"
                
            except Exception as e:
                logging.error(f"Error during file analysis: {str(e)}")
                analysis["analysis_error"] = str(e)
        
        return analysis
    
    def process_message(self, message: str, sender: str, silent: bool = False):
        """Override to handle file URLs in messages."""
        try:
            # Extract file URLs from the message
            words = message.split()
            file_urls = [word for word in words if word.startswith('file:///')]
            
            if file_urls:
                response = "I found the following files and their content:\n\n"
                for file_url in file_urls:
                    analysis = self.analyze_file_content(file_url)
                    response += f"File: {analysis['filename']}\n"
                    response += f"Path: {analysis['path']}\n"
                    
                    if analysis.get("error"):
                        response += f"Error: {analysis['error']}\n"
                    else:
                        response += f"Type: {analysis['metadata'].get('type', 'unknown')}\n"
                        response += f"Size: {analysis['metadata'].get('size', 0)} bytes\n"
                        response += f"Last Modified: {analysis['metadata'].get('modified', 'unknown')}\n"
                        
                        if analysis.get("language"):
                            response += f"Language: {analysis['language']}\n"
                            if analysis.get("functions"):
                                response += "Functions:\n"
                                for func in analysis['functions']:
                                    response += f"- {func}\n"
                            if analysis.get("classes"):
                                response += "Classes:\n"
                                for cls in analysis['classes']:
                                    response += f"- {cls}\n"
                        
                        response += f"\nContent Preview:\n{analysis['content_preview']}\n"
                    
                    response += "\n---\n\n"
                
                # Add file analysis to the message
                message = f"{message}\n\nFile Analysis:\n{response}"
            
            return super().process_message(message, sender, silent)
        except Exception as e:
            if handle_error(e, self.name, self.retry_count):
                self.retry_count += 1
                return self.process_message(message, sender, silent)
            raise

class CoordinatedGroupChat(GroupChat):
    """Enhanced GroupChat with role-based coordination."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.phase = "planning"
        self.success_criteria = []
        self.error_count = 0
        
    def select_speaker(self, *args, **kwargs):
        """Enhanced speaker selection based on current phase and expertise."""
        if self.phase == "planning":
            return next(agent for agent in self.agents if "assistant" in agent.name)
        elif self.phase == "implementation":
            return next(agent for agent in self.agents if "coder" in agent.name)
        elif self.phase == "review":
            return next(agent for agent in self.agents if "reviewer" in agent.name)
        return super().select_speaker(*args, **kwargs)
    
    def run_chat(self, *args, **kwargs):
        """Run chat with error handling and recovery."""
        try:
            return super().run_chat(*args, **kwargs)
        except Exception as e:
            self.error_count += 1
            if self.error_count < MAX_RETRIES:
                logging.warning(f"Error in group chat: {str(e)}. Retrying...")
                return self.run_chat(*args, **kwargs)
            raise

class CoordinatedManager(GroupChatManager):
    """Enhanced manager for coordinated chat."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.checkpoints = []
        
    def process_message(self, message: str, sender: str, silent: bool = False):
        """Enhanced message processing with phase management."""
        try:
            if "PHASE:" in message:
                self.groupchat.phase = message.split("PHASE:")[1].split()[0]
            return super().process_message(message, sender, silent)
        except Exception as e:
            logging.error(f"Error in message processing: {str(e)}")
            return self.initiate_recovery()
            
    def initiate_recovery(self) -> str:
        """Recover from errors by returning to last checkpoint."""
        if self.checkpoints:
            last_checkpoint = self.checkpoints[-1]
            logging.info(f"Recovering to checkpoint: {last_checkpoint['phase']}")
            self.groupchat.phase = last_checkpoint['phase']
            return f"Returning to {last_checkpoint['phase']} phase. Last stable state: {last_checkpoint['message']}"
        return "Restarting conversation from beginning."

def create_progress_tracker() -> Dict[str, List[str]]:
    """Create a progress tracker for monitoring task completion."""
    return {
        "completed_tasks": [],
        "pending_tasks": [],
        "current_phase": None
    }

def monitor_conversation(messages: List[Dict], max_silence: int = 3) -> bool:
    """Monitor conversation health and detect stalls."""
    silence_count = 0
    for msg in messages[-max_silence:]:
        if not msg.get("content", "").strip():
            silence_count += 1
    if silence_count >= max_silence:
        logging.warning("Conversation may be stalled. Initiating recovery...")
        return True
    return False
