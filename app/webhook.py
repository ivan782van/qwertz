from fastapi import APIRouter
from fastapi import Request

router = APIRouter()


@router.post("/webhook")
async def webhook(request: Request):

    payload = await request.json()

    print(payload)

    return {
        "status": "accepted"
    }
