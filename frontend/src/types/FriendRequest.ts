interface FriendRequest
{
	id: number
	sender: number
	receiver: number
	status: "pending" | "accepted" | "rejected" | "removed"
	created_at: string
}
