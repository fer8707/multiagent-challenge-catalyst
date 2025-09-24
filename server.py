import os
import uvicorn
import json
from dotenv import load_dotenv
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.callbacks import OpenAICallbackHandler

load_dotenv()
app = FastAPI()

origins = [
    "http://localhost:5173", # Default port for Vite React apps
    "http://localhost:3000", # Default port for Create React App
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm = AzureChatOpenAI(
    azure_deployment="gpt-4o-mini",
)

class AnalysisRequest(BaseModel):
    input_path: str
    output_path: str
    keywords: list[str]

def find_files_with_keywords(directory_path: str, keywords: list[str]) -> list[str]:
    matched_files = []
    for root, dirs, files in os.walk(directory_path):
        for filename in files:
            if filename.endswith(('.md', '.txt', '.cs')):
                file_path = os.path.join(root, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if any(keyword in content for keyword in keywords):
                            matched_files.append(file_path)
                except Exception:
                    pass
    return matched_files

def read_files_content(file_paths: list[str], base_directory: str) -> str:
    all_content = []
    for file_path in file_paths:
        content = ""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='cp1252') as file:
                    content = file.read()
            except Exception:
                content = f"Error reading file: {file_path}"
        except Exception:
            content = f"Error reading file: {file_path}"
        
        relative_path = os.path.relpath(file_path, base_directory)
        all_content.append(f"--- CONTENT FROM: {relative_path} ---\n\n{content}\n\n")
    return "".join(all_content)

def save_output_to_file(content: str, filename: str, output_directory: str):
    # ... (sin cambios)
    file_path = os.path.join(output_directory, filename)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

async def analysis_pipeline(request: AnalysisRequest):
    # ... (sin cambios)
    input_dir = request.input_path
    output_dir = request.output_path
    keywords = request.keywords

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    yield {"event": "log", "data": f"Searching for files in '{input_dir}'..."}
    relevant_files = find_files_with_keywords(input_dir, keywords)
    if not relevant_files:
        yield {"event": "error", "data": "No relevant files found."}
        return
    yield {"event": "log", "data": f"✅ Found {len(relevant_files)} relevant files."}

    yield {"event": "log", "data": "Reading file contents..."}
    documentation_content = read_files_content(relevant_files, input_dir)
    
    cb = OpenAICallbackHandler()

    try:
        # Eslabón 1
        yield {"event": "log", "data": "🤖 Sending content to AI for general analysis..."}
        analysis_prompt = ChatPromptTemplate.from_template("You are an expert software architect. Analyze the following documentation content "
                    "and provide a concise summary of the business logic. Identify the main domain entities, "
                    "their key properties, and the relationships between them.\n\n"
                    "Documentation Content:\n{content}") # Analysis prompt
        analysis_chain = analysis_prompt | llm
        analysis_result = await analysis_chain.ainvoke({"content": documentation_content}, config={"callbacks": [cb]})
        yield {"event": "log", "data": "Analysis summary received."}

        # Eslabón 2
        yield {"event": "log", "data": "🤖 Asking AI to generate entities.md..."}
        entities_prompt = ChatPromptTemplate.from_template("You are a technical writer creating documentation. Based on the provided documentation, "
                    "generate the content for a markdown file named 'entities.md'. The file should list all "
                    "domain entities, their properties with data types, and their relationships. "
                    "Use the following format exactly:\n\n"
                    "Entities:\n"
                    "- EntityName:\n"
                    "  - Properties:\n"
                    "    - `PropertyName` (type)\n"
                    "  - Relationships:\n"
                    "    - `RelationshipName` (RelatedEntity)\n\n"
                    "Here is the documentation to analyze:\n{content}") # Entities prompt
        entities_chain = entities_prompt | llm
        entities_result = await entities_chain.ainvoke({"content": documentation_content}, config={"callbacks": [cb]})
        save_output_to_file(entities_result.content, "entities.md", output_dir)
        yield {"event": "log", "data": "✅ entities.md file saved."}
        
        # Eslabón 3
        yield {"event": "log", "data": "🤖 Asking AI to generate project_structure.md..."}
        structure_prompt = ChatPromptTemplate.from_template("You are a senior software architect designing a template for new projects. "
                    "Your task is to generate a generic and well-organized project structure for a standard Java Spring Boot application. "
                    "This structure should follow industry best practices for maintainability and scalability. "
                    "Instead of using specific entity names (like 'Article'), use generic placeholder names like '<EntityName>' "
                    "for the example files (e.g., '<EntityName>Controller.java', '<EntityName>Repository.java'). "
                    "Also, include a brief, one-line description for the purpose of each main package (controller, model, repository, service). "
                    "Format the output exactly like the example provided.\n\n"
                    "## Required Project Structure\n"
                    "Organize project to enhance maintainability and scalability.\n\n"
                    "```\n"
                    "sandbox/project/\n"
                    "├── src/\n"
                    "│   └── main/\n"
                    "│       ├── java/\n"
                    "│       │   └── com/\n"
                    "│       │       └── example/\n"
                    "│       │           └── project/\n"
                    "│       │               ├── controller/  // Handles incoming HTTP requests and routes them.\n"
                    "│       │               │   └── <EntityName>Controller.java\n"
                    "│       │               ├── model/       // Contains the domain objects or entities.\n"
                    "│       │               │   └── <EntityName>.java\n"
                    "│       │               ├── repository/  // Handles data persistence and database operations.\n"
                    "│       │               │   └── <EntityName>Repository.java\n"
                    "│       │               ├── service/     // Contains the core business logic.\n"
                    "│       │               │   └── <EntityName>Service.java\n"
                    "│       │               └── Application.java\n"
                    "│       └── resources/\n"
                    "│           └── application.properties\n"
                    "└── pom.xml\n"
                    "```") # Structure prompt
        structure_chain = structure_prompt | llm
        structure_result = await structure_chain.ainvoke({}, config={"callbacks": [cb]})
        save_output_to_file(structure_result.content, "project_structure.md", output_dir)
        yield {"event": "log", "data": "✅ project_structure.md file saved."}

    except Exception as e:
        yield {"event": "error", "data": f"An error occurred during AI processing: {str(e)}"}
        return
    
    cost_summary = (f"Analysis complete. Input Tokens: {cb.prompt_tokens}, " f"Output Tokens: {cb.completion_tokens}, " f"Total Cost (USD): ${cb.total_cost:.6f}")
    yield {"event": "done", "data": cost_summary}


def params_from_query(request_body: str) -> AnalysisRequest:
    return AnalysisRequest.model_validate_json(request_body)

@app.get("/analyze")
async def stream_analysis(request: AnalysisRequest = Depends(params_from_query)):
    return EventSourceResponse(analysis_pipeline(request))

if __name__ == "__main__":
    print("Starting API server with CORS enabled...")
    uvicorn.run(app, host="127.0.0.1", port=8000)