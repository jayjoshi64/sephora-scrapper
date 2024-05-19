import requests 
import csv
import json
import os
import sys
import datetime
import traceback
import click
import functools

if getattr(sys, 'frozen', False):
    SCRIPT_DIR = os.path.dirname(sys.executable)
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

CSV_FILE_PATH = "Reviews.csv"
CSV_HEADERS = ["Category","Brand","Product","Incentivised","Rating","ReviewTitle","Review","ReviewBy","Eyes","Skin","Skintone","Hair"]
CHECKPOINT_PATH = os.path.join(SCRIPT_DIR, "checkpoint.json")
PASSKEY_PATH = os.path.join(SCRIPT_DIR, "passkey.config")
TRACEBACK_PATH = os.path.join(SCRIPT_DIR, "traceback.log")


def write_csv(parent_folder,file_name, products, CSV_HEADERS_EACH):
    
    file_path = os.path.join(parent_folder, file_name)
    with open(file_path, "a", newline='', encoding="utf-8") as csv_file:
        dict_writer = csv.DictWriter(csv_file, CSV_HEADERS_EACH)
        dict_writer.writerows(products)
    # print("\t- Updated the CSV file in this folder: {}".format(file_name))

def get_checkpoint():
    try:
        with open(CHECKPOINT_PATH, "r") as checkpoint_file:
            checkpoint_list = json.load(checkpoint_file)
        return checkpoint_list
    except:
        return {}

def convert_to_slash_case(input_string):
    result = ""
    if len(input_string)>0:
        result = input_string[0].upper()

    for char in input_string[1:]:
        if char.isupper():
            result += "/" + char
        else:
            result += char
    return result

def set_checkpoint(checkpoint):
    with open(CHECKPOINT_PATH, "w") as checkpoint_file:
        json.dump(checkpoint, checkpoint_file)    

def getbetween(string,startstr,endstr):
    start=string.find(startstr) +len(startstr)   
    end = string.find(endstr,start)
    getbetween = string[start:end]
    return getbetween

@functools.cache
def get_passkey():
    default_passkey = "calXm2DyQVjcCy9agq85vmTJv5ELuuBCF2sdg4BnJzJus"
    try:
        with open(PASSKEY_PATH, "r") as conf_file:
            passkey_in_conf = conf_file.read()
            if passkey_in_conf:
                return passkey_in_conf
    except FileNotFoundError:
        with open(PASSKEY_PATH, "w") as conf_file:
            conf_file.write(default_passkey)

    return default_passkey




def prepare_csv(parent_folder, file_name, headers):
    #parent_folder = "products"
    file_path = os.path.join(parent_folder, file_name)
    #print("Checking the CSV file: {}".format(file_name))
    if not os.path.exists(parent_folder):
        os.makedirs(parent_folder)
    if not os.path.exists(file_path):
        with open(file_path, "w", newline='', encoding="utf-8") as csv_file:
            dict_writer = csv.DictWriter(csv_file, headers)
            dict_writer.writeheader()

        # Remote the checkpoint file
        ###set_checkpoint(set())
    else:
        #print("{} file already exists. ".format(file_name))
        print("Preparing CSV...")

def get_single_call(session, url, default_params, offset, limit):
    params = {
        "Offset":offset,
        "Limit": limit,
        "apiversion":5.4,
        "passkey":get_passkey(),
    }
    params.update(default_params)
    res = session.get(
        url,
        params=params,
    )
    return res.json()

def get_paginated_results(url, default_params = None, label="Downloading...", debug=False):
    captured_count = 0
    limit = 100
    total_count = 0
    default_params = default_params or {}
    session = requests.Session()
    # Get total item count
    total_count = get_single_call(
        session, url, default_params, 0, 1
    ).get("TotalResults")

    with click.progressbar(
        length=total_count, label=label, width=0,
        item_show_func=lambda p:f"( {p} out of {total_count} )"
    ) as bar:
        while True:
            res = get_single_call(
                session, url, default_params, captured_count, limit
            )
            if debug:
                print(res)

            # Pagination
            downloaded_count = len(res.get("Results"))
            captured_count += downloaded_count
            yield res

            bar.update(downloaded_count, captured_count)
            if captured_count >= total_count:
                break

def get_categories():
    categories = {}
    for each_res in get_paginated_results(
        "https://api.bazaarvoice.com/data/categories.json",
        label="Downloading categories..."
    ):
        for each_category in each_res.get("Results"):
            categories[each_category.get("Id")] = each_category.get("Name")

    return categories       

