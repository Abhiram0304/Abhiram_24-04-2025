from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from controllers import csv_router, report_router
from database import engine, Base
import uvicorn
from datetime import datetime
import pytz

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(csv_router, prefix="/api", tags=["CSV Upload"])
app.include_router(report_router, prefix="/api", tags=["Reports"])

@app.get("/")
async def root():
    return {"message": "Welcome to the Restaurant Monitoring API"}

now = datetime.now(pytz.UTC)
iso_time = now.isoformat()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True) 