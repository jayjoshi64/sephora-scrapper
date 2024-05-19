import pandas as pd
import csv
import os
import sys
import re
import click
if getattr(sys, 'frozen', False):
    SCRIPT_DIR = os.path.dirname(sys.executable)
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

relative_path = "Brands" 
archives_name = "Archives"
brands_folder = os.path.join(SCRIPT_DIR, relative_path)
archives_folder = os.path.join(SCRIPT_DIR, archives_name)

if not os.path.exists(brands_folder):
    os.makedirs(brands_folder)

if not os.path.exists(archives_folder):
    os.makedirs(archives_folder)

def main():
    
    folder_path = os.path.join(SCRIPT_DIR)

    # Get a list of all files in the folder
    files = os.listdir(folder_path)

    # Filter out only CSV files
     
    csv_files = sorted([file for file in files if file.endswith('.csv')])   #, reverse=True)
    

    # Iterate over each CSV file
    # print("csv files being imported")
    k=0
    with click.progressbar(csv_files, label="Importing downloaded files...", width=0, item_show_func=lambda t:str(t)) as bar:
        if not csv_files:
            bar.update(1, "No new files" )
        for csv_file in csv_files:
            k += 1
            # print("{}) {}".format(k, csv_file) )
            bar.update(1, csv_file)
            temp_file_name = "processing_" + csv_file

            # Make sure the file can be moved
            try:
                os.replace(
                    os.path.join(folder_path, csv_file),
                    os.path.join(folder_path, temp_file_name),
                )
            except OSError:
                print(f"Please close the file {csv_file} from other applications so it can be moved.")
                exit(1)

            # Read the CSV file into a DataFrame
            df = pd.read_csv(os.path.join(folder_path, temp_file_name),dtype={'Eyes': 'str', 'Skin': 'str', 'Skintone': 'str', 'Hair': 'str'})
            df['Brand'] = df['Brand'].str.lower()  #It was treating different in Unique()
            
            # Iterate over unique values in the 'brand' column
            
            for brand in df['Brand'].unique():
                
                # Filter the DataFrame for the current brand
                brand_df = df[df['Brand'] == brand]
                # Define the filename for the CSV file based on the brand name
                filename = f"{convert_to_valid_filename(brand)}.csv"
                
                file_path = os.path.join(brands_folder,filename)
                # Save the filtered DataFrame to a CSV file

                if os.path.isfile(file_path):
                    
                    brand_df.to_csv(file_path, mode='a', header=False, index=False)
                else:
                    # Create a new CSV file for the brand
                    brand_df.to_csv(file_path, index=False)
            
            # Move the parsed file to avoid duplicates
            try:
                os.replace(
                    os.path.join(folder_path, "processing_" + csv_file),
                    os.path.join(archives_folder, csv_file)
                )
            except OSError:
                print(f"file {csv_file} could not be moved to Archives folder...")
                print("Please close the file from other applications.")
                exit(1)

    sort_brandfiles()

def sort_brandfiles():

    files = os.listdir(brands_folder)
    brand_csv_files = sorted([file for file in files if file.endswith('.csv')])   #, reverse=True)

    # print("Brand csv files being Sorted")
    k=0
    with click.progressbar(brand_csv_files, label="Sorting csv files...", width=0, item_show_func=lambda p:p) as bar:
        for csv_file in brand_csv_files:
            k += 1

            # print("{}) {} ".format(k, csv_file) ) 
            bar.update(1, csv_file)

            file_path = os.path.join(brands_folder,csv_file)
            
            brand_df = pd.read_csv(file_path,dtype={'Eyes': 'str', 'Skin': 'str', 'Skintone': 'str', 'Hair': 'str'})           
            brand_df = brand_df.sort_values(by=['Category','Product'], ascending=[True, True], na_position='first')
            brand_df.to_csv(file_path, index=False)


def convert_to_valid_filename(brand_name):
    # Replace special characters with underscores
    return re.sub(r'[^\w]+', '_', brand_name.strip())
 

if __name__ == "__main__":
    main()