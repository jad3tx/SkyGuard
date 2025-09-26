#!/usr/bin/env python3
"""
Inspect the AirBirds dataset structure to understand its format.
"""

from datasets import load_dataset
import json


def inspect_dataset():
    """Inspect the AirBirds dataset structure."""
    print("🔍 Inspecting AirBirds dataset structure...")
    
    try:
        # Load the dataset
        dataset = load_dataset("auniquesun/AirBirds")
        
        print(f"✅ Dataset loaded successfully!")
        print(f"Available splits: {list(dataset.keys())}")
        
        # Inspect each split
        for split_name, split_data in dataset.items():
            print(f"\n📊 Split: {split_name}")
            print(f"   - Number of samples: {len(split_data)}")
            
            if len(split_data) > 0:
                # Get first sample
                sample = split_data[0]
                print(f"   - Sample keys: {list(sample.keys())}")
                
                # Show sample structure
                for key, value in sample.items():
                    if key == 'image':
                        print(f"   - {key}: PIL Image, size: {value.size}")
                    elif key == 'label':
                        print(f"   - {key}: {type(value)} - {value}")
                    else:
                        print(f"   - {key}: {type(value)} - {str(value)[:100]}...")
        
        # Check if there are any features defined
        if hasattr(dataset, 'features'):
            print(f"\n🔧 Dataset features: {dataset.features}")
        
        return dataset
        
    except Exception as e:
        print(f"❌ Error loading dataset: {e}")
        return None


def main():
    """Main function."""
    dataset = inspect_dataset()
    
    if dataset:
        print("\n✅ Dataset inspection complete!")
        print("\nNext steps:")
        print("1. The dataset appears to only have a 'test' split")
        print("2. We need to modify our script to handle this structure")
        print("3. We can use the test split for both training and validation")
    else:
        print("\n❌ Failed to inspect dataset")


if __name__ == "__main__":
    main()
