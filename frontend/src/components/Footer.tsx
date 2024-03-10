"use client"

import Image from "next/image"
import Link from "next/link"

import { useModal } from "@/providers/Modal"

import "@/styles/components/Footer/Footer.css"
import "@/styles/components/Footer/Settings.css"

function Footer(): React.JSX.Element | null {

	const { createModal } = useModal();

	const settingsModal =
	<div className="modal-wrapper">
		<p className="text-title-settings">Settings</p>
		<ul style={{justifyContent: "space-between", display: "flex"}} className="list-inline">
			<div className="d-flex align-items-center">
				<li className="list-inline-item">
					<Image className="modal-icon"
						src={"/svg/volume-setting.svg"}
						width={30}
						height={30}
						alt="volume">
					</Image>
				</li>
				<li className="list-inline-item">Sound</li>
			</div>
			<li className="list-inline-item">
				<div className="btn-group" role="group">
					<input type="radio" className="btn-check" name="sound-outlined" id="success-sound" autoComplete="on"></input>
					<label className="btn btn-outline-success" htmlFor="success-sound">ON</label>
					<input type="radio" className="btn-check" name="sound-outlined" id="danger-sound" autoComplete="on"></input>
					<label className="btn btn-outline-danger" htmlFor="danger-sound">OFF</label>
				</div>
			</li>
		</ul>
		<ul style={{justifyContent: "space-between", display: "flex"}} className="list-inline">
			<div className="d-flex align-items-center">
				<li className="list-inline-item">
					<Image className="modal-icon"
						src={"/svg/dark-mode-setting.svg"}
						width={30}
						height={30}
						alt="dark mode">
					</Image>
				</li>
				<li className="list-inline-item">Dark mode</li>
			</div>
			<li className="list-inline-item">
				<div className="btn-group" role="group">
					<input type="radio" className="btn-check" name="dark-mode-outlined" id="success-dark-mode" autoComplete="on"></input>
					<label className="btn btn-outline-success" htmlFor="success-dark-mode">ON</label>
					<input type="radio" className="btn-check" name="dark-mode-outlined" id="danger-dark-mode" autoComplete="on"></input>
					<label className="btn btn-outline-danger" htmlFor="danger-dark-mode">OFF</label>
				</div>
			</li>
		</ul>
		<ul style={{justifyContent: "space-between", display: "flex"}} className="list-inline">
			<div className="d-flex align-items-center">
				<li className="list-inline-item">
					<Image className="modal-icon"
						src={"/svg/2fa-setting.svg"}
						width={30}
						height={30}
						alt="2fa">
					</Image>
				</li>
				<li className="list-inline-item">Two factor authentication</li>
			</div>
			<li className="list-inline-item">
				<div className="btn-group" role="group">
					<input type="radio" className="btn-check" name="options-outlined" id="success-outlined" autoComplete="on"></input>
					<label className="btn btn-outline-success" htmlFor="success-outlined">ON</label>
					<input type="radio" className="btn-check" name="options-outlined" id="danger-outlined" autoComplete="on"></input>
					<label className="btn btn-outline-danger" htmlFor="danger-outlined">OFF</label>
				</div>
			</li>
		</ul>
		<ul style={{justifyContent: "space-between", display: "flex"}} className="list-inline mt-4">
			<li className="list-inline-item">
				<button type="button" className="btn btn-primary">Change profile picture</button>
			</li>
			<li className="list-inline-item">
				<button type="button" className="btn btn-success btn-size">Change pseudo</button>
			</li>
		</ul>
		<div className="justify-content-center d-flex align-items-center">
			<button type="button" className="btn btn-danger">Log out</button>
		</div>
	</div>

	const session = 1 //! 1 for CONNECTED, 0 for NOT CONNECTED (placeholder for waiting the authentification)

	if (session) {
		return (
			<footer className="footer-wrapper">
				<Link href="/chat" className="link">
					<Image className="image"
						src={"/svg/chat.svg"}
						width={30}
						height={30}
						alt="Chat"
					/>
					Chat
				</Link>

				<button className="btn shadow-none" onClick={() => { createModal(settingsModal, 500, 400); } }>
					<Link href="" className="link">
						<Image className="image"
							src={"/svg/settings.svg"}
							width={30}
							height={30}
							alt="Settings"
						/>
						Settings
					</Link>
				</button>
			</footer>
		)
	}

	return null
}

export default Footer
