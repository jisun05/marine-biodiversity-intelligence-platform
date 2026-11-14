import asyncio
import json

from backend.app.services.worms_service import (
    fetch_worms_taxa,
    resolve_worms_taxon,
)


NAMES = [
    "Thunnus thynnus (Linnaeus, 1758)",
    "Enhydra lutris nereis (Merriam, 1904)",
    "Manta birostris",
    "Balaenoptera musculus brevicauda Ichihara, 1966",
]


async def main():
    for name in NAMES:
        print(f"\n{'=' * 70}")
        print(f"Original name: {name}")

        try:
            records = await fetch_worms_taxa(name)
            resolved = resolve_worms_taxon(records)

            print(f"Records found: {len(records)}")
            print(json.dumps(
                resolved,
                indent=2,
                ensure_ascii=False,
            ))

        except Exception as error:
            print(f"Error: {type(error).__name__}: {error}")


if __name__ == "__main__":
    asyncio.run(main())
