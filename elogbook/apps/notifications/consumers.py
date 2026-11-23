import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from .models import Message

User = get_user_model()

def room_name_for(u1_id: int, u2_id: int) -> str:
    """Generate a consistent room name for two users"""
    a, b = sorted([u1_id, u2_id])
    return f"userchat_{a}_{b}"

def can_message_users(user1, user2):
    """Check if two users are allowed to message each other"""
    
    if user1 == user2:
        return False
    
   
    if hasattr(user1, 'supervisor_profile') and hasattr(user2, 'intern_profile'):
        return user2.intern_profile.supervisor.user == user1
        
    
    elif hasattr(user2, 'supervisor_profile') and hasattr(user1, 'intern_profile'):
        return user1.intern_profile.supervisor.user == user2
        
   
    elif user1.is_staff or user2.is_staff:
        return True
        
    return False

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.user = self.scope.get("user")
        
        if not self.user or isinstance(self.user, AnonymousUser):
            self.close(code=4001)
            return
            
        try:
            self.other_user_id = int(self.scope["url_route"]["kwargs"]["other_user_id"])
            self.other_user = User.objects.get(id=self.other_user_id)
            
            
            if not can_message_users(self.user, self.other_user):
                raise PermissionDenied("Not authorized to message this user")
                
            self.room_group_name = room_name_for(self.user.id, self.other_user_id)

            
            async_to_sync(self.channel_layer.group_add)(
                self.room_group_name, self.channel_name
            )
            
            self.accept()
            
        except (KeyError, ValueError):
            self.close(code=4002)
        except User.DoesNotExist:
            self.close(code=4003)
        except PermissionDenied:
            self.close(code=4004)

    def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            async_to_sync(self.channel_layer.group_discard)(
                self.room_group_name, self.channel_name
            )

    def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return
            
        try:
            data = json.loads(text_data)
            # Typing indicator
            if data.get("typing"):
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    {
                        "type": "chat.message",
                        "type_override": "typing",
                        "sender_username": self.user.get_username(),
                        "sender_id": self.user.id,
                        "timestamp": "",
                        "message": "",
                    },
                )
                return

            # Read receipt: mark other user's unread messages as read
            if data.get("read"):
                from django.utils import timezone
                Message.objects.filter(
                    sender_id=self.other_user_id,
                    recipient_id=self.user.id,
                    is_read=False,
                ).update(is_read=True, read_at=timezone.now())
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    {
                        "type": "chat.message",
                        "type_override": "read",
                        "sender_username": self.user.get_username(),
                        "sender_id": self.user.id,
                        "timestamp": "",
                        "message": "",
                    },
                )
                return

            content = (data.get("message") or "").strip()
            if not content:
                return
                
            
            try:
                recipient = User.objects.get(id=self.other_user_id)
                if not can_message_users(self.user, recipient):
                    raise PermissionDenied("Not authorized to message this user")
            except (User.DoesNotExist, PermissionDenied):
                self.send(text_data=json.dumps({
                    "error": "Cannot message this user",
                    "type": "error"
                }))
                return
            
           
            msg = Message.objects.create(
                sender=self.user, 
                recipient=recipient, 
                content=content
            )

           
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    "type": "chat.message",
                    "type_override": "message",
                    "message": msg.content,
                    "sender_username": self.user.get_username(),
                    "sender_id": self.user.id,
                    "timestamp": msg.timestamp.isoformat(),
                    "id": msg.id,
                },
            )
            
        except json.JSONDecodeError:
            self.send(text_data=json.dumps({
                "error": "Invalid message format",
                "type": "error"
            }))
        except Exception:
            self.send(text_data=json.dumps({
                "error": "Server error processing message",
                "type": "error"
            }))

    def chat_message(self, event):
        # Send message to WebSocket
        payload = dict(event)
        # Normalize type for client: typing/read/message
        payload["type"] = payload.pop("type_override", payload.get("type"))
        self.send(text_data=json.dumps(payload))