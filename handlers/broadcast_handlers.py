import time
import string
import random
import datetime
import aiofiles
import asyncio
import traceback
import aiofiles.os
from configs import Config
from pyrogram.errors import (
    FloodWait,
    InputUserDeactivated,
    UserIsBlocked,
    PeerIdInvalid
)

broadcast_ids = {}  # Initialize the broadcast_ids dictionary

async def main_broadcast_handler(m, db):
    # Your existing send_msg function
    
    all_users = await db.get_all_users()
    broadcast_msg = m.reply_to_message
    while True:
        broadcast_id = ''.join([random.choice(string.ascii_letters) for i in range(3)])
        if not broadcast_ids.get(broadcast_id):
            break
    out = await m.reply_text(
        text=f"Broadcast Started! You will be notified with a log file when all the users are notified."
    )
    start_time = time.time()
    total_users = await db.total_users_count()
    done = 0
    failed = 0
    success = 0
    broadcast_ids[broadcast_id] = dict(
        total=total_users,
        current=done,
        failed=failed,
        success=success
    )
    async with aiofiles.open('broadcast.txt', 'w') as broadcast_log_file:
        for user in all_users:
            try:
                sts, msg = await send_msg(
                    user_id=int(user['id']),
                    message=broadcast_msg
                )
                if msg is not None:
                    await broadcast_log_file.write(msg)
                if sts == 200:
                    success += 1
                else:
                    failed += 1
                if sts == 400:
                    await db.delete_user(user['id'])
                done += 1
                if broadcast_ids.get(broadcast_id) is None:
                    break
                else:
                    broadcast_ids[broadcast_id].update(
                        dict(
                            current=done,
                            failed=failed,
                            success=success
                        )
                    )
            except Exception as e:
                # Handle exceptions here
                traceback.print_exc()
    if broadcast_ids.get(broadcast_id):
        broadcast_ids.pop(broadcast_id)
    completed_in = datetime.timedelta(seconds=int(time.time() - start_time))
    await asyncio.sleep(3)
    await out.delete()
    if failed == 0:
        await m.reply_text(
            text=f"Broadcast completed in `{completed_in}`\n\nTotal users {total_users}.\nTotal done {done}, {success} success and {failed} failed.",
            quote=True
        )
    else:
        await m.reply_document(
            document='broadcast.txt',
            caption=f"Broadcast completed in `{completed_in}`\n\nTotal users {total_users}.\nTotal done {done}, {success} success and {failed} failed.",
            quote=True
        )
    await aiofiles.os.remove('broadcast.txt')