def add_products_to_csv(prev_submission_time):

    latest_submission_time = None
    csv_row_count = 0
    try:
        categories = get_categories()
        params = {
            "Filter":"contentlocale:en*",
            "Sort":"SubmissionTime:asc",
            "Include":"Products,Comments",
            "Stats":"Reviews",
        }
        if prev_submission_time:
            params["Filter"] = f"SubmissionTime:gt:{prev_submission_time}"


        for each_res in get_paginated_results(
            "https://api.bazaarvoice.com/data/reviews.json",
            default_params=params,
            label="Downloading Reviews...",
            debug=False
        ):
            # Products
            reviews_list = []

            products = each_res.get("Includes").get("Products")
            for each_review in each_res.get("Results"):
                incentivized = each_review.get("ContextDataValues", {}).get("IncentivizedReview", {}).get("ValueLabel") or "No"
                mycatagory_id = products.get(each_review.get("ProductId")).get("CategoryId")
                mycatagory = categories.get(mycatagory_id)
                mybrand = products.get(each_review.get("ProductId")).get("Brand").get("Name") or "Unknown"
                myproduct = products.get(each_review.get("ProductId")).get("Name") or "Unknown"
                myrating = each_review.get("Rating")
                myrating = str(myrating).strip() + " out of 5 stars."
                mytitle = each_review.get("Title")
                myreview = each_review.get("ReviewText")
                myuser = each_review.get("UserNickname")
                myeyes = each_review.get("ContextDataValues", {}).get("eyeColor", {}).get("ValueLabel") or ""
                myskin = each_review.get("ContextDataValues", {}).get("skinType", {}).get("ValueLabel") or ""
                myskintone = each_review.get("ContextDataValues", {}).get("skinTone", {}).get("ValueLabel") or ""
                myskintone = convert_to_slash_case(myskintone) # added on 2024-513
                myhair = each_review.get("ContextDataValues", {}).get("hairColor", {}).get("ValueLabel") or ""
                reviews_list.append({
                    "Category": mycatagory, "Brand": mybrand, "Product": myproduct,
                    "Incentivised":incentivized,"Rating":myrating,
                    "ReviewBy":myuser,"Eyes":myeyes,"Skin":myskin,
                    "Skintone":myskintone,"Hair":myhair,
                    "ReviewTitle":mytitle,"Review":myreview
                })

                latest_submission_time = each_review.get("SubmissionTime")
                csv_row_count += 1

            write_csv(SCRIPT_DIR, CSV_FILE_PATH, reviews_list, CSV_HEADERS)
    except KeyboardInterrupt:
        "Exiting Gracefully..."
    except:
        with open(TRACEBACK_PATH, "a") as log:
            log.write(traceback.format_exc())

        print("Unexpected Error, check traceback.log")
    finally:
        if csv_row_count:
            print(f"Downloaded total {csv_row_count} records!")
        if latest_submission_time:
            return latest_submission_time

def add_remaining_products_to_csv():
    prepare_csv(SCRIPT_DIR, CSV_FILE_PATH, CSV_HEADERS)

    prev_submission_epoch = None
    prev_submission_time = get_checkpoint()
    if prev_submission_time:
        prev_submission_epoch = prev_submission_time.get("submission_time") 
        prev_submission_time_str = prev_submission_time.get("submission_time_str")
        print(f"Starting collection from: {prev_submission_time_str}")


    latest_submission_time_str = add_products_to_csv(prev_submission_epoch)
    if not latest_submission_time_str:
        print("Could not download any data, please try again...")
        return
    latest_submission_time = datetime.datetime.fromisoformat(latest_submission_time_str)
    latest_collected_str = latest_submission_time.strftime("%Y_%m_%d_%H_%M")
    
    set_checkpoint({
        "submission_time": int(latest_submission_time.timestamp()),
        "submission_time_str": latest_collected_str
    })

    new_csv_file_path = CSV_FILE_PATH.replace(".csv","") + "_" + latest_collected_str + ".csv"
    os.rename(
        os.path.join(SCRIPT_DIR, CSV_FILE_PATH), 
        os.path.join(SCRIPT_DIR, new_csv_file_path), 
    )
    print(f"CSV Saved to: {new_csv_file_path}")


def main():
    # Prep
    add_remaining_products_to_csv()


if __name__ == "__main__":
    main()
