from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from json.decoder import JSONDecodeError
from uuid import uuid4

from users.models import User
from game.models import Game

import json
import asyncio
import math
import random


WAITING_ROOMS    = []
TOURNAMENT_ROOMS = []
FINAL_ROOMS      = []

MAX_BOUNCE_ANGLE = 5 * math.pi / 12
ACCELERATION_FACTOR = 1.10

MAX_SPEED = 0.015
SPEED_INCREMENT = 0.021

END_GAME = 10

class GameConsumer(AsyncWebsocketConsumer):

############# ? Channel Send Message ? ##############

  async def game_endTournament(self, text_data):
    await self.channel_layer.group_discard(
      self.room_group_name,
      self.channel_name
    )
    await self.send(json.dumps(text_data))

  async def game_finalJoin(self, text_data):
    text_data["type"] = "game.nextStep"
    await self.send(json.dumps(text_data))

  async def game_tournamentJoin(self, text_data):
    await self.send(json.dumps(text_data))

  async def game_tournamentQuit(self, text_data):
    await self.send(json.dumps(text_data))

  async def game_nextStep(self, text_data):
    await self.send(json.dumps(text_data))

  async def game_reloadlogin(self, text_data):
    self.current_room["login"] = text_data["list"]

  async def game_tournamentLaunch(self, text_data):
    for room in TOURNAMENT_ROOMS:
      if room["tournament_uuid"] == text_data["tournament_uuid"]:

        if room["login"][0] == self.user.login or room["login"][1] == self.user.login:
          self.player = 1 if room["login"][0] == self.user.login else 2

          self.room_group_name = text_data["matchs"][0]
          await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
          )
          self.current_room = {
            "type": "game.tournamentLaunch",
            "tournament_uuid": text_data["tournament_uuid"],
            "room_uuid": text_data["matchs"][0],
            "login": [
              room["login"][0],
              room["login"][1],
            ],
            "final": text_data["matchs"][2], 
            "message": f"{self.user.display_name} has joined the room of the tournament",
            "score1": 0,
            "score2": 0,
          }
          await self.send(json.dumps(self.current_room))

        elif room["login"][2] == self.user.login or room["login"][3] == self.user.login:
          self.player = 1 if room["login"][2] == self.user.login else 2

          self.room_group_name = text_data["matchs"][1]
          await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
          )
          self.current_room = {
            "type": "game.tournamentLaunch",
            "tournament_uuid": text_data["tournament_uuid"],
            "room_uuid": text_data["matchs"][1],
            "login": [
              room["login"][2],
              room["login"][3],
            ],
            "final": text_data["matchs"][2],
            "message": f"{self.user.display_name} has joined the room of the tournament",
            "score1": 0,
            "score2": 0,
          }
          await self.send(json.dumps(self.current_room))

  async def game_paddles(self, text_data):
    await self.send(json.dumps({"player": self.player}))
    if self.player == 1:
      if text_data["key"] == "up" and self.py_2 <= 1:
        if (self.py_2 - self.ph / 2) - 0.01 <= 0:
          self.py_2 = 0 + self.ph / 2
        else:
          self.py_2 -= SPEED_INCREMENT

      elif text_data["key"] == "down" and self.py_2 >= 0:
        if (self.py_2 + self.ph / 2) + 0.01 >= 1:
          self.py_2 = 1 - self.ph / 2
        else:
          self.py_2 += SPEED_INCREMENT

  async def game_quit(self, text_data):
    try:
      cancel = self.loop.cancel()
    except Exception:
      # ? Player 2 is not the host
      try:
        await self.channel_layer.group_send(self.room_group_name, {
          "type": "game.break",
        })
      except:
        # * Not in an actual room
        pass
    await self.send(json.dumps(text_data))

  async def game_join(self, text_data):
    await self.send(json.dumps(text_data))

  async def game_update(self, text_data):
    await self.send(json.dumps(text_data))

  async def game_point(self, text_data):
    await self.send(json.dumps(text_data))

  async def game_finished(self, text_data):
    try:
      cancel = self.loop.cancel()
    except Exception:
      # ? Player 2 is not the host
      await self.channel_layer.group_send(self.room_group_name, {
        "type": "game.break",
      })

    try:
      for room in WAITING_ROOMS:
        if room["room_uuid"] == self.room_group_name.split("_")[-1]:
          player_1 = room["login"][0]
          player_2 = room["login"][1]
          score1 = self.score1
          score2 = self.score2

          user_1 = await sync_to_async(User.objects.get)(login=player_1)
          user_2 = await sync_to_async(User.objects.get)(login=player_2)

          trophy_change = abs(score1 - score2) * 3

          game = await sync_to_async(Game.objects.create)(
            player_1=user_1,
            player_2=user_2,
            score1=score1,
            score2=score2,
            room_uuid=room["room_uuid"],
          )

          game.winner.trophies += trophy_change
          if game.winner.highest_trophies < game.winner.trophies:
            game.winner.highest_trophies = game.winner.trophies
          await sync_to_async(game.winner.save)()

          game.looser.trophies -= trophy_change
          if game.looser.trophies < 0:
            game.looser.trophies = 0
          await sync_to_async(game.looser.save)()

          break

    except Exception:
      # ? Player 2 is not the host
      pass

    is_found = False

    for room in WAITING_ROOMS:
      if room["room_uuid"] == self.room_group_name.split("_")[-1] and self.user.login in room["login"]:
        is_found = True
        room["login"].remove(self.user.login)

        if not room["login"]:
          WAITING_ROOMS.remove(room)

        elif room["host"] == self.user.login:
          room["host"] = room["login"][0]

        await self.channel_layer.group_send(self.room_group_name, {
          "type": "game.quit",
          "login": room["login"],
          "message": f"{self.user.display_name} has left the room.",
        })
        break

    if is_found == False:
      await self.channel_layer.group_discard(
        self.room_group_name,
        self.channel_name
      )

      if self.user.login == text_data["winner"]:
        room = self.current_room
        self.room_group_name = room["final"]
        found = False

        # self.player = 1 if 1 <= room["login"].index(self.user.login) <= 2 else 2

        for index in FINAL_ROOMS:
          if index["uuid"] == self.room_group_name:
            await self.send(json.dumps({
              "index": index["login"],
              "room": room["login"],
            }))
            if len(index["login"]) == 2:
              self.current_room["type"] = "game.endTournament"
              self.current_room["message"] = f"{text_data["winner"]} has won the tournament !"

              # ! END OF THE MATCH AND TOURNAMENT
              await self.send(json.dumps(self.current_room))
              # !

              await self.channel_layer.group_send(self.room_group_name,
                self.current_room
              )
              await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
              )
              await self.channel_layer.group_discard(
                self.current_room["tournament_uuid"],
                self.channel_name
              )
              FINAL_ROOMS.remove(index)
              for index_t in TOURNAMENT_ROOMS:
                if index_t["tournament_uuid"] == self.current_room["tournament_uuid"]:
                  TOURNAMENT_ROOMS.remove(index_t)
              self.current_room = {}
              return

          if index["uuid"] == room["final"]:
            index["login"].append(self.user.login)
            final_login = index["login"]
            self.player = 2
            await self.channel_layer.group_send(index["uuid"], {
              "type": "game.reloadlogin",
              "list": final_login,
            })

            await self.channel_layer.group_add(
              self.room_group_name,
              self.channel_name
            )

            self.current_room = {
              "type": "game.finalJoin",
              "tournament_uuid": room["tournament_uuid"],
              "room_uuid": room["final"],
              "login": final_login,
              "final": room["final"],
              "message": f"{self.user.display_name} has joined the room of the tournament",
              "score1": 0,
              "score2": 0,
            }

            await self.channel_layer.group_send(self.room_group_name,
              self.current_room
            )
            found = True
            return

        if not found:
          FINAL_ROOMS.append({
            "uuid": room["final"],
            "login": [
              self.user.login,
            ],
          })

          self.player = 1

          final_login = [
            self.user.login,
          ]

          await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
          )

          self.current_room = {
            "type": "game.finalJoin",
            "tournament_uuid": room["tournament_uuid"],
            "room_uuid": room["final"],
            "login": final_login,
            "final": room["final"],
            "message": f"{self.user.display_name} has joined the room of the tournament ",
            "score1": 0,
            "score2": 0,
          }
          self.room_group_name = room["final"]
          await self.channel_layer.group_send(self.room_group_name,
            self.current_room
          )
          return

      else:
        await self.send(json.dumps({
          "type": "game.nextStep",
          "looser": self.user.login,
          "message": "You lose.", 
        }))
        await self.channel_layer.group_discard(
          self.room_group_name,
          self.channel_name
        )
        await self.channel_layer.group_discard(
          self.tournament_name,
          self.channel_name
        )

        for index in TOURNAMENT_ROOMS:
          if index["tournament_uuid"] == self.current_room["tournament_uuid"]:
            index["login"].remove(self.user.login)

      self.current_room = {}
      return

    self.score1, self.score2 = 0, 0

    await self.channel_layer.group_discard(
      self.room_group_name,
      self.channel_name
    )

    await self.send(json.dumps(text_data))

  async def game_countdown(self, text_data):
    self.countdown = False

