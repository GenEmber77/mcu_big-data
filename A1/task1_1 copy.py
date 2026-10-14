import pandas as pd
import pymongo
import csv

def export_to_csv(data, filename):
    df = pd.DataFrame((list(data.find({}))))
    # Convert ObjectId to string so it's CSV-friendly
    if "_id" in df.columns:
        df["_id"] = df["_id"].astype(str)

    df.to_csv(filename, index=False)

conn = pymongo.MongoClient("localhost:27017")
db = conn["Assignment_1"]

COLLECTION_NAME = "FIFA_players"
COLLECTION_NAME_CLEANED = "FIFA_players_cleaned"

# Drops the collection if it exists to enable re-running of script; safely ignores if it doesn't
db.drop_collection(COLLECTION_NAME)
db.drop_collection(COLLECTION_NAME_CLEANED)

collection = db[COLLECTION_NAME]

df = pd.read_csv("data.csv")
#Convert NaNs to None so Mongo stores them as null instead of NaN
#df = df.where(pd.notnull(df), None)
data = df.to_dict(orient="records")

# with open("data.csv", encoding="utf-8-sig") as file:
#     reader = csv.DictReader(file)
#     data = list(reader)

collection.insert_many(data)
#export_to_csv(collection, "output1.csv")
# unique_values = collection.distinct("player_name")
# cnt = collection.count_documents({"player_name": {"$in": [None, "",float("nan")]}})
# print(cnt)


#sample_doc = collection.find_one()
#print(list(sample_doc.keys())) #check the fields in the document

#sample_doc = collection.find("completition": "Champions League").limit(1)[0]
#print(list(sample_doc.keys())) #check the fields in the document

string_fields = ["player_name", "nationality", "club", "position", "season", "competition"]
required_fields = ["player_name", "competition", "match_id"]
numeric_fields = ["market_value_eur_m", "minutes_played", "goals", "assists", "shots_on_target", "tackles", "match_rating", "fouls_committed"]

lt_regex = r"^\s+|\s+$"  # regex to match leading or trailing spaces
s2_regex = r"\s{2,}"  # regex to match two or more consecutive spaces

records = collection.count_documents({})
unknown_nationality_count = collection.count_documents({"nationality": "Unknown"})
missing_market_value_count = collection.count_documents({"market_value_eur_m": {"$in": [None, "",float("nan")]}})

# start: removing leading and trailing spaces step
for field in string_fields:
    cnt = collection.count_documents({ field: { "$regex": lt_regex }})
    print(f"Before update, leading and trailing spaces in {field} : {cnt}")

for field in string_fields:
    collection.update_many(
        {field: {"$regex": lt_regex}},
        [{"$set": {field: {"$trim": {"input": f"${field}"}}}}]
    )

for field in string_fields:
    cnt = collection.count_documents({ field: { "$regex": lt_regex }})
    print(f"After update, leading and trailing spaces in {field} : {cnt}")
# end: removing leading and trailing spaces step


# start: standardizing competition names step
collection.update_many(
    {"$expr": {"$eq": [{"$toLower": f"$competition"}, "fifa world cup 2026"]}},
    {"$set": {"competition": "FIFA World Cup 2026"}}
)

collection.update_many(
    {"$expr": {"$eq": [{"$toLower": f"$competition"}, "champions league"]}},
    {"$set": {"competition": "Champions League"}}
)

collection.update_many(
    {"$expr": {"$eq": [{"$toLower": f"$competition"}, "domestic cup"]}},
    {"$set": {"competition": "Domestic Cup"}}
)

collection.update_many(
    {"$expr": {"$eq": [{"$toLower": f"$competition"}, "world cup qualifiers"]}},
    {"$set": {"competition": "World Cup Qualifiers"}}
)

collection.update_many(
    {"$expr": {"$eq": [{"$toLower": f"$competition"}, "league"]}},
    {"$set": {"competition": "League"}}
)
#end: standardizing competition names step


# start: replacing multiple consecutive internal spaces with a single space step
for field in string_fields:
    cnt = collection.count_documents({ field: { "$regex": s2_regex }})
    print(f"Before update, consecutive spaces in {field} : {cnt}")

for field in string_fields:
    collection.update_many(
        {field: {"$regex": r"\s{2,}"}},
        [{"$set": {field: {"$replaceAll": {"input": f"${field}", "find": "  ", "replacement": " "}}}}]
    )

for field in string_fields:
    cnt = collection.count_documents({ field: { "$regex": s2_regex }})
    print(f"After update, consecutive spaces in {field} : {cnt}")
# end: replacing multiple consecutive internal spaces with a single space step

string_standardization_count = 0
# start: removing records with missing required identifier fields step
for field in required_fields:
    cnt = collection.count_documents({field: {"$in": [None, "",float("nan")]}})
    print(f"Before update, records with missing {field}: {cnt}")
    string_standardization_count += cnt

for field in required_fields:
    collection.delete_many({field: {"$in": [None, ""]}})   

for field in required_fields:
    cnt = collection.count_documents({field: {"$in": [None, ""]}})
    print(f"After update, records with missing {field}: {cnt}")
# end: removing records with missing required identifier fields step

#start: removing records with negative numeric values step
for field in numeric_fields:
    cnt = collection.count_documents({field: {"$lt": 0}})
    print(f"Before update, records with negative in {field}: {cnt}")

for field in numeric_fields:
    collection.delete_many({field: {"$lt": 0}})

for field in numeric_fields:
    cnt = collection.count_documents({field: {"$lt": 0}})
    print(f"After update, records with negative {field}: {cnt}")
