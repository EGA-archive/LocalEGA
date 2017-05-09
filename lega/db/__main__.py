import asyncio
from aiopg.sa import create_engine
import sqlalchemy as sa

from . import CONF

metadata = sa.MetaData()

tbl = sa.Table('tbl', metadata,
               sa.Column('id', sa.Integer, primary_key=True),
               sa.Column('val', sa.String(255)))


async def create_table(engine):
    async with engine.acquire() as conn:
        await conn.execute('DROP TABLE IF EXISTS tbl')
        await conn.execute('''CREATE TABLE tbl (
                                  id serial PRIMARY KEY,
                                  val varchar(255))''')


async def go():
    async with create_engine(user=CONF.get('db','username'),
                             password=CONF.get('db','password'),
                             database=CONF.get('db','dbname'),
                             host=CONF.get('db','host'),
                             port=CONF.getint('db','port')     ) as engine:

        await create_table(engine)
        async with engine.acquire() as conn:
            await conn.execute(tbl.insert().values(val='abc'))

            async for row in conn.execute(tbl.select()):
                print(row.id, row.val)


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(go())

if __name__ == '__main__':
    CONF.setup('--conf ~/.lega/conf.ini')
    main()
