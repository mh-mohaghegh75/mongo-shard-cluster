from pymongo import MongoClient
import os 


mongo_host = os.getenv("MONGODB_HOST")
mongo_port = int(os.getenv("MONGODB_PORT"))
mongo_database = os.getenv("MONGODB_DATABASE")
mongo_collection = os.getenv("MONGODB_COLLECTION")



HOST=mongo_host
PORT=mongo_port
DATABASE=mongo_database
COLLECTION=mongo_collection



def get_connection():
    try:
      client = MongoClient(host=HOST,port=PORT)
      print("Connection established!!!")
      return client
    except:
      print("Connection failed!!!")
      return 1