#end: removing records with negative numeric values step



# start: Fix records with unknown nationality
operations = []
natl_unknown_docs = collection.find({"nationality": "Unknown"})

for doc in natl_unknown_docs:
    player_name = doc.get("player_name")
    age = doc.get("age")
    club = doc.get("club")

    # Find matching records with the same player_name, age, club, and a KNOWN nationality
    matches = collection.distinct("nationality", {
        "player_name": player_name,
        "age": age,
        "club": club,
        "nationality": {"$ne": "Unknown"}
    })
    # If there's exactly one known nationality, prepare an update operation
    if len(matches) == 1: 
        operations.append( pymongo.UpdateOne({"_id": doc["_id"]}, {"$set": {"nationality": matches[0]}}) )

if operations:
    result = collection.bulk_write(operations)
    print(f"Updated {result.modified_count} documents with nationality inferred from other records.")
else:
    print("No documents updated.")


# end: Fix records with unknown nationality


# start: Fix records with missing market_value_eur_m
averages = {}
operations = []

pipeline = [
    {"$match": {"market_value_eur_m": {'$nin': [None, '', float('nan')]}}},
    {"$group": {
        "_id": {"competition": "$competition", "player_name": "$player_name"},
        "avg_value": {"$avg": "$market_value_eur_m"}
    }}
]

for doc in collection.aggregate(pipeline):
    key = (doc["_id"]["competition"], doc["_id"]["player_name"])
    averages[key] = doc["avg_value"]

#print(averages)    
missing_mv = collection.find({"market_value_eur_m": {"$in": [None, "",float("nan")]}})

for doc in missing_mv:
    key = (doc.get("competition"), doc.get("player_name"))
    if key in averages:
        operations.append(pymongo.UpdateOne({"_id": doc["_id"]}, {"$set": {"market_value_eur_m": round(averages[key],2)}}))

if operations:
    result = collection.bulk_write(operations)
    print(f"Updated {result.modified_count} documents with missing market_value_eur_m")
else:
    print("No documents updated.")
# end: Fix records with missing market_value_eur_m

with open("cleaning_report.txt", "w", encoding="utf-8") as f:
    f.write(f"Total records before cleaning: {records}\n")
    f.write(f"Total records after cleaning: {collection.count_documents({})}\n")
    f.write(f"Total records with nationality = \"Unknown\" before cleaning: {unknown_nationality_count}\n")
    f.write(f"Total records with missing market_value_eur_m before cleaning: {missing_market_value_count}\n")
    f.write(f"Total records after string standardization: {records - string_standardization_count}\n")

print(f"Total records before cleaning: {records}")
print(f"Total records after cleaning: {collection.count_documents({})}")
print(f"Total records with nationality = \"Unknown\" before cleaning: {unknown_nationality_count}")
print(f"Total records with missing market_value_eur_m before cleaning: {missing_market_value_count}")
print(f"Total records after string standardization: {records - string_standardization_count}")
print("Saved to cleaning_report.txt")

collection.aggregate([{"$out": COLLECTION_NAME_CLEANED}])  # Copy cleaned data to new collection
export_to_csv(collection, "output1.csv")



fields = ["player_name", "nationality", "club", "position", "market_value_eur_m", "competition", "match_id", "minutes_played", "goals", "assists", "match_rating"]
fields_header = ["player name", "nationality", "club", "position", "market value", "competition", "match_id", "minutes_played", "goals", "assists", "match_rating"]

# Build projection (1 = include field); exclude _id unless you want it
projection = {field: 1 for field in fields}
projection["_id"] = 0

collection = db[COLLECTION_NAME_CLEANED]
cursor = collection.find({}, projection)

with open("player_data.txt", "w", encoding="utf-8") as f:
    # Optional header row
    f.write(",".join(fields_header) + "\n")

    for doc in cursor:
        row = [str(doc.get(field, "")) for field in fields]
        f.write(",".join(row) + "\n")

print("Saved to player_data.txt")




# Step 2: Clean the data and store the results.
# Apply the following cleaning rules in the specified order. Once a record is removed in a cleaning step, it
# must not be used in any subsequent cleaning, inference, or calculation. Store all records remaining after the
# cleaning process in a new MongoDB collection named "FIFA_players_cleaned".
# 1. String standardization: For all string fields, remove leading and trailing spaces and replace multiple consecutive internal spaces with a single space.
# 2. Competition standardization: Standardise all competition names to one of the following five values:
#   "FIFA World Cup 2026", "Champions League", "Domestic Cup", "World Cup Qualifiers", or "League".
# 3. Missing identifiers: After string standardisation, remove any record with a missing value in one or more required identifier fields: 
#     player_name, competition, or match_id.
# 4. Invalid numeric values: Remove any record containing a negative value in any of the following fields:
#     market_value_eur_m, minutes_played, goals, assists, shots_on_target, tackles, match_rating, or fouls_committed.
# 5. Unknown nationality: For each record where nationality = "Unknown", use records with the same player_name, age, and club to infer the nationality.
#     If the known nationalities in all matching records are the same, replace "Unknown" with that nationality; otherwise, retain "Unknown".
# 6. Missing market value: For records with a missing market_value_eur_m, replace the missing value with
#     the average market_value_eur_m calculated from records with the same competition and player_name.


#"cleaning_report.txt"
#Summarize the data-cleaning process by reporting:
#• the total number of records before cleaning;
#• the total number of records after cleaning;
#• the number of records with nationality = "Unknown" before cleaning;
#• the number of records with missing market_value_eur_m before cleaning;
#• the number of records whose string fields were standardized.