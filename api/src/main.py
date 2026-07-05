from api.src.core import VpnService
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import dotenv

dotenv.load_dotenv()
app = FastAPI()
vpn_service = VpnService(os.getenv("CONFIG_PATH"), os.getenv("DB_PATH"))

class UserRegistration(BaseModel):
    username: str
    telegram_id: str
    
@app.get("/user/{telegram_id}")
def get_user_info(telegram_id: str):
    '''API endpoint to retrieve user information based on Telegram ID.'''
    user_info = vpn_service.get_user_info(telegram_id)
    return user_info

@app.post("/register")
def register_user(user: UserRegistration):
    '''API endpoint to register a new user.'''
    try:
        uuid = vpn_service.register_new_user(user.username, user.telegram_id)
        return {"message": "User registered successfully", "uuid": uuid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@app.post("/invite")
def generate_invite_code():
    '''API endpoint to generate a new invite code.'''
    try:
        code = vpn_service.generate_invite_code()
        return {"message": "Invite code generated successfully", "code": code}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
@app.post("/invite/{code}/use")
def use_invite_code(code: str):
    '''API endpoint to mark an invite code as used.'''
    try:
        vpn_service.mark_code_as_used(code)
        return {"message": "Invite code marked as used"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@app.get("/get_config/{telegram_id}")
def get_user_link(telegram_id: str, username: str, inbound_index: int):
    '''API endpoint to retrieve the VPN configuration link for a user based on Telegram ID and inbound index.'''
    try:
        link = vpn_service.get_user_config(telegram_id, username, inbound_index)
        return {"link": link}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@app.get("/vnstat/daily")
def get_daily_usage():
    '''API endpoint to retrieve daily network usage statistics.'''
    try:
        usage = vpn_service.vnstat_daily_usage()
        return {"daily_usage": usage}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
@app.get("/vnstat/monthly")
def get_monthly_usage():
    '''API endpoint to retrieve monthly network usage statistics.'''
    try:
        usage = vpn_service.vnstat_monthly_usage()
        return {"monthly_usage": usage}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
@app.get("/users")
def get_all_users():
    '''API endpoint to retrieve a list of all users.'''
    try:
        users = vpn_service.get_all_users()
        return {"users": users}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@app.post("/restart")
def restart_service():
    '''API endpoint to restart the VPN service.'''
    try:
        vpn_service.restart_service()
        return {"message": "VPN service restarted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
@app.post("/reset_all_traffic")
def reset_all_traffic_usage():
    '''API endpoint to reset traffic usage for all users.'''
    try:
        vpn_service.reset_all_traffic_usage()
        return {"message": "All users' traffic usage has been reset"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
@app.post("/update_traffic_usage")
def update_traffic_usage():
    '''API endpoint to update traffic usage for all users.'''
    try:
        vpn_service.update_traffic_usage()
        return {"message": "Traffic usage updated for all users"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))