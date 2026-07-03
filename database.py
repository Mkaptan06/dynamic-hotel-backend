import os
from dotenv import load_dotenv
import aiomysql  

load_dotenv()


db_pool = None


async def asenkron_havuz_baslat():
    global db_pool
    if db_pool is None:
        db_pool = await aiomysql.create_pool(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            db=os.getenv("DB_NAME"),
            minsize=1,
            maxsize=5,
            autocommit=True
        )


async def asenkron_havuz_kapat():
    global db_pool
    if db_pool:
        db_pool.close()
        await db_pool.wait_closed()


def veri_tabani_havuzu_getir():
    return db_pool