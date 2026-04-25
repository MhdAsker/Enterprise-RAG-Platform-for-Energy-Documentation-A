from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

def get_contextualize_q_prompt() -> ChatPromptTemplate:
    """
    Prompt used by the History-Aware Retriever.
    It analyzes the chat history and the latest question and rewrites it to be:
    1. A standalone question (replaces pronouns like "it", "that")
    2. More specific for vector search (expands vague terms)
    """
    system_prompt = (
        "Given a chat history and the latest user question, formulate a standalone question that:\n"
        "1. Can be understood without reading the chat history\n"
        "2. Replaces pronouns ('it', 'that', 'this') with specific nouns from context\n"
        "3. Expands vague terms with related technical keywords for better retrieval\n\n"
        "CRITICAL RULES:\n"
        "- Do NOT answer the question\n"
        "- Do NOT include filler like 'Here is the reformulated question:'\n"
        "- ONLY return the precise standalone question text\n"
        "- Keep the technical domain (energy/power systems) in mind"
    )
    return ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{question}"),
    ])


def get_qa_prompt() -> ChatPromptTemplate:
    """
    The primary Generative RAG Prompt.
    Injects the retrieved documents into the context and guides the LLM
    to synthesize answers from them intelligently.
    """
    system_template = (
        "You are an expert Energy Analyst and AI assistant specializing in power grid systems and frequency regulations.\n\n"
        "Your task: Answer the user's technical question using ONLY information from the provided context.\n\n"
        "Important guidelines:\n"
        "1. Synthesize information from the retrieved documents to provide a comprehensive answer\n"
        "2. If the context contains relevant information (even if fragmentary), synthesize it into a coherent answer\n"
        "3. Cite specific values, ranges, or parameters when available (e.g., 'According to the documents, the standard frequency range is ±50 mHz...')\n"
        "4. If the context contains related information but the exact question is vague, provide the closest match and clarify what you found\n"
        "   Example: If asked 'what is safe frequency?' but context discusses 'frequency ranges' and 'deviations', explain: 'The documents don't define a single safe frequency, but rather specify frequency ranges and maximum deviations...'\n"
        "5. If the context genuinely does NOT contain information relevant to answering the question, say: 'I cannot find sufficient information to answer this question in the provided documents.'\n"
        "6. Never invent information not present in the documents\n\n"
        "Context from Documents:\n"
        "{context}"
    )
    return ChatPromptTemplate.from_messages([
        ("system", system_template),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}")
    ])
