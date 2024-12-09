import asyncio
from data.orca_pipeline import OrcaPipeline

async def main():
    pipeline = OrcaPipeline()
    await pipeline.start_pipeline()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nPipeline stopped by user") 