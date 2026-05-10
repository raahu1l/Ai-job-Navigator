#!/usr/bin/env python3
"""Test script to verify stability fixes."""

import sys
sys.path.insert(0, 'Backend')

# Test imports
try:
    from matcher import analyze
    from skill_domain import normalize_user_skills_list
    print("✓ Imports successful")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test 1: Empty skills
print("\nTest 1: Empty skills")
result = analyze([])
assert isinstance(result, dict), "Should return dict for empty skills"
assert "message" in result, "Should have message"
print(f"✓ Empty skills handled: {result.get('message')[:50]}...")

# Test 2: Invalid job results (None)
print("\nTest 2: Invalid job results")
result = analyze(["Python"], None)
assert isinstance(result, (dict, list)), "Should return dict or list"
print("✓ None job_results handled")

# Test 3: Empty job results list
print("\nTest 3: Empty job results list")
result = analyze(["Python"], [])
assert isinstance(result, (dict, list)), "Should return dict or list"
print("✓ Empty job_results list handled")

# Test 4: Malformed job
print("\nTest 4: Malformed job in results")
malformed_jobs = [
    {"job_id": "1", "title": None, "company": None, "description": None},
    {"job_id": "2"},  # Missing required fields
    {"job_id": "3", "title": "Python Developer", "company": "TechCorp"},
]
result = analyze(["Python"], malformed_jobs)
assert isinstance(result, (dict, list)), "Should handle malformed jobs"
print("✓ Malformed jobs handled gracefully")

# Test 5: User skill normalization
print("\nTest 5: User skill normalization")
normalized = normalize_user_skills_list(["Python , SQL,, Docker"])
print(f"  Input: ['Python , SQL,, Docker']")
print(f"  Output: {normalized}")
assert len(normalized) == 3, "Should have 3 skills"
print("✓ Multiple comma handling works")

# Test 6: Duplicate skills
print("\nTest 6: Duplicate skill handling")
normalized = normalize_user_skills_list(["Python", "python", "PYTHON"])
print(f"  Input: ['Python', 'python', 'PYTHON']")
print(f"  Output: {normalized}")
assert len(normalized) <= 1, "Should deduplicate"
print("✓ Duplicate skills deduplicated")

# Test 7: Mixed input
print("\nTest 7: Mixed comma and space separated")
normalized = normalize_user_skills_list(None, "Python, JavaScript AWS Docker")
print(f"  Input: 'Python, JavaScript AWS Docker'")
print(f"  Output: {normalized}")
assert len(normalized) >= 3, "Should parse mixed separators"
print("✓ Mixed separator handling works")

print("\n" + "="*50)
print("All stability tests passed! ✓")
print("="*50)
