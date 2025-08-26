#!/usr/bin/env python3
"""Quick test of refactored imports."""

try:
    from shared.core import ChatMessage, Provider, DEFAULT_PROVIDER
    print("✓ Core imports working")
    
    from shared.llm import LLM, LLMConfig  
    print("✓ LLM imports working")
    
    from shared.utils import setup_logging, create_base_parser
    print("✓ Utils imports working")
    
    print(f"Default provider: {DEFAULT_PROVIDER}")
    print(f"Available providers: {[p.value for p in Provider]}")
    
    print("\n✅ All imports successful! Refactoring is working.")
    
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