################## AT START ###################
    if text_data["when"] == "begin":
      sounds = ["", "wall", "paddle", "score"]
      for i, seconds in enumerate(range(3, -1, -1)):
        data = {
          "type": "game.countdown",
          "when": "begin",
          "seconds": seconds,
        }
        if i < len(sounds):
          data["sound"] = sounds[i]
        await self.send(text_data=json.dumps(data))
        await asyncio.sleep(1)

      self.countdown = True
####################################################

################## HIT A POINT ###################
    elif text_data["when"] == "in-game":
      for seconds in range(1, -1, -1):
        await self.send(text_data=json.dumps({
          "type": "game.countdown",
          "when": "in-game",
          "seconds": seconds,
        }))
      await asyncio.sleep(1)
      self.countdown = True
####################################################

  async def game_break(self, text_data):
    try:
      cancel = self.loop.cancel()
    except Exception:
      # ? Player 2 is not the host
      pass
###################################################?

  async def game_begin(self, text_data=None):
    self.score1 = 0
    self.score2 = 0

    await self.channel_layer.group_send(self.room_group_name, {
      "type": "game.point",
      "player": 1,
      "score1": 0,
    })

    await self.channel_layer.group_send(self.room_group_name, {
      "type": "game.point",
      "player": 2,
      "score2": 0,
    })
    self.loop = asyncio.create_task(self.game_loop()) # ? Line 420

  async def game_tournamentGameBegin(self):
    self.score1 = 0
    self.score2 = 0

    await self.channel_layer.group_send(self.room_group_name, {
      "type": "game.point",
      "player": 1,
      "score1": 0,
    })

    await self.channel_layer.group_send(self.room_group_name, {
      "type": "game.point",
      "player": 2,
      "score2": 0,
    })
    self.loop = asyncio.create_task(self.game_loop()) # ? Line 420

