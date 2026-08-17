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

