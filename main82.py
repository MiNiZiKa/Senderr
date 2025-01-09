import asyncio
import time

from telethon.tl.types import Message

from .. import loader


@loader.tds
class krmkMod(loader.Module):
    """krmk"""

    strings = {"name": "krmk"}

    async def client_ready(self, client, db):
        """ready"""
        self.db = db
        self.client = client
        self.me = await client.get_me()
        self.thr = db.get("Thr", "thr", {})
        self.thr.setdefault("min", 5)  # Интервал рассылки в минутах
        self.thr.setdefault("cod", "У кого eсть C6 Аяка?")  # Кодовая фраза

    async def red(self, iid):
        """add or remove id"""
        if "chats" in self.thr and iid in self.thr["chats"]:
            self.thr["chats"].remove(iid)
            txt = f"<code>{iid}</code><b> удален</b>"
            if not self.thr["chats"]:
                self.thr.pop("chats")
        elif "chats" in self.thr:
            txt = f"<code>{iid}</code><b> добавлен</b>"
            self.thr["chats"].append(iid)
        else:
            self.thr.setdefault("chats", [iid])
            txt = f"<code>{iid}</code><b> добавлен</b>"
        self.db.set("Thr", "thr", self.thr)
        return txt

    async def thccmd(self, m):
        """кодовая фраза"""
        if len(m.text) < 5:
            return await m.edit(
                f"Фраза для добавления чата в список рассылки: <code>{self.thr['cod']}</code>"
            )
        cmn = m.text.split(" ", 1)[1]
        self.thr["cod"] = cmn
        self.db.set("Thr", "thr", self.thr)
        await m.edit(f"Установлена фраза: <code>{cmn}</code>")

    async def thtcmd(self, m):
        """изменить частоту в минутах"""
        if len(m.text) < 5:
            return await m.edit(f"Отправляет каждые {self.thr['min']} минут")
        cmn = m.text.split(" ", 1)[1]
        if not 0 < int(cmn) < 60:
            return await m.edit("Введите в интервале 1 - 59")
        self.thr["min"] = int(cmn)
        self.db.set("Thr", "thr", self.thr)
        await m.edit(f"Будет отправлять каждые {cmn} минут")

    async def thrcmd(self, m):
        """список чатов"""
        if len(m.text) < 5:
            txt = "Главный: "
            if "main" not in self.thr:
                txt += "не задан\n\nСписок:"
            else:
                txt += f'<code>{self.thr["main"]}</code>\n\nСписок:'
            if "chats" not in self.thr:
                txt += "\n Пусто"
            else:
                for i in self.thr["chats"]:
                    txt += f"\n<code>{i}</code>"
            return await m.edit(txt)
        if "del" in m.text:
            self.thr.clear()
            self.db.set("Thr", "thr", self.thr)
            return await m.edit("Список чатов очищен")
        cmn = m.text.split(" ", 2)[1]
        if cmn == "main":
            iid = int(m.text.split(" ", 2)[2])
            self.thr.setdefault("main", iid)
            self.db.set("Thr", "thr", self.thr)
            txt = f"🤙🏾 Главный: <code>{iid}</code>"
            return await m.edit(txt)
        iid = int(cmn)
        txt = ""
        await m.edit(await self.red(iid))

    async def watcher(self, m: Message):
        """алко"""
        if not hasattr(m, "text") or not isinstance(m, Message):
            return
        if self.thr["cod"] in m.text and m.sender_id == self.me.id:
            iid = m.chat_id
            await self.client.send_message("me", await self.red(iid))
        
        # Проверка на то, что чат находится в списке
        if (
            "chats" not in self.thr
            or m.chat_id not in self.thr["chats"]
            or m.sender_id == self.me.id
        ):
            return

        # Получение текущего времени в секундах
        current_time = time.time()

        # Если чат ещё не имеет времени последней рассылки, сохраняем время
        if m.chat_id not in self.thr:
            self.thr[m.chat_id] = current_time - (self.thr["min"] * 60)  # Отправка учитывает минуточный интервал

        last_sent_time = self.thr[m.chat_id]

        # Проверка, если время прошло меньше, чем интервал в минутах
        if current_time - last_sent_time < self.thr["min"] * 60:
            return  # Не отправляем сообщение, если интервал не прошел

        # Обновление времени последней отправки сообщения
        self.thr[m.chat_id] = current_time

        try:
            p = await self.client.get_messages(self.thr["main"], limit=100)
        except Exception:
            return

        if p.total < 2:
            return  # Если сообщений недостаточно, не отправляем

        # Выбираем случайное сообщение из списка
        p = p[random.randint(0, p.total - 2)]

        # Определение чатов для рассылки
        if random.randint(0, 42) == 3:
            cc = self.thr["chats"]
        else:
            cc = [m.chat_id]  # Отправка только в текущий чат

        # Отправка сообщений
        for i in cc:
            try:
                if p.media:
                    await self.client.send_file(i, p, caption=p.text)
                else:
                    await self.client.send_message(i, p.text)
            except Exception:
                continue