####################################################
####################################################
  async def game_loop(self):
    update = 1

    try:
      self.x, self.y = 1 / 2, 1 / 2
      self.w, self.h = 1 / 35, 1 / 35
      self.vx, self.vy = (1 / 200), 0

      self.px_1, self.py_1 = 1 / 30, 1 / 2
      self.px_2, self.py_2 = 29 / 30, 1 / 2
      self.pw, self.ph = 1 / 125, 1 / 5

      ball_info = {
        "coordinates": [self.x, self.y],
        "dimensions": [self.w, self.h],
        "speed": [self.vx, self.vy],
        "paddle_coord_1": [self.px_1, self.py_1],
        "paddle_coord_2": [self.px_2, self.py_2],
        "paddle_dimensions": [self.pw, self.ph],
      }

      await self.channel_layer.group_send(self.room_group_name, {
        "type": "game.update",
        "new_position": ball_info,
        "score1": self.score1,
        "score2": self.score2,
      })
      while True:
        # ? Countdown for starting a game and when a player hit a point
        if not self.countdown:
          await asyncio.sleep(0.016) # 60fps
          continue

        await asyncio.sleep(0.016) # 60fps
        update = await self.update_data(ball_info, update) # ? Line 486
        if update == 0:
          continue
        else:
          self.x, self.y = 1 / 2, 1 / 2
          self.w, self.h = 1 / 35, 1 / 35
          if update == 1:
            self.vx, self.vy = -(1 / 200), random.uniform(-0.005, 0.005)
          else:
            self.vx, self.vy = (1 / 200), random.uniform(-0.005, 0.005)


          self.px_1, self.py_1 = 1 / 30, 1 / 2
          self.px_2, self.py_2 = 29 / 30, 1 / 2
          self.pw, self.ph = 1 / 125, 1 / 5

          await self.channel_layer.group_send(self.room_group_name, {
            "type": "game.update",
            "new_position": ball_info,
            "score1": self.score1,
            "score2": self.score2,
          })
          update = 0
          self.ball_speed = 0.005
          continue

    except asyncio.CancelledError:
      # ! GAME LOOP WAS INTERUPTED
      del ball_info, self.x, self.y, self.w, self.h, self.py_1, self.py_2, self.px_1, self.px_2, self.loop

      pass
