import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
# NEW: Import for token usage and cost tracking
from langchain_community.callbacks import OpenAICallbackHandler

# --- 0. INITIAL CONFIGURATION ---
load_dotenv()

INPUT_DIRECTORY = os.getenv("INPUT_PATH")
OUTPUT_DIRECTORY = os.getenv("OUTPUT_PATH")

llm = AzureChatOpenAI(
    azure_deployment="gpt-4o-mini",
)

def find_files_with_keywords(directory_path: str, keywords: list[str]) -> list[str]:
    """Searches for files in a directory that contain any of the specified keywords."""
    if not directory_path or not os.path.isdir(directory_path):
        print(f"Error: Input directory not found. Check INPUT_PATH in your .env file.")
        return []
    print(f"Searching for files in '{directory_path}'...")
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
                except Exception as e:
                    print(f"Could not read file {file_path}: {e}")
    return matched_files

def read_files_content(file_paths: list[str]) -> str:
    """Reads the content of specified files and concatenates them."""
    print("\nReading content from relevant files...")
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
            except Exception as e:
                print(f"  - Error: Could not read file '{file_path}' with fallback encoding: {e}")
        except Exception as e:
            print(f"  - Error: An unexpected error occurred while reading file '{file_path}': {e}")
        
        if content:
            relative_path = os.path.relpath(file_path, INPUT_DIRECTORY)
            all_content.append(f"--- CONTENT FROM: {relative_path} ---\n\n{content}\n\n")
    return "".join(all_content)

def save_output_to_file(content: str, filename: str):
    """Saves the given content to a file in the output directory."""
    if not OUTPUT_DIRECTORY:
        print("Error: OUTPUT_DIRECTORY not configured in .env file.")
        return
    
    file_path = os.path.join(OUTPUT_DIRECTORY, filename)
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"\n✅ Successfully saved file to: {file_path}")
    except Exception as e:
        print(f"\n❌ Error saving file to {file_path}: {e}")

def setup_output_directory(directory_path: str):
    """Checks if the output directory exists and creates it if it doesn't."""
    if not directory_path:
        print("Error: Output directory not configured. Check OUTPUT_PATH.")
        return False
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
    return True

# This block will only run when you execute the script directly
if __name__ == "__main__":
    BUSINESS_LOGIC_KEYWORDS = [
        "class", "entity", "relationship"
    ]

    if setup_output_directory(OUTPUT_DIRECTORY):
        relevant_files = find_files_with_keywords(INPUT_DIRECTORY, BUSINESS_LOGIC_KEYWORDS)

        if relevant_files:
            print("\n✅ Found relevant files:")
            for file_path in relevant_files:
                print(f"  - {os.path.relpath(file_path, INPUT_DIRECTORY)}")
            
            documentation_content = read_files_content(relevant_files)
            
            if documentation_content:
                # Create an instance of the callback handler to track usage
                cb = OpenAICallbackHandler()

                # --- ESLABÓN 1: ANÁLISIS GENERAL DE LA LÓGICA DE NEGOCIO ---
                analysis_prompt = ChatPromptTemplate.from_template(
                    "You are an expert software architect. Analyze the following documentation content "
                    "and provide a concise summary of the business logic. Identify the main domain entities, "
                    "their key properties, and the relationships between them.\n\n"
                    "Documentation Content:\n{content}"
                )
                analysis_chain = analysis_prompt | llm
                print("\n🤖 Sending content to the AI for general analysis...")
                # Add config for tracking
                analysis_result = analysis_chain.invoke(
                    {"content": documentation_content},
                    config={"callbacks": [cb]}
                )
                print("\n--- AI Business Logic Analysis ---")
                print(analysis_result.content)
                print("------------------------------------")

                # --- ESLABÓN 2: GENERACIÓN DEL ARCHIVO entities.md ---
                entities_prompt = ChatPromptTemplate.from_template(
                    "You are a technical writer creating documentation. Based on the provided documentation, "
                    "generate the content for a markdown file named 'entities.md'. The file should list all "
                    "domain entities, their properties with data types, and their relationships. "
                    "Use the following format exactly:\n\n"
                    "Entities:\n"
                    "- EntityName:\n"
                    "  - Properties:\n"
                    "    - `PropertyName` (type)\n"
                    "  - Relationships:\n"
                    "    - `RelationshipName` (RelatedEntity)\n\n"
                    "Here is the documentation to analyze:\n{content}"
                )
                entities_chain = entities_prompt | llm
                print("\n🤖 Asking AI to generate entities.md content...")
                # Add config for tracking
                entities_result = entities_chain.invoke(
                    {"content": documentation_content},
                    config={"callbacks": [cb]}
                )
                
                save_output_to_file(entities_result.content, "entities.md")
                
                # --- ESLABÓN 3: GENERACIÓN DE LA ESTRUCTURA DEL PROYECTO ---
                structure_prompt = ChatPromptTemplate.from_template(
                    "You are a senior software architect designing a template for new projects. "
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
                    "```"
                )
                structure_chain = structure_prompt | llm
                print("\n🤖 Asking AI to generate generic project_structure.md content...")
                structure_result = structure_chain.invoke(
                    {},
                    config={"callbacks": [cb]}
                )
                save_output_to_file(structure_result.content, "project_structure.md")

                # NEW: Print final cost and token usage from all three calls
                print("\n--- 📊 Token Usage and Cost (Total) ---")
                print(f"Input Tokens: {cb.prompt_tokens}")
                print(f"Output Tokens: {cb.completion_tokens}")
                print(f"Total Tokens: {cb.total_tokens}")
                print(f"Total Cost (USD): ${cb.total_cost:.6f}")
                print("---------------------------------")
        else:
            print("\n❌ No relevant files found.")