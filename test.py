import sys
from energy_docs_chat.src.chat_with_doc.retrieval import RetrievalPipeline
from energy_docs_chat.logger.custom_logger import logger
from energy_docs_chat.exceptions.custom_exception import EnergyDocsException

def run_interactive_test():
    """
    Spins up the terminal interface to test out our newly modularized 
    Conversational RAG pipeline.
    """
    try:
        print("\n" + "="*50)
        print("   Energy Docs Automated RAG Pipeline Test")
        print("="*50 + "\n")
        
        # 1. Initialize the Pipeline (Loads Configs, Models, and DB)
        print("[System] Booting up models and mapping FAISS Database...")
        pipeline = RetrievalPipeline()
        rag_chain = pipeline.build_chain()
        
        session_id = "live_terminal_session"
        print(f"\n[System] Pipeline Ready! Memory session tracking as: '{session_id}'")
        print("[System] Type 'quit' or 'exit' at any time to shut down the connection.\n")
        
        # 2. Infinite Loop to simulate a real chat experience
        while True:
            user_input = input("You: ")
            
            # Safety escape handlers
            if user_input.lower() in ["quit", "exit"]:
                print("\n[System] Closing database connections. Goodbye!")
                break
            if not user_input.strip():
                continue
                
            print("[Groq is analyzing documents...]")
            
            # 3. Native invocation using exactly the dictionary schema we built
            response = rag_chain.invoke(
                {"question": user_input},
                config={"configurable": {"session_id": session_id}}
            )
            
            # 4. Print the final strictly parsed output
            # (In Pure LCEL the response is just the string, not a dictionary!)
            print(f"Groq: {response}\n")
            print("-" * 50)
            
    except Exception as e:
        logger.error("A critical test failure occurred!")
        # Engage our Custom Traceback system
        raise EnergyDocsException(e, sys)

if __name__ == "__main__":
    run_interactive_test()
