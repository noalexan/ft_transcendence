"use client"

import { useEffect, useState } from "react"

import { useSession } from "@/providers/Session"

import "@/styles/profile/Profile.css"
import Link from "next/link"
import toast from "react-hot-toast"

function HistoryExtended({
	user
}: {
	user?: User
}): React.JSX.Element
{
	const { session } = useSession()
	const [Game, setGames] = useState<Game[]>()

	if (session)
	{
		if (user === undefined)
		{
			user = session
		}
	}

	useEffect(() => {
		if (user)
		{
			const fetchStats = async () => {
				const response = await toast.promise(
					fetch(`https://${window.location.hostname}:8000/game/?user=${user?.id}`),
					{
						loading: `Fetching /game/?user=${user?.id}`,
						success: `/game/?user=${user?.id} fetched`,
						error: `Unable to fetch /game/?user=${user?.id}`
					}
				)

				if (response?.ok)
				{
					const data = await response.json()
					setGames(data)
				}
			}

			fetchStats()
		}
	}, [user])

	const formatDateTime = (datetime: string) => {
		const date = new Date(datetime)
		const options: Intl.DateTimeFormatOptions = {
			year: 'numeric',
			month: 'long',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit',
			second: '2-digit',
		}
		return date.toLocaleDateString(undefined, options)
	}

	return (
		<ul>
			{Game?.map((stat, index) => {
				const isPlayer1 = stat.player_1.login === session?.login
				const isVictory = isPlayer1 ? (stat.score1 > stat.score2) : (stat.score2 > stat.score1)
				const formattedDateTime = formatDateTime(stat.created_at)

				return(
					<li className="finished-games" key={index}
					style={{
						flexDirection: "row",
						alignItems: "center",
						backgroundColor:
							isVictory
							? "rgba(86, 174, 87, 1)"
							: "rgba(190, 23, 15, 1)",
					}}>
						<div style={{display: "flex", flexDirection: "column", alignItems: "center"}}>
							<div
								className="rounded-circle bg-cover"
								style={{
									backgroundImage: `url("https://${window.location.hostname}:8000${stat.player_1.avatar}")`,
									backgroundSize: "cover",
									backgroundPosition: "center center",
									backgroundRepeat: "no-repeat",
									width: "75px",
									height: "75px"
								}}
							/>
							<Link href={`/users/${stat.player_1.login}`}>
								<div className="login-name" style={{marginTop: "0.5rem"}}>
									<p>{stat.player_1.display_name}</p>
								</div>
							</Link>
						</div>

						<div className="bubble-info"
							style={{
								backgroundColor: isVictory
								? "rgba(10, 167, 10, 1)"
								: "rgba(255, 0, 0, 1)",
							}}>
							<div>
								{isVictory ? (
									<h2>VICTORY</h2>
								) : (
									<h2>DEFEAT</h2>
								)}
							</div>

							<p>
								{formattedDateTime}
							</p>

							<h1>
								{stat.score1}
								{" - "}
								{stat.score2}
							</h1>
						</div>

						<div style={{display: "flex", flexDirection: "column", alignItems: "center"}}>
							<div
								className="rounded-circle bg-cover"
								style={{
									backgroundImage: `url("https://${window.location.hostname}:8000${stat.player_2.avatar}")`,
									backgroundSize: "cover",
									backgroundPosition: "center center",
									backgroundRepeat: "no-repeat",
									width: "75px",
									height: "75px"
								}}
							/>
							<Link href={`/users/${stat.player_2.login}`}>
								<div className="login-name" style={{marginTop: "0.5rem"}}>
									<p>{stat.player_2.display_name}</p>
								</div>
							</Link>
						</div>
					</li>
				)
			})}
		</ul>
	)
}

export default HistoryExtended
