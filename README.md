# Privacy Agent Backend

## Description

This project is the backend for the Privacy Agent, responsible for handling data processing, API interactions, agent management, and knowledge base operations.

## Project Setup

1. **Docker Installation:** Ensure you have Docker installed on your machine. You can download it from the official Docker website.
2. **Environment Variables:**
    * Set the `OPENAI_API_KEY` environment variable with your OpenAI API key.
    * Set the `GEMINI_API_KEY` environment variable with your Gemini API key.
3. **Building the Docker Image:**
    * Navigate to the project root directory in your terminal.
    * Run the command `docker-compose build` to build the Docker image.
4. **Running the Dev Container:**
    * Run the command `docker-compose up -d` to start the dev container in detached mode. If you want to use an interactive mode, you can use the command: `docker run -it -p 8000:8000 -v $(pwd):/app --name privicyagentbackend-dev privicyagentbackend:latest bash`
5. **Run the server:** If you are in the container run `uvicorn app:app --host 0.0.0.0 --port 8000`

## Project Structure

* **`agents/`:** Contains the different agent implementations.
    * `facts_checker_agent.py`: Agent for checking facts.
    * `legal_agent.py`: Agent for legal-related tasks.
    * `websearch_agent.py`: Agent for web searches.
* **`knowledge_base/`:** Contains the knowledge management logic.
    * `indexing.py`: Code for indexing knowledge.
    * `retrieval.py`: Code for retrieving knowledge.
* **`utils/`:** Contains utility functions and helpers.
    * `api_helpers.py`: Utility functions for API interactions.
    * `data_processing.py`: Utility functions for data processing.
* **`src/`:** Contains core application logic
    * `privicyagentbackend/__init__.py`: Marks the `privicyagentbackend` directory as a Python package.
* **`app.py`:** Main entry point of the application.
* **`.idx/dev.nix`:** File with the development configurations for the current project, with Nix.
* **`docker-compose.yml`:** File with the Docker Compose configurations.
* **`pyproject.toml`:** File with project metadata, build system, and dependency management.