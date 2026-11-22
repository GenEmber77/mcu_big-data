import pandas as pd
import pymongo

conn = pymongo.MongoClient("localhost:27017")
db = conn["Assignment_1"]

COLLECTION_NAME = "FIFA_players"
COLLECTION_NAME_CLEANED = "FIFA_players_cleaned"

# Drops the collection if it exists to enable re-running of script; safely ignores if it doesn't
db.drop_collection(COLLECTION_NAME)
db.drop_collection(COLLECTION_NAME_CLEANED)

collection = db[COLLECTION_NAME]

df = pd.read_csv("data.csv")
df = df.where(pd.notnull(df), None)
data = df.to_dict(orient="records")

collection.insert_many(data)

string_fields = ["player_name", "nationality", "club", "position", "season", "competition"]
required_fields = ["player_name", "competition", "match_id"]
numeric_fields = ["market_value_eur_m", "minutes_played", "goals", "assists", "shots_on_target", "tackles", "match_rating", "fouls_committed"]

lt_regex = r"^\s+|\s+$"  # regex to match leading or trailing spaces
s2_regex = r"\s{2,}"  # regex to match two or more consecutive spaces

records = collection.count_documents({})
unknown_nationality_count = collection.count_documents({"nationality": "Unknown"})
missing_market_value_count = collection.count_documents({"market_value_eur_m": {"$in": [None, "",float("nan")]}})

string_standardization_count = 0
# start: removing leading and trailing spaces step
for field in string_fields:
    cnt = collection.count_documents({ field: { "$regex": lt_regex }})
    print(f"Before update, leading and trailing spaces in {field} : {cnt}")
    string_standardization_count += cnt

for field in string_fields:
    collection.update_many(
        {field: {"$regex": lt_regex}},
        [{"$set": {field: {"$trim": {"input": f"${field}"}}}}]
    )

for field in string_fields:
    cnt = collection.count_documents({ field: { "$regex": lt_regex }})
    print(f"After update, leading and trailing spaces in {field} : {cnt}")
# end: removing leading and trailing spaces step


# start: replacing multiple consecutive internal spaces with a single space step
for field in string_fields:
    cnt = collection.count_documents({ field: { "$regex": s2_regex }})
    print(f"Before update, consecutive spaces in {field} : {cnt}")
    string_standardization_count += cnt

for field in string_fields:
    collection.update_many(
        {field: {"$regex": r"\s{2,}"}},
        [{"$set": {field: {"$replaceAll": {"input": f"${field}", "find": "  ", "replacement": " "}}}}]
    )

for field in string_fields:
    cnt = collection.count_documents({ field: { "$regex": s2_regex }})
    print(f"After update, consecutive spaces in {field} : {cnt}")
# end: replacing multiple consecutive internal spaces with a single space step


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

# start: removing records with missing required identifier fields step
for field in required_fields:
    cnt = collection.count_documents({field: {"$in": [None, "",float("nan")]}})
    print(f"Before update, records with missing {field}: {cnt}")

for field in required_fields:
    collection.delete_many({field: {"$in": [None, "",float("nan")]}})   

for field in required_fields:
    cnt = collection.count_documents({field: {"$in": [None, "",float("nan")]}})
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
print(f"Total records after string standardization: {string_standardization_count}")
print("Saved to cleaning_report.txt")

collection.update_many({}, [{"$set": {"match_id": {"$toInt": "$match_id"}}}])
collection.aggregate([{"$out": COLLECTION_NAME_CLEANED}])  # Copy cleaned data to new collection

fields = ["player_name", "nationality", "club", "position", "market_value_eur_m", "competition", "match_id", "minutes_played", "goals", "assists", "match_rating"]

# Build projection (1 = include field); exclude _id unless you want it
projection = {field: 1 for field in fields}
projection["_id"] = 0

collection = db[COLLECTION_NAME_CLEANED]
cursor = collection.find({}, projection)

with open("player_data.txt", "w", encoding="utf-8") as f:
    for doc in cursor:
        row = [str(doc.get(field, "")) for field in fields]
        f.write(",".join(row) + "\n")

print("Saved to player_data.txt")