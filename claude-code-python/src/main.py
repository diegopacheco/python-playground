import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def read_file(path: str) -> str:
    try:
        with open(path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

def list_files(path: str = ".") -> list:
    try:
        entries = []
        for entry in os.listdir(path):
            full_path = os.path.join(path, entry)
            entry_type = "dir" if os.path.isdir(full_path) else "file"
            entries.append({"name": entry, "type": entry_type})
        return entries
    except Exception as e:
        return [{"error": str(e)}]

def edit_file(path: str, content: str) -> str:
    try:
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        with open(path, 'w') as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

tools = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file at the given path",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The file path to read"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and directories at the given path",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The directory path to list", "default": "."}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Create or overwrite a file with the given content",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The file path to write"},
                    "content": {"type": "string", "description": "The content to write to the file"}
                },
                "required": ["path", "content"]
            }
        }
    }
]

TOOL_REGISTRY = {
    "read_file": read_file,
    "list_files": list_files,
    "edit_file": edit_file
}

SYSTEM_PROMPT = """You are a helpful coding assistant. You can read files, list directories, and edit files to help users with their coding tasks. Always explain what you're doing before taking actions."""

def execute_tool(name: str, arguments: dict) -> str:
    if name not in TOOL_REGISTRY:
        return f"Unknown tool: {name}"
    func = TOOL_REGISTRY[name]
    result = func(**arguments)
    if isinstance(result, (dict, list)):
        return json.dumps(result, indent=2)
    return str(result)

def chat(messages: list) -> tuple:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    return response.choices[0].message, response.choices[0].finish_reason

def agent_loop():
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    print("Simple Code Assistant (type 'quit' to exit)")
    print("-" * 50)

    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})

        while True:
            assistant_message, finish_reason = chat(messages)
            messages.append(assistant_message)

            if assistant_message.content:
                print(f"\nAssistant: {assistant_message.content}")

            if not assistant_message.tool_calls:
                break

            for tool_call in assistant_message.tool_calls:
                name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                print(f"\n[Calling {name} with {args}]")
                result = execute_tool(name, args)
                print(f"[Result: {result[:200]}{'...' if len(result) > 200 else ''}]")
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })

if __name__ == "__main__":
    agent_loop()
