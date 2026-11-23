from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .models import Message

User = get_user_model()

@login_required
def chat_view(request, user_id=None):
    # Dynamically select base template by role
    base_template = 'accounts/base.html'
    if hasattr(request.user, 'supervisor_profile'):
        base_template = 'supervision/base.html'

    if user_id:
        other_user = get_object_or_404(User, id=user_id)
        
        if not can_message_users(request.user, other_user):
            return render(request, "notifications/chat.html", {
                "mode": "direct",
                "other_user": other_user,
                "messages": Message.objects.none(),
                "error": "You are not authorized to message this user.",
                "base_template": base_template,
            })
        
        
        messages = Message.objects.filter(
            Q(sender=request.user, recipient=other_user) |
            Q(sender=other_user, recipient=request.user)
        ).order_by("timestamp")
        
        
        Message.objects.filter(
            sender=other_user,
            recipient=request.user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())

        return render(
            request,
            "notifications/chat.html",
            {
                "mode": "direct",
                "other_user": other_user,
                "messages": messages,
                "base_template": base_template,
            },
        )
    else:
        conversations = []
        
        sent_users = Message.objects.filter(
            sender=request.user
        ).values_list('recipient', flat=True).distinct()
        
        received_users = Message.objects.filter(
            recipient=request.user
        ).values_list('sender', flat=True).distinct()
        
        user_ids = set(sent_users) | set(received_users)
        
        for user_id in user_ids:
            user = User.objects.get(id=user_id)
            
            last_message = Message.objects.filter(
                Q(sender=request.user, recipient=user) |
                Q(sender=user, recipient=request.user)
            ).order_by('-timestamp').first()
            
            unread_count = Message.objects.filter(
                sender=user,
                recipient=request.user,
                is_read=False
            ).count()
            
            conversations.append({
                'user': user,
                'last_message': last_message,
                'unread_count': unread_count
            })
            
        
        conversations.sort(key=lambda x: x['last_message'].timestamp if x['last_message'] else timezone.make_aware(timezone.datetime.min), reverse=True)

        return render(
            request,
            "notifications/chat.html",
            {
                "mode": "inbox",
                "conversations": conversations,
                "total_unread": Message.get_unread_count(request.user),
                "base_template": base_template,
            },
        )


@login_required
@require_POST
def send_message(request, user_id):
    """HTTP POST fallback to send a message if websockets are unavailable."""
    try:
        recipient = get_object_or_404(User, id=user_id)
        if not can_message_users(request.user, recipient):
            return JsonResponse({"ok": False, "error": "Not authorized"}, status=403)

        content = (request.POST.get('content') or '').strip()
        if not content:
            return JsonResponse({"ok": False, "error": "Empty message"}, status=400)

        msg = Message.objects.create(sender=request.user, recipient=recipient, content=content)
        return JsonResponse({
            "ok": True,
            "id": msg.id,
            "timestamp": msg.timestamp.isoformat(),
            "sender_username": request.user.get_username(),
        })
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


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