####################################################
####################################################
  async def update_data(self, ball_info: dict[str, list[float]], update: int) -> int:

    # ? Player 1 paddle collision
    if self.x + self.vx + -(self.w / 2) < self.px_1 + -(self.pw / 2):
      if self.py_1 - (self.ph / 2) < self.y + self.vy < self.py_1 + (self.ph / 2):
        relative_intersect_y = (self.py_1 - self.y) / (self.ph / 2)
        bounce_angle = relative_intersect_y * MAX_BOUNCE_ANGLE
        self.vx = self.ball_speed * math.cos(bounce_angle)
        self.vy = -self.ball_speed * math.sin(bounce_angle)
        if self.ball_speed <= MAX_SPEED:
          self.ball_speed *= ACCELERATION_FACTOR

        ball_info["sound"] = "paddle"
    # ?

    # ? Player 2 paddle collision
    if self.x + self.vx + (self.w / 2) > self.px_2 + (self.pw / 2):
      if self.py_2 - (self.ph / 2) < self.y + self.vy < self.py_2 + (self.ph / 2):
        relative_intersect_y = (self.py_2 - self.y) / (self.ph / 2)
        bounce_angle = relative_intersect_y * MAX_BOUNCE_ANGLE
        self.vx = -self.ball_speed * math.cos(bounce_angle)
        self.vy = -self.ball_speed * math.sin(bounce_angle)
        if self.ball_speed <= MAX_SPEED:
          self.ball_speed *= ACCELERATION_FACTOR

        ball_info["sound"] = "paddle"
    # ?

    # ? Collision woth the top or bot of the screen
    if (self.y + self.vy + (self.h / 2) > 1 or self.y + self.vy - (self.h / 2) < 0):
      self.vy *= -1
      ball_info["sound"] = "wall"
    # ?

    # * ball in the P2 side ---> P1 hit the point
    if self.x + self.vx + (self.w / 2) > 1.01:
      room = self.current_room
      if self.score1 < END_GAME and self.score2 < END_GAME:
        self.score1 += 1
      await self.channel_layer.group_send(self.room_group_name, {
        "type": "game.point",
        "player": 1,
        "score1": self.score1,
      })
      await self.channel_layer.group_send(self.room_group_name, {
        "type": "game.countdown",
        "when": "in-game",
      })
      if self.score1 >= END_GAME:
        await self.channel_layer.group_send(self.room_group_name, {
          "type": "game.finished",
          "winner": room["login"][0],
        })
      return 1
    # *

    # * ball in the P1 side ---> P2 hit the point
    if self.x + self.vx - (self.w / 2) < -0.01:
      room = self.current_room
      if self.score2 < END_GAME and self.score1 < END_GAME:
        self.score2 += 1
      await self.channel_layer.group_send(self.room_group_name, {
        "type": "game.point",
        "player": 2,
        "score2": self.score2,
      })
      await self.channel_layer.group_send(self.room_group_name, {
        "type": "game.countdown",
        "when": "in-game",
      })
      if self.score2 >= END_GAME:
        await self.channel_layer.group_send(self.room_group_name, {
          "type": "game.finished",
          "winner": room["login"][1],
        })
      return 2
    # *

    self.x += self.vx
    self.y += self.vy

    ball_info["coordinates"] = [self.x, self.y]
    ball_info["dimensions"] = [self.w, self.h]
    ball_info["speed"] = [self.vx, self.vy]
    ball_info["paddle_coord_1"] = [self.px_1, self.py_1]
    ball_info["paddle_coord_2"] = [self.px_2, self.py_2]
    ball_info["paddle_dimensions"] = [self.pw, self.ph]

    await self.channel_layer.group_send(self.room_group_name, {
      "type": "game.update",
      "new_position": ball_info,
      "score1": self.score1,
      "score2": self.score2,
    })
    if "sound" in ball_info:
      del ball_info["sound"]

    return 0
