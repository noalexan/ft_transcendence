from django.dispatch import receiver
from django.shortcuts import get_object_or_404
from django.http import HttpRequest, JsonResponse
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_GET

import urllib.parse
import json

from chat.serializers import ChatSerializer
from friends.models import FriendRequest
from users.models import User
from chat.models import Chat
from utils.decorators import need_user


class Block(View):

    @method_decorator((need_user), name="dispatch")
    def get(self, request: HttpRequest, user: User) -> JsonResponse:
        return JsonResponse(
            list(user.blocked.values("id", "login", "display_name", "created_at")),
            safe=False,
        )

    @method_decorator((need_user), name="dispatch")
    def post(self, request: HttpRequest, user: User) -> JsonResponse:
        if len(request.body) == 0:
            return JsonResponse(
                {"error": "Bad Request", "message": "Missing body."}, status=400
            )

        try:
            body_payload = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "Bad Request", "message": "Body must be JSON."}, status=400
            )

        receiver_id = body_payload.get("user_id")

        if receiver_id is None:
            return JsonResponse(
                {"error": "Bad Request", "message": "No 'user_id' provided."},
                status=400,
            )

        receiver = get_object_or_404(User, id=receiver_id)

        if user.id == receiver.id:
            return JsonResponse(
                {"error": "Bad Request", "message": "IDs are equal."}, status=400
            )

        if user.blocked.contains(receiver):
            return JsonResponse(
                {
                    "error": "Bad Request",
                    "message": f"'{receiver.login}' is already in your blocked list.",
                },
                status=400,
            )

        if user.friends.contains(receiver):
            user.friends.remove(receiver)

            try:
                friend_request = FriendRequest.objects.get(
                    sender=user,
                    receiver=receiver,
                    status__in=[
                        FriendRequest.STATUS_PENDING,
                        FriendRequest.STATUS_ACCEPTED,
                    ],
                )
            except FriendRequest.DoesNotExist:
                friend_request = get_object_or_404(
                    FriendRequest,
                    sender=receiver,
                    receiver=user,
                    status__in=[
                        FriendRequest.STATUS_PENDING,
                        FriendRequest.STATUS_ACCEPTED,
                    ],
                )

            friend_request.status = FriendRequest.STATUS_BLOCKED
            friend_request.save()

        user.blocked.add(receiver)

        return JsonResponse(
            list(user.blocked.values("id", "login", "display_name", "created_at")),
            safe=False,
        )

    @method_decorator((need_user), name="dispatch")
    def delete(self, request: HttpRequest, user: User) -> JsonResponse:
        if len(request.body) == 0:
            return JsonResponse(
                {"error": "Bad Request", "message": "Missing body."}, status=400
            )

        try:
            body_payload = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "Bad Request", "message": "Body must be JSON."}, status=400
            )

        receiver_id = body_payload.get("user_id")

        if receiver_id is None:
            return JsonResponse(
                {"error": "Bad Request", "message": "Missing required fields."},
                status=400,
            )

        receiver = get_object_or_404(User, id=receiver_id)

        if user.id == receiver.id:
            return JsonResponse(
                {"error": "Bad Request", "message": "IDs are equal."}, status=400
            )

        if not user.blocked.contains(receiver):
            return JsonResponse(
                {
                    "error": "Bad Request",
                    "message": f"'{receiver.login}' isn't in your blocked list.",
                },
                status=400,
            )

        user.blocked.remove(receiver)

        return JsonResponse(
            list(user.blocked.values("id", "login", "display_name", "created_at")),
            safe=False,
        )


@require_GET
@need_user
def get_conv(request: HttpRequest, user: User) -> JsonResponse:
    target_id = request.GET.get("user")

    if target_id is None:
        return JsonResponse({"error": "Bad Request", "message": "You must provide `user`."}, status=400)

    try:
        target = User.objects.get(id=target_id)
    except User.DoesNotExist:
        return JsonResponse({"error": "Not Found", "message": "The provided id does not match a user."}, status=404)

    all_user_chat = Chat.objects.filter(Q(sender=target, receiver=user) | Q(receiver=target, sender=user))
    chat_list = [ChatSerializer(chat).data for chat in all_user_chat]

    return JsonResponse(chat_list, safe=False)


@require_GET
@need_user
def get_all_convs(request: HttpRequest, user: User) -> JsonResponse:
    crspdts = User.objects.filter(
        id__in=[chat.sender.id for chat in user.received_messages.all()]
            + [chat.receiver.id for chat in user.sent_messages.all()]
    )

    chats = [
        ChatSerializer(
            Chat.objects.filter(
                Q(sender=user, receiver=crspdt)
                    | Q(sender=crspdt, receiver=user)
            ).order_by("-id").first()
        ).data
        for crspdt in crspdts
    ]

    return JsonResponse(chats, safe=False)