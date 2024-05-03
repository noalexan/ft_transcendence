"use client"

import { createContext, useContext, useEffect, useState } from "react"
import { useRouter } from "next/navigation"

import toast from "react-hot-toast"

type Status = "loading" | "conected" | "disconnected"

const GameContext = createContext<{
	status: Status,
	sendMessage?: (message: any) => void,
	message: any,
	players: string[],
}>({
	status: "loading",
	players: [],
	message: undefined,
})

export function useGame() {
	return useContext(GameContext)
}

export function GameProvider({
	children,
}: {
	children: React.ReactNode,
}): React.JSX.Element {

	const router = useRouter()

	const [status, setStatus] = useState<Status>("loading")
	const [players, setPlayers] = useState<string[]>([])
	const [ws, setWs] = useState<WebSocket | null>(null)
	const [message, setMessage] = useState<any>()

	useEffect(() => {
		const ws = new WebSocket(`ws://${window.location.hostname}:8000/ws/game/`)

		ws.onopen = function(event: Event) {
			setStatus("conected")
		}

		ws.onmessage = function(event: MessageEvent<any>) {
			const data = JSON.parse(event.data)

			switch (data["type"]) {
				case "game.create": {
					toast(data.message, {icon: "🍖"})
					setPlayers(data.players)
					router.push(`/game/${data.room_uuid}`)
					break
				}
				case "game.join": {
					toast(data.message, {icon: "⚔️"})
					setPlayers(data.players)
					router.push(`/game/${data.room_uuid}`)
					break
				}

				case "game.quit": {
					setPlayers(data.players)
					toast(data.message, {icon: "🔨"})
					break
				}
				case "game.null": {
					toast(data.message, {icon: "🍊"})
					break
				}

				default: {
					setMessage(data)
					break
				}
			}
		}

		ws.onerror = function(event: Event) {
			console.error("[WEBSOCKET ERROR]: ", event)
		}

		ws.onclose = function(event: CloseEvent) {
			setStatus("disconnected")
			ws.close()
		}

		setWs(ws)

		return () => {
			ws.close()
		}
	}, [router])

	const sendMessage = (message: any) => {
		if (ws && ws?.readyState === WebSocket.OPEN) {
			ws.send(JSON.stringify(message))
		} else {
			console.error("[SEND MESSAGE ERROR]: Websocket isn't open.")
		}
	}

	return (
		<GameContext.Provider value={{ status, players, sendMessage, message }}>
			{children}
		</GameContext.Provider>
	)
}
