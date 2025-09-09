#!/usr/bin/env python3
"""
Script to convert and split default NFI volume pairlists JSON files to have offset filters for using them with NFI consumer mode setup.

!!! IRRESPONSIBLY VIBECODED AS A SINGLE USE THROWAWAY SCRIPT !!!
!!! CHECK THE RESULTS BEFORE USING IN PRODUCTION SETTING !!!
"""

import ast,json
import re
import os
import sys
import glob
import argparse
from pathlib import Path

def convert_pairlist_files(input_dir, output_dir, number_of_copies):
    """
    Process all pairlist JSON files and convert them to .env format
    """
    # Create output directory if it doesn't exist
    
    full_dir = output_dir + "/producers"
    os.makedirs(full_dir, exist_ok=True)
    
    # Find all JSON files starting with 'pairlist-volume-'
    pattern = os.path.join(input_dir, 'pairlist-volume-*.json')
    json_files = glob.glob(pattern)
    
    for json_file in json_files:
        try:
            # Read the JSON file
            with open(json_file, 'r') as f:
              raw_data = f.read()
              no_comments = re.sub("//.*","",raw_data,flags=re.MULTILINE)
              data = ast.literal_eval(no_comments)
            # Find and modify the VolumePairList entries
            pairlists = data.get('pairlists', [])
            volume_pairlists = [i for i, item in enumerate(pairlists) 
                              if item.get('method') == 'VolumePairList']
            
            # Modify the first VolumePairList
            if volume_pairlists:
                first_idx = volume_pairlists[0]
                if 'number_assets' in pairlists[first_idx]:
                    pairlists[first_idx]['number_assets'] = '${NUM_PAIRS_TO_FILTER:?error}'
            
            # Modify the last VolumePairList (if different from first)
            if len(volume_pairlists) > 1:
                last_idx = volume_pairlists[-1]
                if 'number_assets' in pairlists[last_idx]:
                    pairlists[last_idx]['number_assets'] = '${NUM_PAIRS_TO_TRADE:?error}'
            elif len(volume_pairlists) == 1:
                first_idx = volume_pairlists[0]
                if 'number_assets' in pairlists[first_idx]:
                    pairlists[last_idx]['number_assets'] = '${NUM_PAIRS_TO_TRADE:?error}'
            
            # Convert back to JSON string with proper escaping
            pairlist_json = json.dumps(pairlists, indent=2)
            
            pairlist_json = pairlist_json.replace('"${NUM_PAIRS_TO_FILTER:?error}"', '${NUM_PAIRS_TO_FILTER:?error}')
            pairlist_json = pairlist_json.replace('"${NUM_PAIRS_TO_TRADE:?error}"', '${NUM_PAIRS_TO_TRADE:?error}')
            
            # Escape double quotes for .env file
            escaped_json = pairlist_json.replace('"', '\\"')
            
            # Create the .env content
            env_content_full = f'FREQTRADE__PAIRLISTS="{escaped_json}"\n'
            
            # Generate output filename (capitalize suffix)
            base_name = os.path.basename(json_file)
            env_filename = re.sub(r'\.json$', '', base_name)
            
            # Capitalize the suffix (assuming pattern: pairlist-volume-xyz)
            if '-' in env_filename:
                parts = env_filename.split('-')
                if len(parts) >= 3:
                    parts[-1] = parts[-1].upper()  # Capitalize the last part (like usdt -> USDT)
                    env_filename = '-'.join(parts)

            #for copy_number in range(1, number_of_copies + 1):

            skip_string = '${PRODUCER_NUM_PAIRS_TO_SKIP:?error}'
            take_string = '${PRODUCER_NUM_PAIRS_TO_TAKE:?error}'

            offset_filter = {
                "method": "OffsetFilter",
                "offset": skip_string,
                "number_assets": take_string
            }
            
            pairlists_offset = pairlists + [offset_filter]

            pairlists_offset_json = json.dumps(pairlists_offset, indent=2)

            pairlists_offset_json = pairlists_offset_json.replace('"${NUM_PAIRS_TO_FILTER:?error}"', '${NUM_PAIRS_TO_FILTER:?error}')
            pairlists_offset_json = pairlists_offset_json.replace('"${NUM_PAIRS_TO_TRADE:?error}"', '${NUM_PAIRS_TO_TRADE:?error}')
            pairlists_offset_json = pairlists_offset_json.replace('"' + skip_string + '"', skip_string)
            pairlists_offset_json = pairlists_offset_json.replace('"' + take_string + '"', take_string)
            # Escape double quotes for .env file
            escaped_offset_json = pairlists_offset_json.replace('"', '\\"')
            
            # Create the .env content
            env_content_producer = f'FREQTRADE__PAIRLISTS="{escaped_offset_json}"\n'

            env_filename_producer = env_filename + f"-producer.env"
            env_file_producer_path = os.path.join(f"{output_dir}/producers", env_filename_producer)

            # Write the .env file
            with open(env_file_producer_path, 'w') as f:
                f.write(env_content_producer)

            env_filename += '.env'
            env_file_path = os.path.join(output_dir, env_filename)
            
            # Write the .env file
            with open(env_file_path, 'w') as f:
                f.write(env_content_full)
            
            print(f"Processed: {json_file} -> {env_file_path}")
            
        except Exception as e:
            print(f"Error processing {json_file}: {e}")