####################################################
####################################################

################## * Connection * ##################
  async def connect(self):
    self.user: User = self.scope.get("user")

    if self.user is None:
      # No User Authenticated
      await self.close()
    else:
      self.ball_speed = 0.005
      await self.accept()
###################################################*

#################### ? Receive ? ###################
  async def receive(self, text_data=None, bytes_data=None):
    try:
      data = json.loads(text_data)
    except JSONDecodeError:
      await self.send(json.dumps({
        "type": "socket.error",
        "message": "You must send only valid JSON."
      }))

    else:
      match data.get("type"):
      ############## Paddles Movements ###############
        case "game.paddle":
          if self.player == 1:
            if data["key"] == "up" and self.py_1 <= 1:
              if (self.py_1 - self.ph / 2) - 0.01 <= 0:
                self.py_1 = 0 + self.ph / 2
              else:
                self.py_1 -= SPEED_INCREMENT

            elif data["key"] == "down" and self.py_1 >= 0:
              if (self.py_1 + self.ph / 2) + 0.01 >= 1:
                self.py_1 = 1 - self.ph / 2
              else:
                self.py_1 += SPEED_INCREMENT

            ball_info = {
              "coordinates": [self.x, self.y],
              "dimensions": [self.w, self.h],
              "speed": [self.vx, self.vy],
              "paddle_coord_1": [self.px_1, self.py_1],
              "paddle_coord_2": [self.px_2, self.py_2],
              "paddle_dimensions": [self.pw, self.ph],
            }

            await self.channel_layer.group_send(self.room_group_name, {
              "type": "game.update",
              "new_position": ball_info,
              "score1": self.score1,
              "score2": self.score2,
            })

          elif self.player == 2:
            await self.channel_layer.group_send(self.room_group_name, {
              "type": "game.paddles",
              "key": data["key"]
            })
        ################################################

        ############### Launch The Game ################
        case "game.begin":
          await self.channel_layer.group_send(self.room_group_name, {
            "type": "game.countdown",
            "when": "begin",
          })
          await self.game_begin() # ? Line 384
        ################################################

        ############### Finish The Game ################
        case "game.finished":
          if hasattr(self, "room_group_name"):
            for room in WAITING_ROOMS:
              if room["room_uuid"] == self.room_group_name.split("_")[-1] and self.user.login in room["login"]:
                room["login"].remove(self.user.login)
                if not room["login"]:
                  WAITING_ROOMS.remove(room)
                elif room["host"] == self.user.login:
                  room["host"] = room["login"][0]
                await self.channel_layer.group_send(self.room_group_name, {
                  "type": "game.quit",
                  "login": room["login"],
                  "message": f"{self.user.display_name} has left the room.",
                })
                break

            await self.channel_layer.group_discard(
              self.room_group_name,
              self.channel_name
            )
      #      await self.channel_layer.group_discard(
       #       self.tournament_name,
        #      self.channel_name
         #   )
        ################################################

        ############## Creation of a Room ##############
        case "game.create":
          for room in WAITING_ROOMS:
            if self.user.login in room["login"]:
              await self.send(text_data=json.dumps({
                "type": "game.error",
                "message": "You are already in a game",
              }))
              return

          self.player = 1
          self.score1, self.score2 = 0, 0
          room_uuid = uuid4()

          room = {
            "room_uuid": str(room_uuid),
            "host": self.user.login,
            "limit": 2,
            "login": [
              self.user.login,
            ],
          }

          WAITING_ROOMS.append(room)
          self.room_group_name = f"game_room_{room_uuid}"

          await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
          )

          await self.send(text_data=json.dumps({
            "type": "game.create",
            "room_uuid": str(room_uuid),
            "login": room["login"],
            "message": f"A new room was created by {self.user}.",
            "score1": self.score1,
            "score2": self.score2,
          }))
          self.current_room = room
        ################################################

        ################ Joining a Room ################
        case "game.join":
          for room in WAITING_ROOMS:
              if self.user.login in room["login"]:
                await self.send(text_data=json.dumps({
                  "type": "game.error",
                  "message": "You are already in a game",
                }))
                return 
          self.score1, self.score2 = 0, 0
        # * ############### MATCHMAKING ################
          diff = 0
          self.player = 2

          min_diff = float('inf')
          room_index = -1

          for i, room in enumerate(WAITING_ROOMS):
            if room["room_uuid"] and len(room["login"]) < 4:

              if room["host"] == self.user.login or room["login"][0] == self.user.login:
                break

              self.current_room = room

              player_1 = await sync_to_async(User.objects.get)(login=room["login"][0])
              if len(room["login"]) == 1:

                my_trophies = self.user.trophies

                diff = abs(my_trophies - player_1.trophies)

                if diff < min_diff:
                  min_diff = diff
                  room_index = i
              else:
                player_2 = await sync_to_async(User.objects.get)(login=room["login"][1])

                diff = abs(player_1.trophies - player_2.trophies)

                if diff < min_diff:
                  min_diff = diff
                  room_index = i

          if room_index != -1:
            room = WAITING_ROOMS[room_index]
            self.room_group_name = f"game_room_{room["room_uuid"]}"
            await self.channel_layer.group_add(
              self.room_group_name,
              self.channel_name
            )
            room["login"].append(self.user.login)
            await self.channel_layer.group_send(self.room_group_name, {
              "type": "game.join",
              "room_uuid": room["room_uuid"],
              "login": room["login"],
              "message": f"{self.user.display_name} has joined the room.",
              "score1": self.score1,
              "score2": self.score2,
            })
        # * ############################################

          else:
            await self.send(text_data=json.dumps({
              "type": "game.null",
              "message": "No lobby found.",
            }))
            return
        ################################################

        ################## TOURNAMENT ##################
        case "game.tournament":
          for room in TOURNAMENT_ROOMS:
              if room.get("login") and self.user.login in room["login"]:
                await self.send(text_data=json.dumps({
                  "type": "game.error",
                  "message": "You are already in a tournament",
                }))
                return

          tournament_uuid = uuid4()
          self.tournament_name = f"tournament_room_{tournament_uuid}"

          await self.channel_layer.group_add(
            self.tournament_name,
            self.channel_name
          )

          await self.send(text_data=json.dumps({
            "type": "game.tournament",
            "tournament_uuid": str(tournament_uuid),
            "login": [self.user.login],
            "message": f"A new tournament was created by {self.user.display_name}.",
          }))

          TOURNAMENT_ROOMS.append({
            "tournament_uuid": str(tournament_uuid),
            "host": self.user.login,
            "login": [
              self.user.login,
            ],
            "open": True,
          })

        case "game.tournamentJoin":
          for room in TOURNAMENT_ROOMS:
            if self.user.login not in room["login"] and room["open"] and room["tournament_uuid"] and len(room["login"]) < 4 and room["host"] != self.user.login:

              self.tournament_name = f"tournament_room_{room["tournament_uuid"]}"
              await self.channel_layer.group_add(
                self.tournament_name,
                self.channel_name
              )
              room["login"].append(self.user.login)
              await self.channel_layer.group_send(self.tournament_name, {
                "type": "game.tournamentJoin",
                "tournament_uuid": room["tournament_uuid"],
                "login": room["login"],
                "message": f"{self.user.display_name} has joined the tournament.",
              })
              break

          else:
            await self.send(text_data=json.dumps({
              "type": "game.null",
              "message": "No tournament found.",
            }))
            return

        case "game.beginTournament":
          match1 = uuid4()
          match2 = uuid4()
          match3 = uuid4()
          for room in TOURNAMENT_ROOMS:
            if data["tournament_uuid"] == room["tournament_uuid"]:
              if len(room["login"]) == 4:
                room["open"] = False
                await self.channel_layer.group_send(self.tournament_name, {
                  "type": "game.tournamentLaunch",
                  "tournament_uuid": data["tournament_uuid"],
                  "message": "Tournament will begin.",
                  "matchs": [
                    str(match1),
                    str(match2),
                    str(match3),
                  ],
                })

        case "game.tournamentGameBegin":
          await self.channel_layer.group_send(self.room_group_name, {
            "type": "game.countdown",
            "when": "begin",
          })
          await self.game_tournamentGameBegin() # ? Line 401
    ################################################
