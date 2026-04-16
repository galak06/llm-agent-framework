"""Seed prompts from agents/{name}/seeds/prompts.json into the database."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from src.core.config import get_settings
from src.db.engine import create_engine
from src.db.repositories.prompt import PromptRepository


async def seed() -> None:
    settings = get_settings()
    _, session_factory = create_engine(settings)

    agents_dir = Path('agents')
    for agent_dir in agents_dir.iterdir():
        if not agent_dir.is_dir():
            continue
        seeds_file = agent_dir / 'seeds' / 'prompts.json'
        if not seeds_file.exists():
            continue

        prompts = json.loads(seeds_file.read_text())
        agent_name = agent_dir.name

        async with session_factory() as session:
            repo = PromptRepository(session)
            for prompt in prompts:
                await repo.upsert(
                    key=prompt['key'],
                    content=prompt['content'],
                    agent_name=agent_name,
                )
            await session.commit()
            print(f'Seeded {len(prompts)} prompts for agent: {agent_name}')


if __name__ == '__main__':
    asyncio.run(seed())
