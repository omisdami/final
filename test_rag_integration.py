#!/usr/bin/env python3
"""
RAG Parameter Integration Test Script

This script verifies that the RAG parameter system is working correctly
by testing the configuration models, presets, and validation.
"""

import sys
from core.config.rag_config import RagParameters, RagPreset


def test_default_parameters():
    """Test default parameter initialization"""
    print("Testing default parameters...")
    params = RagParameters()

    assert params.similarity_threshold == 0.6, "Default threshold should be 0.6"
    assert params.top_k == 5, "Default top_k should be 5"
    assert params.chunk_size == 512, "Default chunk_size should be 512"
    assert params.overlap == 15, "Default overlap should be 15"

    print("✓ Default parameters initialized correctly")
    return True


def test_custom_parameters():
    """Test custom parameter creation"""
    print("\nTesting custom parameters...")
    params = RagParameters(
        similarity_threshold=0.75,
        top_k=8,
        chunk_size=1024,
        overlap=20
    )

    assert params.similarity_threshold == 0.75
    assert params.top_k == 8
    assert params.chunk_size == 1024
    assert params.overlap == 20

    print("✓ Custom parameters created successfully")
    return True


def test_parameter_validation():
    """Test parameter validation"""
    print("\nTesting parameter validation...")

    # Test invalid similarity threshold
    try:
        params = RagParameters(similarity_threshold=1.5)
        print("✗ Should have raised validation error for threshold > 1.0")
        return False
    except Exception as e:
        print(f"✓ Correctly rejected invalid threshold: {type(e).__name__}")

    # Test invalid top_k
    try:
        params = RagParameters(top_k=100)
        print("✗ Should have raised validation error for top_k > 50")
        return False
    except Exception as e:
        print(f"✓ Correctly rejected invalid top_k: {type(e).__name__}")

    # Test invalid chunk_size
    try:
        params = RagParameters(chunk_size=50)
        print("✗ Should have raised validation error for chunk_size < 100")
        return False
    except Exception as e:
        print(f"✓ Correctly rejected invalid chunk_size: {type(e).__name__}")

    # Test invalid overlap
    try:
        params = RagParameters(overlap=75)
        print("✗ Should have raised validation error for overlap > 50")
        return False
    except Exception as e:
        print(f"✓ Correctly rejected invalid overlap: {type(e).__name__}")

    return True


def test_presets():
    """Test preset configurations"""
    print("\nTesting presets...")

    # Test Default preset
    default = RagPreset.get_preset("default")
    assert default.similarity_threshold == 0.6
    assert default.top_k == 5
    assert default.chunk_size == 512
    assert default.overlap == 15
    print("✓ Default preset correct")

    # Test High Precision preset
    high_precision = RagPreset.get_preset("high_precision")
    assert high_precision.similarity_threshold == 0.8
    assert high_precision.top_k == 3
    assert high_precision.chunk_size == 256
    assert high_precision.overlap == 10
    print("✓ High Precision preset correct")

    # Test Comprehensive preset
    comprehensive = RagPreset.get_preset("comprehensive")
    assert comprehensive.similarity_threshold == 0.5
    assert comprehensive.top_k == 10
    assert comprehensive.chunk_size == 1024
    assert comprehensive.overlap == 20
    print("✓ Comprehensive preset correct")

    # Test Fast preset
    fast = RagPreset.get_preset("fast")
    assert fast.similarity_threshold == 0.7
    assert fast.top_k == 3
    assert fast.chunk_size == 256
    assert fast.overlap == 10
    print("✓ Fast preset correct")

    # Test unknown preset defaults to default
    unknown = RagPreset.get_preset("unknown")
    assert unknown.similarity_threshold == 0.6
    print("✓ Unknown preset correctly defaults to Default")

    return True


def test_model_serialization():
    """Test parameter serialization"""
    print("\nTesting model serialization...")

    params = RagParameters(
        similarity_threshold=0.7,
        top_k=8,
        chunk_size=768,
        overlap=20
    )

    # Test model_dump
    data = params.model_dump()
    assert isinstance(data, dict)
    assert data["similarity_threshold"] == 0.7
    assert data["top_k"] == 8
    assert data["chunk_size"] == 768
    assert data["overlap"] == 20
    print("✓ Model serialization works correctly")

    # Test JSON serialization
    json_str = params.model_dump_json()
    assert isinstance(json_str, str)
    assert "0.7" in json_str
    print("✓ JSON serialization works correctly")

    return True


def test_chunk_overlap_calculation():
    """Test chunk overlap calculation logic"""
    print("\nTesting chunk overlap calculation...")

    params = RagParameters(chunk_size=512, overlap=15)
    overlap_tokens = int(params.chunk_size * (params.overlap / 100.0))
    assert overlap_tokens == 76, f"Expected 76 tokens, got {overlap_tokens}"
    print(f"✓ Overlap calculation correct: {params.chunk_size} * {params.overlap}% = {overlap_tokens} tokens")

    params = RagParameters(chunk_size=1024, overlap=25)
    overlap_tokens = int(params.chunk_size * (params.overlap / 100.0))
    assert overlap_tokens == 256, f"Expected 256 tokens, got {overlap_tokens}"
    print(f"✓ Overlap calculation correct: {params.chunk_size} * {params.overlap}% = {overlap_tokens} tokens")

    return True


def run_all_tests():
    """Run all tests"""
    print("="*60)
    print("RAG Parameter Integration Test Suite")
    print("="*60)

    tests = [
        test_default_parameters,
        test_custom_parameters,
        test_parameter_validation,
        test_presets,
        test_model_serialization,
        test_chunk_overlap_calculation
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except AssertionError as e:
            print(f"\n✗ Test failed: {test.__name__}")
            print(f"  Error: {e}")
            failed += 1
        except Exception as e:
            print(f"\n✗ Test error: {test.__name__}")
            print(f"  Error: {type(e).__name__}: {e}")
            failed += 1

    print("\n" + "="*60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*60)

    if failed == 0:
        print("\n✓ All tests passed! RAG integration is working correctly.")
        return 0
    else:
        print(f"\n✗ {failed} test(s) failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