###################################################?

################ ! Deconnection ! #################
  async def disconnect(self, close_code):
    if hasattr(self, "room_group_name"):

      if hasattr(self, "game_loop"):

        try:
          cancel = self.loop.cancel()
        except Exception:
          # ? Player 2 is not the host
          await self.channel_layer.group_send(self.room_group_name, {
            "type": "game.break",
          })
          pass


      for room in WAITING_ROOMS:
        if room["room_uuid"] == self.room_group_name.split("_")[-1] and self.user.login in room["login"]:
          room["login"].remove(self.user.login)
          if not room["login"]:
            WAITING_ROOMS.remove(room)
          elif room["host"] == self.user.login:
            room["host"] = room["login"][0]
          await self.channel_layer.group_send(self.room_group_name, {
            "type": "game.quit",
            "login": room["login"],
            "message": f"{self.user.display_name} has left the room.",
          })
          break

      if self.room_group_name:
        await self.channel_layer.group_discard(
          self.room_group_name,
          self.channel_name
        )



    if hasattr(self, "tournament_name"):

      if hasattr(self, "game_loop"):

        try:
          cancel = self.loop.cancel()
        except Exception:
          # ? Player 2 is not the host
          try:
            await self.channel_layer.group_send(self.room_group_name, {
              "type": "game.break",
            })
          except Exception:
            # * Not in an actual game
            pass
          pass

      for room in TOURNAMENT_ROOMS:
        if room["tournament_uuid"] == self.tournament_name.split("_")[-1] and self.user.login in room["login"]:
          room["login"].remove(self.user.login)
          if not room["login"]:
            TOURNAMENT_ROOMS.remove(room)
          elif room["host"] == self.user.login:
            room["host"] = room["login"][0]
          await self.channel_layer.group_send(self.tournament_name, {
            "type": "game.tournamentQuit",
            "login": room["login"],
            "message": f"{self.user.display_name} has left the tournament.",
          })

          if len(room["login"]) > 0:
            for participant in room["login"]:
              await self.channel_layer.group_send(self.tournament_name, {
                "type": "game.quit",
                "login": [],
                "message": f"{participant} has left the tournament because {self.user.display_name} left the game.",
              })

          break

      if self.tournament_name:
        await self.channel_layer.group_discard(
          self.tournament_name,
          self.channel_name
        )

      if hasattr(self, "room_group_name"):
        await self.channel_layer.group_discard(
          self.room_group_name,
          self.channel_name
        )

    await self.close()
###################################################!
