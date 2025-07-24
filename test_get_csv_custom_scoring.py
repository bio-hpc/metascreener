#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for get_csv.py custom scoring functionality
Tests the get_score_from_data function independently
"""

import sys
import os
import json
import tempfile
import shutil

# Add the path to import the get_csv module
sys.path.insert(0, 'MetaScreener/extra_metascreener/used_by_metascreener')

from get_csv import get_score_from_data

def create_test_data():
    """Create test JSON data structures for testing"""
    
    # Test data with different scoring fields
    test_data_1 = {
        "global_score": "5.2",
        "global_score_md": "4.8",
        "global_score_qu": "4.5",
        "CNNscore": "0.85",
        "CNNAffinity": "-8.2",
        "CNN_VS": "0.92",
        "graph_global_score": {
            "Gauss1": "-2.1",
            "Repulsion": "1.5",
            "Hydrophobic": "-1.8",
            "Hydrogen_Bonds": "-0.7",
            "Rotational": "0.3",
            "Total_Affinity": "-8.1"
        },
        "coords": [10.5, 20.3, 15.8],
        "file_ori_query": "test_ligand.mol2",
        "num_execution": 1
    }
    
    test_data_2 = {
        "global_score": "6.1",
        "CNNscore": "0.72",
        "CNNAffinity": "-7.5",
        "graph_global_score": {
            "Gauss1": "-1.8",
            "Repulsion": "2.1",
            "Hydrophobic": "-1.2",
            "Hydrogen_Bonds": "-0.5",
            "Rotational": "0.6",
            "Total_Affinity": "-7.2"
        },
        "coords": [12.1, 18.7, 14.2],
        "file_ori_query": "test_ligand2.mol2",
        "num_execution": 2
    }
    
    return test_data_1, test_data_2

def test_default_scoring():
    """Test default scoring hierarchy"""
    print("\n=== Testing Default Scoring Hierarchy ===")
    
    test_data_1, test_data_2 = create_test_data()
    
    # Test hierarchy: global_score_qu > global_score_md > global_score
    score1 = get_score_from_data(test_data_1)
    print(f"Test data 1 - Default score: {score1} (should be 4.5 from global_score_qu)")
    assert score1 == 4.5, f"Expected 4.5, got {score1}"
    
    # Test when global_score_qu is missing
    test_data_2_copy = test_data_2.copy()
    score2 = get_score_from_data(test_data_2_copy)
    print(f"Test data 2 - Default score: {score2} (should be 6.1 from global_score)")
    assert score2 == 6.1, f"Expected 6.1, got {score2}"
    
    print("✅ Default scoring hierarchy test passed")

def test_custom_scoring():
    """Test custom scoring fields"""
    print("\n=== Testing Custom Scoring Fields ===")
    
    test_data_1, test_data_2 = create_test_data()
    
    # Test direct field access
    score_cnn = get_score_from_data(test_data_1, "CNNscore")
    print(f"CNNscore: {score_cnn} (should be 0.85)")
    assert score_cnn == 0.85, f"Expected 0.85, got {score_cnn}"
    
    score_affinity = get_score_from_data(test_data_1, "CNNAffinity")
    print(f"CNNAffinity: {score_affinity} (should be -8.2)")
    assert score_affinity == -8.2, f"Expected -8.2, got {score_affinity}"
    
    # Test graph_global_score field access
    score_gauss = get_score_from_data(test_data_1, "Gauss1")
    print(f"Gauss1: {score_gauss} (should be -2.1)")
    assert score_gauss == -2.1, f"Expected -2.1, got {score_gauss}"
    
    score_hbonds = get_score_from_data(test_data_1, "Hydrogen_Bonds")
    print(f"Hydrogen_Bonds: {score_hbonds} (should be -0.7)")
    assert score_hbonds == -0.7, f"Expected -0.7, got {score_hbonds}"
    
    print("✅ Custom scoring fields test passed")

def test_error_handling():
    """Test error handling for non-existent fields"""
    print("\n=== Testing Error Handling ===")
    
    test_data_1, _ = create_test_data()
    
    try:
        get_score_from_data(test_data_1, "NonExistentField")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"✅ Correctly raised error for non-existent field: {e}")
    
    try:
        get_score_from_data(test_data_1, "NonExistentGraphField")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"✅ Correctly raised error for non-existent graph field: {e}")

def print_usage_examples():
    """Print usage examples for get_csv.py"""
    print("\n=== Usage Examples ===")
    print("Basic usage:")
    print("  python3 get_csv.py experiment_folder/")
    print("")
    print("Custom scoring examples:")
    print("  python3 get_csv.py experiment_folder/ --score-field CNNscore --score-ascending false")
    print("  python3 get_csv.py experiment_folder/ --score-field Gauss1")
    print("  python3 get_csv.py experiment_folder/ --score-field CNNAffinity --score-ascending true")
    print("  python3 get_csv.py experiment_folder/ --score-field Total_Affinity --score-ascending true")

def main():
    print("Testing get_csv.py custom scoring functionality...")
    
    try:
        test_default_scoring()
        test_custom_scoring()
        test_error_handling()
        
        print("\n🎉 All tests passed!")
        print_usage_examples()
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 