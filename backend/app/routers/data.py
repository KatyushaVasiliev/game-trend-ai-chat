from fastapi import APIRouter, HTTPException
from ..schemas import DataCreate, DataPoint, DataUpdate, Summary
from ..services.store import store
from ..services.summary import make_summary

router = APIRouter(prefix="/api/data", tags=["data"])

@router.post("", response_model=DataPoint, status_code=201)
def create_data(item: DataCreate):
    return store.create_data(item.model_dump(mode="json"))

@router.get("", response_model=list[DataPoint])
def get_data():
    return store.list_data()

@router.get("/summary", response_model=Summary)
def get_summary():
    return make_summary(store.list_data())

@router.put("/{item_id}", response_model=DataPoint)
def update_data(item_id: str, item: DataUpdate):
    saved = store.update_data(item_id, item.model_dump(mode="json"))
    if not saved: raise HTTPException(404, "Data not found")
    return saved

@router.delete("/{item_id}", status_code=204)
def delete_data(item_id: str):
    if not store.delete_data(item_id): raise HTTPException(404, "Data not found")
