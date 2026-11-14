import asyncio
import json

from backend.app.services.worms_service import (
    fetch_worms_taxa,
)

NAMES = [
    "Megaptera novaeangliae australis",
    "Megaptera novaeangliae kuzira",
]


async def main():
    for name in NAMES:
        print("\n" + "=" * 70)
        print(f"Scientific name: {name}")

        try:
            records = await fetch_worms_taxa(name)

            print(f"Records found: {len(records)}")

            for record in records:
                print(
                    json.dumps(
                        record,
                        indent=2,
                        ensure_ascii=False,
                    )
                )

        except Exception as error:
            print(
                f"Error: {type(error).__name__}: {error}"
            )


if __name__ == "__main__":
    asyncio.run(main())
