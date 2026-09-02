import os
from memory import init_db, make_context
from core import process_input

def main():
    init_db()
    ctx = make_context()
    
    print("E.D.I.T.H. online. Type 'exit' to shut down.\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in {"exit", "quit"}:
                print("EDITH: Goodbye.")
                break
                
            if not user_input:
                continue
                
            result = process_input(user_input, ctx)
            print(f"EDITH: {result['response']}\n")
            
        except (KeyboardInterrupt, EOFError):
            print("\nEDITH: Goodbye.")
            break
        except Exception as e:
            print(f"EDITH: [System Error] {e}\n")

if __name__ == "__main__":
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("WARNING: ANTHROPIC_API_KEY is not set. Complex intents will fail.\n")
    main()