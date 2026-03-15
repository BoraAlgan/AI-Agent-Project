# Career Assistant AI Agent - Project Report
**Author:** Bora Algan

## 0. Setup & Execution Guide
Below are the instructions to build and run this project locally:

1. **Install Dependencies:**
   Ensure you have Python 3.9+ installed. Run the following command to install required libraries securely:
   ```bash
   pip install -r requirements.txt
   ```
2. **Environment Variables:**
   Create a `.env` file in the root directory and add your OpenRouter API Key:
   `OPENROUTER_API_KEY=your_api_key_here`
3. **Run the Application (Server Mode):**
   This project is built on FastAPI. To start the live server with the custom Web UI, run:
   ```bash
   uvicorn main:app --reload
   ```
   Open your browser and navigate to `http://127.0.0.1:8000/` to test the Web Client.
4. **Run the Application (CLI Mode):**
   If you prefer to see terminal outputs for the strictly hardcoded test cases, you can simply run:
   ```bash
   python main.py
   ```

## 1. Design Decisions
The architecture of this Career Agent follows an **Agent-Evaluator (Critic)** design pattern heavily inspired by modern AI Engineering principles, such as those covered in *The Complete Agentic AI Engineering Course*.

*   **FastAPI Backend & Custom Front-End:** The project was encapsulated in a robust Python FastAPI backend (`POST /chat`). Instead of relying on standard Swagger UI which leaks unnecessary JSON/cURL data, a pristine, custom-coded HTML/CSS/JS frontend was deployed on the root (`GET /`). This provides a seamless, proxy-like user experience.
*   **Prompt Engineering & Persona:** The Primary Agent's prompt forces it to act strictly as a proxy (Bora's representative). Chatbot-like interactions ("How can I help you today?") are explicitly banned to maintain a professional proxy persona.
*   **Decoupled Tools & UI Integration:** We separated tools conceptually into `send_email_notification` (for Salary, Meeting requests, or Direct Contact) and `send_mobile_notification` (for general API-based push rules). Their real-time execution logs are pushed directly to the front-end UI under the "🔔 Triggered Tools" section for transparent demonstration.

## 2. Bonus Features Implemented
According to the assignment guidelines, several bonus features were successfully integrated to make the system more advanced:
*   **Bonus 1 - Continuous Conversation Memory:** A `MemoryManager` class was created to append a sliding-window interaction history (the last 10 messages) to the system prompt. This ensures the agent remembers context across multiple dialogue turns.
*   **Bonus 2 - Live Custom Web Client:** The backend serves a pure, no-dependency custom HTML interface that prevents users from wrestling with API documentation tools like Swagger/cURL.
*   **Bonus 3 - AI Reflection (Self-Correction Loop):** If the Evaluator Agent scores the draft below 8/10, the system automatically loops back, feeds the evaluator's critique into the main agent, and forces a rewrite completely automatically before returning a response to the user.

## 3. Evaluation Strategy
A **Self-Critic / LLM-as-a-Judge** strategy was implemented. Before an employer receives a response, a hidden Evaluator Agent reviews the Primary Agent's response.
*   **Criteria assessed:** Professional Tone, Clarity, Completeness, Safety (No hallucinations), and Relevance.
*   **Strict JSON Parsing:** The evaluator is forced to output a JSON object containing a `score`, `decision` (PASSED / REVISE), and `feedback`.
*   **UI Transparency:** The Evaluator's score and final decision are surfaced directly on the HTML frontend inside a dedicated "🕵️ Evaluator Score" box, allowing the user/instructor to visually confirm the inner workings of the agent without looking at the terminal.

## 4. Failure Cases Analyzed
During development, the following edge cases were handled:
*   **Hallucination on Unknowns:** Employers asking deeply personal, legal, or non-technical questions (e.g., "Favorite football team"). The agent avoids inventing facts and triggers the **Unknown Question Alert** Tool.
*   **Unwanted Polite Tails:** LLMs naturally tend to append "Bana başka bir sorunuz var mı?" (Do you have any other questions?). This was aggressively mitigated in the system prompt protocols.
*   **Execution Orders:** Ensuring that Mobile and Email tools are captured and logged in the correct chronological order so that escalations (like sending an email) appear as the final step in the process.

## 5. Reflection
The assignment successfully demonstrates a Human-in-the-Loop AI system handling uncertainty gracefully. By leveraging techniques from the Agentic AI Engineering Course and building a custom web client, the system goes beyond a terminal wrapper—it acts autonomously while still deferring high-risk topics (like salary negotiation and unknown edge cases) directly to the user through simulated UI-visible mobile and email alerts. It perfectly demonstrates the value of the "Evaluator-Optimizer" routine in agentic design.
