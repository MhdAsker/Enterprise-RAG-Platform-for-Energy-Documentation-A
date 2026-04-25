"""Debug version to see what's happening"""
import sys
import traceback

print("=" * 70)
print("DEBUG: Starting FastAPI server...")
print("=" * 70)

try:
    print("\n1. Importing FastAPI...")
    from fastapi import FastAPI
    print("   OK")

    print("\n2. Importing RetrievalPipeline...")
    from energy_docs_chat.src.chat_with_doc.retrieval import RetrievalPipeline
    print("   OK")

    print("\n3. Initializing RetrievalPipeline (this takes ~10 seconds)...")
    pipeline = RetrievalPipeline()
    print("   OK")

    print("\n4. Building RAG chain...")
    rag_chain = pipeline.build_chain()
    print("   OK")

    print("\n5. Importing main app...")
    import main
    print("   OK")

    print("\n6. Starting server with uvicorn...")
    import uvicorn
    uvicorn.run(
        main.app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

except Exception as e:
    print(f"\n{'-'*70}")
    print("ERROR OCCURRED:")
    print(f"{'-'*70}")
    print(f"Error type: {type(e).__name__}")
    print(f"Error message: {str(e)}")
    print(f"\nFull traceback:")
    traceback.print_exc()
    sys.exit(1)
