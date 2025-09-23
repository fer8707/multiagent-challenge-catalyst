## create .env
AZURE_OPENAI_API_KEY=""
AZURE_OPENAI_ENDPOINT=""
OPENAI_API_VERSION=""
INPUT_PATH=""
OUTPUT_PATH=""

## init virtual enviroment
uv venv
## Activate virtual enviroment
.venv\Scripts\activate
## Install dependencies
uv pip install langchain langchain-openai python-dotenv langchain-community
## Start
python main.py