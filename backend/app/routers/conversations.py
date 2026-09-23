from fastapi import APIRouter, HTTPException
from ..schemas import Conversation, ConversationCreate
from ..services.store import store

router = APIRouter(prefix="/api/conversations", tags=["conversations"])

@router.post("", response_model=Conversation, status_code=201)
def create_conversation(item: ConversationCreate):
    return store.save_conversation(item.model_dump(mode="json"))

@router.get("", response_model=list[Conversation])
def list_conversations():
    return store.list_conversations()

@router.get("/{conversation_id}", response_model=Conversation)
def get_conversation(conversation_id: str):
    item = store.get_conversation(conversation_id)
    if not item: raise HTTPException(404, "Conversation not found")
    return item

@router.delete("/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: str):
    if not store.delete_conversation(conversation_id): raise HTTPException(404, "Conversation not found")
