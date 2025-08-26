#!/usr/bin/env python3
"""Quick test after cleanup"""

print("🧪 Testing imports after cleanup...")

try:
    # Test core imports
    from shared.core import ChatMessage, Provider, DEFAULT_PROVIDER
    print("✓ Core imports working")
    
    # Test LLM imports  
    from shared.llm import LLM, LLMConfig
    print("✓ LLM imports working")
    
    # Test utils imports
    from shared.utils import setup_logging, create_base_parser, save_output
    print("✓ Utils imports working")
    
    # Test configuration
    config = LLMConfig.from_env()
    print(f"✓ Configuration working: {config.provider}/{config.model}")
    
    # Test LLM creation
    llm = LLM(config)
    print("✓ LLM creation working")
    
    print(f"\n📊 Summary:")
    print(f"   Default provider: {DEFAULT_PROVIDER}")
    print(f"   Available providers: {[p.value for p in Provider]}")
    print(f"   Current config: {config.provider} ({config.model})")
    
    print("\n🎉 All tests passed! Cleanup was successful.")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