def process_pairlist_files(directory, new_number_assets, number_of_copies):
  """
  Process all JSON files starting with 'pairlist-volume-' in the specified directory.
  """

  os.makedirs(directory+"/producers", exist_ok=True)

  # Find all matching files
  pattern = os.path.join(directory, "pairlist-volume-*.json")
  json_files = glob.glob(pattern)

  if not json_files:
      print(f"No files found matching pattern: {pattern}")
      return

  print(f"Found {len(json_files)} files to process")

  # Calculate number of assets per copy
  assets_per_copy = new_number_assets // (number_of_copies+1)
  remainder = new_number_assets % (number_of_copies+1)

  for input_file in json_files:
    print(f"Processing: {input_file}")

    try:
      # Read the original JSON file
      with open(input_file, 'r') as f:
        raw_data = f.read()
        no_comments = re.sub("//.*","",raw_data,flags=re.MULTILINE)
        data = ast.literal_eval(no_comments)

      # Find and modify the last VolumePairList method
      volume_pair_lists = [i for i, item in enumerate(data['pairlists'])
                          if item.get('method') == 'VolumePairList']

      if volume_pair_lists:
        first_idx = volume_pair_lists[0]
        last_idx = volume_pair_lists[-1]
        data['pairlists'][first_idx]['number_assets'] = new_number_assets+20
        data['pairlists'][last_idx]['number_assets'] = new_number_assets

      if '-' in input_file:
          parts = input_file.split('-')
          if len(parts) >= 3:
              exchange = parts[-2]  # Capitalize the last part (like usdt -> USDT)

      # Create copies with offset filters
      for copy_number in range(1, number_of_copies + 1):
        # Create copy of data
        copy_data = json.loads(json.dumps(data))  # Deep copy
        # Calculate offset
        offset = (copy_number) * assets_per_copy

        # If this is the last copy, include any remainder assets
        if copy_number == number_of_copies:
            copy_assets = assets_per_copy + remainder
        else:
            copy_assets = assets_per_copy

        # Create offset filter
        offset_filter = {
            "method": "OffsetFilter",
            "offset": offset,
            "number_assets": copy_assets
        }

        # Add offset filter to the end of pairlists
        copy_data['pairlists'].append(offset_filter)

        # Create output filename
        input_path = Path(input_file)
        output_filename = input_path.stem + f"-producer{copy_number}.json"
        output_path = input_path.parent / ".." / "consumer_setup" / "configs" / "producers" / exchange / output_filename

        # Write modified copy
        with open(output_path, 'w') as f:
            json.dump(copy_data, f, indent=2)

        print(f"  Created: {output_path}")

    except Exception as e:
      print(f"Error processing {input_file}: {e}")

def main():
  parser = argparse.ArgumentParser(
    description="""Script to convert and split default NFI volume pairlists JSON files to have offset filters for using them with NFI consumer mode setup.
                IRRESPONSIBLY VIBECODED AS A SINGLE USE THROWAWAY SCRIPT!
                CHECK THE RESULTS BEFORE USING IN PRODUCTION SETTING!"""
  )
  parser.add_argument(
    "directory",
    help="Directory containing pairlist-volume-*.json files"
  )
  parser.add_argument(
    "number_assets",
    type=int,
    help="New number of assets for VolumePairList"
  )
  parser.add_argument(
    "number_producers",
    type=int,
    help="Number of producers to create with offset filters"
  )

  args = parser.parse_args()

  # Validate input
  if not os.path.isdir(args.directory):
    print(f"Error: Directory '{args.directory}' does not exist")
    sys.exit(1)

  if args.number_assets <= 0:
    print("Error: number_assets must be positive")
    sys.exit(1)

  if args.number_producers <= 0:
    print("Error: number_producers must be positive")
    sys.exit(1)

  if args.number_assets < args.number_producers:
    print("Warning: number_assets is less than number_producers, some copies may have 0 assets")

  env_output_directory = f"{args.directory}/../consumer_setup/env/pairlists"
  # Process files
  convert_pairlist_files(args.directory, env_output_directory, args.number_producers)
  process_pairlist_files(args.directory, args.number_assets, args.number_producers)

  print("Processing complete!")

if __name__ == "__main__":
  main()