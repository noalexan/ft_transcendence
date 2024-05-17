"use client"

import Link from "next/link"
import toast from "react-hot-toast"
import { useEffect, useState } from "react"

import { useSession } from "@/providers/Session"
import { useSocket } from "@/providers/Socket"


function FriendsList(): React.JSX.Element {
	const { session } = useSession()
	const socket = useSocket()

	const [friendsList, setFriendsList] = useState<User[]>([])
	const [friendRequestsList, setFriendRequestsList] = useState<User[]>([])

	useEffect(() => {
		if (session) {
			const fetchFriendRequestsList = async () => {
				const response = await session.api("/users/friends/requests/")
				const data = await response.json()
				setFriendRequestsList(data)
			}

			const fetchFriendsList = async () => {
				const response = await session.api("/users/friends/")
				const data = await response.json()
				setFriendsList(data)
			}

			fetchFriendRequestsList().catch(e => toast.error("Something went wrong. Try again later"))
			fetchFriendsList().catch(e => toast.error("Something went wrong. Try again later"))
		}
	}, [session])

	useEffect(() => {
		if (socket) {
		}
	}, [socket])

	const FriendsListItem = ({ user, index }: { user: User, index: number }): React.JSX.Element => {
		const handleRemove = () => {
			session?.api("/users/friends/", "DELETE", JSON.stringify({ user_id: user.id }))
				.catch(() => toast.error("Remove failed, try again"))
				.then(() => setFriendsList(friendsList.slice(index, index)))
		}

		const handleBlock = () => {
			session?.api("/chat/block/", "POST", JSON.stringify({ user_id: user.id }))
				.catch(() => toast.error("Remove failed, try again"))
				.then(() => setFriendsList(friendsList.slice(index, index)))
		}

		return (
			<li style={{display: "flex", flexDirection: "column"}}>
				<Link href={`/users/${user.login}`}>
					<h5>{user.display_name}</h5>
				</Link>
				<div className="btn-group">
					<button className="btn btn-success" onClick={handleRemove}>remove</button>
					<button className="btn btn-danger" onClick={handleBlock}>block</button>
				</div>
			</li>
		)
	}

	const FriendRequestsListItem = ({ user, index }: { user: User, index: number }): React.JSX.Element => {
		const handleAdd = () => {
			session?.api("/users/friends/", "POST", JSON.stringify({ user_id: user.id }))
				.then(() => setFriendRequestsList(friendRequestsList.slice(index, index)))
				.catch(() => toast.error("Add failed, try again"))
		}

		const handleReject = () => {
			session?.api("/users/friends/", "DELETE", JSON.stringify({ user_id: user.id }))
				.then(() => setFriendRequestsList(friendRequestsList.slice(index, index)))
				.catch(() => toast.error("Rejct failed, try again"))
		}

		return (
			<li style={{display: "flex", flexDirection: "column"}}>
				<Link href={`/users/${user.login}`}>
					<h5>{user.display_name}</h5>
				</Link>
				<div className="btn-group">
					<button className="btn btn-success" onClick={handleAdd}>add</button>
					<button className="btn btn-danger" onClick={handleReject}>reject</button>
				</div>
			</li>
		)
	}

	return (
		<ul className="list-unstyled">
			{friendRequestsList.map((friend, key) => <FriendRequestsListItem key={key} user={friend} index={key} />)}
			{friendRequestsList.length != 0 && <hr />}
			{friendsList.map((friend, key) => <FriendsListItem key={key} user={friend} index={key} />)}
		</ul>
	)
}

export default FriendsList
