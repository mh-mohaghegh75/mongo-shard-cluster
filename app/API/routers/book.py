import uuid
from pymongo import MongoClient
from fastapi import Depends, HTTPException, APIRouter
from pydantic import BaseModel
from core.database import get_connection,PORT, HOST, DATABASE, COLLECTION


router = APIRouter(
    prefix="/books",
    tags=["books"],
    responses={
        404: {"description": "Not found!"}
    })


class BookCreate(BaseModel):
    title: str
    name: str
    description: str
    rate: int


def insert_single(data: dict):
    client = get_connection()
    if client == 1:
        print("Insertion has errors")
        return 1
    try:
        Id = uuid.uuid4()
        data.update({"_id":(str(Id))})
        database = client[DATABASE]
        collection = database[COLLECTION]
        
        collection.insert_one(data)
        client.close()
        return data
    except:
        print("Insert one function has problem!!!")
        return 1



@router.post("/")
def create_new_book(book: BookCreate):

    book_dict = insert_single(book.__dict__)
    
    return {"message": "Book created", "book": book_dict}



@router.post("/bulk:{num}")
def create_bulk_book(num: int, book: BookCreate):
    result = []
    
    for i in range(num):
        book_dict = insert_single(book.__dict__)
        result.append(book_dict)
    return {"message": "Book created", "books": result}



@router.get("/")
def get_all_book(client: MongoClient = Depends(get_connection)):
    client = get_connection()
    print(PORT)
    print(HOST)

    if client == 1:
        print("Get has errors")
        return 1

    database = client[DATABASE]
    collection = database[COLLECTION]
    cursor = collection.find()
    
    result = []
    j=0
    
    for i in cursor:
        j = j+1
        result.append(i)
    client.close()
    if len(result) != 0:
        return {"Number of recordss": j, "message": result} 
    else:
        raise HTTPException(status_code=404, detail="Book not found")



# @router.put("/{book_id}")
# def update_single_book(book_id: int, book: BookCreate, client: MongoClient = Depends(get_connection)):
#     db_book = db.query(Book).filter(Book.id == book_id).first()
#     if db_book:
#         db_book.title = book.title
#         db_book.author = book.author
#         db.commit()
#         return {"message": "Book updated"}
#     else:
#         raise HTTPException(status_code=404, detail="Book not found")


@router.delete("/collection")
def delete_single_book(
    client: MongoClient = Depends(get_connection)):
    if client == 1:
        print("Deletion has errors")
        return 1
    database = client[DATABASE]
    collction = database[COLLECTION]
    collction.drop()
    client.close()