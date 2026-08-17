
//================================================================================
// WEEK 2
//================================================================================

//db.getCollection("Tweets").find({})

// No. 1, Insert 2 new Tweets to the collection
db.Tweets.insertMany([
{
   id_str : "test_id_12345",
   text : "test_text_1",
   user : { id: 777, name: "Genesis"}
},
{
   id_str : "test_id_5678",
   text : "test_text_2",
   user : { id: 888, name: "Zlick"}
}
])


//No 2, Write a MongoDB query that returns all the Tweets
db.Tweets.find()

//No 3, Write a MongoDB query to find one of your Tweets with user’s name: "user 30"
db.Tweets.find({"user.name": "user 30"})   

//No 4, Update the tweet of "user 30" by adding a new field called "tag" with the value "My first tag"
db.Tweets.updateMany(
{ "user.name" : {$eq: "user 30"}},
{ $set: {tag:"My first tag edited"}}
)

//No 5, Write a MongoDB query to retrieve all documents from the Tweets collection where user name equals either "user 30" or "user 40"
db.Tweets.find({ "user.name" : {$in: ["user 30","user 40"]}})   
db.Tweets.find({$or: [{"user.name": "user 30"},{"user.name": "user 40"}]})   

//No 6, Write a MongoDB query to retrieve all documents from the Tweets collection where user screen_name is "Twitter User" and user location is "Internet". (Specify ANDConditions)
db.Tweets.find({$and: [{"user.screen_name": "Twitter User"},{"user.location": "Internet"}]})   

//No 7, Write a MongoDB query to retrieve all documents from the Tweets collection where user screen_name is "Twitter User" or user url is "user URL". (Specify OR Conditions)
db.Tweets.find({$or: [{"user.screen_name": "Twitter User"},{"user.url": "user URL"}]})

//No 8, Write a MongoDB query to retrieve all documents from the Tweets collection where user id is not 224499494502
db.Tweets.find({"user.name": {$ne:224499494502}})  



//================================================================================
// WEEK 3
//================================================================================

// 1. Find all documents where user names do not equal "user 30" and "user 40".
db.Tweets.find({"user.name":{$nin:["user 30","user 40"]}})

// 2. Find all Tweets in which the field “tag” has values.
db.Tweets.find({"tag":{$exists:true}})

// 3. Find the Tweets where the Tweet id (i.e., id_str) is greater than 8000000000000000000 but less than 9000000000000000000.
db.Tweets.find({$and: [{id_str:{$gt:"8000000000000000000"}},{id_str:{$lt:"9000000000000000000"}}]})   
db.Tweets.find({id_str:{$gt:"8000000000000000000",$lt:"9000000000000000000"}})   

// 4. Find the Tweets whose user id is greater than 224499494502 but less than 224499494522.
db.Tweets.find({$and: [{"user.id":{$gt:224499494502}},{"user.id":{$lt:224499494522}}]})
db.Tweets.find({"user.id":{$gt:224499494502,$lt:224499494522}}).count()

// 5. Display the Tweet Id ("id_str") for those Tweets, which contain the keyword “Sydney” in their text.
db.Tweets.find({text:{$regex:"Sydney"}},{"id_str":1})

// 6. Display the first 10 Tweets which have the screen name with value "Twitter User".
db.Tweets.find({"user.screen_name":"Twitter User"}).limit(10)

// 7. Display the "user Id", "user name" and "user location" fields for those Tweets, which contain "Thu" as first three letters for its "created_at" field.
db.Tweets.find({created_at:{$regex:"^Thu"}},{"user.id":1,"user.name":1,"user.location":1})

// 8. Find the three earliest tweets (according to created time).
db.Tweets.find().sort({"created_at":-1}).limit(3)



