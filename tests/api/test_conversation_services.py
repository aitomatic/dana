from sqlalchemy.orm import Session

from dana.api.server.models import Conversation
from dana.api.server.schemas import ConversationCreate, MessageCreate
from dana.api.server.services import ConversationService, MessageService


def test_conversation_crud(db_session: Session):
    service = ConversationService()
    # Create
    convo = service.create_conversation(db_session, ConversationCreate(title="Chat"))
    assert convo.id is not None
    # Read
    fetched = service.get_conversation(db_session, convo.id)
    assert fetched.id == convo.id
    # Update
    updated = service.update_conversation(db_session, convo.id, ConversationCreate(title="Updated Chat"))
    assert updated.title == "Updated Chat"
    # Delete
    assert service.delete_conversation(db_session, convo.id) is True
    assert service.get_conversation(db_session, convo.id) is None

def test_message_crud(db_session: Session):
    convo = Conversation(title="Chat")
    db_session.add(convo)
    db_session.commit()
    db_session.refresh(convo)
    service = MessageService()
    # Create
    msg = service.create_message(db_session, convo.id, MessageCreate(sender="user", content="Hi"))
    assert msg.id is not None
    # Read
    fetched = service.get_message(db_session, convo.id, msg.id)
    assert fetched.id == msg.id
    # Update
    updated = service.update_message(db_session, convo.id, msg.id, MessageCreate(sender="bot", content="Hello"))
    assert updated.sender == "bot"
    assert updated.content == "Hello"
    # Delete
    assert service.delete_message(db_session, convo.id, msg.id) is True
    assert service.get_message(db_session, convo.id, msg.id) is None 